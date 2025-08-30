from enum import Enum
from typing import Dict, Any, Optional
import time
from datetime import datetime, timedelta

class AlarmType(Enum):
    PARSING_ERROR = 0
    TEMP_HIGH = 1
    TEMP_LOW = 2
    DO_HIGH = 3
    DO_LOW = 4
    PACKET_ERROR = 5
    DB_ERROR = 6
    WTR_TEMP_HIGH = 7
    WTR_TEMP_LOW = 8
    UNAUTHORIZED_DEVICE = 9
    PACKET_CORRUPTION = 10
    SENSOR_OFFLINE = 11
    ENCRYPTION_ERROR = 12
    DATA_ANOMALY = 13
    CONNECTION_TIMEOUT = 14
    MISSING_DATA = 15
    DEVICE_VALIDATION_FAILED = 16
    # 새로 추가되는 알람 타입들
    SENSOR_RANGE_EXCEEDED = 17
    SENSOR_RESOLUTION_ERROR = 18
    SENSOR_TIMING_ERROR = 19
    DATA_JUMP_ANOMALY = 20
    DATA_STUCK_ANOMALY = 21
    SENSOR_CALIBRATION_ERROR = 22

class AlarmManager:
    def __init__(self, console_manager=None, database_manager=None):
        self.console_manager = console_manager
        self.database_manager = database_manager
        self.last_sensor_data = {}  # Store last data by sensor
        self.sensor_last_received = {}  # Store last received time by sensor
        
        # Alarm message templates by alarm type
        self.alarm_messages = {
            AlarmType.PARSING_ERROR: "Packet parsing failed: {details}",
            AlarmType.TEMP_HIGH: "Temperature upper limit exceeded: {value}°C (threshold: {threshold}°C)",
            AlarmType.TEMP_LOW: "Temperature lower limit exceeded: {value}°C (threshold: {threshold}°C)",
            AlarmType.DO_HIGH: "Dissolved oxygen upper limit exceeded: {value}ppm (threshold: {threshold}ppm)",
            AlarmType.DO_LOW: "Dissolved oxygen lower limit exceeded: {value}ppm (threshold: {threshold}ppm)",
            AlarmType.PACKET_ERROR: "Packet reception error: {details}",
            AlarmType.DB_ERROR: "Database error: {details}",
            AlarmType.WTR_TEMP_HIGH: "Water temperature upper limit exceeded: {value}°C (threshold: {threshold}°C)",
            AlarmType.WTR_TEMP_LOW: "Water temperature lower limit exceeded: {value}°C (threshold: {threshold}°C)",
            AlarmType.UNAUTHORIZED_DEVICE: "Unauthorized device access: {details}",
            AlarmType.PACKET_CORRUPTION: "Packet corruption detected: {details}",
            AlarmType.SENSOR_OFFLINE: "Sensor offline: {details}",
            AlarmType.ENCRYPTION_ERROR: "Encryption error: {details}",
            AlarmType.DATA_ANOMALY: "Data anomaly pattern: {details}",
            AlarmType.CONNECTION_TIMEOUT: "Connection timeout: {details}",
            AlarmType.MISSING_DATA: "Required data missing: {details}",
            AlarmType.DEVICE_VALIDATION_FAILED: "Device validation failed: {details}",
            AlarmType.SENSOR_RANGE_EXCEEDED: "Sensor measurement range exceeded: {value} (range: {sensor_min}~{sensor_max})",
            AlarmType.SENSOR_RESOLUTION_ERROR: "Sensor resolution error: {value} (resolution: {resolution})",
            AlarmType.SENSOR_TIMING_ERROR: "Sensor timing error: {details}",
            AlarmType.DATA_JUMP_ANOMALY: "Data jump anomaly: {details}",
            AlarmType.DATA_STUCK_ANOMALY: "Data stuck anomaly: {details}",
            AlarmType.SENSOR_CALIBRATION_ERROR: "Sensor calibration error: {details}"
        }
    
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
        else:
            # Silently ignore when console manager is absent (panel system priority)
            pass
    
    def trigger_alarm(self, alarm_type: AlarmType, sensor_id: str, details: str = "", **kwargs):
        """Trigger alarm"""
        try:
            # Generate alarm message
            message_template = self.alarm_messages.get(alarm_type, "Unknown alarm: {details}")
            alarm_message = message_template.format(details=details, **kwargs)
            
            # Output alarm to console
            self._log(f"ALARM [Sensor {sensor_id}]: {alarm_message}", "error")
            
            # Save alarm to database
            if self.database_manager:
                success = self.database_manager.insert_alarm_log(
                    sensor_id=sensor_id,
                    alarm_type_id=alarm_type.value,
                    alarm_message=alarm_message
                )
                if success:
                    self._log(f"Alarm log saved successfully: {alarm_type.name}")
                else:
                    self._log(f"Alarm log save failed: {alarm_type.name}", "error")
            
            return True
            
        except Exception as e:
            self._log(f"Error while processing alarm: {e}", "error")
            return False
    
    def check_sensor_thresholds(self, sensor_info: Dict[str, Any], sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check sensor value thresholds and sensor specifications"""
        result = {
            'alarm_triggered': False,
            'error_detected': False,
            'alarm_types': [],
            'error_types': []
        }
        
        try:
            # Check if required keys exist
            if 'ID' not in sensor_data:
                self._log(f"Missing 'ID' key in sensor data: {list(sensor_data.keys())}", "error")
                result['error_detected'] = True
                result['error_types'].append('missing_sensor_id')
                return result
                
            sensor_id = str(sensor_data['ID'])
            sensor_type_id = sensor_info.get('sensor_type_id')
            
            if sensor_type_id is None:
                self._log(f"Missing sensor_type_id for sensor {sensor_id}", "error")
                result['error_detected'] = True
                result['error_types'].append('missing_sensor_type')
                return result
                
            alarm_min = sensor_info.get('alarm_min')
            alarm_max = sensor_info.get('alarm_max')
            sensor_min = sensor_info.get('sensor_min')
            sensor_max = sensor_info.get('sensor_max')
            resolution = sensor_info.get('resolution')
            
            # 센서 타입별 값 확인
            if sensor_type_id == 0:  # temp_sensor
                temp_value = sensor_data['TEMP']
                
                # Check sensor measurement range
                if sensor_min is not None and sensor_max is not None:
                    if temp_value < sensor_min or temp_value > sensor_max:
                        self.trigger_alarm(AlarmType.SENSOR_RANGE_EXCEEDED, sensor_id,
                                         value=temp_value, sensor_min=sensor_min, sensor_max=sensor_max)
                        result['alarm_triggered'] = True
                        result['alarm_types'].append(AlarmType.SENSOR_RANGE_EXCEEDED.value)
                
                # Check resolution
                if resolution is not None and resolution > 0:
                    decimal_places = len(str(temp_value).split('.')[-1]) if '.' in str(temp_value) else 0
                    expected_decimal_places = len(str(resolution).split('.')[-1]) if '.' in str(resolution) else 0
                    if decimal_places > expected_decimal_places:
                        self.trigger_alarm(AlarmType.SENSOR_RESOLUTION_ERROR, sensor_id,
                                         value=temp_value, resolution=resolution)
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.SENSOR_RESOLUTION_ERROR.value)
                
                # Check alarm thresholds
                if temp_value > alarm_max:
                    self.trigger_alarm(AlarmType.TEMP_HIGH, sensor_id, 
                                     value=temp_value, threshold=alarm_max)
                    result['alarm_triggered'] = True
                    result['alarm_types'].append(AlarmType.TEMP_HIGH.value)
                elif temp_value < alarm_min:
                    self.trigger_alarm(AlarmType.TEMP_LOW, sensor_id,
                                     value=temp_value, threshold=alarm_min)
                    result['alarm_triggered'] = True
                    result['alarm_types'].append(AlarmType.TEMP_LOW.value)
                    
            elif sensor_type_id == 1:  # wtr_temp_sensor
                wtr_temp_value = sensor_data['WTR_TEMP']
                
                # Check sensor measurement range
                if sensor_min is not None and sensor_max is not None:
                    if wtr_temp_value < sensor_min or wtr_temp_value > sensor_max:
                        self.trigger_alarm(AlarmType.SENSOR_RANGE_EXCEEDED, sensor_id,
                                         value=wtr_temp_value, sensor_min=sensor_min, sensor_max=sensor_max)
                        result['alarm_triggered'] = True
                        result['alarm_types'].append(AlarmType.SENSOR_RANGE_EXCEEDED.value)
                
                # Check resolution
                if resolution is not None and resolution > 0:
                    decimal_places = len(str(wtr_temp_value).split('.')[-1]) if '.' in str(wtr_temp_value) else 0
                    expected_decimal_places = len(str(resolution).split('.')[-1]) if '.' in str(resolution) else 0
                    if decimal_places > expected_decimal_places:
                        self.trigger_alarm(AlarmType.SENSOR_RESOLUTION_ERROR, sensor_id,
                                         value=wtr_temp_value, resolution=resolution)
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.SENSOR_RESOLUTION_ERROR.value)
                
                # Check alarm thresholds
                if wtr_temp_value > alarm_max:
                    self.trigger_alarm(AlarmType.WTR_TEMP_HIGH, sensor_id,
                                     value=wtr_temp_value, threshold=alarm_max)
                    result['alarm_triggered'] = True
                    result['alarm_types'].append(AlarmType.WTR_TEMP_HIGH.value)
                elif wtr_temp_value < alarm_min:
                    self.trigger_alarm(AlarmType.WTR_TEMP_LOW, sensor_id,
                                     value=wtr_temp_value, threshold=alarm_min)
                    result['alarm_triggered'] = True
                    result['alarm_types'].append(AlarmType.WTR_TEMP_LOW.value)
                    
            elif sensor_type_id == 2:  # do_sensor
                do_value = sensor_data['DO']
                
                # Check sensor measurement range
                if sensor_min is not None and sensor_max is not None:
                    if do_value < sensor_min or do_value > sensor_max:
                        self.trigger_alarm(AlarmType.SENSOR_RANGE_EXCEEDED, sensor_id,
                                         value=do_value, sensor_min=sensor_min, sensor_max=sensor_max)
                        result['alarm_triggered'] = True
                        result['alarm_types'].append(AlarmType.SENSOR_RANGE_EXCEEDED.value)
                
                # Check resolution
                if resolution is not None and resolution > 0:
                    decimal_places = len(str(do_value).split('.')[-1]) if '.' in str(do_value) else 0
                    expected_decimal_places = len(str(resolution).split('.')[-1]) if '.' in str(resolution) else 0
                    if decimal_places > expected_decimal_places:
                        self.trigger_alarm(AlarmType.SENSOR_RESOLUTION_ERROR, sensor_id,
                                         value=do_value, resolution=resolution)
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.SENSOR_RESOLUTION_ERROR.value)
                
                # Check alarm thresholds
                if do_value > alarm_max:
                    self.trigger_alarm(AlarmType.DO_HIGH, sensor_id,
                                     value=do_value, threshold=alarm_max)
                    result['alarm_triggered'] = True
                    result['alarm_types'].append(AlarmType.DO_HIGH.value)
                elif do_value < alarm_min:
                    self.trigger_alarm(AlarmType.DO_LOW, sensor_id,
                                     value=do_value, threshold=alarm_min)
                    result['alarm_triggered'] = True
                    result['alarm_types'].append(AlarmType.DO_LOW.value)
            
            return result
            
        except Exception as e:
            self._log(f"Error while checking thresholds: {e}", "error")
            return result
    
    # Convenience methods for various error situations
    def alarm_parsing_error(self, sensor_id: str, error_details: str):
        """Parsing error alarm"""
        return self.trigger_alarm(AlarmType.PARSING_ERROR, sensor_id, error_details)
    
    def alarm_packet_error(self, sensor_id: str, error_details: str):
        """Packet reception error alarm"""
        return self.trigger_alarm(AlarmType.PACKET_ERROR, sensor_id, error_details)
    
    def alarm_db_error(self, sensor_id: str, error_details: str):
        """Database error alarm"""
        return self.trigger_alarm(AlarmType.DB_ERROR, sensor_id, error_details)
    
    def alarm_unauthorized_device(self, device_id: str, client_addr: str):
        """Unauthorized device alarm"""
        return self.trigger_alarm(AlarmType.UNAUTHORIZED_DEVICE, "unknown", 
                                f"Device {device_id}, Client {client_addr}")
    
    def alarm_packet_corruption(self, sensor_id: str, error_details: str):
        """Packet corruption alarm"""
        return self.trigger_alarm(AlarmType.PACKET_CORRUPTION, sensor_id, error_details)
    
    def alarm_encryption_error(self, sensor_id: str, error_details: str):
        """Encryption error alarm"""
        return self.trigger_alarm(AlarmType.ENCRYPTION_ERROR, sensor_id, error_details)
    
    def alarm_connection_timeout(self, client_addr: str):
        """Connection timeout alarm"""
        return self.trigger_alarm(AlarmType.CONNECTION_TIMEOUT, "unknown", 
                                f"Client {client_addr}")
    
    def alarm_device_validation_failed(self, device_id: str, client_addr: str):
        """Device validation failed alarm"""
        return self.trigger_alarm(AlarmType.DEVICE_VALIDATION_FAILED, "unknown",
                                f"Device {device_id}, Client {client_addr}")
    
    def check_sensor_timing(self, sensor_info: Dict[str, Any], sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sensor timing verification"""
        result = {
            'error_detected': False,
            'error_types': []
        }
        
        try:
            sensor_id = str(sensor_data['ID'])
            sensing_period = sensor_info.get('sensing_period')
            transfer_period = sensor_info.get('transfer_period')
            current_time = time.time()
            
            # Record last reception time
            if sensor_id in self.sensor_last_received:
                last_time = self.sensor_last_received[sensor_id]
                time_diff = current_time - last_time
                
                # Check transfer_period (compare expected transmission interval with actual interval)
                if transfer_period and transfer_period > 0:
                    # 20% tolerance
                    min_expected = transfer_period * 0.8
                    max_expected = transfer_period * 1.2
                    
                    if time_diff < min_expected:
                        self.trigger_alarm(AlarmType.SENSOR_TIMING_ERROR, sensor_id,
                                         f"Transmission interval too fast: {time_diff:.1f}s (expected: {transfer_period}s)")
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.SENSOR_TIMING_ERROR.value)
                    elif time_diff > max_expected:
                        self.trigger_alarm(AlarmType.SENSOR_TIMING_ERROR, sensor_id,
                                         f"Transmission interval delayed: {time_diff:.1f}s (expected: {transfer_period}s)")
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.SENSOR_TIMING_ERROR.value)
            
            self.sensor_last_received[sensor_id] = current_time
            return result
            
        except Exception as e:
            self._log(f"Error while checking sensor timing: {e}", "error")
            return result
    
    def check_data_anomalies(self, sensor_info: Dict[str, Any], sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Data anomaly pattern detection"""
        result = {
            'error_detected': False,
            'error_types': []
        }
        
        try:
            sensor_id = str(sensor_data['ID'])
            sensor_type_id = sensor_info['sensor_type_id']
            
            current_value = None
            
            # Extract current value by sensor type
            if sensor_type_id == 0:  # temp_sensor
                current_value = sensor_data['TEMP']
            elif sensor_type_id == 1:  # wtr_temp_sensor
                current_value = sensor_data['WTR_TEMP']
            elif sensor_type_id == 2:  # do_sensor
                current_value = sensor_data['DO']
            
            if current_value is not None and sensor_id in self.last_sensor_data:
                last_value = self.last_sensor_data[sensor_id]
                
                # Detect sudden changes
                change_rate = abs(current_value - last_value)
                if sensor_type_id in [0, 1]:  # Temperature sensors
                    if change_rate > 10.0:  # Sudden change of 10 degrees or more
                        self.trigger_alarm(AlarmType.DATA_JUMP_ANOMALY, sensor_id,
                                         f"Temperature sudden change: {last_value:.1f}°C → {current_value:.1f}°C")
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.DATA_JUMP_ANOMALY.value)
                elif sensor_type_id == 2:  # DO 센서
                    if change_rate > 5.0:  # Sudden change of 5ppm or more
                        self.trigger_alarm(AlarmType.DATA_JUMP_ANOMALY, sensor_id,
                                         f"Dissolved oxygen sudden change: {last_value:.1f}ppm → {current_value:.1f}ppm")
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.DATA_JUMP_ANOMALY.value)
                
                # Data stuck detection (consecutive same values)
                if abs(current_value - last_value) < 0.01:  # Nearly identical values
                    if not hasattr(self, 'stuck_counter'):
                        self.stuck_counter = {}
                    
                    if sensor_id not in self.stuck_counter:
                        self.stuck_counter[sensor_id] = 0
                    
                    self.stuck_counter[sensor_id] += 1
                    
                    # Trigger alarm if 10 consecutive identical values
                    if self.stuck_counter[sensor_id] >= 10:
                        self.trigger_alarm(AlarmType.DATA_STUCK_ANOMALY, sensor_id,
                                         f"Data stuck: {current_value} (consecutive {self.stuck_counter[sensor_id]} times)")
                        result['error_detected'] = True
                        result['error_types'].append(AlarmType.DATA_STUCK_ANOMALY.value)
                        self.stuck_counter[sensor_id] = 0
                else:
                    # Reset counter if value changed
                    if hasattr(self, 'stuck_counter') and sensor_id in self.stuck_counter:
                        self.stuck_counter[sensor_id] = 0
            
            # Store current value as last value
            self.last_sensor_data[sensor_id] = current_value
            return result
            
        except Exception as e:
            self._log(f"Error while detecting data anomalies: {e}", "error")
            return result
    
    def check_sensor_offline(self, timeout_seconds: int = 300) -> bool:
        """Offline sensor detection (5-minute timeout)"""
        try:
            current_time = time.time()
            alarm_triggered = False
            
            offline_sensors = []
            for sensor_id, last_time in self.sensor_last_received.items():
                if current_time - last_time > timeout_seconds:
                    offline_sensors.append(sensor_id)
            
            for sensor_id in offline_sensors:
                offline_duration = current_time - self.sensor_last_received[sensor_id]
                self.trigger_alarm(AlarmType.SENSOR_OFFLINE, sensor_id,
                                 f"Sensor offline: No data received for {offline_duration:.0f} seconds")
                alarm_triggered = True
            
            return alarm_triggered
            
        except Exception as e:
            self._log(f"Error while checking offline sensors: {e}", "error")
            return False