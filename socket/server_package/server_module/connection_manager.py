import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class ClientConnection:
    """Individual client connection information"""
    def __init__(self, address: Tuple[str, int]):
        self.address = address
        self.addr_str = f"{address[0]}:{address[1]}"
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.device_id = None
        self.status = "CONNECTED"
        self.packet_count = 0
        
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.packet_count += 1
    
    def set_device_id(self, device_id: str):
        """Set device ID after key exchange"""
        self.device_id = device_id
    
    def disconnect(self):
        """Mark as disconnected"""
        self.status = "DISCONNECTED"
    
    def get_info(self) -> Dict:
        """Get connection information"""
        return {
            'address': self.addr_str,
            'device_id': self.device_id,
            'connected_at': self.connected_at,
            'last_activity': self.last_activity,
            'status': self.status,
            'packet_count': self.packet_count,
            'connection_duration': (datetime.now() - self.connected_at).total_seconds()
        }

class ConnectionManager:
    """Manage client connections and their lifecycle"""
    def __init__(self, console_manager=None):
        self.console_manager = console_manager
        self.connections: Dict[str, ClientConnection] = {}
        self.connection_lock = threading.Lock()
        
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
    
    def add_client(self, client_address: Tuple[str, int]) -> str:
        """Add new client connection"""
        addr_str = f"{client_address[0]}:{client_address[1]}"
        
        with self.connection_lock:
            if addr_str in self.connections:
                # Update existing connection
                self.connections[addr_str].connected_at = datetime.now()
                self.connections[addr_str].status = "CONNECTED"
                self._log(f"Client reconnected: {addr_str}")
            else:
                # Create new connection
                self.connections[addr_str] = ClientConnection(client_address)
                self._log(f"New client connected: {addr_str}")
            
            return addr_str
    
    def update_client_activity(self, addr_str: str):
        """Update client last activity"""
        with self.connection_lock:
            if addr_str in self.connections:
                self.connections[addr_str].update_activity()
    
    def set_client_device_id(self, addr_str: str, device_id: str):
        """Set device ID for client after key exchange"""
        with self.connection_lock:
            if addr_str in self.connections:
                self.connections[addr_str].set_device_id(device_id)
                self._log(f"Device ID set for {addr_str}: {device_id}")
    
    def remove_client(self, addr_str: str):
        """Remove client connection"""
        with self.connection_lock:
            if addr_str in self.connections:
                self.connections[addr_str].disconnect()
                self._log(f"Client disconnected: {addr_str}")
                # Keep connection info for a while for statistics
                # Can be cleaned up later by a background task
    
    def get_connected_clients(self) -> List[Dict]:
        """Get list of currently connected clients"""
        with self.connection_lock:
            return [
                conn.get_info() 
                for conn in self.connections.values() 
                if conn.status == "CONNECTED"
            ]
    
    def get_all_clients(self) -> List[Dict]:
        """Get list of all clients (connected and disconnected)"""
        with self.connection_lock:
            return [conn.get_info() for conn in self.connections.values()]
    
    def get_client_by_device_id(self, device_id: str) -> Optional[Dict]:
        """Get client by device ID"""
        with self.connection_lock:
            for conn in self.connections.values():
                if conn.device_id == device_id and conn.status == "CONNECTED":
                    return conn.get_info()
            return None
    
    def disconnect_all_clients(self):
        """Disconnect all clients"""
        with self.connection_lock:
            for conn in self.connections.values():
                if conn.status == "CONNECTED":
                    conn.disconnect()
            self._log("All clients disconnected")
    
    def cleanup_old_connections(self, max_age_hours: int = 24):
        """Clean up old disconnected connections"""
        cutoff_time = datetime.now() - datetime.timedelta(hours=max_age_hours)
        
        with self.connection_lock:
            to_remove = []
            for addr_str, conn in self.connections.items():
                if conn.status == "DISCONNECTED" and conn.last_activity < cutoff_time:
                    to_remove.append(addr_str)
            
            for addr_str in to_remove:
                del self.connections[addr_str]
                self._log(f"Cleaned up old connection: {addr_str}")
            
            if to_remove:
                self._log(f"Cleaned up {len(to_remove)} old connections")
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        with self.connection_lock:
            connected_count = sum(1 for conn in self.connections.values() if conn.status == "CONNECTED")
            total_count = len(self.connections)
            total_packets = sum(conn.packet_count for conn in self.connections.values())
            
            return {
                'connected_clients': connected_count,
                'total_clients': total_count,
                'total_packets_received': total_packets,
                'average_packets_per_client': total_packets / max(total_count, 1)
            }