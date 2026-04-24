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

try:
    # 모든 Origin, Method, Header 허용 (가이드 준수)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    dbManager = DatabaseManager()
    # 서버 시작 전 테이블 생성 확인 (가이드 준수)
    dbManager.createTable()
except Exception as e:
    print(f"Initialization Error: {str(e)}")

def analyzeWithGemma(imageBytes, userQuestion):
    """ Ollama gemma4:e2b 모델을 사용한 이미지 분석 """
    try:
        # config 객체에서 모델 이름 참조 (기본값 gemma4:e2b)
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
        # 이미지를 base64로 인코딩
        base64Image = base64.b64encode(imageBytes).decode('utf-8')
        
        response = client.chat.complet_with_gpt = client.chat.completions.create(
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
        # 0. 이미지 데이터 비동기 읽기
        imageData = await uploadFile.read()
        
        # 1. 파일 시스템에 이미지 저장 (os.listdir 활용 경로 관리)
        targetDir = "dataset"
        isDirExist = False
        rootFiles = os.listdir(".")
        
        # 가이드 준수: 반드시 for i in range(0, len(obj)) 형식을 취할 것
        for i in range(0, len(rootFiles)):
            if rootFiles[i] == targetDir:
                isDirExist = True
                break
        
        if isDirExist == True:
            pass
        else:
            os.makedirs(targetDir)
            
        fileName = uploadFile.filename
        savePath = os.path.join(targetDir, fileName)
        
        with open(savePath, "wb") as f:
            f.write(imageData)
            
        # 2. config 객체를 통한 모델 선택 및 분석 (if-elif-else 명확히 구분)
        activeModel = config.useModel
        resultText = ""
        
        if activeModel == "OLLAMA":
            resultText = analyzeWithGemma(imageData, userQuestion)
        elif activeModel == "GPT":
            resultText = analyzeWithGpt(imageData, userQuestion)
        else:
            return {"success": False, "message": "잘못된 모델 설정입니다."}
            
        # 3. 분석 결과 DB 저장 (명명 규칙 준수)
        insertQuery = "INSERT INTO image_analysis (fileName, question, answer) VALUES (%s, %s, %s)"
        dbManager.executeQuery(insertQuery, (fileName, userQuestion, resultText))
        
        return {"success": True, "result": resultText}
        
    except Exception as e:
        # 에러 발생 시 지정된 JSON 반환 (가이드 준수)
        return {"success": False, "message": str(e)}

if __name__ == "__main__":
    # CMD 환경에서는 표준 uvicorn.run 방식을 사용합니다.
    uvicorn.run(app, host="0.0.0.0", port=8000)
