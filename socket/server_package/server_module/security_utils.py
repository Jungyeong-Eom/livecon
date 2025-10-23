"""
Security utilities for LIVECON
Includes sensitive data masking for logs
"""

def mask_device_id(device_id: str) -> str:
    """Mask device ID for logging (show first 3 and last 2 characters)

    Example: device001 -> dev***01
    """
    if not device_id or len(device_id) <= 5:
        return "***"
    return device_id[:3] + "***" + device_id[-2:]

def mask_key_material(key_bytes: bytes) -> str:
    """Mask cryptographic key material for logging

    Shows only first 4 hex characters
    """
    if not key_bytes:
        return "***"
    hex_str = key_bytes.hex()
    if len(hex_str) <= 8:
        return "****"
    return hex_str[:4] + "..." + f"({len(key_bytes)} bytes)"

def mask_ip_address(ip: str) -> str:
    """Mask IP address for logging (show first octet and last octet)

    Example: 192.168.1.100 -> 192.***.***100
    """
    if not ip:
        return "***"
    parts = ip.split('.')
    if len(parts) != 4:
        # Not IPv4, just mask half
        if len(ip) <= 4:
            return "***"
        return ip[:2] + "***" + ip[-2:]
    return f"{parts[0]}.***.***{parts[3]}"

def safe_log_session_info(device_id: str, client_ip: str) -> str:
    """Create safe log string for session information"""
    return f"device={mask_device_id(device_id)}, client={mask_ip_address(client_ip)}"
