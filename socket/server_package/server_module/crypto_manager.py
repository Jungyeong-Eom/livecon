import os
import secrets
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

class ClientSession:
    """Individual client session with PFS"""
    def __init__(self, device_id: str, shared_key: bytes):
        self.device_id = device_id
        self.shared_key = shared_key
        self.cipher = ChaCha20Poly1305(shared_key)
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.packet_count = 0
        self.nonce_counter = 0
        
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data with session key"""
        nonce = self._get_next_nonce()
        ciphertext = self.cipher.encrypt(nonce, plaintext, None)
        self.last_activity = datetime.now()
        self.packet_count += 1
        return nonce + ciphertext
        
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data with session key"""
        if len(ciphertext) < 12:
            raise ValueError("Ciphertext too short")
        
        nonce = ciphertext[:12]
        encrypted_data = ciphertext[12:]
        
        plaintext = self.cipher.decrypt(nonce, encrypted_data, None)
        self.last_activity = datetime.now()
        self.packet_count += 1
        return plaintext
        
    def _get_next_nonce(self) -> bytes:
        """Generate unique nonce for each encryption"""
        self.nonce_counter += 1
        # 12 bytes nonce: 8 bytes counter + 4 bytes random
        counter_bytes = self.nonce_counter.to_bytes(8, 'big')
        random_bytes = secrets.token_bytes(4)
        return counter_bytes + random_bytes
        
    def is_expired(self, session_timeout_minutes: int = 60) -> bool:
        """Check if session is expired"""
        return datetime.now() - self.last_activity > timedelta(minutes=session_timeout_minutes)

class CryptoManager:
    """ECDHE + Ed25519 signature based crypto manager with PFS"""
    def __init__(self, console_manager=None):
        self.console_manager = console_manager
        self.server_signing_key = None  # Ed25519 for authentication
        self.client_sessions: Dict[str, ClientSession] = {}  # device_id -> session
        self.session_lock = threading.Lock()
        self.cleanup_thread = None
        self.running = False
        
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
        else:
            pass
            
    def initialize_keys(self):
        """Initialize server Ed25519 signing key"""
        try:
            # Generate server's long-term signing key
            self.server_signing_key = Ed25519PrivateKey.generate()
            
            # Start session cleanup thread
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._session_cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            
            self._log("ECDHE + Ed25519 crypto system initialized")
            self._log("Perfect Forward Secrecy (PFS) enabled for all client sessions")
            return True
            
        except Exception as e:
            self._log(f"Crypto system initialization failed: {e}", "error")
            return False
    
    def get_server_public_key(self) -> bytes:
        """Get server's Ed25519 public key for client verification"""
        if not self.server_signing_key:
            raise Exception("Server signing key not initialized - call initialize_keys() first")
            
        public_key = self.server_signing_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def perform_key_exchange(self, device_id: str, client_public_key_bytes: bytes) -> Tuple[bytes, bytes]:
        """Perform ECDHE key exchange with client"""
        try:
            # Check if server signing key is initialized
            if not self.server_signing_key:
                raise Exception("Server signing key not initialized - call initialize_keys() first")
            # Parse client's X25519 public key
            client_public_key = X25519PublicKey.from_public_bytes(client_public_key_bytes)
            
            # Generate server's ephemeral X25519 key pair
            server_private_key = X25519PrivateKey.generate()
            server_public_key = server_private_key.public_key()
            
            # Perform ECDHE
            shared_secret = server_private_key.exchange(client_public_key)
            
            # Derive session key using HKDF
            session_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,  # ChaCha20Poly1305 key size
                salt=None,
                info=f"session_key_{device_id}".encode()
            ).derive(shared_secret)
            
            # Create signature for authentication
            server_public_key_bytes = server_public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            # Sign: server_pubkey + client_pubkey + device_id
            message_to_sign = server_public_key_bytes + client_public_key_bytes + device_id.encode()
            signature = self.server_signing_key.sign(message_to_sign)
            
            # Store session
            with self.session_lock:
                # Remove existing session if any
                if device_id in self.client_sessions:
                    self._log(f"Replacing existing session for device {device_id}")
                    del self.client_sessions[device_id]
                
                # Create new session
                self.client_sessions[device_id] = ClientSession(device_id, session_key)
                self._log(f"New secure session established for device {device_id}")
            
            return server_public_key_bytes, signature
            
        except Exception as e:
            self._log(f"Key exchange failed for device {device_id}: {e}", "error")
            raise
    
    def decrypt_data(self, device_id: str, encrypted_data: bytes) -> bytes:
        """Decrypt data from specific client"""
        with self.session_lock:
            if device_id not in self.client_sessions:
                raise Exception(f"No active session for device {device_id}")
            
            session = self.client_sessions[device_id]
            if session.is_expired():
                del self.client_sessions[device_id]
                raise Exception(f"Session expired for device {device_id}")
            
            return session.decrypt(encrypted_data)
    
    def get_session_info(self, device_id: str) -> Optional[Dict]:
        """Get session information for monitoring"""
        with self.session_lock:
            if device_id not in self.client_sessions:
                return None
            
            session = self.client_sessions[device_id]
            return {
                'device_id': session.device_id,
                'created_at': session.created_at,
                'last_activity': session.last_activity,
                'packet_count': session.packet_count,
                'is_expired': session.is_expired()
            }
    
    def get_all_sessions(self) -> Dict[str, Dict]:
        """Get all session information"""
        with self.session_lock:
            result = {}
            for device_id, session in self.client_sessions.items():
                result[device_id] = {
                    'device_id': session.device_id,
                    'created_at': session.created_at,
                    'last_activity': session.last_activity,
                    'packet_count': session.packet_count,
                    'is_expired': session.is_expired()
                }
            return result
    
    def remove_session(self, device_id: str) -> bool:
        """Remove client session"""
        with self.session_lock:
            if device_id in self.client_sessions:
                del self.client_sessions[device_id]
                self._log(f"Session removed for device {device_id}")
                return True
            return False
    
    def _session_cleanup_loop(self):
        """Background thread to cleanup expired sessions"""
        while self.running:
            try:
                expired_devices = []
                with self.session_lock:
                    for device_id, session in self.client_sessions.items():
                        if session.is_expired():
                            expired_devices.append(device_id)
                
                for device_id in expired_devices:
                    self.remove_session(device_id)
                    self._log(f"Expired session cleaned up for device {device_id}")
                
                time.sleep(300)  # Check every 5 minutes
            except Exception as e:
                self._log(f"Session cleanup error: {e}", "error")
                time.sleep(60)
    
    def stop(self):
        """Stop crypto manager"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=1.0)
        
        with self.session_lock:
            session_count = len(self.client_sessions)
            self.client_sessions.clear()
            self._log(f"Crypto manager stopped - {session_count} sessions cleared")
    
    def is_initialized(self):
        """Check if crypto system is initialized"""
        return self.server_signing_key is not None
        
    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        with self.session_lock:
            return len(self.client_sessions)