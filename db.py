#!/usr/bin/env python3
"""
해양수산물 운송 TCP 서버 미들웨어
TCP 소켓으로 센서 데이터 수신 → 파싱 → MySQL DB 저장
Author: 해양수산물 운송팀
"""

import socket
import threading
import json
import pymysql
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tcp_middleware.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SensorData:
    """센서 데이터 구조체"""
    device_id: str
    sensor_id: str
    sensor_value: float
    value_type_id: int
    alarm_state: int = 0
    error_state: int = 0
    location: str = ""
    raw_packet: str = ""


@dataclass
class AlarmData:
    """알람 데이터 구조체"""
    sensor_id: str
    alarm_type_id: int
    alarm_log: str


class DatabaseManager:
    """데이터베이스 연결 및 작업 관리"""

    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'livecn_db'),
            'charset': 'utf8mb4',
            'autocommit': False
        }
        self._test_connection()

    def _test_connection(self):
        """DB 연결 테스트"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    logger.info("데이터베이스 연결 성공")
        except Exception as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"데이터베이스 오류: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def insert_raw_packet(self, device_id: str, packet_data: str, parse_success: bool) -> str:
        """raw_packet_log 테이블에 원시 패킷 데이터 삽입"""
        packet_id = f"PKT_{uuid.uuid4().hex[:16].upper()}"

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO raw_packet_log 
                    (packet_id, device_id, received_at, packet_log, parse_success) 
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        packet_id,
                        device_id,
                        datetime.now(),
                        packet_data,
                        1 if parse_success else 0
                    ))
                    conn.commit()
                    logger.info(f"원시 패킷 저장 완료: {packet_id}")
                    return packet_id
        except Exception as e:
            logger.error(f"원시 패킷 저장 실패: {e}")
            raise

    def insert_sensor_result(self, sensor_data: SensorData) -> str:
        """sensor_result 테이블에 센서 결과 삽입"""
        result_id = f"RES_{uuid.uuid4().hex[:16].upper()}"

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO sensor_result 
                    (result_id, device_id, sensor_id, value_type_id, sensor_value, 
                     alarm_state, error_state, location, measured_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        result_id,
                        sensor_data.device_id,
                        sensor_data.sensor_id,
                        sensor_data.value_type_id,
                        sensor_data.sensor_value,
                        sensor_data.alarm_state,
                        sensor_data.error_state,
                        sensor_data.location,
                        datetime.now()
                    ))
                    conn.commit()
                    logger.info(f"센서 결과 저장 완료: {result_id}")
                    return result_id
        except Exception as e:
            logger.error(f"센서 결과 저장 실패: {e}")
            raise

    def insert_alarm_log(self, alarm_data: AlarmData) -> str:
        """alarm_log 테이블에 알람 로그 삽입"""
        alarm_id = int(time.time() * 1000000) % 2147483647  # INT 범위 내 고유 ID

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO alarm_log 
                    (alarm_id, alarmed_at, sensor_id, alarm_type_id, alarm_log) 
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        alarm_id,
                        datetime.now(),
                        alarm_data.sensor_id,
                        alarm_data.alarm_type_id,
                        alarm_data.alarm_log
                    ))
                    conn.commit()
                    logger.info(f"알람 로그 저장 완료: {alarm_id}")
                    return str(alarm_id)
        except Exception as e:
            logger.error(f"알람 로그 저장 실패: {e}")
            raise

    def get_sensor_info(self, sensor_id: str) -> Optional[Dict]:
        """센서 정보 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql = """
                    SELECT si.*, st.name as sensor_type_name, st.description as sensor_type_desc
                    FROM sensor_info si
                    LEFT JOIN sensor_type st ON si.sensor_type_id = st.sensor_type_id
                    WHERE si.sensor_id = %s
                    """
                    cursor.execute(sql, (sensor_id,))
                    result = cursor.fetchone()
                    return result
        except Exception as e:
            logger.error(f"센서 정보 조회 실패: {e}")
            return None


