import os
import signal
import atexit
import sys

class ProcessManager:
    def __init__(self, console_manager=None, port=12351):
        self.console_manager = console_manager
        self.port = port
        self.pid_file = f"server_{self.port}.pid"
        self.shutdown_callbacks = []
        
    def _log(self, message, level="info"):
        """Log output"""
        if self.console_manager:
            getattr(self.console_manager, level)(message)
        else:
            # Silently ignore when console manager is absent (panel system priority)
            pass
    
    def setup_shutdown_handlers(self):
        """Setup shutdown handlers"""
        # Register signal handlers (Unix/Linux)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Register atexit handler (on process termination)
        atexit.register(self._cleanup_on_exit)
    
    def _signal_handler(self, signum, frame):
        """Signal handler"""
        self._log(f"Termination signal received: {signum}")
        self._execute_shutdown_callbacks()
        sys.exit(0)
    
    def _cleanup_on_exit(self):
        """Cleanup tasks on process termination"""
        self._log("Cleaning up server on process termination...")
        self._execute_shutdown_callbacks()
    
    def _execute_shutdown_callbacks(self):
        """Execute registered shutdown callbacks"""
        for callback in self.shutdown_callbacks:
            try:
                callback()
            except Exception as e:
                self._log(f"Shutdown callback execution error: {e}", "error")
    
    def add_shutdown_callback(self, callback):
        """Add callback to execute on shutdown"""
        self.shutdown_callbacks.append(callback)
    
    def create_pid_file(self):
        """Create PID file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self._log(f"PID file created: {self.pid_file}")
        except Exception as e:
            self._log(f"PID file creation failed: {e}", "error")
    
    def remove_pid_file(self):
        """Remove PID file"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                self._log(f"PID file removed: {self.pid_file}")
        except Exception as e:
            self._log(f"PID file removal failed: {e}", "error")
    
    def check_existing_server(self):
        """Check for existing server instance"""
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                self._log(f"Existing PID file found: {old_pid}")
                return True
            except Exception as e:
                self._log(f"PID file read error: {e}", "error")
                # Remove corrupted PID file
                self.remove_pid_file()
        return False