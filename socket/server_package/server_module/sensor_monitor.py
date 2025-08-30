import threading
import time
from typing import Dict, Any
from .alarm_manager import AlarmManager

class SensorMonitor:
    def __init__(self, alarm_manager: AlarmManager, console_manager=None):
        self.alarm_manager = alarm_manager
        self.console_manager = console_manager
        self.monitor_thread = None
        self.monitoring = False
        self.monitor_interval = 60  # Monitor every 1 minute
        self._lock = threading.Lock()
    
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
        else:
            # Silently ignore when console manager is absent (panel system priority)
            pass
    
    def start_monitoring(self):
        """Start sensor monitoring"""
        with self._lock:
            if self.monitoring:
                self._log("Sensor monitoring is already running", "warning")
                return
            
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            self._log("Sensor monitoring started")
    
    def stop_monitoring(self):
        """Stop sensor monitoring"""
        with self._lock:
            if not self.monitoring:
                self._log("Sensor monitoring is not running", "warning")
                return
            
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5.0)
            self._log("Sensor monitoring stopped")
    
    def _monitor_loop(self):
        """Monitoring loop"""
        self._log("Sensor monitoring loop started")
        
        while self.monitoring:
            try:
                # Check offline sensors
                self.alarm_manager.check_sensor_offline(timeout_seconds=300)
                
                # Wait until next monitoring
                for _ in range(self.monitor_interval):
                    if not self.monitoring:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self._log(f"Error during sensor monitoring: {e}", "error")
                time.sleep(5)  # Wait 5 seconds on error
        
        self._log("Sensor monitoring loop ended")
    
    def set_monitor_interval(self, seconds: int):
        """Set monitoring interval"""
        if seconds < 10:
            self._log("Monitoring interval must be at least 10 seconds", "warning")
            return
        
        self.monitor_interval = seconds
        self._log(f"Monitoring interval set to {seconds} seconds")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Return monitoring status"""
        return {
            'monitoring': self.monitoring,
            'interval': self.monitor_interval,
            'thread_alive': self.monitor_thread.is_alive() if self.monitor_thread else False,
            'sensor_count': len(self.alarm_manager.sensor_last_received),
            'last_data_count': len(self.alarm_manager.last_sensor_data)
        }