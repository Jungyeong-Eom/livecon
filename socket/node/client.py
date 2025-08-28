#!/usr/bin/env python3
import socket
import json
import random
import time
from datetime import datetime

SERVER_HOST = 'localhost'
SERVER_PORT = 9999

DEVICE_IDS = ["DEV001", "DEV002", "DEV003", "SHIP_A1", "CONTAINER_B2"]
SENSOR_TYPES = {
    "TEMP": {"min": -5, "max": 35, "type_id": 1},
    "DO": {"min": 18, "max": 23, "type_id": 2},
    "WTR_TEMP": {"min": 0, "max": 30, "type_id": 3},
}
LOCATIONS = ["Container_A1", "Container_A2", "Hold_1", "Hold_2"]

def generate_sensor_data():
    device_id = random.choice(DEVICE_IDS)
    sensors = []
    for name, cfg in SENSOR_TYPES.items():
        value = round(random.uniform(cfg["min"], cfg["max"]), 2)
        sensors.append({
            "sensor_id": f"{name}_{random.randint(1,99):03d}",
            "value_type_id": cfg["type_id"],
            "value": value,
            "location": random.choice(LOCATIONS),
            "alarm_state": 0,
            "error_state": 0
        })
    return {
        "device_id": device_id,
        "timestamp": datetime.now().isoformat(),
        "sensors": sensors
    }

def send_to_server(packet):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((SERVER_HOST, SERVER_PORT))
            sock.sendall(json.dumps(packet).encode('utf-8'))
            response = sock.recv(1024)
            print(f"서버 응답: {response.decode('utf-8').strip()}")
    except Exception as e:
        print(f"서버 전송 실패: {e}")

def main():
    while True:
        packet = generate_sensor_data()
        send_to_server(packet)
        time.sleep(2)  # 2초마다 전송

if __name__ == "__main__":
    main()
