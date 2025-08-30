import sys
import os
import socket
import time
import json

# Add current directory to Python path (for independent package)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from node_module.ecdhe_crypto import ECDHECrypto
from node_module.generate_packet import generate_random_packet

def establish_ecdhe_session(device_id, server_address, server_port):
    """Establish ECDHE session with server and return both crypto and socket"""
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
            return ecdhe_crypto, socket_conn
        else:
            timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
            print(f"{timestamp} iot-client[{device_id}]: ERROR: ECDHE key exchange failed")
            return None, None
            
    except Exception as e:
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{device_id}]: ERROR: ECDHE session setup failed - {e}")
        return None, None

def load_config():
    """Load configuration file"""
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

# ECDHE session setup and socket connection
timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
print(f"{timestamp} iot-client[{DEVICE_ID}]: establishing secure ECDHE session with server")
ecdhe_crypto, client_socket = establish_ecdhe_session(DEVICE_ID, SERVER_ADDRESS, SERVER_PORT)

if ecdhe_crypto is None or client_socket is None:
    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
    print(f"{timestamp} iot-client[{DEVICE_ID}]: FATAL: unable to establish secure ECDHE session")
    print(f"{timestamp} iot-client[{DEVICE_ID}]: troubleshooting: check server status, address/port, ECDHE support")
    sys.exit(1)

timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
print(f"{timestamp} iot-client[{DEVICE_ID}]: secure ECDHE session established - ready for data transmission")

try:
    # device_id를 문자열에서 정수로 변환 (device001 -> 1)
    device_num = int(DEVICE_ID.replace('device', '')) if DEVICE_ID.startswith('device') else 1
    
    while True:
        packet = generate_random_packet(device_id=device_num)
        encrypted_packet = ecdhe_crypto.encrypt(packet)
        client_socket.sendall(encrypted_packet)
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{DEVICE_ID}]: encrypted sensor data transmitted - {len(encrypted_packet)} bytes")
        time.sleep(SEND_INTERVAL)
except KeyboardInterrupt:
    timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
    print(f"\n{timestamp} iot-client[{DEVICE_ID}]: shutdown signal received")
finally:
    client_socket.close()
    if ecdhe_crypto:
        ecdhe_crypto.clear_session()
        timestamp = time.strftime("%b %d %H:%M:%S", time.localtime())
        print(f"{timestamp} iot-client[{DEVICE_ID}]: secure session cleanup completed")