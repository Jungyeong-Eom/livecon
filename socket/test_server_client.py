#!/usr/bin/env python3
"""
서버-클라이언트 통합 테스트 스크립트
GUI 없이 콜백 시스템이 제대로 작동하는지 확인
"""

import sys
import os
import time
import threading
import socket

# 경로 설정
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from server.server import LiveConServer
from node_module.rsa_utils import load_public_key, encrypt
from node_module.generate_packet import generate_random_packet

class TestCallbackHandler:
    """테스트용 콜백 핸들러"""
    def __init__(self):
        self.received_data = []
        self.connected_clients = []
        self.logs = []
    
    def on_log(self, message):
        print(f"[LOG] {message}")
        self.logs.append(message)
    
    def on_client_connected(self, client_addr):
        print(f"[EVENT] 클라이언트 연결: {client_addr}")
        self.connected_clients.append(client_addr)
    
    def on_client_disconnected(self, client_addr):
        print(f"[EVENT] 클라이언트 연결 해제: {client_addr}")
        if client_addr in self.connected_clients:
            self.connected_clients.remove(client_addr)
    
    def on_data_received(self, data, client_addr):
        print(f"[DATA] {client_addr}에서 데이터 수신:")
        print(f"  - 센서 ID: {data['ID']}")
        print(f"  - 온도: {data['TEMP']}°C")
        print(f"  - 용존산소: {data['DO']}ppm")
        print(f"  - 수온: {data['WTR_TEMP']}°C")
        print(f"  - 위치: {data['LOC']}")
        print(f"  - 시간: {data['TIME']}")
        self.received_data.append(data)

def test_server_client():
    """서버-클라이언트 통합 테스트"""
    print("=== 서버-클라이언트 통합 테스트 시작 ===")
    
    # 테스트 핸들러 생성
    handler = TestCallbackHandler()
    
    # 서버 시작
    print("1. 서버 시작 중...")
    server = LiveConServer(host='127.0.0.1', port=12347, callback_handler=handler, skip_db_validation=True)
    
    def start_server():
        try:
            server.start()
        except Exception as e:
            print(f"서버 시작 오류: {e}")
    
    server_thread = threading.Thread(target=start_server, daemon=False)  # daemon=False로 변경
    server_thread.start()
    
    # 서버 시작 대기 (더 오래)
    print("   서버 초기화 대기 중...")
    time.sleep(3)
    
    # 클라이언트 테스트
    print("2. 클라이언트 테스트 시작...")
    
    try:
        # 패킷 생성 및 암호화
        packet = generate_random_packet()
        public_key = load_public_key('node/public.pem')
        encrypted_packet = encrypt(packet, public_key)
        
        print(f"   패킷 생성 완료: {len(packet)} 바이트 -> {len(encrypted_packet)} 바이트 (암호화)")
        
        # 서버에 연결하여 패킷 전송
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("   서버에 연결 중...")
        client_socket.connect(('127.0.0.1', 12347))
        print("   서버 연결 성공")
        
        client_socket.sendall(encrypted_packet)
        print("   패킷 전송 완료")
        
        # 서버 처리 대기 (더 오래)
        print("   서버 처리 대기 중...")
        time.sleep(5)
        
        client_socket.close()
        print("   클라이언트 연결 종료")
        
        # 결과 확인
        time.sleep(1)
        
        print("3. 테스트 결과:")
        print(f"   - 로그 메시지 수: {len(handler.logs)}")
        print(f"   - 수신된 데이터 수: {len(handler.received_data)}")
        print(f"   - 연결된 클라이언트 수: {len(handler.connected_clients)}")
        
        if handler.received_data:
            print("   ✅ 데이터 수신 성공!")
            for i, data in enumerate(handler.received_data):
                print(f"      데이터 {i+1}: 센서 ID {data['ID']}, 온도 {data['TEMP']}°C")
        else:
            print("   ❌ 데이터 수신 실패")
            
        print("\n최근 로그 메시지:")
        for log in handler.logs[-5:]:
            print(f"   {log}")
            
    except Exception as e:
        print(f"   ❌ 클라이언트 오류: {e}")
    
    finally:
        print("4. 서버 종료...")
        server.stop()
        time.sleep(1)
        
    print("=== 테스트 완료 ===")

if __name__ == "__main__":
    test_server_client()