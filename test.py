#!/usr/bin/env python3
"""
해양수산물 운송 TCP 서버 미들웨어 테스트 도구
- 센서 데이터 시뮬레이션
- TCP 클라이언트 테스트
- 다양한 데이터 형식 테스트
"""

import socket
import json
import time
import random
import threading
import logging
from datetime import datetime
from typing import List, Dict
import argparse
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SensorDataGenerator:
    """센서 데이터 생성기"""

    def __init__(self):
        self.device_ids = ["DEV001", "DEV002", "DEV003", "SHIP_A1", "CONTAINER_B2"]
        self.sensor_types = {
            "TEMP": {"min": -5.0, "max": 35.0, "unit": "°C", "type_id": 1},
            "HUMID": {"min": 30.0, "max": 95.0, "unit": "%", "type_id": 2},
            "PRESS": {"min": 990.0, "max": 1030.0, "unit": "hPa", "type_id": 3},
            "O2": {"min": 18.0, "max": 23.0, "unit": "%", "type_id": 4},
            "CO2": {"min": 300.0, "max": 1500.0, "unit": "ppm", "type_id": 5},
            "VIBR": {"min": 0.0, "max": 10.0, "unit": "G", "type_id": 6}
        }
        self.locations = ["Container_A1", "Container_A2", "Container_B1", "Container_B2",
                          "Hold_1", "Hold_2", "Deck_Area", "Cold_Storage"]

    def generate_sensor_data(self, device_id: str = None, alarm_probability: float = 0.1) -> Dict:
        """랜덤 센서 데이터 생성"""
        if not device_id:
            device_id = random.choice(self.device_ids)

        sensors = []
        num_sensors = random.randint(1, 4)  # 1-4개 센서 데이터

        for _ in range(num_sensors):
            sensor_type = random.choice(list(self.sensor_types.keys()))
            sensor_config = self.sensor_types[sensor_type]

            # 센서 ID 생성
            sensor_id = f"{sensor_type}_{random.randint(1, 99):03d}"

            # 정상 값 생성
            normal_value = random.uniform(sensor_config["min"], sensor_config["max"])

            # 알람 상태 결정
            alarm_state = 0
            error_state = 0

            if random.random() < alarm_probability:
                # 알람 발생 시뮬레이션
                if random.random() < 0.5:
                    # 범위 초과
                    normal_value = random.uniform(sensor_config["max"], sensor_config["max"] * 1.2)
                    alarm_state = 2  # 최대값 초과
                else:
                    # 범위 미달
                    normal_value = random.uniform(sensor_config["min"] * 0.8, sensor_config["min"])
                    alarm_state = 1  # 최소값 미달

            # 에러 상태 (낮은 확률)
            if random.random() < 0.02:
                error_state = 1
                normal_value = -999.0  # 에러 값

            sensor_data = {
                "sensor_id": sensor_id,
                "value_type_id": sensor_config["type_id"],
                "value": round(normal_value, 2),
                "location": random.choice(self.locations),
                "alarm_state": alarm_state,
                "error_state": error_state
            }
            sensors.append(sensor_data)

        return {
            "device_id": device_id,
            "timestamp": datetime.now().isoformat(),
            "sensors": sensors
        }

    def generate_csv_data(self, device_id: str = None) -> str:
        """CSV 형식 데이터 생성 (레거시 형식)"""
        if not device_id:
            device_id = random.choice(self.device_ids)

        sensor_type = random.choice(list(self.sensor_types.keys()))
        sensor_config = self.sensor_types[sensor_type]

        sensor_id = f"{sensor_type}_{random.randint(1, 99):03d}"
        value = round(random.uniform(sensor_config["min"], sensor_config["max"]), 2)
        type_id = sensor_config["type_id"]
        alarm_state = 1 if random.random() < 0.1 else 0
        error_state = 0
        location = random.choice(self.locations)

        return f"{device_id},{sensor_id},{value},{type_id},{alarm_state},{error_state},{location}"


