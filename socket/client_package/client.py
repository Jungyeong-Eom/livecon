import sys
import os
import socket
import time
import json

# Add current directory to Python path (for independent package)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from node_module.ecdhe_crypto import ECDHECrypto, AuthenticationError, ConnectionError
from node_module.generate_packet import generate_random_packet

def establish_ecdhe_session(device_id, server_address, server_port):
    """Establish ECDHE session with server and return crypto, socket, and error type"""
    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
    print(f"{timestamp} iot-client[{device_id}]: starting ECDHE session to {server_address}:{server_port}")
    
    try:
        # Create ECDHE crypto object
        ecdhe_crypto = ECDHECrypto(device_id)
        
        # Perform key exchange and get socket
        socket_conn = ecdhe_crypto.perform_key_exchange(server_address, server_port)
        if socket_conn:
            timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
            print(f"{timestamp} iot-client[{device_id}]: ECDHE key exchange successful - PFS activated")
            return ecdhe_crypto, socket_conn, None
        else:
            timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
            print(f"{timestamp} iot-client[{device_id}]: ERROR: ECDHE key exchange failed")
            return None, None, "connection"
            
    except AuthenticationError as e:
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{device_id}]: AUTHENTICATION FAILED: {e}")
        return None, None, "authentication"
        
    except ConnectionError as e:
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{device_id}]: CONNECTION FAILED: {e}")
        return None, None, "connection"
        
    except Exception as e:
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{device_id}]: ERROR: ECDHE session setup failed - {e}")
        return None, None, "unknown"

def load_config():
    """Load configuration file"""
    # PyInstaller 호환: exe 파일이 있는 실제 디렉토리에서 config.json 찾기
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller로 빌드된 경우: exe 파일 위치 기준
        exe_dir = os.path.dirname(sys.executable)
        config_path = os.path.join(exe_dir, 'config.json')
    else:
        # 일반 Python 스크립트 실행: 스크립트 파일 위치 기준
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    
    # 기본 설정
    default_config = {
        "server": {
            "address": "localhost", 
            "port": 12351
        },
        "client": {
            "device_id": "device001",
            "send_interval": 10
        }
    }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client: configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client: WARNING: config file not found, using defaults - {config_path}")
        # 기본 설정 파일 생성
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client: default configuration file created - {config_path}")
        return default_config
    except json.JSONDecodeError as e:
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client: ERROR: config file parse error - {e}")
        print(f"{timestamp} iot-client: using default configuration")
        return default_config

# Load configuration
config = load_config()
SERVER_ADDRESS = config['server']['address']
SERVER_PORT = config['server']['port']
DEVICE_ID = config['client']['device_id']
SEND_INTERVAL = config['client']['send_interval']

timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
print(f"{timestamp} iot-client: starting IoT sensor client")
print(f"{timestamp} iot-client: server={SERVER_ADDRESS}:{SERVER_PORT} device_id={DEVICE_ID} interval={SEND_INTERVAL}s")

def main_client_loop():
    """Main client loop with reconnection logic"""
    # device_id를 문자열에서 정수로 변환 (device001 -> 1)
    device_num = int(DEVICE_ID.replace('device', '')) if DEVICE_ID.startswith('device') else 1
    
    # Connection retry settings
    max_connection_retries = -1  # Infinite retries for connection failures
    connection_retry_delay = 5   # Wait 5 seconds between connection retries
    reconnect_delay = 10         # Wait 10 seconds before reconnecting after session loss
    
    ecdhe_crypto = None
    client_socket = None
    
    while True:
        try:
            # Establish connection (retry on connection failures)
            connection_retries = 0
            while True:
                timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                print(f"{timestamp} iot-client[{DEVICE_ID}]: establishing secure ECDHE session with server")
                
                ecdhe_crypto, client_socket, error_type = establish_ecdhe_session(DEVICE_ID, SERVER_ADDRESS, SERVER_PORT)
                
                if ecdhe_crypto and client_socket:
                    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: secure ECDHE session established - ready for data transmission")
                    break
                
                # Handle different error types
                if error_type == "authentication":
                    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: FATAL: Authentication failed - shutting down")
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: Possible causes: wrong device ID, server key mismatch, MITM attack")
                    return False
                
                elif error_type == "connection":
                    connection_retries += 1
                    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: connection attempt {connection_retries} failed")
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: retrying in {connection_retry_delay} seconds...")
                    time.sleep(connection_retry_delay)
                    continue
                
                else:
                    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: unknown error occurred - retrying in {connection_retry_delay} seconds...")
                    time.sleep(connection_retry_delay)
                    continue
            
            # Data transmission loop
            while True:
                try:
                    packet = generate_random_packet(device_id=device_num)
                    encrypted_packet = ecdhe_crypto.encrypt(packet)
                    client_socket.sendall(encrypted_packet)
                    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: encrypted sensor data transmitted - {len(encrypted_packet)} bytes")
                    time.sleep(SEND_INTERVAL)
                    
                except (socket.error, OSError, BrokenPipeError) as e:
                    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: connection lost during transmission: {e}")
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: attempting to reconnect in {reconnect_delay} seconds...")
                    break  # Break inner loop to reconnect
                    
                except Exception as e:
                    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: transmission error: {e}")
                    print(f"{timestamp} iot-client[{DEVICE_ID}]: attempting to reconnect in {reconnect_delay} seconds...")
                    break  # Break inner loop to reconnect
            
            # Clean up current session before reconnecting
            if client_socket:
                try:
                    client_socket.close()
                except:
                    pass
            
            if ecdhe_crypto:
                ecdhe_crypto.clear_session()
            
            # Wait before reconnecting
            time.sleep(reconnect_delay)
            
        except KeyboardInterrupt:
            timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
            print(f"\n{timestamp} iot-client[{DEVICE_ID}]: shutdown signal received")
            break
            
        except Exception as e:
            timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
            print(f"{timestamp} iot-client[{DEVICE_ID}]: unexpected error: {e}")
            print(f"{timestamp} iot-client[{DEVICE_ID}]: restarting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)
    
    # Final cleanup
    if client_socket:
        try:
            client_socket.close()
        except:
            pass
    
    if ecdhe_crypto:
        ecdhe_crypto.clear_session()
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{DEVICE_ID}]: secure session cleanup completed")
    
    return True

# Start the main client loop
if __name__ == "__main__":
    try:
        main_client_loop()
    except Exception as e:
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{DEVICE_ID}]: fatal error: {e}")
        sys.exit(1)