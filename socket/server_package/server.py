#!/usr/bin/env python3
"""
LIVECON IoT Server - Interactive Console Mode Only
ECDHE + Perfect Forward Secrecy enabled
No dashboard mode - command-based interface only
"""

import threading
import time
import sys
import os
import signal
import shutil

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from server_module.console_manager import ConsoleManager
from server_module.console_interface import ServerConsole
from server_module.database_manager import DatabaseManager
from server_module.crypto_manager import CryptoManager
from server_module.process_manager import ProcessManager
from server_module.server_core import ServerCore
from server_module.client_manager import ClientManager

class LiveConServer:
    def __init__(self, host='0.0.0.0', port=12351):
        self.host = host
        self.port = port
        self.running = False
        self.server_thread = None
        self.last_terminal_width = 0
        self.resize_monitor_thread = None
        self.terminal_lock = threading.Lock()  # 터미널 출력 동기화
        self.console_active = False  # 콘솔이 활성화되었는지 추적
        
        # 컴포넌트들 초기화 (인터랙티브 모드용)
        self.console_manager = ConsoleManager()
        self.database_manager = DatabaseManager(console_manager=self.console_manager)
        self.crypto_manager = CryptoManager(console_manager=self.console_manager)
        self.process_manager = ProcessManager(console_manager=self.console_manager, port=port)
        self.server_core = ServerCore(console_manager=self.console_manager, host=host, port=port)
        self.client_manager = ClientManager(
            console_manager=self.console_manager,
            crypto_manager=self.crypto_manager,
            database_manager=self.database_manager
        )
        
        # 종료 핸들러 등록
        self._setup_shutdown_handlers()
        
    def _setup_shutdown_handlers(self):
        """종료 핸들러 설정"""
        self.process_manager.setup_shutdown_handlers()
        self.process_manager.add_shutdown_callback(self.stop)
        
    def _log(self, message, level="info"):
        """로그 출력 (인터랙티브 모드: 명령어로만 확인 가능)"""
        getattr(self.console_manager, level)(message)
    
    def _draw_ascii_art(self, initial=False):
        """터미널 크기에 따른 ASCII 아트 출력 (스레드 안전)"""
        try:
            with self.terminal_lock:
                # 콘솔이 활성화된 상태에서는 리사이즈 시 출력하지 않음
                if self.console_active and not initial:
                    return
                    
                terminal_width = shutil.get_terminal_size().columns
                
                # 화면 지우고 커서를 맨 위로 (초기 실행시에만)
                if initial:
                    print("\033[2J\033[H", end="")
                
                if terminal_width >= 70:  # 넓은 터미널: LIVECON 로고
                    print(f"""
\033[36m ██╗     ██╗██╗   ██╗███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║     ██║██║   ██║██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║     ██║██║   ██║█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║     ██║╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ███████╗██║ ╚████╔╝ ███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚══════╝╚═╝  ╚═══╝  ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝\033[0m

\033[32m        IoT Server with ECDHE + Perfect Forward Secrecy\033[0m
\033[90m              Server: {self.host}:{self.port} | Status: \033[32mRUNNING\033[0m
""")
                else:  # 작은 터미널: 간단한 텍스트 표시
                    print(f"""
\033[1mLivecon\033[0m version \033[36m1.0\033[0m

IoT Sensor Server
Status: \033[32mRUNNING\033[0m  Port: \033[90m{self.port}\033[0m
""")
                
                # 초기 실행시에만 프롬프트를 출력하지 않음 (ServerConsole에서 처리)
        except (OSError, ValueError):
            # 터미널 크기를 가져올 수 없는 경우 무시
            pass
    
    def _monitor_terminal_resize(self):
        """터미널 크기 변화 모니터링 (스레드 안전)"""
        consecutive_errors = 0
        max_errors = 10
        
        while self.running:
            try:
                current_width = shutil.get_terminal_size().columns
                if current_width != self.last_terminal_width and not self.console_active:
                    self.last_terminal_width = current_width
                    self._draw_ascii_art(initial=False)
                
                consecutive_errors = 0  # 성공시 에러 카운트 리셋
                time.sleep(0.2)  # CPU 사용량 최적화: 200ms마다 체크
                
            except (OSError, ValueError) as e:
                consecutive_errors += 1
                if consecutive_errors >= max_errors:
                    # 연속 에러가 많으면 모니터링 중단
                    break
                time.sleep(1)  # 에러 시 더 긴 대기
            except Exception:
                # 예상치 못한 에러 시 중단
                break
    
    def start(self):
        """서버 시작"""
        # 인터랙티브 모드: 대시보드 없이 로그만 수집
        # 실제 콘솔 출력은 명령어를 통해서만 확인 가능
        
        # 기존 서버 인스턴스 확인
        if self.process_manager.check_existing_server():
            self._log("Existing server instance may be running", "warning")
        
        # ECDHE + Ed25519 키 초기화
        self._log("Initializing ECDHE + Ed25519 crypto system...")
        if not self.crypto_manager.initialize_keys():
            self._log("Crypto system initialization failed", "error")
            return False
        self._log("ECDHE + PFS cryptographic system initialized")
        
        # 포트 사용 가능 여부 확인 및 서버 소켓 생성
        self._log(f"Checking port {self.port} availability...")
        try:
            self.server_core.check_port_available()
            self._log(f"Port {self.port} is available")
        except Exception as e:
            self._log(f"Port availability check failed: {e}", "error")
            return False
        
        # 서버 소켓 생성
        self._log("Creating server socket...")
        try:
            self.server_core.create_server_socket()
            self._log("Server socket created successfully")
        except Exception as e:
            self._log(f"Server socket creation failed: {e}", "error")
            return False
            
        try:
            self.running = True
            self.process_manager.create_pid_file()
            self._log(f"Starting server listener on {self.host}:{self.port}")
            self.server_core.start_listening()
            
            # 센서 모니터링 시작
            self._log("Starting sensor monitoring system")
            self.client_manager.start_sensor_monitoring()
            
            self._log("Server started successfully. Ready for client connections...")
            return True
            
        except Exception as e:
            self._log(f"Server startup failed: {e}", "error")
            return False
        finally:
            if not self.running:
                self._cleanup()
            
        return True
    
    def start_background_server(self):
        """백그라운드에서 클라이언트 처리 시작"""
        self.server_thread = threading.Thread(target=self._background_server_loop, daemon=True)
        self.server_thread.start()
    
    def _background_server_loop(self):
        """백그라운드 서버 루프"""
        try:
            while self.running:
                try:
                    client_socket, client_address = self.server_core.accept_client()
                    
                    if client_socket and client_address:
                        if not self.running:
                            client_socket.close()
                            break
                            
                        client_thread = threading.Thread(
                            target=self.client_manager.handle_client,
                            args=(client_socket, client_address),
                            daemon=True
                        )
                        client_thread.start()
                        
                except Exception as e:
                    if self.running:
                        self._log(f"Background server loop error: {e}", "error")
                        time.sleep(1)
                        
        except Exception as e:
            self._log(f"Background server error: {e}", "error")
    
    def stop(self):
        """서버 중지"""
        if not self.running:
            return
            
        self._log("Server shutdown initiated...")
        self.running = False
        
        # 센서 모니터링 중지
        self.client_manager.stop_sensor_monitoring()
        
        # 모든 클라이언트 연결 강제 종료
        self.client_manager.disconnect_all_clients()
        
        # 암호화 매니저 중지 (세션 정리)
        self.crypto_manager.stop()
        
        # 서버 소켓 종료
        self.server_core.stop()
        
        # PID 파일 제거
        self.process_manager.remove_pid_file()
        
        self._log("Server shutdown completed")
    
    def _cleanup(self):
        """정리 작업"""
        self.client_manager.stop_sensor_monitoring()
        self.client_manager.disconnect_all_clients()
        self.crypto_manager.stop()
        self.server_core.stop()
        self.process_manager.remove_pid_file()
        self._log("Server cleanup completed")
    
    def get_connected_clients(self):
        """연결된 클라이언트 목록 반환"""
        return self.client_manager.get_connected_clients()
    
    def is_running(self):
        """서버 실행 상태 반환"""
        return self.running and self.server_core.is_running()
    
    def get_monitoring_status(self):
        """센서 모니터링 상태 반환"""
        return self.client_manager.get_monitoring_status()

