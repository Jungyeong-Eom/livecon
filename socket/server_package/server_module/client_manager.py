import socket
import time
from .packet_parser import PacketParser
from .connection_manager import ConnectionManager
from .key_exchange_handler import KeyExchangeHandler
from .alarm_manager import AlarmManager
from .sensor_monitor import SensorMonitor

class ClientManager:
    def __init__(self, console_manager=None, crypto_manager=None, database_manager=None):
        self.console_manager = console_manager
        self.crypto_manager = crypto_manager
        self.database_manager = database_manager
        
        # 전담 컴포넌트들
        self.packet_parser = PacketParser(console_manager=console_manager)
        self.connection_manager = ConnectionManager(console_manager=console_manager)
        self.key_exchange_handler = KeyExchangeHandler(console_manager=console_manager, crypto_manager=crypto_manager)
        self.alarm_manager = AlarmManager(console_manager=console_manager, database_manager=database_manager)
        self.sensor_monitor = SensorMonitor(alarm_manager=self.alarm_manager, console_manager=console_manager)
    
        
    def _log(self, message, level="info"):
        """로그 출력"""
        if self.console_manager:
            try:
                getattr(self.console_manager, level)(message)
            except Exception:
                # 로그 출력 오류 시 무시 (디스플레이 충돌 방지)
                pass
        else:
            # 콘솔 매니저가 없을 때는 조용히 무시 (패널 시스템 우선)
            pass
    
    
    def handle_client(self, client_socket, client_address):
        """클라이언트 연결 처리 - ECDHE 키 교환 지원"""
        client_addr_str = self.connection_manager.add_client(client_address)
        client_socket.settimeout(60)  # ECDHE 키 교환을 위해 타임아웃 증가
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 즉시 전송
        
        # 클라이언트 연결 통계 업데이트
        if self.console_manager:
            self.console_manager.update_client_stats(client_addr_str, 'connect')
        
        device_id = None  # 키 교환 후 설정됨
        
        try:
            while True:
                data = client_socket.recv(4096)  # ECDHE 키 교환을 위해 버퍼 크기 증가
                if not data:
                    self._log(f"[{client_addr_str}] Connection close requested")
                    break
                
                # ECDHE 키 교환 요청 처리
                if data.startswith(b"ECDHE_KEY_EXCHANGE:"):
                    device_id = self._handle_key_exchange(client_socket, data, client_addr_str)
                    if not device_id:
                        break
                    continue
                
                # 서버 공개키 요청 처리 (레거시 호환)
                if data == b"REQUEST_PUBLIC_KEY":
                    self._handle_legacy_public_key_request(client_socket, client_addr_str)
                    continue
                
                # 세션이 설정되지 않은 상태에서 데이터 수신
                if not device_id:
                    self._log(f"[{client_addr_str}] Data received before key exchange", "warning")
                    try:
                        client_socket.send(b"ERROR: KEY_EXCHANGE_REQUIRED")
                    except:
                        pass
                    break
                
                # 암호화된 데이터 처리 (ECDHE 세션 사용)
                if not self._handle_encrypted_data_with_session(data, device_id, client_addr_str):
                    break
                    
        except socket.timeout:
            self._log(f"[{client_addr_str}] Connection timeout")
            self.alarm_manager.alarm_connection_timeout(client_addr_str)
        except ConnectionResetError as e:
            self._log(f"[{client_addr_str}] Connection reset by client: {e}", "warning")
            # 클라이언트가 연결을 강제로 끊은 경우 - 정상적인 상황으로 처리
        except Exception as e:
            self._log(f"[{client_addr_str}] Connection error: {e}", "error")
            self.alarm_manager.alarm_packet_error("unknown", f"Connection error: {str(e)}")
        finally:
            client_socket.close()
            self.connection_manager.remove_client(client_addr_str)
            
            # 세션 정리
            if device_id and self.crypto_manager:
                self.crypto_manager.remove_session(device_id)
            
            # 클라이언트 연결 해제 통계 업데이트
            if self.console_manager:
                self.console_manager.update_client_stats(client_addr_str, 'disconnect')
    
    def _handle_key_exchange(self, client_socket, data, client_addr_str):
        """ECDHE 키 교환 처리"""
        try:
            # 데이터 형식: "ECDHE_KEY_EXCHANGE:<device_id>:<32-byte-x25519-public-key>"
            parts = data.decode().split(':', 2)
            if len(parts) != 3 or parts[0] != "ECDHE_KEY_EXCHANGE":
                self._log(f"[{client_addr_str}] Invalid key exchange format", "error")
                self._send_error_response(client_socket, "INVALID_KEY_EXCHANGE_FORMAT")
                return None
            
            device_id = parts[1]
            client_public_key_hex = parts[2]
            
            # X25519 공개키 파싱 (hex 형식)
            try:
                client_public_key_bytes = bytes.fromhex(client_public_key_hex)
                if len(client_public_key_bytes) != 32:
                    raise ValueError("Invalid key length")
            except ValueError:
                self._log(f"[{client_addr_str}] Invalid X25519 public key format", "error")
                self._send_error_response(client_socket, "INVALID_PUBLIC_KEY")
                return None
            
            # ECDHE 키 교환 수행
            server_public_key, signature = self.crypto_manager.perform_key_exchange(
                device_id, client_public_key_bytes
            )
            
            # 응답 전송: server_pubkey + signature + server_ed25519_pubkey
            server_ed25519_pubkey = self.crypto_manager.get_server_public_key()
            response = server_public_key + signature + server_ed25519_pubkey
            
            # 응답 길이 전송 (4바이트) 먼저
            response_length = len(response).to_bytes(4, 'big')
            client_socket.send(response_length)
            # 그 다음 응답 데이터 전송
            client_socket.send(response)
            
            self._log(f"[{client_addr_str}] ECDHE key exchange completed for device {device_id}")
            return device_id
            
        except Exception as e:
            self._log(f"[{client_addr_str}] Key exchange failed: {e}", "error")
            try:
                self._send_error_response(client_socket, "KEY_EXCHANGE_FAILED")
            except:
                pass
            return None
    
    def _send_error_response(self, client_socket, error_message):
        """Send error response with proper length header"""
        try:
            error_data = f"ERROR: {error_message}".encode()
            response_length = len(error_data)
            
            # Send response length first (4 bytes)
            client_socket.send(response_length.to_bytes(4, 'big'))
            # Send error message
            client_socket.send(error_data)
            
        except Exception as e:
            self._log(f"Failed to send error response: {e}", "error")
    
    def _handle_legacy_public_key_request(self, client_socket, client_addr_str):
        """레거시 RSA 공개키 요청 처리 (하위 호환성)"""
        try:
            # 클라이언트에게 ECDHE 사용을 권장하는 메시지 전송
            message = b"DEPRECATED: Use ECDHE_KEY_EXCHANGE instead"
            client_socket.send(len(message).to_bytes(4, 'big') + message)
            self._log(f"[{client_addr_str}] Legacy public key request - sent deprecation notice")
        except Exception as e:
            self._log(f"[{client_addr_str}] Failed to send legacy response: {e}", "error")
    
    def _handle_encrypted_data_with_session(self, data, device_id, client_addr_str):
        """세션 기반 암호화된 데이터 처리"""
        decrypted_data = None
        parsed = None
        parse_success = False
        start_time = time.time()
        
        try:
            # 세션 기반 복호화
            try:
                decrypted_data = self.crypto_manager.decrypt_data(device_id, data)
                self._log(f"[{client_addr_str}] Data decryption successful ({len(decrypted_data)} bytes)")
            except Exception as decrypt_error:
                self._log(f"[{client_addr_str}] Session decryption failed: {decrypt_error}", "error")
                self.alarm_manager.alarm_encryption_error(device_id, f"Session decryption failed: {str(decrypt_error)}")
                
                # 세션 만료 또는 암호화 오류 시 재연결 요청
                if "expired" in str(decrypt_error).lower() or "session" in str(decrypt_error).lower():
                    self._log(f"[{client_addr_str}] Session expired, requesting reconnection")
                return False
            
            # 패킷 파싱
            parsed = self.packet_parser.parse_packet(decrypted_data)
            if not parsed:
                self._log(f"[{client_addr_str}] Packet parsing failed", "error")
                # 파싱 실패 알람
                self.alarm_manager.alarm_parsing_error(device_id, "Packet structure error or checksum mismatch")
                # 파싱 실패해도 원본 패킷은 저장
                self._save_raw_packet(decrypted_data, device_id, False, client_addr_str)
                return True
            
            parse_success = True
            
            # 파싱된 device_id와 세션 device_id 일치 확인
            parsed_device_id = parsed['DEVICE_ID']
            if parsed_device_id != device_id:
                self._log(f"[{client_addr_str}] Device ID mismatch: session={device_id}, packet={parsed_device_id}", "warning")
                self.alarm_manager.alarm_authentication_failure(client_addr_str, "Device ID mismatch")
                return False
            
            self._log(f"[{client_addr_str}] Sensor data received - ID: {parsed['ID']}, Device: {device_id}, Temperature: {parsed['TEMP']}°C")
            self._log(f"DEBUG: Parsed data keys: {list(parsed.keys())}", "debug")
            self._log(f"DEBUG: Full parsed data: {parsed}", "debug")
            
            # 원본 패킷 저장 (파싱 성공)
            self._save_raw_packet(decrypted_data, device_id, parse_success, client_addr_str)
            
            # 디바이스 ID 확인
            if not self._validate_device_id(device_id, client_addr_str):
                self._log(f"[{client_addr_str}] Device ID validation failed, connection closed", "error")
                self.alarm_manager.alarm_device_validation_failed(device_id, client_addr_str)
                return False
            
            # 연결 매니저에 디바이스 ID 설정 (클라이언트 조회용)
            if self.connection_manager:
                self.connection_manager.set_client_device_id(client_addr_str, device_id)
            
            # 센서 임계값 확인 및 알람 처리
            sensor_status = self._check_sensor_alarms(parsed, client_addr_str)
            
            # 콘솔에 데이터 출력
            if self.console_manager:
                self.console_manager.display_sensor_data(parsed, client_addr_str)
            
            # 센서 데이터 저장 시도 (상태 정보 포함)
            self._save_sensor_data(parsed, client_addr_str, sensor_status)
            
        except Exception as e:
            self._log(f"[{client_addr_str}] Data processing error: {e}", "error")
            self.alarm_manager.alarm_packet_error(device_id, str(e))
            
            # 세션 만료 또는 암호화 오류 시 재연결 요청
            if "expired" in str(e).lower() or "session" in str(e).lower():
                self._log(f"[{client_addr_str}] Session expired, requesting reconnection")
            return False
        
        # 통계 업데이트
        response_time = (time.time() - start_time) * 1000
        if self.console_manager:
            self.console_manager.update_packet_stats(success=parse_success, response_time=response_time, 
                                                     latency=response_time, processing_time=response_time)
            self.console_manager.update_client_stats(client_addr_str, 'packet', success=parse_success, 
                                                    latency=response_time, processing_time=response_time)
            
            # 알람 통계 업데이트
            if parse_success and 'sensor_status' in locals() and sensor_status:
                if sensor_status.get('alarm_triggered', False):
                    self.console_manager.update_client_stats(client_addr_str, 'alarm')
                
                # 오류 통계 업데이트  
                if sensor_status.get('error_detected', False):
                    self.console_manager.update_client_stats(client_addr_str, 'error')
        
        return True
    
    def _validate_device_id(self, device_id, client_addr_str):
        """디바이스 ID 유효성 검사"""
        if not self.database_manager:
            self._log(f"[{client_addr_str}] Database manager not available, skipping device ID validation", "warning")
            return True
        
        try:
            is_valid = self.database_manager.validate_device_id(device_id)
            if not is_valid:
                self._log(f"[{client_addr_str}] Device ID '{device_id}' validation failed", "error")
                return False
            
            self._log(f"[{client_addr_str}] Device ID '{device_id}' validated successfully")
            return True
        except Exception as e:
            self._log(f"[{client_addr_str}] Device ID validation error: {e}", "error")
            return False
    
    def _check_sensor_alarms(self, parsed_data, client_addr_str):
        """센서 데이터 알람 확인 - device_id로 모든 센서 조회 후 각각 확인"""
        try:
            device_id = parsed_data['DEVICE_ID']
            overall_alarm_status = {'alarm_triggered': False, 'error_detected': False}
            
            # device_id로 모든 센서 정보 조회
            all_sensors = self.database_manager.get_all_sensor_info_by_device_id(device_id)
            if not all_sensors:
                self._log(f"[{client_addr_str}] No sensor info found for device: {device_id}", "warning")
                return {'alarm_triggered': False, 'error_detected': False}
            
            # 센서 유형과 데이터 키 매핑
            sensor_type_to_data_key = {
                0: 'TEMP',      # 온도 센서
                1: 'WTR_TEMP',  # 수온 센서
                2: 'DO'         # 용존산소 센서
            }
            
            # 각 센서별로 알람 확인
            for sensor_info in all_sensors:
                sensor_id = sensor_info['sensor_id']
                sensor_type_id = sensor_info['sensor_type_id']
                
                # 해당 센서 유형에 맞는 데이터 키 찾기
                data_key = sensor_type_to_data_key.get(sensor_type_id)
                if not data_key or data_key not in parsed_data:
                    continue
                
                # 해당 센서의 데이터만 포함한 딕셔너리 생성
                single_sensor_data = {
                    'DEVICE_ID': device_id,
                    'ID': sensor_id,
                    data_key: parsed_data[data_key]
                }
                
                self._log(f"[{client_addr_str}] Checking alarm for sensor_id: {sensor_id}, type: {sensor_type_id}, value: {parsed_data[data_key]}, thresholds: {sensor_info['alarm_min']}-{sensor_info['alarm_max']}")
                
                # 센서별 알람 확인 (sensor_info 전체 전달)
                alarm_status = self.alarm_manager.check_sensor_thresholds(sensor_info, single_sensor_data)
                
                # 전체 알람 상태 업데이트
                if alarm_status.get('alarm_triggered', False):
                    overall_alarm_status['alarm_triggered'] = True
                if alarm_status.get('error_detected', False):
                    overall_alarm_status['error_detected'] = True
                    
            return overall_alarm_status
            
        except Exception as e:
            self._log(f"[{client_addr_str}] Alarm check error: {e}", "error")
            return {'alarm_triggered': False, 'error_detected': True}
    
    def _save_raw_packet(self, raw_data, device_id, parse_success, client_addr_str):
        """원본 패킷 저장"""
        if not self.database_manager:
            return
            
        try:
            self.database_manager.save_raw_packet(
                raw_data=raw_data,
                device_id=device_id,
                client_address=client_addr_str,
                parse_success=parse_success
            )
        except Exception as e:
            self._log(f"[{client_addr_str}] Raw packet save error: {e}", "error")
    
    def _save_sensor_data(self, parsed_data, client_addr_str, sensor_status):
        """센서 데이터 저장"""
        if not self.database_manager:
            return
            
        try:
            self.database_manager.insert_sensor_data(parsed_data, sensor_status)
            self._log(f"[{client_addr_str}] Sensor data saved successfully for device {parsed_data['DEVICE_ID']}")
        except Exception as e:
            self._log(f"[{client_addr_str}] Sensor data save error: {e}", "error")
    
    # 기존 메서드들 (센서 모니터링 등)
    def start_sensor_monitoring(self):
        """센서 모니터링 시작"""
        if self.sensor_monitor:
            self.sensor_monitor.start_monitoring()
    
    def stop_sensor_monitoring(self):
        """센서 모니터링 중지"""
        if self.sensor_monitor:
            self.sensor_monitor.stop_monitoring()
    
    def disconnect_all_clients(self):
        """모든 클라이언트 연결 해제"""
        if self.connection_manager:
            self.connection_manager.disconnect_all_clients()
    
    def get_connected_clients(self):
        """연결된 클라이언트 목록 반환"""
        if self.connection_manager:
            return self.connection_manager.get_connected_clients()
        return []
    
    def get_monitoring_status(self):
        """센서 모니터링 상태 반환"""
        if self.sensor_monitor:
            return self.sensor_monitor.get_monitoring_status()
        return {}