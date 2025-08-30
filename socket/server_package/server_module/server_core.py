import socket
import struct
import threading
import errno
import time
from typing import Optional, Tuple

class ServerCoreError(Exception):
    """Base exception for server core operations"""
    pass

class PortUnavailableError(ServerCoreError):
    """Exception raised when port is unavailable"""
    pass

class SocketCreationError(ServerCoreError):
    """Exception raised when socket creation fails"""
    pass

class ServerCore:
    def __init__(self, console_manager=None, host='localhost', port=12351):
        self.host = host
        self.port = port
        self.console_manager = console_manager
        self.server_socket = None
        self.running = False
        self._socket_lock = threading.Lock()
        self._connection_retry_count = 0
        self._max_retries = 3
        
    def _log(self, message, level="info"):
        """Log output with error tracking"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
            # Track errors for monitoring
            if level == "error":
                self.console_manager.system_stats['total_errors'] += 1
        else:
            # Silently ignore when console manager is absent (panel system priority)
            pass
    
    def check_port_available(self) -> bool:
        """Check port availability with detailed error handling"""
        try:
            # Test without SO_REUSEADDR - accurately check actual usage
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind((self.host, self.port))
            test_socket.close()
            self._log(f"Port {self.port} is available")
            return True
        except socket.error as e:
            error_code = getattr(e, 'errno', None) or e.args[0] if e.args else None
            
            if error_code == errno.EADDRINUSE:
                self._log(f"Port {self.port} is already in use by another process", "error")
            elif error_code == errno.EACCES:
                self._log(f"Permission denied for port {self.port} (requires admin rights)", "error")
            elif error_code == errno.EADDRNOTAVAIL:
                self._log(f"Address {self.host}:{self.port} is not available", "error")
            else:
                self._log(f"Port {self.port} check failed: {e} (errno: {error_code})", "error")
            
            raise PortUnavailableError(f"Port {self.port} is unavailable: {e}")
        except Exception as e:
            self._log(f"Unexpected error during port availability check: {e}", "error")
            return False
    
    def create_server_socket(self) -> bool:
        """Create and configure server socket with retry mechanism"""
        for attempt in range(self._max_retries):
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                # Enhanced port reuse option
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                # Additional option for resolving TIME_WAIT state on Windows
                try:
                    self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except (AttributeError, OSError):
                    # Ignore on systems that don't support SO_REUSEPORT
                    self._log("SO_REUSEPORT not supported on this system", "debug")
                
                # Configure socket to close immediately (prevent TIME_WAIT state)
                linger_struct = struct.pack('ii', 1, 0)  # l_onoff=1, l_linger=0 (close immediately)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger_struct)
                
                # Set 1-second timeout for accept
                self.server_socket.settimeout(1.0)
                
                # Binding and listen
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(5)
                
                self._log(f"Server socket bound to {self.host}:{self.port}")
                self._connection_retry_count = 0  # Reset retry counter on success
                return True
                
            except socket.error as e:
                error_code = getattr(e, 'errno', None) or e.args[0] if e.args else None
                attempt_msg = f"(attempt {attempt + 1}/{self._max_retries})"
                
                if error_code == errno.EADDRINUSE:
                    self._log(f"Socket creation failed - port in use {attempt_msg}: {e}", "error")
                elif error_code == errno.EACCES:
                    self._log(f"Socket creation failed - permission denied {attempt_msg}: {e}", "error")
                else:
                    self._log(f"Socket creation failed {attempt_msg}: {e}", "error")
                
                # Clean up socket on failure
                if self.server_socket:
                    try:
                        self.server_socket.close()
                    except:
                        pass
                    self.server_socket = None
                
                # Wait before retry (except on last attempt)
                if attempt < self._max_retries - 1:
                    time.sleep(1.0 * (attempt + 1))  # Progressive delay
                    
            except Exception as e:
                self._log(f"Unexpected error during socket creation: {e}", "error")
                if self.server_socket:
                    try:
                        self.server_socket.close()
                    except:
                        pass
                    self.server_socket = None
                break
        
        self._connection_retry_count += 1
        raise SocketCreationError(f"Failed to create server socket after {self._max_retries} attempts")
    
    def start_listening(self):
        """Start accepting client connections"""
        self.running = True
        self._log("Waiting for client connections...")
    
    def accept_client(self):
        """Accept client connection (non-blocking)"""
        if not self.running or not self.server_socket:
            return None, None
        
        try:
            client_socket, client_address = self.server_socket.accept()
            self._log(f"Client connection accepted: {client_address}")
            return client_socket, client_address
            
        except socket.timeout:
            # Timeout is a normal situation
            return None, None
        except socket.error as e:
            if self.running:
                self._log(f"Client connection accept error: {e}", "error")
            return None, None
        except Exception as e:
            if self.running:
                self._log(f"Unexpected connection accept error: {e}", "error")
            return None, None
    
    def stop(self):
        """Stop server socket"""
        self.running = False
        
        with self._socket_lock:
            if self.server_socket:
                try:
                    self.server_socket.close()
                    self._log("Server socket stopped")
                except Exception as e:
                    self._log(f"Server socket stop error: {e}", "error")
                finally:
                    self.server_socket = None
    
    def is_running(self):
        """Return server running status"""
        return self.running and self.server_socket is not None