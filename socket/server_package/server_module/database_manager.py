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

    def _create_connection_without_db(self):
        """Create MySQL connection without specifying database (for database creation)"""
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
        except pymysql.MySQLError as e:
            self._log(f"MySQL server connection failed: {e}", "error")
            return None

    def database_exists(self) -> bool:
        """Check if database exists"""
        conn = self._create_connection_without_db()
        if conn is None:
            return False

        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW DATABASES LIKE %s", (self.database,))
                result = cursor.fetchone()
                return result is not None
        except pymysql.MySQLError as e:
            self._log(f"Database existence check failed: {e}", "error")
            return False
        finally:
            conn.close()

    def create_database(self) -> bool:
        """Create database automatically"""
        self._log(f"Creating database '{self.database}'...")

        conn = self._create_connection_without_db()
        if conn is None:
            self._log("Failed to connect to MySQL server", "error")
            return False

        try:
            with conn.cursor() as cursor:
                # Create database
                cursor.execute(f"CREATE DATABASE `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.commit()
                self._log(f"Database '{self.database}' created successfully", "info")
                return True
        except pymysql.MySQLError as e:
            self._log(f"Database creation failed: {e}", "error")
            return False
        finally:
            conn.close()

    def create_tables(self) -> bool:
        """Create all required tables automatically"""
        self._log("Creating database tables...")

        # Table creation SQL statements
        tables = {
            'device_info': """
                CREATE TABLE IF NOT EXISTS `device_info` (
                    `device_id` VARCHAR(50) PRIMARY KEY COMMENT 'Device ID',
                    `device_name` VARCHAR(100) COMMENT 'Device name',
                    `device_type` VARCHAR(50) COMMENT 'Device type',
                    `registered_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Registration time'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Device information table';
            """,
            'sensor_type': """
                CREATE TABLE IF NOT EXISTS `sensor_type` (
                    `sensor_type_id` INT PRIMARY KEY COMMENT 'Sensor type ID (0:temp, 1:wtr_temp, 2:do)',
                    `sensor_type_name` VARCHAR(50) NOT NULL COMMENT 'Sensor type name'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sensor type table';
            """,
            'value_type': """
                CREATE TABLE IF NOT EXISTS `value_type` (
                    `value_type_id` INT PRIMARY KEY COMMENT 'Value type ID (1:temp, 2:do, 3:wtr_temp)',
                    `value_type_name` VARCHAR(50) NOT NULL COMMENT 'Value type name',
                    `unit` VARCHAR(20) COMMENT 'Unit'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Value type table';
            """,
            'sensor_info': """
                CREATE TABLE IF NOT EXISTS `sensor_info` (
                    `sensor_id` VARCHAR(20) PRIMARY KEY COMMENT 'Sensor ID',
                    `device_id` VARCHAR(50) NOT NULL COMMENT 'Device ID',
                    `sensor_type_id` INT NOT NULL COMMENT 'Sensor type ID',
                    `sensor_name` VARCHAR(100) COMMENT 'Sensor name',
                    `alarm_min` DECIMAL(10,2) COMMENT 'Alarm threshold (minimum)',
                    `alarm_max` DECIMAL(10,2) COMMENT 'Alarm threshold (maximum)',
                    `sensor_min` DECIMAL(10,2) COMMENT 'Sensor measurement range (minimum)',
                    `sensor_max` DECIMAL(10,2) COMMENT 'Sensor measurement range (maximum)',
                    `resolution` DECIMAL(10,4) COMMENT 'Sensor resolution',
                    `registered_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Registration time',
                    FOREIGN KEY (`device_id`) REFERENCES `device_info`(`device_id`) ON DELETE CASCADE,
                    FOREIGN KEY (`sensor_type_id`) REFERENCES `sensor_type`(`sensor_type_id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sensor information table';
            """,
            'alarm_type': """
                CREATE TABLE IF NOT EXISTS `alarm_type` (
                    `alarm_type_id` INT PRIMARY KEY COMMENT 'Alarm type ID',
                    `alarm_type_name` VARCHAR(50) NOT NULL COMMENT 'Alarm type name'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Alarm type table';
            """,
            'sensor_result': """
                CREATE TABLE IF NOT EXISTS `sensor_result` (
                    `result_id` VARCHAR(20) PRIMARY KEY COMMENT 'Result ID',
                    `device_id` VARCHAR(50) NOT NULL COMMENT 'Device ID',
                    `sensor_id` VARCHAR(20) NOT NULL COMMENT 'Sensor ID',
                    `value_type_id` INT NOT NULL COMMENT 'Value type ID',
                    `sensor_value` DECIMAL(10,4) COMMENT 'Sensor measurement value',
                    `alarm_state` INT DEFAULT 0 COMMENT 'Alarm state (0:normal, 1~:alarm type)',
                    `error_state` INT DEFAULT 0 COMMENT 'Error state (0:normal, 1:error)',
                    `location` VARCHAR(100) COMMENT 'Measurement location',
                    `measured_at` DATETIME NOT NULL COMMENT 'Measurement time',
                    FOREIGN KEY (`sensor_id`) REFERENCES `sensor_info`(`sensor_id`) ON DELETE CASCADE,
                    FOREIGN KEY (`value_type_id`) REFERENCES `value_type`(`value_type_id`),
                    INDEX idx_measured_at (`measured_at`),
                    INDEX idx_device_sensor (`device_id`, `sensor_id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Sensor measurement result table';
            """,
            'alarm_log': """
                CREATE TABLE IF NOT EXISTS `alarm_log` (
                    `alarm_id` VARCHAR(20) PRIMARY KEY COMMENT 'Alarm ID',
                    `alarmed_at` DATETIME NOT NULL COMMENT 'Alarm occurrence time',
                    `sensor_id` VARCHAR(20) NOT NULL COMMENT 'Sensor ID',
                    `alarm_type_id` INT NOT NULL COMMENT 'Alarm type ID',
                    `alarm_log` TEXT COMMENT 'Alarm log message',
                    FOREIGN KEY (`sensor_id`) REFERENCES `sensor_info`(`sensor_id`) ON DELETE CASCADE,
                    FOREIGN KEY (`alarm_type_id`) REFERENCES `alarm_type`(`alarm_type_id`),
                    INDEX idx_alarmed_at (`alarmed_at`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Alarm log table';
            """,
            'raw_packet_log': """
                CREATE TABLE IF NOT EXISTS `raw_packet_log` (
                    `packet_id` VARCHAR(20) PRIMARY KEY COMMENT 'Packet ID',
                    `device_id` VARCHAR(50) COMMENT 'Device ID',
                    `received_at` DATETIME NOT NULL COMMENT 'Packet reception time',
                    `packet_log` TEXT COMMENT 'Raw packet data (hexadecimal)',
                    `parse_success` TINYINT(1) DEFAULT 1 COMMENT 'Parse success (0:fail, 1:success)',
                    INDEX idx_received_at (`received_at`),
                    INDEX idx_device_id (`device_id`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Raw packet log table';
            """
        }

        try:
            for table_name, create_sql in tables.items():
                result = self.execute_query(create_sql)
                if result is not None:
                    self._log(f"Table '{table_name}' created successfully")
                else:
                    self._log(f"Failed to create table '{table_name}'", "error")
                    return False

            self._log("All tables created successfully", "info")
            return True

        except Exception as e:
            self._log(f"Table creation error: {e}", "error")
            return False

    def insert_default_data(self) -> bool:
        """Insert default master data"""
        self._log("Inserting default data...")

        try:
            # Insert sensor types
            sensor_types = [
                (0, 'Temperature Sensor'),
                (1, 'Water Temperature Sensor'),
                (2, 'Dissolved Oxygen Sensor')
            ]
            for type_id, type_name in sensor_types:
                self.execute_query(
                    "INSERT IGNORE INTO sensor_type (sensor_type_id, sensor_type_name) VALUES (%s, %s)",
                    (type_id, type_name)
                )

            # Insert value types
            value_types = [
                (1, 'Temperature', '°C'),
                (2, 'Dissolved Oxygen', 'mg/L'),
                (3, 'Water Temperature', '°C')
            ]
            for type_id, type_name, unit in value_types:
                self.execute_query(
                    "INSERT IGNORE INTO value_type (value_type_id, value_type_name, unit) VALUES (%s, %s, %s)",
                    (type_id, type_name, unit)
                )

            # Insert alarm types
            alarm_types = [
                (0, 'Normal'),
                (1, 'High Threshold Alarm'),
                (2, 'Low Threshold Alarm'),
                (3, 'Sensor Offline'),
                (4, 'Sensor Error'),
                (5, 'Data Anomaly'),
                (6, 'Range Overflow')
            ]
            for type_id, type_name in alarm_types:
                self.execute_query(
                    "INSERT IGNORE INTO alarm_type (alarm_type_id, alarm_type_name) VALUES (%s, %s)",
                    (type_id, type_name)
                )

            self._log("Default data inserted successfully", "info")
            return True

        except Exception as e:
            self._log(f"Default data insertion error: {e}", "error")
            return False

    def initialize_database(self) -> bool:
        """Initialize database (check existence, create if not exists, create tables)"""
        self._log("Starting database initialization...")

        # 1. Check if database exists
        if not self.database_exists():
            self._log(f"Database '{self.database}' does not exist", "warning")

            # 2. Create database
            if not self.create_database():
                self._log("Database creation failed", "error")
                return False
        else:
            self._log(f"Database '{self.database}' already exists")

        # 3. Create tables
        if not self.create_tables():
            self._log("Table creation failed", "error")
            return False

        # 4. Insert default data
        if not self.insert_default_data():
            self._log("Default data insertion failed", "error")
            return False

        self._log("Database initialization completed successfully", "info")
        return True