# pip install pymysql python-dotenv
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """ MySQL 데이터베이스 연동 및 쿼리 관리 클래스 """
    
    def __init__(self):
        """ DB 연결 설정 초기화 """
        try:
            self.host = os.getenv("DB_HOST")
            self.user = os.getenv("DB_USER")
            self.password = os.getenv("DB_PASSWORD")
            self.database = os.getenv("DB_NAME")
            self.connection = None
        except Exception as e:
            print(f"Init Error: {str(e)}")

    def connectDb(self):
        """ 데이터베이스에 연결 """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            return False

    def executeQuery(self, query, params=None):
        """ 쿼리 실행 함수 (INSERT, UPDATE, DELETE) """
        try:
            if self.connection is None:
                self.connectDb()
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return {"success": True, "message": "Success"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def fetchAll(self, query, params=None):
        """ 데이터 조회 함수 (SELECT) """
        try:
            if self.connection is None:
                self.connectDb()
                
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                
                # 명시적 반복문 사용 예시 (가이드 준수: for i in range(0, len(obj)))
                processedData = []
                for i in range(0, len(result)):
                    processedData.append(result[i])
                    
                return {"success": True, "data": processedData}
        except Exception as e:
            return {"success": False, "message": str(e)}
