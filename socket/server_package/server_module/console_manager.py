"""
Simplified Console Manager for Interactive Mode Only
No real-time dashboard, only command-based logging
"""

import threading
from datetime import datetime
from collections import deque, defaultdict
from enum import Enum

class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

class ConsoleManager:
    """Simplified console manager for command-based interface only"""
    def __init__(self, log_level=LogLevel.DEBUG):
        self._lock = threading.RLock()  # Use RLock for better performance
        self.log_level = log_level
        
        # System logs (keep recent 50 to reduce memory usage)
        self.system_logs = deque(maxlen=50)
        
        # System statistics
        self.system_stats = {
            'start_time': datetime.now(),
            'total_packets': 0,
            'successful_packets': 0,
            'failed_packets': 0,
            'total_alarms': 0,
            'total_errors': 0,
            'response_times': deque(maxlen=50),
            'packets_per_minute': deque(maxlen=60),
            'processing_times': deque(maxlen=50),   # Packet processing times
            'latency_samples': deque(maxlen=100),   # Network latency samples
        }
        
        # Client statistics
        self.client_stats = defaultdict(lambda: {
            'first_connect': None,
            'last_activity': None,
            'total_packets': 0,
            'successful_packets': 0,
            'failed_packets': 0,
            'alarms': 0,
            'errors': 0,
            'avg_response_time': 0.0,
            'status': 'DISCONNECTED',
            'latency_samples': deque(maxlen=25),
            'processing_times': deque(maxlen=25),
            'packet_intervals': deque(maxlen=20),  # Time between packets
        })
        
    def start_display(self):
        """No-op for interactive mode (no dashboard)"""
        pass
        
    def stop_display(self):
        """No-op for interactive mode (no dashboard)"""
        pass
    
    def log(self, message, level=LogLevel.INFO):
        """Thread-safe log output - optimized for performance"""
        if not self._should_log(level):
            return
        
        # Fast path - avoid lock for most common case
        if len(self.system_logs) >= 45:  # Near capacity
            with self._lock:
                log_entry = {
                    'timestamp': datetime.now(),
                    'level': level.name,
                    'message': message[:500]  # Limit message length
                }
                self.system_logs.append(log_entry)
        else:
            # Non-blocking append when buffer has space
            log_entry = {
                'timestamp': datetime.now(),
                'level': level.name,
                'message': message[:500]
            }
            self.system_logs.append(log_entry)
    
    def _should_log(self, level):
        """Determine output based on log level"""
        return level.value >= self.log_level.value
    
    def info(self, message):
        """Info log"""
        self.log(message, LogLevel.INFO)
    
    def warning(self, message):
        """Warning log"""
        self.log(message, LogLevel.WARNING)
    
    def error(self, message):
        """Error log"""
        self.log(message, LogLevel.ERROR)
        # Auto-increment error counter
        self.system_stats['total_errors'] += 1
    
    def debug(self, message):
        """Debug log"""
        self.log(message, LogLevel.DEBUG)
    
    def update_packet_stats(self, success=True, response_time=None, processing_time=None, latency=None):
        """Update packet statistics with performance metrics - optimized"""
        # Use atomic operations where possible to reduce lock contention
        self.system_stats['total_packets'] += 1
        if success:
            self.system_stats['successful_packets'] += 1
        else:
            self.system_stats['failed_packets'] += 1
        
        # Only use lock for deque operations
        if response_time is not None or processing_time is not None or latency is not None:
            with self._lock:
                if response_time is not None:
                    self.system_stats['response_times'].append(response_time)
                
                if processing_time is not None:
                    self.system_stats['processing_times'].append(processing_time)
                
                if latency is not None:
                    self.system_stats['latency_samples'].append(latency)
    
    def update_client_stats(self, client_addr, event_type, **kwargs):
        """Update client statistics - optimized"""
        # Only use lock when necessary, cache stats reference
        stats = self.client_stats[client_addr]
        
        if event_type == 'connect':
            with self._lock:
                stats['status'] = 'CONNECTED'
                if stats['first_connect'] is None:
                    stats['first_connect'] = datetime.now()
                stats['last_activity'] = datetime.now()
                
        elif event_type == 'disconnect':
            stats['status'] = 'DISCONNECTED'
                
        elif event_type == 'packet':
            # Minimize lock time for packet updates
            current_time = datetime.now()
            
            # Atomic increments
            stats['total_packets'] += 1
            if kwargs.get('success', False):
                stats['successful_packets'] += 1
            else:
                stats['failed_packets'] += 1
            
            # Lock only for complex operations
            with self._lock:
                # Calculate packet interval
                if stats['last_activity']:
                    interval = (current_time - stats['last_activity']).total_seconds() * 1000
                    if len(stats['packet_intervals']) < 20:  # Only if not full
                        stats['packet_intervals'].append(interval)
                
                stats['last_activity'] = current_time
                
                # Add performance metrics (sample to avoid overhead)
                if 'latency' in kwargs and len(stats['latency_samples']) < 25:
                    stats['latency_samples'].append(kwargs['latency'])
                if 'processing_time' in kwargs and len(stats['processing_times']) < 25:
                    stats['processing_times'].append(kwargs['processing_time'])
                    
        elif event_type == 'alarm':
            stats['alarms'] += 1
            self.system_stats['total_alarms'] += 1
            
        elif event_type == 'error':
            stats['errors'] += 1
            self.system_stats['total_errors'] += 1
    
    def display_sensor_data(self, data, client_addr):
        """No-op for interactive mode (no real-time display)"""
        # Only update statistics, no console output
        self.update_client_stats(client_addr, 'packet', success=True)
        self.update_packet_stats(success=True)
    
    def set_log_level(self, level):
        """Change log level"""
        with self._lock:
            self.log_level = level
    
    def get_latency_stats(self, client_addr=None):
        """Get latency statistics for system or specific client - optimized"""
        if client_addr:
            # Client-specific latency stats
            client_stats = self.client_stats.get(client_addr, {})
            latency_samples = client_stats.get('latency_samples', [])
        else:
            # System-wide latency stats
            latency_samples = self.system_stats['latency_samples']
        
        if not latency_samples:
            return None
        
        # Convert to list only once and cache calculations
        samples = list(latency_samples)
        samples.sort()
        count = len(samples)
        
        if count == 0:
            return None
        
        # Fast calculation for common case
        total = sum(samples)
        
        return {
            'count': count,
            'min': samples[0],
            'max': samples[-1],
            'avg': total / count,
            'median': samples[count // 2] if count % 2 == 1 else 
                     (samples[count // 2 - 1] + samples[count // 2]) / 2,
            'p95': samples[min(int(count * 0.95), count - 1)],
            'p99': samples[min(int(count * 0.99), count - 1)],
        }
    
    def get_processing_stats(self, client_addr=None):
        """Get packet processing time statistics"""
        with self._lock:
            if client_addr:
                client_stats = self.client_stats.get(client_addr, {})
                processing_times = list(client_stats.get('processing_times', []))
            else:
                processing_times = list(self.system_stats['processing_times'])
            
            if not processing_times:
                return None
            
            processing_times.sort()
            count = len(processing_times)
            
            return {
                'count': count,
                'min': min(processing_times),
                'max': max(processing_times),
                'avg': sum(processing_times) / count,
                'median': processing_times[count // 2] if count % 2 == 1 else 
                         (processing_times[count // 2 - 1] + processing_times[count // 2]) / 2,
                'p95': processing_times[int(count * 0.95)] if count > 0 else 0,
                'p99': processing_times[int(count * 0.99)] if count > 0 else 0,
            }
    
    def get_packet_interval_stats(self, client_addr):
        """Get packet interval statistics for specific client"""
        with self._lock:
            client_stats = self.client_stats.get(client_addr, {})
            intervals = list(client_stats.get('packet_intervals', []))
            
            if not intervals:
                return None
            
            intervals.sort()
            count = len(intervals)
            
            return {
                'count': count,
                'min': min(intervals),
                'max': max(intervals),
                'avg': sum(intervals) / count,
                'median': intervals[count // 2] if count % 2 == 1 else 
                         (intervals[count // 2 - 1] + intervals[count // 2]) / 2,
                'std_dev': self._calculate_std_dev(intervals),
            }
    
    def _calculate_std_dev(self, values):
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5