class TCPTestClient:
    """TCP 테스트 클라이언트"""

    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.generator = SensorDataGenerator()

    def send_single_message(self, message: str) -> bool:
        """단일 메시지 전송"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect((self.host, self.port))

                # 메시지 전송
                sock.send(f"{message}\n".encode('utf-8'))
                logger.info(f"전송됨: {message[:100]}...")

                # 응답 수신
                response = sock.recv(1024).decode('utf-8')
                logger.info(f"응답: {response.strip()}")
                return True

        except Exception as e:
            logger.error(f"메시지 전송 실패: {e}")
            return False

    def send_json_data(self, device_id: str = None, alarm_probability: float = 0.1) -> bool:
        """JSON 형식 데이터 전송"""
        data = self.generator.generate_sensor_data(device_id, alarm_probability)
        message = json.dumps(data, ensure_ascii=False)
        return self.send_single_message(message)

    def send_csv_data(self, device_id: str = None) -> bool:
        """CSV 형식 데이터 전송"""
        message = self.generator.generate_csv_data(device_id)
        return self.send_single_message(message)

    def send_invalid_data(self) -> bool:
        """잘못된 형식 데이터 전송 (파싱 실패 테스트)"""
        invalid_messages = [
            "invalid json {broken",
            "incomplete,csv,data",
            "",
            "random text without format",
            '{"missing_device_id": true}',
            "special,chars,테스트,데이터,♠♣♥♦"
        ]
        message = random.choice(invalid_messages)
        return self.send_single_message(message)

    def continuous_send(self, duration: int = 30, interval: float = 2.0):
        """연속 데이터 전송"""
        logger.info(f"{duration}초 동안 {interval}초 간격으로 데이터 전송 시작")

        start_time = time.time()
        sent_count = 0
        success_count = 0

        while time.time() - start_time < duration:
            try:
                # 80% JSON, 15% CSV, 5% 잘못된 데이터
                rand = random.random()
                if rand < 0.8:
                    success = self.send_json_data()
                elif rand < 0.95:
                    success = self.send_csv_data()
                else:
                    success = self.send_invalid_data()

                if success:
                    success_count += 1
                sent_count += 1

                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("사용자에 의해 중단됨")
                break

        logger.info(f"전송 완료: 총 {sent_count}개, 성공 {success_count}개")


class MultiClientTester:
    """다중 클라이언트 테스트"""

    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.clients = []
        self.threads = []

    def client_worker(self, client_id: int, duration: int, interval: float):
        """클라이언트 작업자 스레드"""
        client = TCPTestClient(self.host, self.port)
        logger.info(f"클라이언트 {client_id} 시작")

        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                # 각 클라이언트마다 다른 디바이스 ID 사용
                device_id = f"DEV{client_id:03d}"
                client.send_json_data(device_id, alarm_probability=0.15)
                time.sleep(interval + random.uniform(-0.5, 0.5))  # 약간의 랜덤성
            except Exception as e:
                logger.error(f"클라이언트 {client_id} 오류: {e}")
                break

        logger.info(f"클라이언트 {client_id} 종료")

    def run_multi_client_test(self, num_clients: int = 3, duration: int = 30, interval: float = 2.0):
        """다중 클라이언트 테스트 실행"""
        logger.info(f"{num_clients}개 클라이언트로 {duration}초 동안 테스트")

        # 스레드 시작
        for i in range(num_clients):
            thread = threading.Thread(
                target=self.client_worker,
                args=(i + 1, duration, interval)
            )
            thread.start()
            self.threads.append(thread)

        # 모든 스레드 종료 대기
        for thread in self.threads:
            thread.join()

        logger.info("다중 클라이언트 테스트 완료")


class AlarmTester:
    """알람 상황 테스트"""

    def __init__(self, host='localhost', port=9999):
        self.client = TCPTestClient(host, port)

    def test_temperature_alarms(self):
        """온도 센서 알람 테스트"""
        logger.info("온도 알람 테스트 시작")

        # 고온 알람
        high_temp_data = {
            "device_id": "TEST_DEV",
            "timestamp": datetime.now().isoformat(),
            "sensors": [{
                "sensor_id": "TEMP_TEST_001",
                "value_type_id": 1,
                "value": 45.0,  # 정상 범위 초과
                "location": "Test_Container",
                "alarm_state": 2,  # 최대값 초과
                "error_state": 0
            }]
        }
        self.client.send_single_message(json.dumps(high_temp_data))

        # 저온 알람
        low_temp_data = {
            "device_id": "TEST_DEV",
            "timestamp": datetime.now().isoformat(),
            "sensors": [{
                "sensor_id": "TEMP_TEST_002",
                "value_type_id": 1,
                "value": -10.0,  # 정상 범위 미달
                "location": "Test_Container",
                "alarm_state": 1,  # 최소값 미달
                "error_state": 0
            }]
        }
        self.client.send_single_message(json.dumps(low_temp_data))

    def test_sensor_errors(self):
        """센서 오류 상태 테스트"""
        logger.info("센서 오류 테스트 시작")

        error_data = {
            "device_id": "TEST_DEV",
            "timestamp": datetime.now().isoformat(),
            "sensors": [{
                "sensor_id": "SENSOR_ERROR_001",
                "value_type_id": 1,
                "value": -999.0,  # 오류 값
                "location": "Test_Container",
                "alarm_state": 0,
                "error_state": 1  # 오류 상태
            }]
        }
        self.client.send_single_message(json.dumps(error_data))

    def test_multiple_alarms(self):
        """복수 알람 테스트"""
        logger.info("복수 알람 테스트 시작")

        multi_alarm_data = {
            "device_id": "MULTI_ALARM_DEV",
            "timestamp": datetime.now().isoformat(),
            "sensors": [
                {
                    "sensor_id": "TEMP_MULTI_001",
                    "value_type_id": 1,
                    "value": 50.0,
                    "location": "Container_A",
                    "alarm_state": 2,
                    "error_state": 0
                },
                {
                    "sensor_id": "HUMID_MULTI_001",
                    "value_type_id": 2,
                    "value": 98.0,
                    "location": "Container_A",
                    "alarm_state": 2,
                    "error_state": 0
                },
                {
                    "sensor_id": "O2_MULTI_001",
                    "value_type_id": 4,
                    "value": 15.0,
                    "location": "Container_A",
                    "alarm_state": 1,
                    "error_state": 0
                }
            ]
        }
        self.client.send_single_message(json.dumps(multi_alarm_data))


def main():
    parser = argparse.ArgumentParser(description='TCP 미들웨어 테스트 도구')
    parser.add_argument('--host', default='localhost', help='서버 호스트')
    parser.add_argument('--port', type=int, default=9999, help='서버 포트')
    parser.add_argument('--mode', choices=['single', 'continuous', 'multi', 'alarm', 'interactive'],
                        default='interactive', help='테스트 모드')
    parser.add_argument('--duration', type=int, default=30, help='테스트 지속 시간 (초)')
    parser.add_argument('--interval', type=float, default=2.0, help='메시지 전송 간격 (초)')
    parser.add_argument('--clients', type=int, default=3, help='다중 클라이언트 수')

    args = parser.parse_args()

    logger.info(f"TCP 미들웨어 테스트 시작 - {args.host}:{args.port}")

    if args.mode == 'single':
        # 단일 메시지 테스트
        client = TCPTestClient(args.host, args.port)
        logger.info("JSON 데이터 전송 테스트")
        client.send_json_data()

        logger.info("CSV 데이터 전송 테스트")
        client.send_csv_data()

        logger.info("잘못된 데이터 전송 테스트")
        client.send_invalid_data()

    elif args.mode == 'continuous':
        # 연속 전송 테스트
        client = TCPTestClient(args.host, args.port)
        client.continuous_send(args.duration, args.interval)

    elif args.mode == 'multi':
        # 다중 클라이언트 테스트
        tester = MultiClientTester(args.host, args.port)
        tester.run_multi_client_test(args.clients, args.duration, args.interval)

    elif args.mode == 'alarm':
        # 알람 테스트
        alarm_tester = AlarmTester(args.host, args.port)
        alarm_tester.test_temperature_alarms()
        time.sleep(1)
        alarm_tester.test_sensor_errors()
        time.sleep(1)
        alarm_tester.test_multiple_alarms()

    elif args.mode == 'interactive':
        # 대화형 모드
        client = TCPTestClient(args.host, args.port)
        alarm_tester = AlarmTester(args.host, args.port)

        while True:
            print("\n=== TCP 미들웨어 테스트 메뉴 ===")
            print("1. JSON 데이터 전송")
            print("2. CSV 데이터 전송")
            print("3. 잘못된 데이터 전송")
            print("4. 연속 데이터 전송 (30초)")
            print("5. 알람 테스트")
            print("6. 다중 클라이언트 테스트")
            print("7. 커스텀 JSON 전송")
            print("0. 종료")

            try:
                choice = input("선택하세요: ").strip()

                if choice == '0':
                    break
                elif choice == '1':
                    client.send_json_data()
                elif choice == '2':
                    client.send_csv_data()
                elif choice == '3':
                    client.send_invalid_data()
                elif choice == '4':
                    client.continuous_send(30, 2.0)
                elif choice == '5':
                    alarm_tester.test_temperature_alarms()
                    time.sleep(0.5)
                    alarm_tester.test_sensor_errors()
                    time.sleep(0.5)
                    alarm_tester.test_multiple_alarms()
                elif choice == '6':
                    tester = MultiClientTester(args.host, args.port)
                    tester.run_multi_client_test(3, 20, 1.5)
                elif choice == '7':
                    json_str = input("JSON 문자열을 입력하세요: ")
                    client.send_single_message(json_str)
                else:
                    print("잘못된 선택입니다.")

            except KeyboardInterrupt:
                print("\n테스트 중단됨")
                break
            except Exception as e:
                logger.error(f"테스트 중 오류: {e}")

    logger.info("테스트 완료")


if __name__ == "__main__":
    main()