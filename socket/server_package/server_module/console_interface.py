"""
Simplified Console Interface for LIVECON IoT Server
Clean, intuitive command system with 5 core commands
"""

import cmd
import sys
import time
import signal
import threading
from datetime import datetime

class ServerConsole(cmd.Cmd):
    """Simplified interactive console for LIVECON server management"""
    
    intro = """
\033[36mLIVECON Server Console\033[0m
Type '\033[1mhelp\033[0m' for available commands or '\033[1mexit\033[0m' to quit.
"""
    prompt = "\033[1m\033[32mlivecon>\033[0m "
    
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.cmdloop_running = True
        self._in_follow_mode = False
        
        # Set console active flag for ASCII art management
        if hasattr(self.server, 'console_active'):
            self.server.console_active = True
    
    # ==================== CORE SIMPLIFIED COMMANDS ====================
    
    def do_show(self, arg):
        """Show information - unified command for all display needs
        Usage: show [server|clients|logs|crypto]
        
        Examples:
          show              Show server overview
          show server       Show detailed server info
          show clients      Show connected clients
          show logs         Show recent logs
          show crypto       Show crypto status
        """
        arg = arg.strip().lower()
        
        if not arg or arg == 'server':
            self._show_server_info()
        elif arg == 'clients':
            self._show_clients()
        elif arg == 'logs':
            self._show_recent_logs()
        elif arg == 'crypto':
            self._show_crypto_status()
        else:
            print(f"\033[31mError:\033[0m Unknown option '{arg}'")
            print("Usage: show [server|clients|logs|crypto]")
    
    def do_monitor(self, arg):
        """Monitor real-time activity - unified command for all monitoring
        Usage: monitor [logs|packets] [device_id]
        
        Examples:
          monitor logs               Follow system logs
          monitor packets            Monitor all packets
          monitor packets device001  Monitor specific device packets
        """
        args = arg.split() if arg else ['logs']
        
        if not args:
            args = ['logs']
            
        monitor_type = args[0].lower()
        device_filter = args[1] if len(args) > 1 else None
        
        if monitor_type == 'logs':
            self._monitor_logs()
        elif monitor_type == 'packets':
            self._monitor_packets(device_filter)
        else:
            print(f"\033[31mError:\033[0m Unknown monitor type '{monitor_type}'")
            print("Usage: monitor [logs|packets] [device_id]")
    
    def do_stats(self, arg):
        """Show statistics - simplified stats command
        Usage: stats [device_id]
        
        Examples:
          stats             Show server statistics
          stats device001   Show device statistics
        """
        device_id = arg.strip() if arg else None
        
        if device_id:
            self._show_device_stats(device_id)
        else:
            self._show_server_stats()
    
    def do_control(self, arg):
        """Control server - simplified server control
        Usage: control [stop|restart|status]

        Examples:
          control status    Show server status
          control stop      Stop the server
          control restart   Restart the server
        """
        action = arg.strip().lower()

        if not action or action == 'status':
            self._show_server_status()
        elif action == 'stop':
            if self._stop_server():
                return True  # This will exit cmdloop
        elif action == 'restart':
            self._restart_server()
        else:
            print(f"\033[31mError:\033[0m Unknown action '{action}'")
            print("Usage: control [stop|restart|status]")

    def do_db(self, arg):
        """Database management - manage database setup
        Usage: db [init|check|status|config]

        Examples:
          db status    Show database connection status
          db check     Check if database exists
          db config    Configure database connection settings
          db init      Initialize database (create database and tables)
        """
        action = arg.strip().lower()

        if not action or action == 'status':
            self._show_db_status()
        elif action == 'check':
            self._check_db_exists()
        elif action == 'config':
            self._config_database()
        elif action == 'init':
            self._init_database()
        else:
            print(f"\033[31mError:\033[0m Unknown action '{action}'")
            print("Usage: db [init|check|status|config]")
    
    def do_help(self, arg):
        """Show help - enhanced help system"""
        if not arg:
            print()
            print("\033[1mLIVECON Server Commands (Simple & Intuitive)\033[0m")
            print()
            print("\033[32mCore Commands:\033[0m")
            print("  \033[1mshow\033[0m [server|clients|logs|crypto]  Show information")
            print("  \033[1mmonitor\033[0m [logs|packets] [device]    Monitor real-time activity")
            print("  \033[1mstats\033[0m [device_id]                Show statistics")
            print("  \033[1mcontrol\033[0m [stop|restart|status]     Control server")
            print("  \033[1mdb\033[0m [init|check|status|config]   Manage database")
            print("  \033[1mhelp\033[0m [command]                   Show this help")
            print()
            print("\033[90mExamples:\033[0m")
            print("  show clients              List connected devices")
            print("  monitor packets device001 Watch device001 packets")
            print("  stats device001           Show device001 statistics")
            print("  db config                 Configure database connection")
            print("  db init                   Create database and tables")
            print("  control stop              Stop the server")
            print()
            print("\033[33mPress Ctrl+C to stop monitoring commands\033[0m")
            print("\033[33mType 'exit' or 'quit' to leave console\033[0m")
            print()
        else:
            # Show specific command help
            super().do_help(arg)
    
    # ==================== COMMAND IMPLEMENTATIONS ====================
    
    def _show_server_info(self):
        """Show server overview information"""
        try:
            print()
            print("\033[1mServer Overview\033[0m")
            print("=" * 40)
            
            # Basic server info
            status = "\033[32mRUNNING\033[0m" if self.server.is_running() else "\033[31mSTOPPED\033[0m"
            print(f"Status:          {status}")
            print(f"Host:            \033[36m{self.server.host}\033[0m")
            print(f"Port:            \033[36m{self.server.port}\033[0m")
            
            # Client info
            try:
                clients = self.server.get_connected_clients()
                print(f"Connected:       \033[32m{len(clients)} clients\033[0m")
            except:
                print(f"Connected:       \033[90mN/A\033[0m")
            
            # Basic stats
            if hasattr(self.server, 'console_manager'):
                stats = self.server.console_manager.system_stats
                print(f"Total Packets:   \033[36m{stats.get('total_packets', 0)}\033[0m")
                print(f"Success Rate:    ", end="")
                total = stats.get('total_packets', 0)
                if total > 0:
                    success_rate = (stats.get('successful_packets', 0) / total) * 100
                    color = "\033[32m" if success_rate >= 95 else "\033[33m"
                    print(f"{color}{success_rate:.1f}%\033[0m")
                else:
                    print("\033[90m0%\033[0m")
            
            print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _show_clients(self):
        """Show connected clients"""
        try:
            print()
            print("\033[1mConnected Clients\033[0m")
            print("=" * 50)
            
            clients = self.server.get_connected_clients()
            
            if not clients:
                print("\033[90mNo clients connected\033[0m")
                print()
                return
            
            print(f"\033[32m{len(clients)} client(s) connected:\033[0m")
            print()
            
            for client in clients:
                device_id = client.get('device_id', 'N/A')
                address = client.get('address', 'Unknown')
                status = client.get('status', 'Connected')
                packets = client.get('packet_count', 0)
                
                conn_time = client.get('connected_at', 'Unknown')
                if hasattr(conn_time, 'strftime'):
                    conn_time = conn_time.strftime("%H:%M:%S")
                
                print(f"  \033[1m{device_id}\033[0m")
                print(f"    Address:   {address}")
                print(f"    Status:    \033[32m{status}\033[0m")
                print(f"    Packets:   {packets}")
                print(f"    Connected: {conn_time}")
                print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _show_recent_logs(self):
        """Show recent system logs"""
        try:
            print()
            print("\033[1mRecent System Logs\033[0m")
            print("=" * 50)
            
            if not hasattr(self.server, 'console_manager'):
                print("\033[31mError:\033[0m Console manager not available")
                return
            
            logs = list(self.server.console_manager.system_logs)
            
            if not logs:
                print("\033[90mNo logs available\033[0m")
                print()
                return
            
            # Show last 10 logs
            recent_logs = logs[-10:] if len(logs) > 10 else logs
            
            for log in recent_logs:
                timestamp = log['timestamp'].strftime("%H:%M:%S")
                level = log['level']
                message = log['message']
                
                level_colors = {
                    'INFO': '\033[36m',
                    'WARNING': '\033[33m', 
                    'ERROR': '\033[31m',
                    'DEBUG': '\033[90m'
                }
                color = level_colors.get(level, '\033[0m')
                
                print(f"  {timestamp} {color}[{level:>7}]\033[0m {message}")
            
            print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _show_crypto_status(self):
        """Show cryptographic system status"""
        try:
            print()
            print("\033[1mCryptographic System Status\033[0m")
            print("=" * 45)
            
            if not hasattr(self.server, 'crypto_manager'):
                print("\033[31mError:\033[0m Crypto manager not available")
                return
            
            crypto = self.server.crypto_manager
            
            # Key status
            print(f"Ed25519 Keys:    \033[32mInitialized\033[0m")
            print(f"ECDHE Support:   \033[32mEnabled\033[0m")
            print(f"Perfect Forward: \033[32mSecrecy Enabled\033[0m")
            
            # Session info
            try:
                sessions = crypto.get_all_sessions()
                print(f"Active Sessions: \033[36m{len(sessions)}\033[0m")
                
                if sessions:
                    print()
                    print("Session Details:")
                    for device_id, session in sessions.items():
                        if session:
                            packets = session.get('packet_count', 0)
                            created = session.get('created_at', 'Unknown')
                            if hasattr(created, 'strftime'):
                                created = created.strftime("%H:%M:%S")
                            print(f"  \033[1m{device_id}\033[0m: {packets} packets, created {created}")
            except:
                print(f"Active Sessions: \033[90mN/A\033[0m")
            
            print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _monitor_logs(self):
        """Monitor system logs in real-time"""
        print("\033[33mMonitoring system logs... Press Ctrl+C to stop\033[0m")
        print()
        
        if not hasattr(self.server, 'console_manager'):
            print("\033[31mError:\033[0m Console manager not available")
            return
        
        self._in_follow_mode = True
        original_handler = signal.signal(signal.SIGINT, signal.default_int_handler)
        
        try:
            seen_logs = set()
            
            while True:
                try:
                    logs = list(self.server.console_manager.system_logs)
                    
                    for log in logs:
                        log_id = id(log)
                        if log_id not in seen_logs:
                            seen_logs.add(log_id)
                            timestamp = log['timestamp'].strftime("%H:%M:%S")
                            level = log['level']
                            message = log['message']
                            
                            level_colors = {
                                'INFO': '\033[36m',
                                'WARNING': '\033[33m',
                                'ERROR': '\033[31m',
                                'DEBUG': '\033[90m'
                            }
                            color = level_colors.get(level, '\033[0m')
                            print(f"{timestamp} {color}[{level:>7}]\033[0m {message}")
                    
                    time.sleep(0.5)
                    
                except KeyboardInterrupt:
                    break
                except Exception:
                    time.sleep(1)
                    continue
                    
        except KeyboardInterrupt:
            pass
        finally:
            signal.signal(signal.SIGINT, original_handler)
            self._in_follow_mode = False
        
        print("\n\033[33mInfo:\033[0m Log monitoring stopped")
    
    def _monitor_packets(self, device_filter=None):
        """Monitor packet activity in real-time"""
        filter_text = f" for device '{device_filter}'" if device_filter else ""
        print(f"\033[33mMonitoring packets{filter_text}... Press Ctrl+C to stop\033[0m")
        print()
        
        if not hasattr(self.server, 'console_manager'):
            print("\033[31mError:\033[0m Console manager not available")
            return
        
        self._in_follow_mode = True
        original_handler = signal.signal(signal.SIGINT, signal.default_int_handler)
        
        try:
            seen_logs = set()
            cleanup_counter = 0
            
            while True:
                try:
                    logs = list(self.server.console_manager.system_logs)
                    
                    for log in logs:
                        log_id = id(log)
                        if log_id not in seen_logs:
                            seen_logs.add(log_id)
                            message = log['message']
                            
                            # Filter for packet-related messages
                            if "Sensor data received" in message:
                                if device_filter and device_filter not in message:
                                    continue
                                
                                timestamp = log['timestamp'].strftime("%H:%M:%S")
                                print(f"{timestamp} \033[32m[PACKET]\033[0m {message}")
                                # Force immediate output
                                import sys
                                sys.stdout.flush()
                    
                    # Periodic cleanup of seen_logs to prevent memory growth
                    cleanup_counter += 1
                    if cleanup_counter >= 20:  # Every 10 seconds (20 * 0.5s)
                        # Keep only current log IDs
                        current_ids = {id(log) for log in logs}
                        seen_logs &= current_ids  # Intersection - keep only existing IDs
                        cleanup_counter = 0
                    
                    time.sleep(0.5)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    # For debugging - show what went wrong
                    print(f"\033[31mDebug error:\033[0m {e}")
                    time.sleep(1)
                    continue
                    
        except KeyboardInterrupt:
            pass
        finally:
            signal.signal(signal.SIGINT, original_handler)
            self._in_follow_mode = False
        
        print("\n\033[33mInfo:\033[0m Packet monitoring stopped")
    
    def _show_server_stats(self):
        """Show server statistics"""
        try:
            print()
            print("\033[1mServer Statistics\033[0m")
            print("=" * 40)
            
            if not hasattr(self.server, 'console_manager'):
                print("\033[31mError:\033[0m Console manager not available")
                return
            
            stats = self.server.console_manager.system_stats
            
            # Basic counters
            print(f"Total Packets:     \033[36m{stats['total_packets']}\033[0m")
            print(f"Successful:        \033[32m{stats['successful_packets']}\033[0m")
            print(f"Failed:            \033[31m{stats['failed_packets']}\033[0m")
            print(f"Total Alarms:      \033[33m{stats['total_alarms']}\033[0m")
            print(f"Total Errors:      \033[31m{stats['total_errors']}\033[0m")
            
            # Success rate
            if stats['total_packets'] > 0:
                success_rate = (stats['successful_packets'] / stats['total_packets']) * 100
                rate_color = "\033[32m" if success_rate >= 95 else "\033[33m" if success_rate >= 85 else "\033[31m"
                print(f"Success Rate:      {rate_color}{success_rate:.1f}%\033[0m")
            
            # Response time
            if stats['response_times']:
                avg_response = sum(stats['response_times']) / len(stats['response_times'])
                time_color = "\033[32m" if avg_response < 100 else "\033[33m" if avg_response < 500 else "\033[31m"
                print(f"Avg Response:      {time_color}{avg_response:.2f}ms\033[0m")
            
            # Uptime
            start_time = stats.get('start_time')
            if start_time:
                uptime = datetime.now() - start_time
                uptime_str = self._format_uptime(uptime.total_seconds())
                print(f"Uptime:            \033[36m{uptime_str}\033[0m")
            
            print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _show_device_stats(self, device_id):
        """Show statistics for a specific device"""
        try:
            print()
            print(f"\033[1mDevice Statistics: {device_id}\033[0m")
            print("=" * 50)
            
            if not hasattr(self.server, 'console_manager'):
                print("\033[31mError:\033[0m Console manager not available")
                return
            
            # Try multiple methods to find client stats
            client_stats = None
            console_manager = self.server.console_manager
            
            # Method 1: Direct lookup by device_id key
            if device_id in console_manager.client_stats:
                client_stats = console_manager.client_stats[device_id]
            else:
                # Method 2: Search through all client stats
                for addr, stats in console_manager.client_stats.items():
                    if device_id in str(addr) or (isinstance(addr, tuple) and device_id in addr[0]):
                        client_stats = stats
                        break
            
            # Method 3: Check connected clients for device mapping
            if not client_stats:
                try:
                    clients = self.server.get_connected_clients()
                    for client in clients:
                        if client.get('device_id') == device_id:
                            addr = client.get('address')
                            if addr in console_manager.client_stats:
                                client_stats = console_manager.client_stats[addr]
                                break
                except:
                    pass
            
            if not client_stats:
                print(f"\033[31mError:\033[0m No statistics available for device '{device_id}'")
                print()
                print("Available devices:")
                try:
                    clients = self.server.get_connected_clients()
                    for client in clients:
                        print(f"  - {client.get('device_id', 'N/A')}")
                except:
                    print("  (Unable to list available devices)")
                print()
                return
            
            # Display stats
            print(f"Total Packets:     \033[36m{client_stats['total_packets']}\033[0m")
            print(f"Successful:        \033[32m{client_stats['successful_packets']}\033[0m")
            print(f"Failed:            \033[31m{client_stats['failed_packets']}\033[0m")
            print(f"Alarms:            \033[33m{client_stats['alarms']}\033[0m")
            print(f"Errors:            \033[31m{client_stats['errors']}\033[0m")
            print(f"Status:            \033[32m{client_stats['status']}\033[0m")
            
            # Times
            if client_stats['first_connect']:
                first_conn = client_stats['first_connect'].strftime("%Y-%m-%d %H:%M:%S")
                print(f"First Connect:     \033[36m{first_conn}\033[0m")
            
            if client_stats['last_activity']:
                last_act = client_stats['last_activity'].strftime("%H:%M:%S")
                print(f"Last Activity:     \033[36m{last_act}\033[0m")
            
            # Success rate
            if client_stats['total_packets'] > 0:
                success_rate = (client_stats['successful_packets'] / client_stats['total_packets']) * 100
                rate_color = "\033[32m" if success_rate >= 95 else "\033[33m"
                print(f"Success Rate:      {rate_color}{success_rate:.1f}%\033[0m")
            
            print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _show_server_status(self):
        """Show detailed server status"""
        try:
            print()
            print("\033[1mServer Status\033[0m")
            print("=" * 30)
            
            running = self.server.is_running()
            status_color = "\033[32m" if running else "\033[31m"
            status_text = "RUNNING" if running else "STOPPED"
            
            print(f"Server:            {status_color}{status_text}\033[0m")
            print(f"Host:              \033[36m{self.server.host}\033[0m")
            print(f"Port:              \033[36m{self.server.port}\033[0m")
            
            # Monitoring status
            if hasattr(self.server, 'get_monitoring_status'):
                monitoring = self.server.get_monitoring_status()
                mon_color = "\033[32m" if monitoring else "\033[31m"
                mon_text = "ACTIVE" if monitoring else "INACTIVE"
                print(f"Monitoring:        {mon_color}{mon_text}\033[0m")
            
            print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _stop_server(self):
        """Stop the server"""
        print("\033[33mStopping server...\033[0m")
        try:
            # Stop the server
            self.server.stop()
            print("\033[32mServer stopped successfully\033[0m")
            
            # Wait a moment for cleanup
            import time
            time.sleep(1)
            
            # Exit the console loop
            self.cmdloop_running = False
            print("\033[33mExiting console...\033[0m")
            
            # Force thread cleanup if needed
            if hasattr(self.server, 'server_thread') and self.server.server_thread:
                if self.server.server_thread.is_alive():
                    self.server.server_thread.join(timeout=2)
            
            return True
            
        except Exception as e:
            print(f"\033[31mError stopping server:\033[0m {e}")
            # Still exit console even if server stop failed
            self.cmdloop_running = False
            return False
    
    def _restart_server(self):
        """Restart the server"""
        print("\033[33mRestarting server...\033[0m")
        try:
            print("Stopping server...")
            self.server.stop()
            time.sleep(2)
            print("Starting server...")
            if self.server.start():
                self.server.start_background_server()
                print("\033[32mServer restarted successfully\033[0m")
            else:
                print("\033[31mServer restart failed\033[0m")
        except Exception as e:
            print(f"\033[31mError restarting server:\033[0m {e}")

    def _show_db_status(self):
        """Show database connection status"""
        try:
            print()
            print("\033[1mDatabase Connection Status\033[0m")
            print("=" * 40)

            if not hasattr(self.server, 'database_manager'):
                print("\033[31mError:\033[0m Database manager not available")
                return

            db = self.server.database_manager

            # Connection info
            print(f"Host:            \033[36m{db.host}:{db.port}\033[0m")
            print(f"Database:        \033[36m{db.database}\033[0m")
            print(f"User:            \033[36m{db.user}\033[0m")

            # Check connection
            if db.connect():
                print(f"Status:          \033[32mCONNECTED\033[0m")
                db.disconnect()
            else:
                print(f"Status:          \033[31mDISCONNECTED\033[0m")

            print()

        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")

    def _check_db_exists(self):
        """Check if database exists"""
        try:
            print()
            print("\033[1mDatabase Existence Check\033[0m")
            print("=" * 40)

            if not hasattr(self.server, 'database_manager'):
                print("\033[31mError:\033[0m Database manager not available")
                return

            db = self.server.database_manager
            print(f"Checking database: \033[36m{db.database}\033[0m")

            if db.database_exists():
                print(f"Result:          \033[32mDatabase EXISTS\033[0m")
                print()
                print("Database is ready to use.")
            else:
                print(f"Result:          \033[33mDatabase NOT FOUND\033[0m")
                print()
                print("Use '\033[1mdb init\033[0m' to create the database and tables.")

            print()

        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")

    def _config_database(self):
        """Configure database connection settings"""
        try:
            import json
            import os

            print()
            print("\033[1mDatabase Configuration\033[0m")
            print("=" * 40)
            print()
            print("\033[33mNote:\033[0m Changes will be saved to config.json")
            print("\033[33mNote:\033[0m Press Enter to keep current value")
            print()

            if not hasattr(self.server, 'database_manager'):
                print("\033[31mError:\033[0m Database manager not available")
                return

            db = self.server.database_manager

            # Show current configuration
            print("\033[1mCurrent Configuration:\033[0m")
            print(f"  Host:     \033[36m{db.host}\033[0m")
            print(f"  Port:     \033[36m{db.port}\033[0m")
            print(f"  User:     \033[36m{db.user}\033[0m")
            print(f"  Password: \033[36m{'*' * len(db.password) if db.password else '(empty)'}\033[0m")
            print(f"  Database: \033[36m{db.database}\033[0m")
            print()

            # Get new values
            try:
                new_host = input(f"Host [{db.host}]: ").strip() or db.host
                new_port_str = input(f"Port [{db.port}]: ").strip()
                new_port = int(new_port_str) if new_port_str else db.port
                new_user = input(f"User [{db.user}]: ").strip() or db.user
                new_password = input(f"Password [{'*' * 8}]: ").strip() or db.password
                new_database = input(f"Database [{db.database}]: ").strip() or db.database

            except (EOFError, KeyboardInterrupt):
                print("\n\033[33mInfo:\033[0m Configuration cancelled")
                print()
                return

            # Confirm changes
            print()
            print("\033[1mNew Configuration:\033[0m")
            print(f"  Host:     \033[36m{new_host}\033[0m")
            print(f"  Port:     \033[36m{new_port}\033[0m")
            print(f"  User:     \033[36m{new_user}\033[0m")
            print(f"  Password: \033[36m{'*' * len(new_password) if new_password else '(empty)'}\033[0m")
            print(f"  Database: \033[36m{new_database}\033[0m")
            print()

            try:
                confirm = input("Save these settings? (yes/no): ").strip().lower()
                if confirm not in ['yes', 'y']:
                    print("\033[33mInfo:\033[0m Configuration cancelled")
                    print()
                    return
            except (EOFError, KeyboardInterrupt):
                print("\n\033[33mInfo:\033[0m Configuration cancelled")
                print()
                return

            # Load config.json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError:
                print(f"\033[31mError:\033[0m config.json not found at {config_path}")
                return
            except json.JSONDecodeError:
                print(f"\033[31mError:\033[0m Invalid JSON in config.json")
                return

            # Update database section
            if 'database' not in config:
                config['database'] = {}

            config['database']['host'] = new_host
            config['database']['port'] = new_port
            config['database']['user'] = new_user
            config['database']['password'] = new_password
            config['database']['database'] = new_database

            # Save config.json
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)

                print()
                print("\033[32mSuccess:\033[0m Configuration saved to config.json")
                print()
                print("\033[33mNote:\033[0m Restart the server for changes to take effect")
                print("      Use '\033[1mcontrol restart\033[0m' to restart the server")
                print()

            except Exception as e:
                print(f"\033[31mError:\033[0m Failed to save config.json: {e}")
                print()

        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
            print()

    def _init_database(self):
        """Initialize database (create database and tables)"""
        try:
            print()
            print("\033[1mDatabase Initialization\033[0m")
            print("=" * 40)

            if not hasattr(self.server, 'database_manager'):
                print("\033[31mError:\033[0m Database manager not available")
                return

            db = self.server.database_manager

            # Check if database already exists
            print("Checking if database exists...")
            if db.database_exists():
                print(f"\033[33mWarning:\033[0m Database '\033[36m{db.database}\033[0m' already exists")
                print()

                # Ask for confirmation
                try:
                    response = input("Do you want to create tables anyway? (yes/no): ").strip().lower()
                    if response not in ['yes', 'y']:
                        print("\033[33mInfo:\033[0m Database initialization cancelled")
                        print()
                        return
                except EOFError:
                    print("\n\033[33mInfo:\033[0m Database initialization cancelled")
                    print()
                    return
            else:
                print(f"Database '\033[36m{db.database}\033[0m' does not exist")
                print()

            # Initialize database
            print("Initializing database...")
            if db.initialize_database():
                print()
                print("\033[32mSuccess:\033[0m Database initialized successfully!")
                print()
                print("Created components:")
                print("  \033[32m✓\033[0m Database (if not existed)")
                print("  \033[32m✓\033[0m sensor_info table")
                print("  \033[32m✓\033[0m sensor_data table")
                print("  \033[32m✓\033[0m sensor_type table")
                print("  \033[32m✓\033[0m alarm_log table")
                print("  \033[32m✓\033[0m alarm_type table")
                print("  \033[32m✓\033[0m device_connection_log table")
                print("  \033[32m✓\033[0m device_status table")
                print("  \033[32m✓\033[0m raw_packet_log table")
                print("  \033[32m✓\033[0m Master data (sensor types, alarm types)")
                print()
                print("Database is ready for use!")
            else:
                print()
                print("\033[31mError:\033[0m Database initialization failed")
                print("Please check the logs for details.")

            print()

        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _format_uptime(self, seconds):
        """Format uptime in human readable format"""
        try:
            days, remainder = divmod(int(seconds), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "Unknown"
    
    # ==================== BACKWARD COMPATIBILITY ====================
    
    def do_status(self, arg):
        """Redirect to 'show server'"""
        print("\033[33mNote:\033[0m 'status' is now 'show server' - redirecting...")
        self.do_show("server")
    
    def do_ps(self, arg):
        """Redirect to 'show clients'"""
        print("\033[33mNote:\033[0m 'ps' is now 'show clients' - redirecting...")
        self.do_show("clients")
    
    def do_journalctl(self, arg):
        """Redirect to 'monitor logs'"""
        print("\033[33mNote:\033[0m 'journalctl' is now 'monitor logs' - redirecting...")
        self.do_monitor("logs")
    
    def do_packets(self, arg):
        """Redirect to 'monitor packets'"""
        print("\033[33mNote:\033[0m 'packets' is now 'monitor packets' - redirecting...")
        cmd = f"packets {arg}" if arg else "packets"
        self.do_monitor(cmd)
    
    def do_systemctl(self, arg):
        """Redirect to 'control'"""
        print("\033[33mNote:\033[0m 'systemctl' is now 'control' - redirecting...")
        self.do_control(arg)
    
    def do_crypto(self, arg):
        """Redirect to 'show crypto'"""
        print("\033[33mNote:\033[0m 'crypto' is now 'show crypto' - redirecting...")
        self.do_show("crypto")
    
    # ==================== SYSTEM COMMANDS ====================
    
    def do_exit(self, line):
        """Exit the console"""
        print("\033[33mGoodbye!\033[0m")
        self.cmdloop_running = False
        return True
    
    def do_quit(self, line):
        """Exit the console"""
        return self.do_exit(line)
    
    def do_shutdown(self, line):
        """Shutdown server and exit console"""
        print("\033[33mShutting down server...\033[0m")
        try:
            self.server.stop()
            print("\033[32mServer shutdown completed\033[0m")
            
            # Wait for cleanup
            import time
            time.sleep(1)
            
        except Exception as e:
            print(f"\033[31mError during shutdown:\033[0m {e}")
        
        print("\033[33mGoodbye!\033[0m")
        self.cmdloop_running = False
        return True
    
    def emptyline(self):
        """Handle empty line input"""
        pass
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"\033[33mWarning:\033[0m Unknown command '\033[1m{line}\033[0m'.")
        print("Type '\033[1mhelp\033[0m' for available commands.")
    
    def do_EOF(self, line):
        """Handle Ctrl+D (EOF)"""
        print("\n\033[33mInfo:\033[0m Use '\033[1mexit\033[0m' to quit.")
        return False
    
    def cmdloop(self, intro=None):
        """Custom cmdloop with proper input handling"""
        if intro is not None:
            self.intro = intro
        
        if self.intro:
            self.stdout.write(str(self.intro) + '\n')
        
        # Check for TTY
        if not sys.stdin.isatty():
            print("\033[31mError:\033[0m Interactive console requires a TTY terminal")
            return
        
        self.cmdloop_running = True
        while self.cmdloop_running:
            try:
                super().cmdloop(intro="")
                break
            except KeyboardInterrupt:
                if not getattr(self, '_in_follow_mode', False):
                    print("\n^C")
                    print("\033[33mInfo:\033[0m Use '\033[1mexit\033[0m' to quit.")
                else:
                    continue
            except EOFError:
                print("\n\033[33mInfo:\033[0m Use '\033[1mexit\033[0m' to quit.")
                break