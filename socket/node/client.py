import sys
import os
import socket
import time

# 현재 파일의 디렉토리에서 상위 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from node_module.rsa_utils import load_public_key, encrypt
from node_module.generate_packet import generate_random_packet 

SERVER_ADDRESS = 'localhost'
SERVER_PORT = 12347

# 현재 실행 위치에 관계없이 올바른 경로 설정
if os.path.basename(os.getcwd()) == 'node':
    # node 디렉토리에서 실행 중
    PUBLIC_KEY_PATH = 'public.pem'
else:
    # 루트 디렉토리에서 실행 중
    PUBLIC_KEY_PATH = 'node/public.pem'

# 공개 키 로드
public_key = load_public_key(PUBLIC_KEY_PATH)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_ADDRESS, SERVER_PORT))

try:
    while True:  
        packet = generate_random_packet()
        encrypted_packet = encrypt(packet, public_key)
        client_socket.sendall(encrypted_packet)
        print(f"암호화된 패킷 전송 완료 (길이: {len(encrypted_packet)} 바이트)")
        time.sleep(10)
except KeyboardInterrupt:
    client_socket.close()
    print("\n클라이언트 종료 요청됨")
finally:
    client_socket.close()
