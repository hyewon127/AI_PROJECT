import os
import io
import base64
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from config import config
from database import DatabaseManager
from PIL import Image
import ollama
import openai
import uvicorn

app = FastAPI()

# 모든 Origin, Method, Header 허용 (가이드 준수)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dbManager = DatabaseManager()

# 서버 시작 시 실행되는 이벤트
@app.on_event("startup")
async def startupEvent():
    """ 서버 시작 시 DB와 테이블을 자동으로 생성 및 초기화합니다. """
    print("------------------------------------------")
    print("시스템 초기화를 시작합니다...")
    initResult = dbManager.initializeDb()
    if initResult["success"]:
        print("모든 DB 환경이 정상적으로 준비되었습니다.")
    else:
        print(f"시스템 초기화 실패: {initResult['message']}")
    print("------------------------------------------")

def analyzeWithGemma(imageBytes, userQuestion):
    """ Ollama gemma4:e2b 모델을 사용한 이미지 분석 """
    try:
        modelName = config.ollamaModel
        response = ollama.generate(
            model=modelName,
            prompt=userQuestion,
            images=[imageBytes]
        )
        return response['response']
    except Exception as e:
        raise e

def analyzeWithGpt(imageBytes, userQuestion):
    """ OpenAI GPT-4o 모델을 사용한 이미지 분석 """
    try:
        client = openai.OpenAI(api_key=config.openaiApiKey)
        base64Image = base64.b64encode(imageBytes).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": userQuestion},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64Image}"}}
                    ],
                }
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        raise e   

@app.post("/analyze")
async def analyzeImage(uploadFile: UploadFile = File(...), userQuestion: str = Form(...)):
    """ 이미지 업로드 및 모델 기반 질문 답변 API """
    try:
        imageData = await uploadFile.read()
        
        # 데이터셋 저장 폴더 체크
        targetDir = "dataset"
        rootFiles = os.listdir(".")
        isDirExist = False
        for i in range(0, len(rootFiles)):
            if rootFiles[i] == targetDir:
                isDirExist = True
                break
        
        if isDirExist == False:
            os.makedirs(targetDir)
            
        fileName = uploadFile.filename
        savePath = os.path.join(targetDir, fileName)
        
        with open(savePath, "wb") as f:
            f.write(imageData)
            
        # 모델 분석 로직
        activeModel = config.useModel
        resultText = ""
        
        if activeModel == "OLLAMA":
            resultText = analyzeWithGemma(imageData, userQuestion)
        elif activeModel == "GPT":
            resultText = analyzeWithGpt(imageData, userQuestion)
        else:
            return {"success": False, "message": "잘못된 모델 설정입니다."}
            
        # 결과 DB 저장
        insertQuery = "INSERT INTO image_analysis (fileName, question, answer) VALUES (%s, %s, %s)"
        dbResult = dbManager.executeQuery(insertQuery, (fileName, userQuestion, resultText))
        
        if dbResult["success"]:
            return {"success": True, "result": resultText}
        else:
            return {"success": False, "message": f"DB 저장 실패: {dbResult['message']}"}
        
    except Exception as e:
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
