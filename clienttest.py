import socket
import json
import random
from datetime import datetime
import time

HOST = '127.0.0.1'
PORT = 9999

device_ids = ["DEV001", "DEV002", "DEV003"]
sensor_types = ["TEMP", "HUMID", "O2"]

def generate_sensor_data():
    device_id = random.choice(device_ids)
    sensors = []
    for sensor in sensor_types:
        value = round(random.uniform(0, 100), 2)
        sensors.append({
            "sensor_id": f"{sensor}_{random.randint(1,99):03d}",
            "value_type_id": sensor_types.index(sensor) + 1,
            "value": value,
            "location": f"LOC_{random.randint(1,10)}",
            "alarm_state": 0,
            "error_state": 0
        })
    return {
        "device_id": device_id,
        "timestamp": datetime.now().isoformat(),
        "sensors": sensors
    }

def send_data():
    data = generate_sensor_data()
    message = json.dumps(data, ensure_ascii=False)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(f"{message}\n".encode('utf-8'))
        response = s.recv(1024).decode('utf-8').strip()
        print(f"[서버 응답] {response}")

if __name__ == "__main__":
    for _ in range(5):
        send_data()
        time.sleep(1)