class SensorDataParser:
    """센서 데이터 파싱 클래스"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def parse_packet(self, raw_data: str) -> Tuple[List[SensorData], List[AlarmData], bool]:
        """
        TCP 패킷 데이터 파싱

        예상 데이터 형식 (JSON):
        {
            "device_id": "DEV001",
            "timestamp": "2024-01-01T12:00:00",
            "sensors": [
                {
                    "sensor_id": "TEMP001",
                    "value_type_id": 1,
                    "value": 25.5,
                    "location": "Container_A1",
                    "alarm_state": 0,
                    "error_state": 0
                }
            ]
        }
        """
        sensor_data_list = []
        alarm_data_list = []
        parse_success = False

        try:
            # JSON 파싱 시도
            if raw_data.strip().startswith('{'):
                data = json.loads(raw_data.strip())
                parse_success = True

                device_id = data.get('device_id', 'UNKNOWN')
                sensors = data.get('sensors', [])

                for sensor in sensors:
                    # 센서 데이터 생성
                    sensor_data = SensorData(
                        device_id=device_id,
                        sensor_id=sensor.get('sensor_id', ''),
                        sensor_value=float(sensor.get('value', 0)),
                        value_type_id=int(sensor.get('value_type_id', 1)),
                        alarm_state=int(sensor.get('alarm_state', 0)),
                        error_state=int(sensor.get('error_state', 0)),
                        location=sensor.get('location', ''),
                        raw_packet=raw_data
                    )
                    sensor_data_list.append(sensor_data)

                    # 알람 상태 확인
                    if sensor_data.alarm_state > 0:
                        alarm_data = AlarmData(
                            sensor_id=sensor_data.sensor_id,
                            alarm_type_id=sensor_data.alarm_state,
                            alarm_log=f"센서 알람 발생 - 값: {sensor_data.sensor_value}, 위치: {sensor_data.location}"
                        )
                        alarm_data_list.append(alarm_data)

            else:
                # CSV 형식 파싱 시도 (예: DEV001,TEMP001,25.5,1,0,0,Container_A1)
                parts = raw_data.strip().split(',')
                if len(parts) >= 4:
                    sensor_data = SensorData(
                        device_id=parts[0],
                        sensor_id=parts[1],
                        sensor_value=float(parts[2]),
                        value_type_id=int(parts[3]),
                        alarm_state=int(parts[4]) if len(parts) > 4 else 0,
                        error_state=int(parts[5]) if len(parts) > 5 else 0,
                        location=parts[6] if len(parts) > 6 else '',
                        raw_packet=raw_data
                    )
                    sensor_data_list.append(sensor_data)
                    parse_success = True

                    # 알람 확인
                    if sensor_data.alarm_state > 0:
                        alarm_data = AlarmData(
                            sensor_id=sensor_data.sensor_id,
                            alarm_type_id=sensor_data.alarm_state,
                            alarm_log=f"센서 알람 발생 - 값: {sensor_data.sensor_value}"
                        )
                        alarm_data_list.append(alarm_data)

        except Exception as e:
            logger.error(f"데이터 파싱 실패: {e}")
            parse_success = False

        return sensor_data_list, alarm_data_list, parse_success


class TCPServer:
    """TCP 서버 클래스"""

    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.db_manager = DatabaseManager()
        self.parser = SensorDataParser(self.db_manager)
        self.client_threads = []

    def start_server(self):
        """서버 시작"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)

            self.running = True
            logger.info(f"TCP 서버 시작: {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    logger.info(f"클라이언트 연결: {client_address}")

                    # 클라이언트 처리 스레드 시작
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    self.client_threads.append(client_thread)

                except Exception as e:
                    if self.running:
                        logger.error(f"클라이언트 수락 오류: {e}")

        except Exception as e:
            logger.error(f"서버 시작 실패: {e}")
        finally:
            self.stop_server()

    def handle_client(self, client_socket, client_address):
        """클라이언트 연결 처리"""
        try:
            with client_socket:
                buffer = ""
                while self.running:
                    try:
                        data = client_socket.recv(1024).decode('utf-8')
                        if not data:
                            break

                        buffer += data

                        # 줄바꿈을 기준으로 완전한 메시지 분리
                        while '\n' in buffer:
                            message, buffer = buffer.split('\n', 1)
                            message = message.strip()

                            if message:
                                logger.info(f"수신된 데이터 ({client_address}): {message[:100]}...")
                                self.process_sensor_data(message, client_address)

                                # 클라이언트에 응답 전송
                                response = {"status": "success", "timestamp": datetime.now().isoformat()}
                                client_socket.send(f"{json.dumps(response)}\n".encode('utf-8'))

                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.error(f"클라이언트 처리 오류 ({client_address}): {e}")
                        break

        except Exception as e:
            logger.error(f"클라이언트 연결 오류 ({client_address}): {e}")
        finally:
            logger.info(f"클라이언트 연결 종료: {client_address}")

    def process_sensor_data(self, raw_data: str, client_address):
        """센서 데이터 처리 및 DB 저장"""
        device_id = "UNKNOWN"

        try:
            # 1. 데이터 파싱
            sensor_data_list, alarm_data_list, parse_success = self.parser.parse_packet(raw_data)

            if sensor_data_list:
                device_id = sensor_data_list[0].device_id

            # 2. 원시 패킷 로그 저장
            packet_id = self.db_manager.insert_raw_packet(device_id, raw_data, parse_success)

            if not parse_success:
                logger.warning(f"파싱 실패한 패킷 저장됨: {packet_id}")
                return

            # 3. 센서 결과 저장
            for sensor_data in sensor_data_list:
                # 센서 정보 조회로 유효성 검증
                sensor_info = self.db_manager.get_sensor_info(sensor_data.sensor_id)
                if sensor_info:
                    # 센서 범위 체크
                    if (sensor_info.get('sensor_min') is not None and
                            sensor_data.sensor_value < sensor_info['sensor_min']):
                        sensor_data.alarm_state = 1  # 최소값 초과 알람
                    elif (sensor_info.get('sensor_max') is not None and
                          sensor_data.sensor_value > sensor_info['sensor_max']):
                        sensor_data.alarm_state = 2  # 최대값 초과 알람

                result_id = self.db_manager.insert_sensor_result(sensor_data)
                logger.info(f"센서 데이터 저장 완료: {result_id}")

            # 4. 알람 로그 저장
            for alarm_data in alarm_data_list:
                alarm_id = self.db_manager.insert_alarm_log(alarm_data)
                logger.warning(f"알람 발생: {alarm_id} - {alarm_data.alarm_log}")

        except Exception as e:
            logger.error(f"센서 데이터 처리 실패 ({client_address}): {e}")

    def stop_server(self):
        """서버 중지"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

        # 모든 클라이언트 스레드 대기
        for thread in self.client_threads:
            thread.join(timeout=1.0)

        logger.info("TCP 서버 중지")


class MiddlewareService:
    """미들웨어 서비스 메인 클래스"""

    def __init__(self):
        self.tcp_server = None
        self.server_thread = None

    def start(self, host='localhost', port=9999):
        """서비스 시작"""
        logger.info("해양수산물 운송 TCP 미들웨어 시작")

        try:
            self.tcp_server = TCPServer(host, port)
            self.server_thread = threading.Thread(target=self.tcp_server.start_server)
            self.server_thread.daemon = True
            self.server_thread.start()

            # 메인 스레드에서 사용자 입력 대기
            while True:
                try:
                    command = input("명령어 입력 (stop: 중지): ").strip().lower()
                    if command == 'stop':
                        break
                except KeyboardInterrupt:
                    break

        except Exception as e:
            logger.error(f"서비스 시작 실패: {e}")
        finally:
            self.stop()

    def stop(self):
        """서비스 중지"""
        logger.info("미들웨어 서비스 중지 중...")

        if self.tcp_server:
            self.tcp_server.stop_server()

        if self.server_thread:
            self.server_thread.join(timeout=5.0)

        logger.info("미들웨어 서비스 중지 완료")


def main():
    """메인 함수"""
    # .env 파일 예시 설정
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("""# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=livecn_db

# TCP 서버 설정
TCP_HOST=localhost
TCP_PORT=9999
""")
        logger.info(".env 파일이 생성되었습니다. 데이터베이스 설정을 확인하세요.")
        return

    # 서비스 시작
    service = MiddlewareService()
    host = os.getenv('TCP_HOST', 'localhost')
    port = int(os.getenv('TCP_PORT', 9999))

    try:
        service.start(host, port)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중지됨")
    except Exception as e:
        logger.error(f"서비스 오류: {e}")


if __name__ == "__main__":
    main()