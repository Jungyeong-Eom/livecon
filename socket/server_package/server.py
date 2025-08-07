import sys
import os
import socket
import threading
import signal
import atexit

# 현재 디렉토리를 Python 경로에 추가 (독립 패키지용)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from server_module.rsa_utils import generate_server_keys, generate_and_save_keys, load_private_key, decrypt
from server_module import parsing
from server_module.sql_utils import connect_to_database, database_query, select_query, insert_sensor_results

class LiveConServer:
    def __init__(self, host='localhost', port=12351):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.private_key = None
        self.connected_clients = set()
        
        # 종료 핸들러 등록
        self._setup_shutdown_handlers()
        
        # PID 파일 경로
        self.pid_file = f"server_{self.port}.pid"
        
    def _setup_shutdown_handlers(self):
        """종료 핸들러 설정"""
        # 시그널 핸들러 등록 (Unix/Linux)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        # atexit 핸들러 등록 (프로세스 종료 시)
        atexit.register(self._cleanup_on_exit)
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        self._log(f"종료 시그널 수신: {signum}")
        self.stop()
        sys.exit(0)
    
    def _cleanup_on_exit(self):
        """프로세스 종료 시 정리 작업"""
        if self.running:
            self._log("프로세스 종료 시 서버 정리 중...")
            self.stop()
        
    def initialize_keys(self):
        """RSA 키 생성 및 로드 (보안 개선)"""
        try:
            # 독립 패키지용 - 현재 디렉토리에 키 파일 생성
            private_key_path = "private.pem"
            public_key_path = "public.pem"
            
            # 서버 키만 생성 (보안 개선)
            generate_server_keys(private_key_path, public_key_path)
            self.private_key = load_private_key(private_key_path)
            self.public_key_path = public_key_path  # 공개키 경로 저장
            self._log(f"서버 RSA 키 로드 완료 - 클라이언트는 {public_key_path}에서 공개키를 가져가세요")
            return True
        except Exception as e:
            self._log(f"RSA 키 초기화 실패: {e}")
            return False
    
    def get_public_key(self):
        """클라이언트가 사용할 수 있도록 공개키 반환"""
        try:
            with open(self.public_key_path, 'rb') as f:
                return f.read()
        except Exception as e:
            self._log(f"공개키 로드 실패: {e}")
            return None
    
    def _create_pid_file(self):
        """PID 파일 생성"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self._log(f"PID 파일 생성됨: {self.pid_file}")
        except Exception as e:
            self._log(f"PID 파일 생성 실패: {e}")
    
    def _remove_pid_file(self):
        """PID 파일 제거"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                self._log(f"PID 파일 제거됨: {self.pid_file}")
        except Exception as e:
            self._log(f"PID 파일 제거 실패: {e}")
    
    def _check_existing_server(self):
        """기존 서버 인스턴스 확인"""
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                self._log(f"기존 PID 파일 발견: {old_pid}")
                return True
            except Exception as e:
                self._log(f"PID 파일 읽기 오류: {e}")
                # 손상된 PID 파일 제거
                self._remove_pid_file()
        return False
    
    def _check_port_available(self):
        """포트 사용 가능 여부 확인"""
        try:
            # SO_REUSEADDR 없이 테스트 - 실제 사용 여부를 정확히 확인
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind((self.host, self.port))
            test_socket.close()
            self._log(f"포트 {self.port} 사용 가능")
            return True
        except socket.error as e:
            self._log(f"포트 {self.port} 사용 불가: {e}")
            return False
    
    def start(self):
        """서버 시작"""
        # 기존 서버 인스턴스 확인
        if self._check_existing_server():
            self._log("기존 서버 인스턴스가 실행 중일 수 있습니다.")
        
        if not self.initialize_keys():
            return False
        
        # 포트 사용 가능 여부 확인
        if not self._check_port_available():
            self._log(f"오류: 포트 {self.port}가 이미 사용 중입니다. 다른 서버 인스턴스가 실행 중일 수 있습니다.")
            return False
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 포트 재사용 옵션 강화
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Windows에서 TIME_WAIT 상태 해결을 위한 추가 옵션
            try:
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, OSError):
                # SO_REUSEPORT가 지원되지 않는 시스템에서는 무시
                pass
            
            # 소켓이 즉시 닫히도록 설정 (TIME_WAIT 상태 방지)
            import struct
            linger_struct = struct.pack('ii', 1, 0)  # l_onoff=1, l_linger=0 (즉시 닫기)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger_struct)
            
            self.server_socket.settimeout(1.0)  # accept에 1초 타임아웃 설정
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            self._create_pid_file()
            self._log(f"서버가 {self.host}:{self.port}에서 시작되었습니다")
            self._log("클라이언트 연결 대기 중...")
            
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
                    # 타임아웃은 정상적인 상황 - 계속 대기 (로그 출력 안함)
                    continue
                except socket.error as e:
                    if self.running:
                        self._log(f"클라이언트 연결 수락 오류: {e}")
                except Exception as e:
                    if self.running:
                        self._log(f"예상치 못한 오류: {e}")
                        
        except Exception as e:
            self._log(f"서버 시작 실패: {e}")
            return False
        finally:
            self._cleanup()
            
        return True
    
    def stop(self):
        """서버 중지"""
        if not self.running:
            return
            
        self._log("서버 종료 시작...")
        self.running = False
        
        # 모든 클라이언트 연결 강제 종료
        for client_addr in list(self.connected_clients):
            self._log(f"클라이언트 연결 강제 종료: {client_addr}")
        self.connected_clients.clear()
        
        # 서버 소켓 종료
        if self.server_socket:
            try:
                self.server_socket.close()
                self._log("서버 소켓 종료됨")
            except Exception as e:
                self._log(f"서버 소켓 종료 오류: {e}")
        
        # PID 파일 제거
        self._remove_pid_file()
        
        self._log("서버 종료 완료")
    
    def _handle_client(self, client_socket, client_address):
        """클라이언트 연결 처리"""
        client_addr_str = f"{client_address[0]}:{client_address[1]}"
        self.connected_clients.add(client_addr_str)
        self._on_client_connected(client_addr_str)
        
        client_socket.settimeout(10)
        
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    self._log(f"[{client_addr_str}] 연결 종료 요청")
                    break
                
                # 공개키 요청 처리
                if data == b"REQUEST_PUBLIC_KEY":
                    self._log(f"[{client_addr_str}] 공개키 요청 수신")
                    try:
                        with open(self.public_key_path, 'rb') as f:
                            public_key_data = f.read()
                        
                        # 공개키 크기를 먼저 전송 (4바이트)
                        key_size = len(public_key_data)
                        client_socket.sendall(key_size.to_bytes(4, 'big'))
                        
                        # 공개키 데이터 전송
                        client_socket.sendall(public_key_data)
                        self._log(f"[{client_addr_str}] 공개키 전송 완료 ({key_size} 바이트)")
                        continue
                        
                    except Exception as e:
                        self._log(f"[{client_addr_str}] 공개키 전송 실패: {e}")
                        error_msg = b"ERROR: PUBLIC_KEY_FAILED"
                        client_socket.sendall(len(error_msg).to_bytes(4, 'big'))
                        client_socket.sendall(error_msg)
                        continue
                    
                # 암호화된 데이터 처리
                try:
                    # 복호화
                    decrypted_data = decrypt(data, self.private_key)
                    
                    # 패킷 파싱
                    parsed = parsing.parse_packet(decrypted_data)
                    if parsed:
                        self._log(f"[{client_addr_str}] 센서 데이터 수신 - ID: {parsed['ID']}, 온도: {parsed['TEMP']}°C")
                        
                        # 센서 ID 확인
                        validation_result = self._validate_sensor_id(parsed['ID'], client_addr_str)
                        if not validation_result:
                            self._log(f"[{client_addr_str}] 센서 ID 검증 실패, 연결 종료")
                            break
                        
                        # 콘솔에 데이터 출력
                        self._display_data(parsed, client_addr_str)
                        
                        # 데이터베이스 저장 시도
                        try:
                            result = insert_sensor_results(parsed)
                            if result:
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
                
            # 데이터베이스의 센서 ID를 정수로 변환하여 비교
            sensor_ids = []
            for row in rows:
                try:
                    # 문자열로 저장된 센서 ID를 정수로 변환
                    db_sensor_id = int(row['sensor_id'])
                    sensor_ids.append(db_sensor_id)
                except (ValueError, TypeError):
                    # 변환 실패 시 원래 값도 포함
                    sensor_ids.append(row['sensor_id'])
            
            self._log(f"[{client_addr_str}] 검증 중 - 수신된 센서 ID: {sensor_id} (타입: {type(sensor_id)})")
            self._log(f"[{client_addr_str}] 데이터베이스 센서 ID들: {sensor_ids}")
            
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
        
        # PID 파일 제거
        self._remove_pid_file()
        self._log("서버 정리 완료")
    
    def _log(self, message):
        """로그 출력"""
        print(message)
    
    def _on_client_connected(self, client_addr):
        """클라이언트 연결 콜백"""
        self._log(f"클라이언트 연결: {client_addr}")
    
    def _on_client_disconnected(self, client_addr):
        """클라이언트 연결 해제 콜백"""
        self._log(f"클라이언트 연결 해제: {client_addr}")
    
    def _display_data(self, data, client_addr):
        """센서 데이터 콘솔 출력"""
        print(f"\n{'='*50}")
        print(f"클라이언트 주소: [{client_addr}]")
        print(f"센서 ID: {data['ID']}")
        print(f"온도: {data['TEMP']}°C")
        print(f"용존산소: {data['DO']}ppm")
        print(f"수온: {data['WTR_TEMP']}°C")
        print(f"위치: {data['LOC']}")
        print(f"시간: {data['TIME']}")
        print(f"체크섬: {data['CHK']}")
        print(f"{'='*50}\n")
    
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
        print("서버 시작 중... (Ctrl+C로 종료)")
        server.start()
    except KeyboardInterrupt:
        print("\n키보드 인터럽트 수신, 서버 종료 중...")
    except Exception as e:
        print(f"서버 오류: {e}")
    finally:
        server.stop()
        print("서버 종료됨")

if __name__ == "__main__":
    start_console_server()
