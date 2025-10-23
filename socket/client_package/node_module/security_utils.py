"""
Security utilities for LIVECON client
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

def mask_server_address(address: str) -> str:
    """Mask server address for logging"""
    if not address:
        return "***"
    parts = address.split('.')
    if len(parts) == 4:
        # IPv4
        return f"{parts[0]}.***.***{parts[3]}"
    else:
        # Domain or other format
        if len(address) <= 4:
            return "***"
        return address[:3] + "***" + address[-3:]
