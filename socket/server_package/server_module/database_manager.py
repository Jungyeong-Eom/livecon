import pymysql
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
import threading
import binascii

class DatabaseManager:
    def __init__(self, console_manager=None, 
                 host='localhost', port=3306, user='root', 
                 password='fnqwha2001', database='livecon_db', 
                 charset='utf8mb4'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.console_manager = console_manager
        self._connection_lock = threading.Lock()
    
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
        else:
            # Silently ignore when console manager is absent (panel system priority)
            pass
    
    def _create_connection(self):
        """Create database connection"""
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
        except pymysql.MySQLError as e:
            self._log(f"Database connection failed: {e}", "error")
            return None
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        """Execute general query"""
        with self._connection_lock:
            conn = self._create_connection()
            if conn is None:
                return None
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    
                    if query.strip().upper().startswith("SELECT"):
                        result = cursor.fetchall()
                    else:
                        result = cursor.rowcount
                    
                    conn.commit()
                    return result
                    
            except pymysql.MySQLError as e:
                self._log(f"Query execution failed: Database error {e}", "error")
                conn.rollback()
                return None
            except Exception as e:
                self._log(f"Query execution failed: General error {e}", "error")
                conn.rollback()
                return None
            finally:
                conn.close()
    
    def select_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[Dict[str, Any]]]:
        """SELECT query specific method"""
        with self._connection_lock:
            conn = self._create_connection()
            if conn is None:
                return None
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchall()
                    return result
                    
            except pymysql.MySQLError as e:
                self._log(f"SELECT query execution failed: {e}", "error")
                return None
            except Exception as e:
                self._log(f"SELECT query execution failed: {e}", "error")
                return None
            finally:
                conn.close()
    
    def validate_device_id(self, device_id: str) -> bool:
        """Device ID validation"""
        try:
            rows = self.select_query("SELECT device_id FROM device_info")
            if rows is None:
                self._log("Database query for device ID validation failed", "error")
                return False
            
            device_ids = []
            for row in rows:
                device_ids.append(row['device_id'])
            
            self._log(f"Database device IDs: {device_ids}")
            self._log(f"Device ID to validate: {device_id}")
            
            return device_id in device_ids
            
        except Exception as e:
            self._log(f"Device ID validation error: {e}", "error")
            return False
    
    def insert_sensor_data(self, parsed_data: Dict[str, Any], sensor_status: Dict[str, Any] = None) -> bool:
        """Store parsed sensor data to database"""
        try:
            # Query sensor information based on device ID from packet
            device_id = parsed_data['DEVICE_ID']
            sensor = self.get_sensor_info_by_device_id(device_id)
            
            if not sensor:
                self._log(f"Cannot find information for device ID {device_id}", "error")
                return False
            sensor_type_id = sensor['sensor_type_id']
            sensor_id = sensor['sensor_id']  # Get sensor_id from sensor_info table
            
            # Determine data to store and value_type_id based on sensor type
            sensor_value = None
            value_type_id = None
            
            if sensor_type_id == 0:  # temp_sensor
                sensor_value = parsed_data['TEMP']
                value_type_id = 1  # temp
            elif sensor_type_id == 1:  # wtr_temp_sensor  
                sensor_value = parsed_data['WTR_TEMP']
                value_type_id = 3  # wtr_temp
            elif sensor_type_id == 2:  # do_sensor
                sensor_value = parsed_data['DO']
                value_type_id = 2  # do
            else:
                self._log(f"Unknown sensor type: {sensor_type_id}", "error")
                return False
            
            # Determine sensor status
            alarm_state = 0  # Default: Normal
            error_state = 0  # Default: Normal
            
            if sensor_status:
                # Set alarm status - directly store triggered alarm type ID
                if sensor_status.get('alarm_triggered', False):
                    alarm_types = sensor_status.get('alarm_types', [])
                    if alarm_types:
                        # Store first alarm type (when multiple alarms occur simultaneously)
                        alarm_state = alarm_types[0]
                
                # Set error status - simply occurred/not occurred (1/0)
                if sensor_status.get('error_detected', False):
                    error_state = 1  # Error occurred
                else:
                    error_state = 0  # No error
            
            # Current time and location information
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            location_str = f"{parsed_data['LOC'][0]:.6f},{parsed_data['LOC'][1]:.6f}"
            
            # Insert single record
            insert_query = """
            INSERT INTO sensor_result
            (result_id, device_id, sensor_id, value_type_id, sensor_value, 
             alarm_state, error_state, location, measured_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                str(uuid.uuid4())[:20],        # result_id
                parsed_data['DEVICE_ID'],      # device_id (패킷에서 파싱된 것)
                sensor_id,                     # sensor_id (실제 센서 ID)
                value_type_id,                 # value_type_id (센서 타입에 맞는 값)
                sensor_value,                  # sensor_value (해당 센서가 측정한 값)
                alarm_state,                   # alarm_state (알람 상태)
                error_state,                   # error_state (오류 상태)
                location_str,                  # location
                current_time                   # measured_at
            )
            
            result = self.execute_query(insert_query, params)
            if result is not None:
                sensor_type_names = {0: "Temperature", 1: "Water Temperature", 2: "Dissolved Oxygen"}
                status_info = ""
                if alarm_state > 0:
                    status_info += f" [AlarmType:{alarm_state}]"
                if error_state > 0:
                    status_info += f" [ErrorOccurred]"
                    
                self._log(f"{sensor_type_names.get(sensor_type_id, 'Unknown')} sensor data saved successfully{status_info}")
                return True
            else:
                self._log("Sensor data save failed", "error")
                return False
                
        except Exception as e:
            self._log(f"Error while saving sensor data: {e}", "error")
            return False
    
    def insert_raw_packet(self, raw_packet: bytes, device_id: str = None, parse_success: bool = True) -> bool:
        """Save raw packet to raw_packet_log table"""
        try:
            # Convert packet to hexadecimal string
            packet_hex = binascii.hexlify(raw_packet).decode('ascii').upper()
            
            # Format packet for readability (space-separated pairs)
            packet_formatted = ' '.join([packet_hex[i:i+2] for i in range(0, len(packet_hex), 2)])
            
            insert_query = """
            INSERT INTO raw_packet_log
            (packet_id, device_id, received_at, packet_log, parse_success)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                str(uuid.uuid4())[:20],                    # packet_id
                device_id,                                 # device_id 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # received_at
                packet_formatted,                          # packet_log (16진수 포맷)
                1 if parse_success else 0                  # parse_success
            )
            
            result = self.execute_query(insert_query, params)
            if result is not None:
                self._log(f"Raw packet log saved successfully ({len(raw_packet)} bytes)")
                return True
            else:
                self._log("Raw packet log save failed", "error")
                return False
                
        except Exception as e:
            self._log(f"Error while saving raw packet log: {e}", "error")
            return False
    
    def save_raw_packet(self, raw_data: bytes, device_id: str = None, parse_success: bool = True, **kwargs) -> bool:
        """Alias for insert_raw_packet for compatibility"""
        return self.insert_raw_packet(raw_data, device_id, parse_success)
    
    def insert_alarm_log(self, sensor_id: str, alarm_type_id: int, alarm_message: str) -> bool:
        """Save alarm log to alarm_log table"""
        try:
            insert_query = """
            INSERT INTO alarm_log
            (alarm_id, alarmed_at, sensor_id, alarm_type_id, alarm_log)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            params = (
                str(uuid.uuid4())[:20],                    # alarm_id
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # alarmed_at
                sensor_id,                                 # sensor_id
                alarm_type_id,                            # alarm_type_id
                alarm_message                             # alarm_log
            )
            
            result = self.execute_query(insert_query, params)
            if result is not None:
                self._log(f"Alarm log saved successfully: Type {alarm_type_id}, Sensor {sensor_id}")
                return True
            else:
                self._log("Alarm log save failed", "error")
                return False
                
        except Exception as e:
            self._log(f"Error while saving alarm log: {e}", "error")
            return False
    
    def get_sensor_info_by_id(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """Query sensor information by sensor ID (including alarm thresholds)"""
        try:
            rows = self.select_query("SELECT * FROM sensor_info WHERE sensor_id = %s", (sensor_id,))
            if rows and len(rows) > 0:
                return rows[0]
            return None
        except Exception as e:
            self._log(f"Sensor information query error: {e}", "error")
            return None
    
    def get_sensor_info_by_device_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Query sensor information by device ID (including alarm thresholds)"""
        try:
            rows = self.select_query("SELECT * FROM sensor_info WHERE device_id = %s", (device_id,))
            if rows and len(rows) > 0:
                return rows[0]
            return None
        except Exception as e:
            self._log(f"Sensor information query by device ID error: {e}", "error")
            return None
    
    def get_all_sensor_info_by_device_id(self, device_id: str) -> List[Dict[str, Any]]:
        """Query all sensor information for a device ID"""
        try:
            rows = self.select_query("SELECT * FROM sensor_info WHERE device_id = %s", (device_id,))
            return rows if rows else []
        except Exception as e:
            self._log(f"All sensor information query by device ID error: {e}", "error")
            return []