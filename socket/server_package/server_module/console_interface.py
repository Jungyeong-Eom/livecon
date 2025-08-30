import threading
import time
import cmd
import sys
from datetime import datetime
from typing import Dict, Any, List

class ServerConsole(cmd.Cmd):
    """Interactive server console with command support"""
    
    intro = ""  # No intro message, server.py handles the display
    prompt = "livecon> "
    
    def __init__(self, server_instance=None):
        super().__init__()
        self.server = server_instance
        self.running = True
        # 서버 인스턴스에 콘솔 활성화 상태 설정
        if self.server:
            self.server.console_active = True
        
    def do_status(self, arg):
        """Show server status and statistics"""
        if not self.server:
            print("\033[31mError:\033[0m Server instance not available")
            return
            
        try:
            print()
            print("\033[1mServer Status:\033[0m")
            
            status_color = "\033[32m" if self.server.is_running() else "\033[31m"
            status_text = "RUNNING" if self.server.is_running() else "STOPPED"
            print(f"  Status:          {status_color}{status_text}\033[0m")
            print(f"  Address:         \033[36m{self.server.host}:{self.server.port}\033[0m")
            print(f"  Uptime:          \033[33m{self._get_uptime()}\033[0m")
            
            # ECDHE 세션 정보
            if self.server.crypto_manager:
                session_count = self.server.crypto_manager.get_active_session_count()
                sessions = self.server.crypto_manager.get_all_sessions()
                print(f"  ECDHE Sessions:  \033[35m{session_count}\033[0m")
            
            # 클라이언트 연결 정보
            clients = self.server.get_connected_clients() if hasattr(self.server, 'get_connected_clients') else []
            print(f"  Connected:       \033[34m{len(clients)}\033[0m clients")
            
            # ECDHE 세션 상세 정보
            if self.server.crypto_manager and sessions:
                print()
                print("\033[1mActive Sessions:\033[0m")
                for device_id, session_info in sessions.items():
                    if session_info:
                        created = session_info['created_at'].strftime("%H:%M:%S")
                        last_activity = session_info['last_activity'].strftime("%H:%M:%S")
                        packets = session_info['packet_count']
                        print(f"  \033[36m{device_id:<15}\033[0m created: {created}, activity: {last_activity}, packets: {packets}")
                
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def do_sessions(self, arg):
        """List ECDHE sessions with filtering options
        Usage: sessions [device_id] [--active] [--expired] [--details]
        Options:
          device_id    Show specific session information
          --active     Show only active sessions
          --expired    Show only expired sessions  
          --details    Show detailed session information
        """
        if not self.server or not self.server.crypto_manager:
            print("\033[31mError:\033[0m Crypto manager not available")
            return
        
        # Parse arguments
        args = arg.split() if arg else []
        target_device = None
        show_active_only = False
        show_expired_only = False
        show_details = False
        
        for arg_item in args:
            if arg_item == '--active':
                show_active_only = True
            elif arg_item == '--expired':
                show_expired_only = True
            elif arg_item == '--details':
                show_details = True
            elif not arg_item.startswith('--'):
                target_device = arg_item
        
        sessions = self.server.crypto_manager.get_all_sessions()
        if not sessions:
            print("\033[33mInfo:\033[0m No ECDHE sessions found")
            return
        
        # Show specific session
        if target_device:
            if target_device in sessions:
                self._show_session_details(target_device, sessions[target_device], show_details)
            else:
                print(f"\033[31mError:\033[0m Session for device '{target_device}' not found")
            return
        
        # Filter sessions
        filtered_sessions = {}
        for device_id, session_info in sessions.items():
            if not session_info:
                continue
            
            is_expired = session_info['is_expired']
            if show_active_only and is_expired:
                continue
            if show_expired_only and not is_expired:
                continue
            
            filtered_sessions[device_id] = session_info
        
        if not filtered_sessions:
            filter_msg = "active" if show_active_only else "expired" if show_expired_only else ""
            print(f"\033[33mInfo:\033[0m No {filter_msg} sessions found")
            return
        
        print()
        filter_desc = ""
        if show_active_only:
            filter_desc = " (active only)"
        elif show_expired_only:
            filter_desc = " (expired only)"
        
        print(f"\033[1mECDHE Sessions ({len(filtered_sessions)}{filter_desc}):\033[0m")
        print()
        
        for device_id, session_info in filtered_sessions.items():
            created = session_info['created_at'].strftime("%H:%M:%S")
            last_activity = session_info['last_activity'].strftime("%H:%M:%S")
            packets = session_info['packet_count']
            
            if session_info['is_expired']:
                status_color = "\033[31m"
                status = "EXPIRED"
            else:
                status_color = "\033[32m"
                status = "ACTIVE"
            
            if show_details:
                print(f"  \033[1m{device_id}\033[0m")
                print(f"    Created:       {created}")
                print(f"    Last Activity: {last_activity}")
                print(f"    Packets:       {packets}")
                print(f"    Status:        {status_color}{status}\033[0m")
                
                # Additional details
                duration = session_info['last_activity'] - session_info['created_at']
                duration_str = f"{duration.total_seconds():.1f}s"
                print(f"    Duration:      {duration_str}")
                
                if packets > 0:
                    avg_interval = duration.total_seconds() / packets
                    print(f"    Avg Interval:  {avg_interval:.1f}s")
                
                print()
            else:
                # Compact format
                print(f"  \033[1m{device_id:<15}\033[0m {created} → {last_activity} | {packets:>3} packets | {status_color}{status}\033[0m")
    
    def _show_session_details(self, device_id, session_info, detailed=False):
        """Show detailed information for a specific session"""
        if not session_info:
            print(f"\033[31mError:\033[0m Session information not available for {device_id}")
            return
        
        print()
        print(f"\033[1mSession Details: {device_id}\033[0m")
        
        created = session_info['created_at']
        last_activity = session_info['last_activity']
        packets = session_info['packet_count']
        is_expired = session_info['is_expired']
        
        status_color = "\033[31m" if is_expired else "\033[32m"
        status = "EXPIRED" if is_expired else "ACTIVE"
        
        print(f"  Device ID:       \033[36m{device_id}\033[0m")
        print(f"  Status:          {status_color}{status}\033[0m")
        print(f"  Created:         {created.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Last Activity:   {last_activity.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Packet Count:    \033[33m{packets}\033[0m")
        
        # Duration calculation
        duration = last_activity - created
        days = duration.days
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            duration_str = f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        print(f"  Session Duration: {duration_str}")
        
        # Performance metrics
        if packets > 0:
            avg_interval = duration.total_seconds() / packets
            packets_per_minute = packets / max(duration.total_seconds() / 60, 1)
            print(f"  Avg Interval:    \033[35m{avg_interval:.1f}s\033[0m")
            print(f"  Packets/min:     \033[35m{packets_per_minute:.1f}\033[0m")
        
        if detailed:
            print()
            print("\033[1mTechnical Details:\033[0m")
            print(f"  Key Exchange:    ECDHE (X25519)")
            print(f"  Encryption:      ChaCha20-Poly1305")
            print(f"  Forward Secrecy: \033[32mEnabled\033[0m")
            
            # Time until expiration (if active)
            if not is_expired:
                from datetime import timedelta
                time_since_activity = datetime.now() - last_activity
                # Assuming 60-minute session timeout
                time_remaining = timedelta(minutes=60) - time_since_activity
                if time_remaining.total_seconds() > 0:
                    remaining_minutes = int(time_remaining.total_seconds() / 60)
                    print(f"  Time Remaining:  \033[33m~{remaining_minutes} minutes\033[0m")
    
    def do_clients(self, arg):
        """List connected clients or show specific client info
        Usage: clients [device_id|address] [--logs] [--stats]
        Options:
          device_id/address  Show specific client information
          --logs            Show client-specific logs
          --stats           Show client statistics
        """
        if not self.server:
            print("\033[31mError:\033[0m Server instance not available")
            return
        
        # Parse arguments
        args = arg.split() if arg else []
        target_client = args[0] if args else None
        show_logs = '--logs' in args
        show_stats = '--stats' in args
        
        try:
            clients = self.server.get_connected_clients() if hasattr(self.server, 'get_connected_clients') else []
            
            if not clients:
                print("\033[33mInfo:\033[0m No clients currently connected")
                return
            
            # Show specific client
            if target_client and not target_client.startswith('--'):
                client_info = None
                for client in clients:
                    if (client.get('device_id') == target_client or 
                        client.get('address') == target_client or
                        target_client in client.get('address', '')):
                        client_info = client
                        break
                
                if not client_info:
                    print(f"\033[31mError:\033[0m Client '{target_client}' not found")
                    return
                
                self._show_client_details(client_info, show_logs, show_stats)
                return
            
            # Show all clients
            print()
            print(f"\033[1mConnected Clients ({len(clients)}):\033[0m")
            print()
            
            for client in clients:
                addr = client.get('address', 'Unknown')
                device_id = client.get('device_id', 'N/A')
                conn_time = client.get('connected_at', 'Unknown')
                status = client.get('status', 'Connected')
                
                if isinstance(conn_time, str) and conn_time != 'Unknown':
                    try:
                        conn_time = datetime.fromisoformat(conn_time).strftime("%H:%M:%S")
                    except:
                        pass
                
                print(f"  \033[1m{addr}\033[0m (\033[36m{device_id}\033[0m)")
                print(f"    Connected: {conn_time} | Status: \033[32m{status}\033[0m")
                print()
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _show_client_details(self, client_info, show_logs=False, show_stats=False):
        """Show detailed information for a specific client"""
        addr = client_info.get('address', 'Unknown')
        device_id = client_info.get('device_id', 'N/A')
        conn_time = client_info.get('connected_at', 'Unknown')
        status = client_info.get('status', 'Connected')
        packet_count = client_info.get('packet_count', 0)
        
        print()
        print(f"\033[1mClient Details: {addr}\033[0m")
        print(f"  Device ID:       \033[36m{device_id}\033[0m")
        print(f"  Address:         \033[34m{addr}\033[0m")
        print(f"  Connected:       {conn_time}")
        print(f"  Status:          \033[32m{status}\033[0m")
        print(f"  Packets:         \033[33m{packet_count}\033[0m")
        
        # Show ECDHE session info
        if self.server.crypto_manager and device_id != 'N/A':
            session_info = self.server.crypto_manager.get_session_info(device_id)
            if session_info:
                print(f"  Session Status:  \033[32mACTIVE\033[0m")
                print(f"  Session Created: {session_info['created_at'].strftime('%H:%M:%S')}")
                print(f"  Last Activity:   {session_info['last_activity'].strftime('%H:%M:%S')}")
            else:
                print(f"  Session Status:  \033[31mNOT FOUND\033[0m")
        
        if show_stats and hasattr(self.server, 'console_manager'):
            print()
            print("\033[1mClient Statistics:\033[0m")
            client_stats = self.server.console_manager.client_stats.get(addr, {})
            if client_stats:
                print(f"  Total Packets:   \033[36m{client_stats.get('total_packets', 0)}\033[0m")
                print(f"  Successful:      \033[32m{client_stats.get('successful_packets', 0)}\033[0m")
                print(f"  Failed:          \033[31m{client_stats.get('failed_packets', 0)}\033[0m")
                print(f"  Alarms:          \033[33m{client_stats.get('alarms', 0)}\033[0m")
                print(f"  Errors:          \033[31m{client_stats.get('errors', 0)}\033[0m")
        
        if show_logs and hasattr(self.server, 'console_manager'):
            print()
            print("\033[1mClient Logs:\033[0m")
            # Filter logs for this specific client
            all_logs = list(self.server.console_manager.system_logs)
            client_logs = [log for log in all_logs 
                          if addr in log.get('message', '') or device_id in log.get('message', '')]
            
            if client_logs:
                for log_entry in client_logs[-10:]:  # Show last 10 client-specific logs
                    timestamp = log_entry['timestamp'].strftime("%H:%M:%S")
                    level = log_entry['level']
                    message = log_entry['message']
                    
                    level_colors = {
                        'ERROR': '\033[31m',
                        'WARNING': '\033[33m',
                        'INFO': '\033[34m',
                        'DEBUG': '\033[90m'
                    }
                    
                    level_color = level_colors.get(level, '\033[0m')
                    print(f"  \033[90m{timestamp}\033[0m {level_color}[{level:<7}]\033[0m {message}")
            else:
                print("  \033[90mNo client-specific logs found\033[0m")
    
    def do_logs(self, arg):
        """Show recent system logs with filtering options
        Usage: logs [--level LEVEL] [--count N] [--grep PATTERN] [--follow]
        Options:
          --level LEVEL     Show only logs of specific level (ERROR, WARNING, INFO, DEBUG)
          --count N         Number of recent logs to show (default: 20)
          --grep PATTERN    Filter logs containing pattern
          --follow          Follow logs in real-time (Ctrl+C to stop)
        """
        if not self.server or not hasattr(self.server, 'console_manager'):
            print("\033[31mError:\033[0m Console manager not available")
            return
        
        # Parse arguments
        args = arg.split() if arg else []
        level_filter = None
        count = 20
        grep_pattern = None
        follow_mode = False
        
        i = 0
        while i < len(args):
            if args[i] == '--level' and i + 1 < len(args):
                level_filter = args[i + 1].upper()
                i += 2
            elif args[i] == '--count' and i + 1 < len(args):
                try:
                    count = int(args[i + 1])
                except ValueError:
                    print(f"\033[31mError:\033[0m Invalid count: {args[i + 1]}")
                    return
                i += 2
            elif args[i] == '--grep' and i + 1 < len(args):
                grep_pattern = args[i + 1].lower()
                i += 2
            elif args[i] == '--follow':
                follow_mode = True
                i += 1
            else:
                print(f"\033[33mWarning:\033[0m Unknown option: {args[i]}")
                i += 1
        
        if follow_mode:
            self._follow_logs(level_filter, grep_pattern)
            return
        
        try:
            all_logs = list(self.server.console_manager.system_logs)
            
            # Apply filters
            filtered_logs = all_logs
            if level_filter:
                filtered_logs = [log for log in filtered_logs if log['level'] == level_filter]
            if grep_pattern:
                filtered_logs = [log for log in filtered_logs 
                               if grep_pattern in log['message'].lower()]
            
            # Get recent logs
            logs = filtered_logs[-count:]
            
            if not logs:
                if level_filter or grep_pattern:
                    print("\033[33mInfo:\033[0m No logs match the specified filters")
                else:
                    print("\033[33mInfo:\033[0m No logs available")
                return
            
            print()
            filters_info = []
            if level_filter:
                filters_info.append(f"level={level_filter}")
            if grep_pattern:
                filters_info.append(f"grep='{grep_pattern}'")
            
            filter_str = f" ({', '.join(filters_info)})" if filters_info else ""
            print(f"\033[1mSystem Logs ({len(logs)}{filter_str}):\033[0m")
            print()
            
            for log_entry in logs:
                timestamp = log_entry['timestamp'].strftime("%H:%M:%S")
                level = log_entry['level']
                message = log_entry['message']
                
                # 레벨별 색상
                level_colors = {
                    'ERROR': '\033[31m',
                    'WARNING': '\033[33m',
                    'INFO': '\033[34m',
                    'DEBUG': '\033[90m'
                }
                
                level_color = level_colors.get(level, '\033[0m')
                
                # Highlight grep pattern
                if grep_pattern and grep_pattern in message.lower():
                    # Simple highlighting
                    highlighted_message = message.replace(grep_pattern, f"\033[43m{grep_pattern}\033[0m")
                    highlighted_message = highlighted_message.replace(grep_pattern.upper(), f"\033[43m{grep_pattern.upper()}\033[0m")
                    message = highlighted_message
                
                print(f"  \033[90m{timestamp}\033[0m {level_color}[{level:<7}]\033[0m {message}")
                
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _follow_logs(self, level_filter=None, grep_pattern=None):
        """Follow logs in real-time - optimized"""
        import time
        
        print("\033[1mFollowing logs... (Press Ctrl+C to stop and return to prompt)\033[0m")
        print("\033[90m(Real-time log monitoring active - new logs will appear below)\033[0m")
        print()
        
        last_count = len(self.server.console_manager.system_logs)
        
        try:
            while True:
                try:
                    # Reduce CPU usage by checking less frequently
                    current_count = len(self.server.console_manager.system_logs)
                    
                    if current_count > last_count:
                        # Only get new logs to avoid copying entire list
                        current_logs = list(self.server.console_manager.system_logs)
                        new_logs = current_logs[last_count:]
                        
                        # Always update last_count to prevent infinite loop
                        last_count = current_count
                        
                        for log_entry in new_logs:
                            # Apply filters
                            if level_filter and log_entry['level'] != level_filter:
                                continue
                            if grep_pattern and grep_pattern not in log_entry['message'].lower():
                                continue
                            
                            timestamp = log_entry['timestamp'].strftime("%H:%M:%S")
                            level = log_entry['level']
                            message = log_entry['message']
                            
                            level_colors = {
                                'ERROR': '\033[31m',
                                'WARNING': '\033[33m',
                                'INFO': '\033[34m',
                                'DEBUG': '\033[90m'
                            }
                            
                            level_color = level_colors.get(level, '\033[0m')
                            print(f"  \033[90m{timestamp}\033[0m {level_color}[{level:<7}]\033[0m {message}")
                    
                    time.sleep(2)  # Check every 2 seconds to reduce CPU usage
                    
                except KeyboardInterrupt:
                    # 내부 KeyboardInterrupt를 잡아서 루프 종료
                    break
                except Exception as e:
                    # 다른 예외는 무시하고 계속
                    time.sleep(1)
                    continue
                
        except KeyboardInterrupt:
            pass  # 외부 KeyboardInterrupt도 처리
        
        print("\n\033[33mInfo:\033[0m Log following stopped - returning to console prompt")
        return
    
    def do_stats(self, arg):
        """Show detailed server statistics with performance metrics
        Usage: stats [--latency] [--processing] [--details] [--client device_id]
        Options:
          --latency      Show detailed latency statistics
          --processing   Show packet processing time statistics
          --details      Show both latency and processing statistics
          --client ID    Show statistics for specific client
        """
        if not self.server or not hasattr(self.server, 'console_manager'):
            print("\033[31mError:\033[0m Console manager not available")
            return
        
        # Parse arguments
        args = arg.split() if arg else []
        show_latency = '--latency' in args
        show_processing = '--processing' in args
        show_details = '--details' in args
        client_id = None
        
        # --details는 --latency와 --processing 모두 활성화
        if show_details:
            show_latency = True
            show_processing = True
        
        i = 0
        while i < len(args):
            if args[i] == '--client' and i + 1 < len(args):
                client_id = args[i + 1]
                i += 2
            else:
                i += 1
        
        try:
            console_manager = self.server.console_manager
            stats = console_manager.system_stats
            
            print()
            if client_id:
                print(f"\033[1mClient Statistics: {client_id}\033[0m")
                self._show_client_stats(client_id, show_latency, show_processing)
            else:
                print("\033[1mServer Statistics:\033[0m")
                self._show_server_stats(stats, show_latency, show_processing)
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _show_server_stats(self, stats, show_latency=False, show_processing=False):
        """Show system-wide statistics"""
        print(f"  Total Packets:     \033[36m{stats['total_packets']}\033[0m")
        print(f"  Successful:        \033[32m{stats['successful_packets']}\033[0m")
        print(f"  Failed:            \033[31m{stats['failed_packets']}\033[0m")
        print(f"  Total Alarms:      \033[33m{stats['total_alarms']}\033[0m")
        print(f"  Total Errors:      \033[31m{stats['total_errors']}\033[0m")
        
        # Success rate
        if stats['total_packets'] > 0:
            success_rate = (stats['successful_packets'] / stats['total_packets']) * 100
            rate_color = "\033[32m" if success_rate >= 95 else "\033[33m" if success_rate >= 85 else "\033[31m"
            print(f"  Success Rate:      {rate_color}{success_rate:.1f}%\033[0m")
        
        # Average response time
        if stats['response_times']:
            avg_response = sum(stats['response_times']) / len(stats['response_times'])
            time_color = "\033[32m" if avg_response < 100 else "\033[33m" if avg_response < 500 else "\033[31m"
            print(f"  Avg Response:      {time_color}{avg_response:.2f}ms\033[0m")
        
        # Latency statistics
        if show_latency:
            latency_stats = self.server.console_manager.get_latency_stats()
            if latency_stats:
                print()
                print("\033[1mLatency Statistics (ms):\033[0m")
                self._print_performance_stats(latency_stats, "ms")
            else:
                print(f"  \033[90mNo latency data available\033[0m")
        
        # Processing time statistics
        if show_processing:
            processing_stats = self.server.console_manager.get_processing_stats()
            if processing_stats:
                print()
                print("\033[1mProcessing Time Statistics (ms):\033[0m")
                self._print_performance_stats(processing_stats, "ms")
            else:
                print(f"  \033[90mNo processing time data available\033[0m")
    
    def _show_client_stats(self, client_id, show_latency=False, show_processing=False):
        """Show client-specific statistics"""
        console_manager = self.server.console_manager
        
        # First try to use client_id directly as address
        client_stats = console_manager.client_stats.get(client_id, {})
        actual_client_addr = client_id
        
        # If not found, try to find by device_id
        if not client_stats or client_stats.get('total_packets', 0) == 0:
            if hasattr(self.server, 'connection_manager'):
                client_info = self.server.connection_manager.get_client_by_device_id(client_id)
                if client_info:
                    actual_client_addr = client_info['address']
                    client_stats = console_manager.client_stats.get(actual_client_addr, {})
        
        if not client_stats or client_stats.get('total_packets', 0) == 0:
            print(f"\033[33mInfo:\033[0m No statistics available for client '{client_id}'")
            print(f"\033[90mTried address lookup and device ID lookup\033[0m")
            return
        
        print(f"  Total Packets:     \033[36m{client_stats.get('total_packets', 0)}\033[0m")
        print(f"  Successful:        \033[32m{client_stats.get('successful_packets', 0)}\033[0m")
        print(f"  Failed:            \033[31m{client_stats.get('failed_packets', 0)}\033[0m")
        print(f"  Alarms:            \033[33m{client_stats.get('alarms', 0)}\033[0m")
        print(f"  Errors:            \033[31m{client_stats.get('errors', 0)}\033[0m")
        print(f"  Status:            \033[32m{client_stats.get('status', 'UNKNOWN')}\033[0m")
        
        # Client success rate
        total_packets = client_stats.get('total_packets', 0)
        if total_packets > 0:
            success_rate = (client_stats.get('successful_packets', 0) / total_packets) * 100
            rate_color = "\033[32m" if success_rate >= 95 else "\033[33m" if success_rate >= 85 else "\033[31m"
            print(f"  Success Rate:      {rate_color}{success_rate:.1f}%\033[0m")
        
        # Packet intervals
        interval_stats = console_manager.get_packet_interval_stats(actual_client_addr)
        if interval_stats:
            print()
            print("\033[1mPacket Intervals (ms):\033[0m")
            print(f"  Min:               \033[32m{interval_stats['min']:.1f}ms\033[0m")
            print(f"  Max:               \033[31m{interval_stats['max']:.1f}ms\033[0m")
            print(f"  Average:           \033[34m{interval_stats['avg']:.1f}ms\033[0m")
            print(f"  Median:            \033[36m{interval_stats['median']:.1f}ms\033[0m")
            print(f"  Std Dev:           \033[35m{interval_stats['std_dev']:.1f}ms\033[0m")
        
        # Client latency statistics
        if show_latency:
            latency_stats = console_manager.get_latency_stats(actual_client_addr)
            if latency_stats:
                print()
                print("\033[1mClient Latency Statistics (ms):\033[0m")
                self._print_performance_stats(latency_stats, "ms")
            else:
                print(f"  \033[90mNo client latency data available\033[0m")
        
        # Client processing statistics
        if show_processing:
            processing_stats = console_manager.get_processing_stats(actual_client_addr)
            if processing_stats:
                print()
                print("\033[1mClient Processing Statistics (ms):\033[0m")
                self._print_performance_stats(processing_stats, "ms")
            else:
                print(f"  \033[90mNo client processing data available\033[0m")
    
    def _print_performance_stats(self, stats, unit):
        """Print performance statistics in a formatted way"""
        print(f"  Samples:           \033[90m{stats['count']}\033[0m")
        print(f"  Min:               \033[32m{stats['min']:.2f}{unit}\033[0m")
        print(f"  Max:               \033[31m{stats['max']:.2f}{unit}\033[0m")
        print(f"  Average:           \033[34m{stats['avg']:.2f}{unit}\033[0m")
        print(f"  Median:            \033[36m{stats['median']:.2f}{unit}\033[0m")
        print(f"  95th Percentile:   \033[33m{stats['p95']:.2f}{unit}\033[0m")
        print(f"  99th Percentile:   \033[35m{stats['p99']:.2f}{unit}\033[0m")
    
    def do_crypto(self, arg):
        """Show cryptographic system information"""
        if not self.server or not self.server.crypto_manager:
            print("\033[31mError:\033[0m Crypto manager not available")
            return
            
        try:
            print()
            print("\033[1mCryptographic System:\033[0m")
            print(f"  Protocol:          \033[36mECDHE(X25519) + Ed25519\033[0m")
            print(f"  Encryption:        \033[36mChaCha20-Poly1305 AEAD\033[0m")
            print(f"  Forward Secrecy:   \033[32mENABLED\033[0m")
            print(f"  Key Exchange:      \033[35mEphemeral X25519 (32-byte)\033[0m")
            print(f"  Authentication:    \033[35mEd25519 Digital Signatures\033[0m")
            
            session_count = self.server.crypto_manager.get_active_session_count()
            session_color = "\033[32m" if session_count > 0 else "\033[90m"
            print(f"  Active Sessions:   {session_color}{session_count}\033[0m")
            
            # 서버의 Ed25519 공개키 표시
            try:
                server_pubkey = self.server.crypto_manager.get_server_public_key()
                pubkey_hex = server_pubkey[:8].hex() + "..." + server_pubkey[-8:].hex()
                print(f"  Server Public Key: \033[33m{pubkey_hex}\033[0m")
            except:
                print(f"  Server Public Key: \033[31mNot available\033[0m")
            
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def do_stop(self, arg):
        """Stop the server"""
        if not self.server:
            print("\033[31mError:\033[0m Server instance not available")
            return
            
        print("Stopping server...")
        try:
            self.server.stop()
            print("\033[32m✓\033[0m Server stopped successfully")
            self.running = False
            return True  # Exit the console
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def do_restart(self, arg):
        """Restart the server"""
        print("\033[33mInfo:\033[0m Restart functionality would be implemented here")
        print("\033[33mInfo:\033[0m Currently, please stop and start the server manually")
    
    def do_clear(self, arg):
        """Clear the console screen"""
        import os
        import shutil
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Display server header based on terminal size
        if self.server:
            terminal_width = shutil.get_terminal_size().columns
            
            if terminal_width >= 80:
                # Full ASCII art for wide terminals
                print(f"""
\033[36m ██╗     ██╗██╗   ██╗███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║     ██║██║   ██║██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║     ██║██║   ██║█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║     ██║╚██╗ ██╔╝██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ███████╗██║ ╚████╔╝ ███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚══════╝╚═╝  ╚═══╝  ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝\033[0m

\033[32m        IoT Server with ECDHE + Perfect Forward Secrecy\033[0m
\033[90m              Server: {self.server.host}:{self.server.port} | Status: \033[32m{'RUNNING' if self.server.is_running() else 'STOPPED'}\033[0m
""")
            elif terminal_width >= 60:
                # Compact ASCII art for medium terminals
                print(f"""
\033[36m ██╗     ██╗██╗   ██╗███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║     ██║██║   ██║██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║     ██║██║   ██║█████╗  ██║     ██║   ██║██╔██╗ ██║
 ███████╗██║ ╚████╔╝ ███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚══════╝╚═╝  ╚═══╝  ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝\033[0m

\033[32m    IoT Server with ECDHE + Perfect Forward Secrecy\033[0m
\033[90m          Server: {self.server.host}:{self.server.port} | Status: \033[32m{'RUNNING' if self.server.is_running() else 'STOPPED'}\033[0m
""")
            else:
                # Minimal display for small terminals
                print(f"""
\033[36m ██╗     ██╗██╗   ██╗███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██║     ██║██║   ██║██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ███████╗██║ ╚████╔╝ ███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚══════╝╚═╝  ╚═══╝  ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝\033[0m

\033[32mLIVECON IoT Server - ECDHE + PFS\033[0m
\033[90m{self.server.host}:{self.server.port} | Status: \033[32m{'RUNNING' if self.server.is_running() else 'STOPPED'}\033[0m
""")
    
    def do_packets(self, arg):
        """Monitor and inspect client packet contents in real-time
        Usage: packets [device_id] [--follow] [--raw] [--parsed] [--count N]
        Options:
          device_id    Show packets from specific device only
          --follow     Follow packets in real-time (Ctrl+C to stop)
          --raw        Show raw packet data (hex dump)
          --parsed     Show parsed packet contents
          --count N    Number of recent packets to show (default: 10)
        """
        if not self.server or not hasattr(self.server, 'console_manager'):
            print("\033[31mError:\033[0m Console manager not available")
            return
        
        # Parse arguments
        args = arg.split() if arg else []
        device_id = None
        follow_mode = '--follow' in args
        show_raw = '--raw' in args
        show_parsed = '--parsed' in args
        count = 10
        
        # If no format specified, show both raw and parsed
        if not show_raw and not show_parsed:
            show_raw = True
            show_parsed = True
        
        for i, arg_item in enumerate(args):
            if arg_item == '--count' and i + 1 < len(args):
                try:
                    count = int(args[i + 1])
                except ValueError:
                    print(f"\033[31mError:\033[0m Invalid count: {args[i + 1]}")
                    return
            elif not arg_item.startswith('--'):
                device_id = arg_item
        
        if follow_mode:
            self._follow_packets(device_id, show_raw, show_parsed)
        else:
            self._show_recent_packets(device_id, show_raw, show_parsed, count)
    
    def _show_recent_packets(self, device_id, show_raw, show_parsed, count):
        """Show recent packets"""
        try:
            # Get recent logs that contain sensor data
            all_logs = list(self.server.console_manager.system_logs)
            
            # Filter for sensor data logs
            packet_logs = []
            for log in all_logs:
                if 'Sensor data received' in log['message'] or 'Full parsed data' in log['message']:
                    if not device_id or device_id in log['message']:
                        packet_logs.append(log)
            
            # Get the most recent packets
            recent_packets = packet_logs[-count:]
            
            if not recent_packets:
                if device_id:
                    print(f"\033[33mInfo:\033[0m No recent packets found for device '{device_id}'")
                else:
                    print("\033[33mInfo:\033[0m No recent packets found")
                return
            
            print()
            print(f"\033[1mRecent Packet Contents ({len(recent_packets)} packets):\033[0m")
            if device_id:
                print(f"\033[90mFiltered for device: {device_id}\033[0m")
            print()
            
            current_device = None
            for log in recent_packets:
                timestamp = log['timestamp'].strftime("%H:%M:%S")
                message = log['message']
                
                # Extract device ID from log message
                if 'Device:' in message:
                    device_start = message.find('Device: ') + 8
                    device_end = message.find(',', device_start)
                    if device_end == -1:
                        device_end = message.find(' ', device_start)
                    if device_end == -1:
                        device_end = len(message)
                    extracted_device = message[device_start:device_end].strip()
                    
                    if extracted_device != current_device:
                        current_device = extracted_device
                        print(f"\033[36m──── Device: {current_device} ────\033[0m")
                
                print(f"\033[90m[{timestamp}]\033[0m", end=" ")
                
                if 'Full parsed data' in message and show_parsed:
                    # Extract and format parsed data
                    data_start = message.find('{')
                    if data_start != -1:
                        try:
                            import ast
                            data_str = message[data_start:]
                            data = ast.literal_eval(data_str)
                            print("\033[32mParsed Data:\033[0m")
                            for key, value in data.items():
                                if key == 'TEMP':
                                    print(f"    Temperature: \033[33m{value}°C\033[0m")
                                elif key == 'HUMIDITY':
                                    print(f"    Humidity:    \033[34m{value}%\033[0m")
                                elif key == 'LAT':
                                    print(f"    Latitude:    \033[35m{value}\033[0m")
                                elif key == 'LON':
                                    print(f"    Longitude:   \033[35m{value}\033[0m")
                                elif key == 'ID':
                                    print(f"    Packet ID:   \033[36m{value}\033[0m")
                                elif key == 'DEVICE_ID':
                                    print(f"    Device ID:   \033[36m{value}\033[0m")
                                else:
                                    print(f"    {key}: {value}")
                        except:
                            print(f"\033[32mParsed:\033[0m {data_str}")
                elif 'Sensor data received' in message and show_raw:
                    print(f"\033[37m{message}\033[0m")
                
                print()
        
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}")
    
    def _follow_packets(self, device_id, show_raw, show_parsed):
        """Follow packets in real-time"""
        import time
        
        filter_text = f" for device '{device_id}'" if device_id else ""
        print(f"\033[1mFollowing packet contents{filter_text}... (Press Ctrl+C to stop)\033[0m")
        print("\033[90m(Real-time packet monitoring active - new packets will appear below)\033[0m")
        print()
        
        last_count = len(self.server.console_manager.system_logs)
        following = True
        
        try:
            while following:
                try:
                    current_count = len(self.server.console_manager.system_logs)
                    
                    if current_count > last_count:
                        current_logs = list(self.server.console_manager.system_logs)
                        new_logs = current_logs[last_count:]
                        
                        for log_entry in new_logs:
                            if not following:
                                break
                            
                            message = log_entry['message']
                            
                            # Filter for packet-related logs
                            is_packet_log = ('Sensor data received' in message or 
                                           'Full parsed data' in message)
                            
                            if not is_packet_log:
                                continue
                            
                            # Device filter
                            if device_id and device_id not in message:
                                continue
                            
                            timestamp = log_entry['timestamp'].strftime("%H:%M:%S")
                            
                            if 'Full parsed data' in message and show_parsed:
                                print(f"\033[90m[{timestamp}]\033[0m \033[32mParsed Data:\033[0m")
                                
                                # Extract and format parsed data
                                data_start = message.find('{')
                                if data_start != -1:
                                    try:
                                        import ast
                                        data_str = message[data_start:]
                                        data = ast.literal_eval(data_str)
                                        for key, value in data.items():
                                            if key == 'TEMP':
                                                print(f"  Temperature: \033[33m{value}°C\033[0m")
                                            elif key == 'HUMIDITY':
                                                print(f"  Humidity:    \033[34m{value}%\033[0m")
                                            elif key == 'LAT':
                                                print(f"  Latitude:    \033[35m{value}\033[0m")
                                            elif key == 'LON':
                                                print(f"  Longitude:   \033[35m{value}\033[0m")
                                            elif key == 'ID':
                                                print(f"  Packet ID:   \033[36m{value}\033[0m")
                                            elif key == 'DEVICE_ID':
                                                print(f"  Device ID:   \033[36m{value}\033[0m")
                                            else:
                                                print(f"  {key}: {value}")
                                    except:
                                        print(f"  {data_str}")
                                print()
                                
                            elif 'Sensor data received' in message and show_raw:
                                print(f"\033[90m[{timestamp}]\033[0m \033[37m{message}\033[0m")
                        
                        last_count = current_count
                    
                    if following:
                        time.sleep(0.5)  # Check twice per second
                        
                except KeyboardInterrupt:
                    following = False
                    break
                except Exception:
                    time.sleep(1)
                    continue
                    
        except KeyboardInterrupt:
            pass
            
        print("\n\033[33mInfo:\033[0m Packet monitoring stopped - returning to console prompt")
    
    def do_exit(self, arg):
        """Exit the console (keeps server running)"""
        print("\033[33mInfo:\033[0m Exiting console... (Server continues running)")
        self.running = False
        if hasattr(self, 'cmdloop_running'):
            self.cmdloop_running = False
        return True
    
    def do_shutdown(self, arg):
        """Shutdown the server and exit console"""
        if self.server:
            print("Shutting down server...")
            self.server.stop()
            print("\033[32m✓\033[0m Server shutdown complete")
        self.running = False
        if hasattr(self, 'cmdloop_running'):
            self.cmdloop_running = False
        return True
    
    def do_help(self, arg):
        """Show available commands or detailed help for specific command"""
        if arg:
            # Show detailed help for specific command
            command = arg.strip()
            method_name = f"do_{command}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                if method.__doc__:
                    print()
                    print(f"\033[1m{command}\033[0m - {method.__doc__.split()[0].lower()}")
                    print()
                    # Extract usage and options from docstring
                    doc_lines = method.__doc__.strip().split('\n')
                    for line in doc_lines[1:]:  # Skip first line
                        line = line.strip()
                        if line:
                            print(f"  {line}")
                else:
                    print(f"\033[33mInfo:\033[0m No detailed help available for '{command}'")
            else:
                print(f"\033[31mError:\033[0m Unknown command '{command}'")
            return
        
        print()
        print("Available commands:")
        print()
        print("  \033[1mstatus\033[0m      show server status and overview")
        print("  \033[1msessions\033[0m    list ECDHE sessions [device_id] [--active] [--expired] [--details]")
        print("  \033[1mclients\033[0m     show connected clients [device_id|address] [--logs] [--stats]")
        print("  \033[1mlogs\033[0m        display system logs [--level LEVEL] [--count N] [--grep PATTERN] [--follow]")
        print("  \033[1mpackets\033[0m     inspect client packet contents [device_id] [--follow] [--raw] [--parsed] [--count N]")
        print("  \033[1mstats\033[0m       show statistics [--latency] [--processing] [--client ID]")
        print("  \033[1mcrypto\033[0m      display cryptographic system information")
        print("  \033[1mclear\033[0m       clear the console screen")
        print("  \033[1mstop\033[0m        stop the server")
        print("  \033[1mrestart\033[0m     restart the server")
        print("  \033[1mexit\033[0m        exit console (server keeps running)")
        print("  \033[1mshutdown\033[0m    shutdown server and exit console")
        print("  \033[1mhelp\033[0m        show this help message")
        print()
        print("\033[90mUsage examples:\033[0m")
        print("  \033[36mclients device001 --logs\033[0m          Show client details with logs")
        print("  \033[36msessions --active --details\033[0m       Show detailed active sessions")
        print("  \033[36mlogs --level ERROR --count 50\033[0m    Show last 50 error logs")
        print("  \033[36mlogs --follow --grep 'device001'\033[0m Follow logs for specific device")
        print("  \033[36mstats --latency --processing\033[0m     Show detailed performance stats")
        print("  \033[36mstats --client device001 --latency\033[0m Show client latency statistics")
        print("  \033[36mpackets device001 --follow --parsed\033[0m   Follow parsed packets from specific device")
        print("  \033[36mpackets --count 20 --raw\033[0m            Show last 20 raw packets")
        print()
        print("For detailed help on a command: \033[1mhelp <command>\033[0m")
    
    def _get_uptime(self):
        """서버 업타임 계산"""
        if not hasattr(self.server, 'console_manager') or not self.server.console_manager:
            return "Unknown"
            
        try:
            start_time = self.server.console_manager.system_stats['start_time']
            uptime = datetime.now() - start_time
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "Unknown"
    
    def emptyline(self):
        """Handle empty line input"""
        pass
    
    def default(self, line):
        """Handle unknown commands"""
        print(f"\033[33mWarning:\033[0m Unknown command '\033[1m{line}\033[0m'. Type '\033[1mhelp\033[0m' for available commands.")
    
    def do_EOF(self, line):
        """Handle Ctrl+D (EOF)"""
        print("\n\033[33mInfo:\033[0m Use '\033[1mexit\033[0m' or '\033[1mshutdown\033[0m' to quit.")
        return False
    
    def cmdloop(self, intro=None):
        """Custom cmdloop with proper input handling"""
        import sys
        
        if intro is not None:
            self.intro = intro
        
        if self.intro:
            self.stdout.write(str(self.intro) + '\n')
        
        # stdin이 tty가 아니거나 사용할 수 없는 경우 대화형 모드 불가
        if not sys.stdin.isatty():
            print("\033[31mError:\033[0m Interactive console requires a TTY terminal")
            return
        
        self.cmdloop_running = True
        while self.cmdloop_running:
            try:
                super().cmdloop(intro="")
                break
            except KeyboardInterrupt:
                print("\n^C")
                print("\033[33mInfo:\033[0m Use '\033[1mexit\033[0m' or '\033[1mshutdown\033[0m' to quit.")
            except EOFError:
                print("\n\033[33mInfo:\033[0m Use '\033[1mexit\033[0m' or '\033[1mshutdown\033[0m' to quit.")
                break
    

# ConsoleManager는 이제 console_manager.py에서 import