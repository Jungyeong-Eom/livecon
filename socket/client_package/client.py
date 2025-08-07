import sys
import os
import socket
import time
import json

# 현재 디렉토리를 Python 경로에 추가 (독립 패키지용)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from node_module.rsa_utils import load_public_key, encrypt
from node_module.generate_packet import generate_random_packet
from Crypto.PublicKey import RSA 

def request_public_key_from_server(server_address, server_port):
    """서버에서 공개키를 요청하여 메모리에 로드"""
    print(f"서버에서 공개키 요청 중: {server_address}:{server_port}")
    
    try:
        # 서버에 연결
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_socket.settimeout(30)  # 30초 타임아웃
        temp_socket.connect((server_address, server_port))
        
        # 공개키 요청
        temp_socket.sendall(b"REQUEST_PUBLIC_KEY")
        
        # 공개키 크기 수신 (4바이트)
        key_size_bytes = temp_socket.recv(4)
        if len(key_size_bytes) != 4:
            raise Exception("공개키 크기 정보 수신 실패")
        
        key_size = int.from_bytes(key_size_bytes, 'big')
        print(f"공개키 크기: {key_size} 바이트")
        
        # 공개키 데이터 수신
        public_key_data = b""
        while len(public_key_data) < key_size:
            chunk = temp_socket.recv(key_size - len(public_key_data))
            if not chunk:
                raise Exception("공개키 데이터 수신 중단")
            public_key_data += chunk
        
        temp_socket.close()
        
        # RSA 키 객체로 변환
        public_key = RSA.import_key(public_key_data)
        print("서버에서 공개키 수신 성공")
        return public_key
        
    except socket.timeout:
        print("오류: 서버 응답 타임아웃")
        return None
    except ConnectionRefusedError:
        print("오류: 서버에 연결할 수 없습니다")
        return None
    except Exception as e:
        print(f"공개키 요청 실패: {e}")
        return None

def load_config():
    """설정 파일 로드"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    
    # 기본 설정
    default_config = {
        "server": {
            "address": "localhost", 
            "port": 12351
        },
        "client": {
            "sensor_id": "SENSOR_001",
            "send_interval": 10,
            "public_key_path": "public.pem"
        }
    }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"설정 파일 로드 성공: {config_path}")
        return config
    except FileNotFoundError:
        print(f"설정 파일이 없습니다. 기본 설정을 사용합니다: {config_path}")
        # 기본 설정 파일 생성
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        print(f"기본 설정 파일을 생성했습니다: {config_path}")
        return default_config
    except json.JSONDecodeError as e:
        print(f"설정 파일 파싱 오류: {e}")
        print("기본 설정을 사용합니다.")
        return default_config

# 설정 로드
config = load_config()
SERVER_ADDRESS = config['server']['address']
SERVER_PORT = config['server']['port']
SENSOR_ID = config['client']['sensor_id']
SEND_INTERVAL = config['client']['send_interval']
PUBLIC_KEY_PATH = config['client']['public_key_path']

print(f"서버 설정: {SERVER_ADDRESS}:{SERVER_PORT}")
print(f"센서 ID: {SENSOR_ID}")
print(f"전송 간격: {SEND_INTERVAL}초")

# 서버의 공개키 로드 (파일 우선, 실패 시 네트워크에서 요청)
public_key = None

# 1. 로컬 파일에서 공개키 로드 시도
print(f"로컬 공개키 파일 확인: {PUBLIC_KEY_PATH}")
try:
    public_key = load_public_key(PUBLIC_KEY_PATH)
    print("로컬 공개키 파일 로드 성공")
except FileNotFoundError:
    print("로컬 공개키 파일이 없습니다. 서버에서 요청합니다.")
    
    # 2. 서버에서 공개키 요청
    public_key = request_public_key_from_server(SERVER_ADDRESS, SERVER_PORT)
    
    if public_key is None:
        print("오류: 공개키를 가져올 수 없습니다.")
        print("해결 방법:")
        print("1. 서버가 실행 중인지 확인")
        print("2. 서버 주소와 포트가 올바른지 확인")
        print("3. 또는 서버의 public.pem 파일을 수동으로 복사")
        sys.exit(1)
    
    # 3. 네트워크에서 받은 공개키를 로컬에 저장 (선택사항)
    try:
        with open(PUBLIC_KEY_PATH, 'wb') as f:
            f.write(public_key.export_key())
        print(f"공개키를 로컬에 저장했습니다: {PUBLIC_KEY_PATH}")
    except Exception as e:
        print(f"공개키 로컬 저장 실패 (무시됨): {e}")

print("공개키 준비 완료")

print(f"서버 연결 시도: {SERVER_ADDRESS}:{SERVER_PORT}")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_ADDRESS, SERVER_PORT))
print("서버 연결 성공")

try:
    while True:  
        packet = generate_random_packet()
        encrypted_packet = encrypt(packet, public_key)
        client_socket.sendall(encrypted_packet)
        print(f"암호화된 패킷 전송 완료 (길이: {len(encrypted_packet)} 바이트)")
        time.sleep(SEND_INTERVAL)
except KeyboardInterrupt:
    client_socket.close()
    print("\n클라이언트 종료 요청됨")
finally:
    client_socket.close()
