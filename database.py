# pip install pymysql python-dotenv
import pymysql
from config import config

class DatabaseManager:
    """ MySQL 데이터베이스 및 테이블을 자동으로 생성하고 관리하는 클래스 """
    
    def __init__(self):
        """ DB 연결 설정 초기화 (config 객체 사용) """
        try:
            self.host = config.dbHost
            self.port = config.dbPort
            self.user = config.dbUser
            self.password = config.dbPassword
            self.database = config.dbName
            self.connection = None
        except Exception as e:
            print(f"Init Error: {str(e)}")

    def initializeDb(self):
        """ 데이터베이스와 테이블이 없으면 자동으로 생성하는 통합 함수 """
        try:
            # 1. 먼저 데이터베이스 자체를 생성 (DB 지정 없이 연결)
            tempConn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            tempConn.cursor().execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            tempConn.commit()
            tempConn.close()
            print(f"Database 확인 완료: {self.database}")

            # 2. 실제 데이터베이스에 연결
            self.connectDb()

            # 3. 테이블 생성 실행
            self.createTable()
            return {"success": True, "message": "DB 및 테이블 초기화 성공"}
        except Exception as e:
            print(f"Initialization Error: {str(e)}")
            return {"success": False, "message": str(e)}

    def connectDb(self):
        """ 데이터베이스에 실제 연결을 수행 """
        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            print(f"Connection Error: {str(e)}")
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

    def createTable(self):
        """ 이미지 분석 결과를 저장할 테이블이 없으면 생성 """
        try:
            query = """
            CREATE TABLE IF NOT EXISTS image_analysis (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fileName VARCHAR(255),
                question TEXT,
                answer TEXT,
                createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            result = self.executeQuery(query)
            if result["success"]:
                print("Table 확인 완료: image_analysis")
            return result
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
                
                processedData = []
                for i in range(0, len(result)):
                    processedData.append(result[i])
                    
                return {"success": True, "data": processedData}
        except Exception as e:
            return {"success": False, "message": str(e)}