def start_interactive_server():
    """인터랙티브 콘솔 모드 서버 시작"""
    
    server = LiveConServer(host='0.0.0.0')
    
    print("\nStarting server components...")
    
    try:
        if server.start():
            # 백그라운드에서 클라이언트 처리 시작
            server.start_background_server()
            
            # 성공 시 3초 대기 후 화면 지우고 ASCII 아트 표시
            import os
            import shutil
            import time
            time.sleep(3)  # 3초 대기
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # 초기 ASCII 아트 출력
            try:
                server.last_terminal_width = shutil.get_terminal_size().columns
                server._draw_ascii_art(initial=True)
                
                # 터미널 크기 변화 모니터링 스레드 시작
                server.resize_monitor_thread = threading.Thread(
                    target=server._monitor_terminal_resize, 
                    daemon=True
                )
                server.resize_monitor_thread.start()
            except (OSError, ValueError):
                # 터미널 크기 감지 실패시 기본 로고만 출력
                print("\n\033[32mLIVECON IoT Server - RUNNING\033[0m\n")
            
            # TTY 체크 - 대화형 터미널이 있는 경우만 콘솔 시작
            import sys
            if sys.stdin.isatty() and sys.stdout.isatty():
                console = ServerConsole(server)
                
                console.cmdloop()
            else:
                print("\033[33mInfo:\033[0m Non-interactive mode: Server running in background")
                print("\033[33mInfo:\033[0m Send SIGTERM or SIGINT to stop the server")
                try:
                    # 서버가 중단될 때까지 대기
                    import signal
                    import time
                    
                    def signal_handler(signum, frame):
                        print(f"\nReceived signal {signum}, shutting down...")
                        server.stop()
                        
                    signal.signal(signal.SIGTERM, signal_handler)
                    signal.signal(signal.SIGINT, signal_handler)
                    
                    while server.running:
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt received")
            
        else:
            print("Server startup failed")
            
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\nShutting down server...")
        try:
            server.stop()
        except:
            pass
        print("Server shutdown complete")

if __name__ == "__main__":
    start_interactive_server()