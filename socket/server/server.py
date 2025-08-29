import socket
import threading
import mysql.connector
from modules.rsa_utils import load_private_key, decrypt, generate_and_save_keys
from modules import parsing
import base64

# RSA 키 생성 및 저장
generate_and_save_keys()
private_key = load_private_key("server/private.pem")

HOST = 'localhost'
PORT = 12346

# ✅ MySQL DB 연결
db = mysql.connector.connect(
    host="localhost",
    user="root",         # ← 여기에 너의 MySQL 사용자명
    password="a97a11a04@",     # ← 여기에 너의 MySQL 비밀번호
    database="livecon_db"
)
cursor = db.cursor()

def insert_sensor_result(result_id, device_id, sensor_id, value_type_id, value, location, time_str):
    try:
        sql = """
            INSERT INTO sensor_result (
                result_id, device_id, sensor_id, value_type_id,
                sensor_value, alarm_state, error_state,
                location, measured_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            result_id,
            device_id,
            sensor_id,
            value_type_id,
            float(value),
            0,  # alarm_state
            0,  # error_state
            location,
            time_str
        ))
        db.commit()
        print(f"✅ sensor_result 저장됨: {sensor_id}={value}")
    except Exception as e:
        print(f"❌ sensor_result 저장 실패: {e}")

def insert_raw_packet_log(packet_id, device_id, raw_data, time_str):
    try:
        sql = """
            INSERT INTO raw_packet_log (
                packet_id, device_id, received_at, packet_log, parse_success
            ) VALUES (%s, %s, %s, %s, %s)
        """
        # Base64로 인코딩
        encoded_data = base64.b64encode(raw_data).decode('utf-8')
        cursor.execute(sql, (
            packet_id,
            device_id,
            time_str,
            encoded_data,
            1  # parse_success
        ))
        db.commit()
        print(f"✅ raw_packet_log 저장됨")
    except Exception as e:
        print(f"❌ raw_packet_log 저장 실패: {e}")

# 클라이언트 처리
def handle_client(client_socket, client_address):
    print(f"클라이언트 {client_address} 연결됨")
    client_socket.settimeout(10)

    try:
        while True:
            encrypted = client_socket.recv(1024)
            if not encrypted:
                print(f"{client_address} 연결 종료 요청")
                break
            print(f"[{client_address}] 데이터 수신 완료")
            try:
                decrypted_data = decrypt(encrypted, private_key)
            except Exception as e:
                print(f"복호화 실패 from {client_address}: {e}")
                continue

            try:
                parsed = parsing.parse_packet(decrypted_data)
                if parsed:
                    print(f"[{client_address}] 데이터 수신 완료")
                    # ID 기반 정보 분해
                    result_id = str(parsed["ID"])
                    time_str = str(parsed["TIME"])  # TIME이 이미 str이어야 하지만, 안전을 위해 변환
                    location = str(parsed["LOC"])

                    # ✅ 센서별 저장
                    insert_sensor_result(result_id + "_TEMP", "TEMP", 1, 1, parsed["TEMP"], location, time_str)  # value_type_id = 1
                    insert_sensor_result(result_id + "_O2", "O2", 2, 2, parsed["O2"], location, time_str)       # value_type_id = 2
                    insert_sensor_result(result_id + "_WTR", "WTR", 3, 3, parsed["WTR_TEMP"], location, time_str)  # value_type_id = 3

                    # ✅ 원문 저장
                    insert_raw_packet_log(result_id + "_RAW", "default_device", decrypted_data, time_str)
                    print(f"DB 삽입 시도: {parsed}")
                    print(f"[{client_address}] 데이터베이스에 저장됨 (sensor_result 사용)")

                else:
                    print(f"[{client_address}] 유효하지 않은 패킷")

            except Exception as e:
                print(f"[{client_address}] 파싱 오류: {e}")

    except socket.timeout:
        print(f"[{client_address}] 연결 타임아웃")
    finally:
        client_socket.close()
        print(f"연결 종료: {client_address}\n")

# 서버 시작
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"서버가 {HOST}:{PORT}에서 클라이언트 대기 중")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n서버 종료 요청됨")
    finally:    
        server_socket.close()
        print("서버 소켓 닫힘")
        db.close()
        print("DB 연결 종료")

if __name__ == "__main__":
    start_server()
