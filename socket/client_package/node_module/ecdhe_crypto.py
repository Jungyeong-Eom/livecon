import secrets
import socket
from typing import Optional, Tuple
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

class AuthenticationError(Exception):
    """Authentication/signature verification failed"""
    pass

class ConnectionError(Exception):
    """Network connection failed"""  
    pass

class ECDHECrypto:
    """Client-side ECDHE + Ed25519 signature crypto with PFS"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.session_key = None
        self.cipher = None
        self.nonce_counter = 0
        self.server_ed25519_pubkey = None
        
    def perform_key_exchange(self, server_address: str, server_port: int) -> Optional[socket.socket]:
        """Perform ECDHE key exchange with server and return connected socket"""
        try:
            print(f"Starting ECDHE key exchange with server {server_address}:{server_port}")
            
            # Generate client's ephemeral X25519 key pair
            client_private_key = X25519PrivateKey.generate()
            client_public_key = client_private_key.public_key()
            
            # Get client's public key bytes
            client_public_key_bytes = client_public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            # Connect to server for key exchange
            exchange_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            exchange_socket.settimeout(120)  # 원격 연결을 위해 타임아웃 증가
            exchange_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 즉시 전송
            exchange_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # Keep-alive 활성화
            exchange_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 주소 재사용 허용
            try:
                exchange_socket.connect((server_address, server_port))
            except (socket.error, OSError) as e:
                raise ConnectionError(f"Failed to connect to server {server_address}:{server_port} - {e}")
            
            try:
                # Send key exchange request
                key_exchange_request = f"ECDHE_KEY_EXCHANGE:{self.device_id}:{client_public_key_bytes.hex()}"
                exchange_socket.send(key_exchange_request.encode())
                
                # Receive response length (4 bytes) with timeout handling
                response_length_bytes = b""
                while len(response_length_bytes) < 4:
                    try:
                        chunk = exchange_socket.recv(4 - len(response_length_bytes))
                        if not chunk:
                            raise Exception("Connection closed while receiving response length")
                        response_length_bytes += chunk
                    except socket.timeout:
                        raise ConnectionError("Timeout while receiving response length from server")
                
                response_length = int.from_bytes(response_length_bytes, 'big')
                print(f"Expecting key exchange response: {response_length} bytes")
                
                # Receive response data with improved error handling
                response_data = b""
                while len(response_data) < response_length:
                    try:
                        remaining = response_length - len(response_data)
                        chunk = exchange_socket.recv(min(remaining, 4096))  # 청크 크기 제한
                        if not chunk:
                            raise Exception("Connection closed during key exchange response")
                        response_data += chunk
                    except socket.timeout:
                        raise ConnectionError("Timeout while receiving key exchange response from server")
                
                if response_data.startswith(b"ERROR:"):
                    error_msg = response_data.decode()
                    # Check if it's authentication/signature failure
                    if "signature" in error_msg.lower() or "auth" in error_msg.lower() or "verify" in error_msg.lower():
                        raise AuthenticationError(f"Authentication failed: {error_msg}")
                    else:
                        raise ConnectionError(f"Server error: {error_msg}")
                
                # Parse response: server_x25519_pubkey (32) + signature (64) + server_ed25519_pubkey (32)
                if len(response_data) != 128:  # 32 + 64 + 32
                    raise Exception(f"Invalid response length: {len(response_data)} bytes")
                
                server_x25519_pubkey_bytes = response_data[:32]
                signature = response_data[32:96]
                self.server_ed25519_pubkey_bytes = response_data[96:128]
                
                # Verify signature
                server_ed25519_pubkey = Ed25519PublicKey.from_public_bytes(self.server_ed25519_pubkey_bytes)
                message_to_verify = server_x25519_pubkey_bytes + client_public_key_bytes + self.device_id.encode()
                
                try:
                    server_ed25519_pubkey.verify(signature, message_to_verify)
                    print("Server signature verification successful")
                except Exception:
                    raise AuthenticationError("Server signature verification failed - potential MITM attack")
                
                # Perform ECDHE
                server_x25519_pubkey = X25519PublicKey.from_public_bytes(server_x25519_pubkey_bytes)
                shared_secret = client_private_key.exchange(server_x25519_pubkey)
                
                # Derive session key using HKDF
                self.session_key = HKDF(
                    algorithm=hashes.SHA256(),
                    length=32,  # ChaCha20Poly1305 key size
                    salt=None,
                    info=f"session_key_{self.device_id}".encode()
                ).derive(shared_secret)
                
                # Initialize cipher with session key
                self.cipher = ChaCha20Poly1305(self.session_key)
                self.nonce_counter = 0
                
                print(f"ECDHE key exchange completed successfully for device {self.device_id}")
                print("Perfect Forward Secrecy (PFS) established")
                
                # Return the connected socket for data communication
                return exchange_socket
                
            except Exception:
                exchange_socket.close()
                raise
                
        except Exception as e:
            print(f"ECDHE key exchange failed: {e}")
            return None
    
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data with session key"""
        if not self.cipher:
            raise Exception("Session not established - perform key exchange first")
        
        nonce = self._get_next_nonce()
        ciphertext = self.cipher.encrypt(nonce, plaintext, None)
        return nonce + ciphertext
    
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data with session key"""
        if not self.cipher:
            raise Exception("Session not established - perform key exchange first")
        
        if len(ciphertext) < 12:
            raise ValueError("Ciphertext too short")
        
        nonce = ciphertext[:12]
        encrypted_data = ciphertext[12:]
        
        return self.cipher.decrypt(nonce, encrypted_data, None)
    
    def _get_next_nonce(self) -> bytes:
        """Generate unique nonce for each encryption"""
        self.nonce_counter += 1
        # 12 bytes nonce: 8 bytes counter + 4 bytes random
        counter_bytes = self.nonce_counter.to_bytes(8, 'big')
        random_bytes = secrets.token_bytes(4)
        return counter_bytes + random_bytes
    
    def is_session_active(self) -> bool:
        """Check if session is active"""
        return self.session_key is not None and self.cipher is not None
    
    def clear_session(self):
        """Clear session data for security"""
        if self.session_key:
            # Overwrite session key with random data
            self.session_key = secrets.token_bytes(32)
            self.session_key = None
        
        self.cipher = None
        self.nonce_counter = 0
        self.server_ed25519_pubkey = None
        print(f"Session cleared for device {self.device_id}")