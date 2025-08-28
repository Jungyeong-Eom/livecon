import socket
import json
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def insert_sensor_data(conn, data):
    with conn.cursor() as cursor:
        sql = """
        INSERT INTO alarm_log (device_id, alarm_type, alarm_time, details)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (
            data.get('device_id'),
            data.get('alarm_type'),
            data.get('alarm_time'),
            data.get('details')
        ))
    conn.commit()


HOST = '0.0.0.0'  # 모든 인터페이스에서 접속 대기
PORT = 12345  # 원하는 포트번호

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"서버 시작 - {HOST}:{PORT}")

    while True:
        conn_sock, addr = s.accept()
        print(f"클라이언트 연결됨: {addr}")
        with conn_sock:
            data_bytes = b''
            while True:
                chunk = conn_sock.recv(4096)
                if not chunk:
                    break
                data_bytes += chunk

            try:
                data_str = data_bytes.decode()
                data_json = json.loads(data_str)
                print("받은 데이터:", data_json)

                db_conn = get_connection()
                insert_sensor_data(db_conn, data_json)
                db_conn.close()

                conn_sock.sendall(b"OK")
            except Exception as e:
                print("처리 중 에러:", e)
                conn_sock.sendall(b"ERROR")
