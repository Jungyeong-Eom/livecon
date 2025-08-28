import socket
import threading
import json
from datetime import datetime
from server_module import parsing, rsa_utils, sql_utils  # 이미 만든 서버 모듈 그대로

HOST = '127.0.0.1'
PORT = 9999

def handle_client(conn, addr):
    print(f"[연결됨] {addr}")
    try:
        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                message = data.decode('utf-8').strip()
                print(f"[수신] {message[:100]}...")  # 일부만 출력
                # 여기에 parsing + DB insert 적용 가능
                parsed = parsing.parse_packet(message)
                sql_utils.insert_sensor_results(parsed)
                conn.sendall(b"ACK\n")
    except Exception as e:
        print(f"[오류] {e}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[서버 시작] {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[스레드 생성] 클라이언트 {addr}")

if __name__ == "__main__":
    start_server()
