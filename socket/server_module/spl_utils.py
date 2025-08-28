import pymysql
from pymysql.cursors import DictCursor

DB_CONFIG = {
    "host": "localhost",
    "user": "your_user",
    "password": "your_password",
    "database": "sensor_db",
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
}

def insert_sensor_data(packet):
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for sensor in packet["sensors"]:
            sql = """
            INSERT INTO sensor_result (device_id, sensor_id, value_type_id, value, location, timestamp, alarm_state, error_state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                packet["device_id"],
                sensor["sensor_id"],
                sensor["value_type_id"],
                sensor["value"],
                sensor["location"],
                packet["timestamp"],
                sensor["alarm_state"],
                sensor["error_state"]
            ))
        conn.commit()
    except Exception as e:
        print(f"DB 저장 오류: {e}")
    finally:
        if conn:
            conn.close()
