import socket
import threading
from typing import Optional, Tuple

class KeyExchangeHandler:
    """Handle ECDHE key exchange protocol with clients"""
    
    def __init__(self, console_manager=None, crypto_manager=None):
        self.console_manager = console_manager
        self.crypto_manager = crypto_manager
        self.exchange_lock = threading.Lock()
        
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
    
    def handle_key_exchange_request(self, client_socket: socket.socket, request_data: str) -> Tuple[bool, Optional[str]]:
        """Handle ECDHE key exchange request from client"""
        try:
            # Parse request: "ECDHE_KEY_EXCHANGE:device_id:client_public_key_hex"
            parts = request_data.split(':', 2)
            if len(parts) != 3 or parts[0] != "ECDHE_KEY_EXCHANGE":
                self._log("Invalid key exchange request format", "error")
                self._send_error_response(client_socket, "Invalid request format")
                return False, None
            
            device_id = parts[1]
            client_public_key_hex = parts[2]
            
            self._log(f"Processing ECDHE key exchange for device: {device_id}")
            
            # Validate device ID
            if not device_id or len(device_id) > 64:
                self._log(f"Invalid device ID: {device_id}", "error")
                self._send_error_response(client_socket, "Invalid device ID")
                return False, None
            
            # Validate client public key
            if len(client_public_key_hex) != 64:  # 32 bytes = 64 hex chars
                self._log(f"Invalid client public key length: {len(client_public_key_hex)}", "error")
                self._send_error_response(client_socket, "Invalid public key format")
                return False, None
            
            try:
                client_public_key_bytes = bytes.fromhex(client_public_key_hex)
            except ValueError:
                self._log("Invalid hex format for client public key", "error")
                self._send_error_response(client_socket, "Invalid public key encoding")
                return False, None
            
            # Perform ECDHE key exchange with crypto manager
            with self.exchange_lock:
                if not self.crypto_manager or not self.crypto_manager.is_initialized():
                    self._log("Crypto manager not initialized", "error")
                    self._send_error_response(client_socket, "Server crypto system not ready")
                    return False, None
                
                try:
                    # Perform key exchange (returns salt now)
                    server_public_key_bytes, signature, hkdf_salt = self.crypto_manager.perform_key_exchange(
                        device_id, client_public_key_bytes
                    )

                    # Get server's Ed25519 public key for client verification
                    server_ed25519_public_key = self.crypto_manager.get_server_public_key()

                    # Prepare response: server_x25519_pubkey (32) + signature (64) + server_ed25519_pubkey (32) + hkdf_salt (16)
                    response_data = server_public_key_bytes + signature + server_ed25519_public_key + hkdf_salt
                    
                    # Send response length first (4 bytes)
                    response_length = len(response_data)
                    client_socket.send(response_length.to_bytes(4, 'big'))
                    
                    # Send response data
                    client_socket.send(response_data)
                    
                    self._log(f"ECDHE key exchange completed successfully for device: {device_id}")
                    return True, device_id
                    
                except Exception as e:
                    self._log(f"Key exchange failed for device {device_id}: {e}", "error")
                    self._send_error_response(client_socket, f"Key exchange failed: {str(e)}")
                    return False, None
                    
        except Exception as e:
            self._log(f"Key exchange handler error: {e}", "error")
            self._send_error_response(client_socket, "Internal server error")
            return False, None
    
    def _send_error_response(self, client_socket: socket.socket, error_message: str):
        """Send error response to client"""
        try:
            error_data = f"ERROR: {error_message}".encode()
            response_length = len(error_data)
            
            # Send response length first
            client_socket.send(response_length.to_bytes(4, 'big'))
            # Send error message
            client_socket.send(error_data)
            
        except Exception as e:
            self._log(f"Failed to send error response: {e}", "error")
    
    def is_key_exchange_request(self, data: bytes) -> bool:
        """Check if received data is a key exchange request"""
        try:
            decoded_data = data.decode('utf-8', errors='ignore')
            return decoded_data.startswith("ECDHE_KEY_EXCHANGE:")
        except:
            return False
    
    def get_exchange_stats(self) -> dict:
        """Get key exchange statistics"""
        if self.crypto_manager:
            return {
                'active_sessions': self.crypto_manager.get_active_session_count(),
                'crypto_initialized': self.crypto_manager.is_initialized()
            }
        return {
            'active_sessions': 0,
            'crypto_initialized': False
        }