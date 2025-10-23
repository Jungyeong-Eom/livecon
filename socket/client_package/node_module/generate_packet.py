import random
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
from .geohash_encode import geohash_encode

class PacketConfig:
    """Configuration for packet generation"""
    def __init__(self):
        self.STX = 0x24
        self.ETX = 0x5C
        self.device_id = 1
        self.temp_range = (15.0, 35.0)
        self.o2_range = (18.0, 25.0)
        self.water_temp_range = (15.0, 35.0)
        self.location_bounds = {"lat": (-90.0, 90.0), "lon": (-180.0, 180.0)}
        self.geohash_precision = 10

def calculate_checksum(packet_data: bytes) -> int:
    """Calculate packet checksum"""
    return sum(packet_data) & 0xFFFF

def validate_sensor_value(value: int, min_val: int = 0, max_val: int = 65535, name: str = "value") -> int:
    """Validate sensor value is within u16 range

    Args:
        value: The value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value (default: 65535 for u16)
        name: Name of the value for error messages

    Raises:
        ValueError: If value is out of range
    """
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value)}")
    if not (min_val <= value <= max_val):
        raise ValueError(f"{name} {value} out of range [{min_val}, {max_val}]")
    return value

def generate_sensor_data(config: PacketConfig) -> Dict:
    """Generate random sensor data with validation"""
    # Generate values and validate they fit in u16
    temp = int(random.uniform(*config.temp_range) * 10)
    oxygen = int(random.uniform(*config.o2_range) * 100)
    water_temp = int(random.uniform(*config.water_temp_range) * 10)

    # Validate all sensor values are within u16 range
    validate_sensor_value(temp, name="temperature")
    validate_sensor_value(oxygen, name="oxygen")
    validate_sensor_value(water_temp, name="water_temperature")

    return {
        'temperature': temp,
        'oxygen': oxygen,
        'water_temperature': water_temp,
        'location': {
            'lat': random.uniform(*config.location_bounds['lat']),
            'lon': random.uniform(*config.location_bounds['lon'])
        },
        'timestamp': datetime.now()
    }

def build_packet(device_id: int, sensor_data: Dict, config: PacketConfig) -> bytes:
    """Build packet from sensor data

    Packet structure:
    - STX (1 byte)
    - DeviceID (2 bytes)
    - Length (3 bytes) - AUTO-CALCULATED
    - Data (variable):
        - Temperature (2 bytes)
        - Oxygen (2 bytes)
        - Water Temperature (2 bytes)
        - Geohash (10 bytes)
        - Timestamp (7 bytes - YYYY:2, MM:1, DD:1, hh:1, mm:1, ss:1)
    - Checksum (2 bytes)
    - ETX (1 byte)

    Total Data Section: 2+2+2+10+7 = 23 bytes
    Total Packet: 1+2+3+23+2+1 = 32 bytes
    """
    # Validate device_id is in u16 range
    if not (0 <= device_id <= 65535):
        raise ValueError(f"device_id {device_id} out of range [0, 65535]")

    # Validate sensor values
    validate_sensor_value(sensor_data['temperature'], name="temperature")
    validate_sensor_value(sensor_data['oxygen'], name="oxygen")
    validate_sensor_value(sensor_data['water_temperature'], name="water_temperature")

    packet = bytearray()
    packet.append(config.STX)
    packet += device_id.to_bytes(2, 'big')

    # Placeholder for length (will be calculated later)
    length_pos = len(packet)
    packet += (0).to_bytes(3, 'big')

    # Build data section
    data_start = len(packet)

    # Add sensor data
    packet += sensor_data['temperature'].to_bytes(2, 'big')
    packet += sensor_data['oxygen'].to_bytes(2, 'big')
    packet += sensor_data['water_temperature'].to_bytes(2, 'big')

    # Add location (geohash) - ensure exactly 10 bytes
    location = sensor_data['location']
    geohash = geohash_encode(location['lat'], location['lon'], precision=config.geohash_precision)
    geohash_bytes = geohash.encode('ascii')
    if len(geohash_bytes) != 10:
        raise ValueError(f"Geohash must be exactly 10 bytes, got {len(geohash_bytes)}")
    packet += geohash_bytes

    # Add timestamp (7 bytes: YYYY, MM, DD, hh, mm, ss)
    timestamp = sensor_data['timestamp']
    packet += timestamp.year.to_bytes(2, 'big')
    packet += timestamp.month.to_bytes(1, 'big')
    packet += timestamp.day.to_bytes(1, 'big')
    packet += timestamp.hour.to_bytes(1, 'big')
    packet += timestamp.minute.to_bytes(1, 'big')
    packet += timestamp.second.to_bytes(1, 'big')

    # Calculate actual data length
    data_length = len(packet) - data_start

    # Update length field (auto-calculated)
    packet[length_pos:length_pos+3] = data_length.to_bytes(3, 'big')

    # Add checksum (STX excluded, DeviceID + Length + Data included)
    checksum = calculate_checksum(packet[1:])
    packet += checksum.to_bytes(2, 'big')
    packet.append(config.ETX)

    return bytes(packet)

def generate_random_packet(device_id: Optional[int] = None, config: Optional[PacketConfig] = None) -> bytes:
    """Generate random packet with improved flexibility"""
    if config is None:
        config = PacketConfig()
    
    if device_id is None:
        device_id = config.device_id
    
    sensor_data = generate_sensor_data(config)
    return build_packet(device_id, sensor_data, config)
