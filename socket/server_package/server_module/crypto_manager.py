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
from .security_utils import mask_device_id, mask_key_material

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
        # Generate 4-byte session-specific nonce prefix (prevents nonce reuse across sessions)
        self.nonce_session_prefix = secrets.token_bytes(4)
        # Replay attack protection: track received nonces
        self.last_received_counter = 0  # Track highest counter value seen
        
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt data with session key

        Uses AEAD with Additional Authenticated Data (AAD) for context binding
        """
        nonce = self._get_next_nonce()
        # AAD: device_id + protocol version (prevents context confusion attacks)
        aad = self.device_id.encode() + b"|LIVECON_v1.0"
        ciphertext = self.cipher.encrypt(nonce, plaintext, aad)
        self.last_activity = datetime.now()
        self.packet_count += 1
        return nonce + ciphertext
        
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt data with session key

        Includes replay attack protection by validating nonce counter
        """
        if len(ciphertext) < 12:
            raise ValueError("Ciphertext too short")

        nonce = ciphertext[:12]
        encrypted_data = ciphertext[12:]

        # REPLAY PROTECTION: Extract and validate counter from nonce
        # Nonce format: 4-byte prefix + 8-byte counter
        nonce_counter = int.from_bytes(nonce[4:12], 'big')

        # Reject if counter is not strictly increasing (replay or out-of-order)
        if nonce_counter <= self.last_received_counter:
            raise ValueError(
                f"Replay attack detected: received counter {nonce_counter} <= "
                f"last counter {self.last_received_counter}"
            )

        # Decrypt with AAD
        # AAD: device_id + protocol version (must match encryption AAD)
        aad = self.device_id.encode() + b"|LIVECON_v1.0"
        plaintext = self.cipher.decrypt(nonce, encrypted_data, aad)

        # Update tracking after successful decryption
        self.last_received_counter = nonce_counter
        self.last_activity = datetime.now()
        self.packet_count += 1
        return plaintext
        
    def _get_next_nonce(self) -> bytes:
        """Generate unique nonce for each encryption

        Format: 4-byte session prefix + 8-byte counter (12 bytes total)
        """
        self.nonce_counter += 1
        # 12 bytes nonce: 4 bytes session prefix + 8 bytes counter
        counter_bytes = self.nonce_counter.to_bytes(8, 'big')
        return self.nonce_session_prefix + counter_bytes
        
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
    
    def perform_key_exchange(self, device_id: str, client_public_key_bytes: bytes) -> Tuple[bytes, bytes, bytes]:
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

            # Generate random salt for HKDF (SECURITY: prevents rainbow table attacks)
            hkdf_salt = secrets.token_bytes(16)  # 16 bytes (128 bits) random salt

            # Derive session key using HKDF with salt
            session_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,  # ChaCha20Poly1305 key size
                salt=hkdf_salt,  # CRITICAL: Use random salt per session
                info=b"LIVECON_v1.0_session_key"  # Clear protocol context
            ).derive(shared_secret)

            # Create signature for authentication
            server_public_key_bytes = server_public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )

            # Sign: server_pubkey + client_pubkey + device_id + salt
            message_to_sign = server_public_key_bytes + client_public_key_bytes + device_id.encode() + hkdf_salt
            signature = self.server_signing_key.sign(message_to_sign)

            # Store session
            with self.session_lock:
                # Remove existing session if any
                if device_id in self.client_sessions:
                    self._log(f"Replacing existing session for device {mask_device_id(device_id)}")
                    del self.client_sessions[device_id]

                # Create new session
                self.client_sessions[device_id] = ClientSession(device_id, session_key)
                self._log(f"New secure session established for device {mask_device_id(device_id)}")

            return server_public_key_bytes, signature, hkdf_salt
            
        except Exception as e:
            self._log(f"Key exchange failed for device {mask_device_id(device_id)}: {e}", "error")
            raise
    
    def decrypt_data(self, device_id: str, encrypted_data: bytes) -> bytes:
        """Decrypt data from specific client"""
        with self.session_lock:
            if device_id not in self.client_sessions:
                raise Exception(f"No active session for device {mask_device_id(device_id)}")

            session = self.client_sessions[device_id]
            if session.is_expired():
                del self.client_sessions[device_id]
                raise Exception(f"Session expired for device {mask_device_id(device_id)}")

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
                self._log(f"Session removed for device {mask_device_id(device_id)}")
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
                    self._log(f"Expired session cleaned up for device {mask_device_id(device_id)}")
                
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