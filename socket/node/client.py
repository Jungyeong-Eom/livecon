import socket
import time
from modules.rsa_utils import load_public_key, encrypt
from modules.generate_packet import generate_random_packet

SERVER_ADDRESS = 'localhost'
SERVER_PORT = 12346
PUBLIC_KEY_PATH = 'node/public.pem'

# 공개 키 로드
public_key = load_public_key(PUBLIC_KEY_PATH)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_ADDRESS, SERVER_PORT))

try:
    while True:  # 5번 반복 전송
        packet = generate_random_packet()
        encrypted_packet = encrypt(packet, public_key)
        client_socket.sendall(encrypted_packet)
        print(f"암호화된 패킷 전송 완료 (길이: {len(encrypted_packet)} 바이트)")
        time.sleep(2)
except KeyboardInterrupt:
    client_socket.close()
    print("\n클라이언트 종료 요청됨")
finally:
    client_socket.close()
