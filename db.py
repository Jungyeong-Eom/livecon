import os
import pymysql
from dotenv import load_dotenv

# 1. .env 불러오기
load_dotenv()

# 2. DB 연결 함수
def get_connection():
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn

# 3. 모든 테이블 내용 불러오기
if __name__ == "__main__":
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # 데이터베이스 내 모든 테이블 목록 조회
            cursor.execute("SHOW TABLES;")
            tables = [list(t.values())[0] for t in cursor.fetchall()]

            print(f"✅ 총 {len(tables)}개의 테이블 발견: {tables}\n")

            # 각 테이블 데이터 출력
            for table in tables:
                print(f"📌 {table} 테이블 데이터:")
                cursor.execute(f"SELECT * FROM {table};")
                rows = cursor.fetchall()
                if rows:
                    for row in rows:
                        print(row)
                else:
                    print("⚠ 데이터 없음")
                print("-" * 50)

    except Exception as e:
        print("❌ DB 연결 또는 데이터 불러오기 실패:", e)
    finally:
        conn.close()
