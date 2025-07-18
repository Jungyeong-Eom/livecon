import socket
import threading
from modules.rsa_utils import load_private_key, decrypt, generate_and_save_keys
from modules import parsing

# RSA 키 생성 및 저장
generate_and_save_keys()

private_key = load_private_key("private.pem")
HOST = 'localhost'
PORT = 12346

# 클라이언트 연결 처리 함수
# 클라이언트로부터 암호화된 데이터를 수신하고 복호화하여 패킷을 파싱
def handle_client(client_socket, client_address):
    print(f"클라이언트 {client_address} 연결됨")
    client_socket.settimeout(10)

    # 클라이언트로부터 암호화 된 데이터 수신
    try:
        while True:
            encrypted = client_socket.recv(1024)
            # 암호화된 패킷인지 확인
            if not encrypted:
                print(f"{client_address} 연결 종료 요청")
                break
            # 복호화
            try:
                decrypted_data = decrypt(encrypted, private_key)
            except Exception as e:
                print(f"복호화 실패 from {client_address}: {e}")
                continue

            # 패킷 파싱 시도
            try:
                parsed = parsing.parse_packet(decrypted_data)
                if parsed:
                    print(f"[{client_address}] → ID: {parsed['ID']}, TEMP: {parsed['TEMP']}°C, "
                          f"O2: {parsed['O2']}ppm, WTR_TEMP: {parsed['WTR_TEMP']}°C, "
                          f"LOC: {parsed['LOC']}, TIME: {parsed['TIME']}, CHK: {parsed['CHK']}")
                else:
                    print(f"[{client_address}] 유효하지 않은 패킷")
            except Exception as e:
                print(f"[{client_address}] 파싱 오류: {e}")

    except socket.timeout:
        print(f"[{client_address}] 연결 타임아웃")

    finally:
        client_socket.close()
        print(f"연결 종료: {client_address}\n")
        
# 서버 소켓을 생성하고 클라이언트와 연결
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"서버가 {HOST}:{PORT}에서 클라이언트 대기 중")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n서버 종료 요청됨")
    finally:
        server_socket.close()
        print("서버 소켓 닫힘")

if __name__ == "__main__":
    start_server()
