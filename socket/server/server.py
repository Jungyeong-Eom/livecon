import sys
import os
import socket
import threading

# 현재 파일의 디렉토리에서 상위 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from server_module.rsa_utils import generate_and_save_keys, load_private_key, decrypt
from server_module import parsing
from server_module.sql_utils import connect_to_database, database_query, select_query, insert_sensor_results

class LiveConServer:
    def __init__(self, host='localhost', port=12346, callback_handler=None, skip_db_validation=False):
        self.host = host
        self.port = port
        self.callback_handler = callback_handler
        self.skip_db_validation = skip_db_validation  # 데이터베이스 검증 우회 옵션
        self.running = False
        self.server_socket = None
        self.private_key = None
        self.connected_clients = set()
        
    def initialize_keys(self):
        """RSA 키 생성 및 로드"""
        try:
            # 현재 실행 위치에 관계없이 올바른 경로 설정
            if os.path.basename(os.getcwd()) == 'server':
                # server 디렉토리에서 실행 중
                private_key_path = "private.pem"
                public_key_path = "../node/public.pem"
            else:
                # 루트 디렉토리에서 실행 중
                private_key_path = "server/private.pem"
                public_key_path = "node/public.pem"
            
            generate_and_save_keys(private_key_path, public_key_path)
            self.private_key = load_private_key(private_key_path)
            self._log(f"RSA 키 로드 완료")
            return True
        except Exception as e:
            self._log(f"RSA 키 초기화 실패: {e}")
            return False
    
    def start(self):
        """서버 시작"""
        if not self.initialize_keys():
            return False
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(1.0)  # accept에 1초 타임아웃 설정
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            self._log(f"서버가 {self.host}:{self.port}에서 시작되었습니다")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self._log(f"클라이언트 연결 수락됨: {client_address}")
                    
                    if not self.running:
                        client_socket.close()
                        break
                        
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    # 타임아웃은 정상적인 상황 - 계속 대기
                    continue
                except socket.error as e:
                    if self.running:
                        self._log(f"클라이언트 연결 수락 오류: {e}")
                        
        except Exception as e:
            self._log(f"서버 시작 실패: {e}")
            return False
        finally:
            self._cleanup()
            
        return True
    
    def stop(self):
        """서버 중지"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self._log("서버 중지 요청됨")
    
    def _handle_client(self, client_socket, client_address):
        """클라이언트 연결 처리"""
        client_addr_str = f"{client_address[0]}:{client_address[1]}"
        self.connected_clients.add(client_addr_str)
        self._on_client_connected(client_addr_str)
        
        client_socket.settimeout(10)
        
        try:
            while self.running:
                encrypted = client_socket.recv(1024)
                if not encrypted:
                    self._log(f"[{client_addr_str}] 연결 종료 요청")
                    break
                    
                try:
                    # 복호화
                    decrypted_data = decrypt(encrypted, self.private_key)
                    
                    # 패킷 파싱
                    parsed = parsing.parse_packet(decrypted_data)
                    if parsed:
                        self._log(f"[{client_addr_str}] 센서 데이터 수신 - ID: {parsed['ID']}, 온도: {parsed['TEMP']}°C")
                        
                        # 센서 ID 확인
                        if not self.skip_db_validation:
                            validation_result = self._validate_sensor_id(parsed['ID'], client_addr_str)
                            if not validation_result:
                                self._log(f"[{client_addr_str}] 센서 ID 검증 실패, 연결 종료")
                                break
                        
                        # GUI에 데이터 전달
                        self._on_data_received(parsed, client_addr_str)
                        
                        # 데이터베이스 저장 시도 (옵션)
                        if not self.skip_db_validation:
                            try:
                                result = database_query(insert_sensor_results(parsed))
                                if result is not None:
                                    self._log(f"[{client_addr_str}] 데이터베이스 저장 성공")
                                else:
                                    self._log(f"[{client_addr_str}] 데이터베이스 저장 실패")
                            except Exception as db_e:
                                self._log(f"[{client_addr_str}] 데이터베이스 오류: {db_e}")
                            
                    else:
                        self._log(f"[{client_addr_str}] 패킷 파싱 실패")
                        
                except Exception as e:
                    self._log(f"[{client_addr_str}] 패킷 처리 오류: {e}")
                    
        except socket.timeout:
            self._log(f"[{client_addr_str}] 연결 타임아웃")
        except Exception as e:
            self._log(f"[{client_addr_str}] 연결 오류: {e}")
        finally:
            client_socket.close()
            self.connected_clients.discard(client_addr_str)
            self._on_client_disconnected(client_addr_str)
    
    def _validate_sensor_id(self, sensor_id, client_addr_str):
        """센서 ID 유효성 검사"""
        try:
            rows = select_query("SELECT sensor_id FROM sensor_info")
            if rows is None:
                self._log(f"[{client_addr_str}] 데이터베이스 조회 실패")
                return False
                
            sensor_ids = [row['sensor_id'] for row in rows]
            if sensor_id not in sensor_ids:
                self._log(f"[{client_addr_str}] 등록되지 않은 센서 ID: {sensor_id}")
                return False
                
            return True
        except Exception as e:
            self._log(f"[{client_addr_str}] 센서 ID 검증 오류: {e}")
            return False
    
    def _cleanup(self):
        """정리 작업"""
        self.connected_clients.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self._log("서버 정리 완료")
    
    def _log(self, message):
        """로그 출력"""
        if self.callback_handler and hasattr(self.callback_handler, 'on_log'):
            self.callback_handler.on_log(message)
        else:
            print(message)
    
    def _on_client_connected(self, client_addr):
        """클라이언트 연결 콜백"""
        self._log(f"클라이언트 연결: {client_addr}")
        if self.callback_handler and hasattr(self.callback_handler, 'on_client_connected'):
            self.callback_handler.on_client_connected(client_addr)
    
    def _on_client_disconnected(self, client_addr):
        """클라이언트 연결 해제 콜백"""
        self._log(f"클라이언트 연결 해제: {client_addr}")
        if self.callback_handler and hasattr(self.callback_handler, 'on_client_disconnected'):
            self.callback_handler.on_client_disconnected(client_addr)
    
    def _on_data_received(self, data, client_addr):
        """데이터 수신 콜백"""
        if self.callback_handler and hasattr(self.callback_handler, 'on_data_received'):
            self.callback_handler.on_data_received(data, client_addr)
        else:
            # 기본 콘솔 출력
            print(f"클라이언트 주소: [{client_addr}]\nID: {data['ID']}\nTEMP: {data['TEMP']}°C\n"
                  f"DO: {data['DO']}ppm\nWTR_TEMP: {data['WTR_TEMP']}°C\n"
                  f"위치: {data['LOC']}\n시간: {data['TIME']}\nCHK: {data['CHK']}\n")
    
    def get_connected_clients(self):
        """연결된 클라이언트 목록 반환"""
        return list(self.connected_clients)
    
    def is_running(self):
        """서버 실행 상태 반환"""
        return self.running

# 콘솔 모드로 실행할 때의 기본 서버
def start_console_server():
    """콘솔 모드 서버 시작"""
    server = LiveConServer()
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n서버 종료 요청됨")
        server.stop()

if __name__ == "__main__":
    start_console_server()
