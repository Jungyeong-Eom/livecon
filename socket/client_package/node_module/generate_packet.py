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

def generate_sensor_data(config: PacketConfig) -> Dict:
    """Generate random sensor data"""
    return {
        'temperature': int(random.uniform(*config.temp_range) * 10),
        'oxygen': int(random.uniform(*config.o2_range) * 100),
        'water_temperature': int(random.uniform(*config.water_temp_range) * 10),
        'location': {
            'lat': random.uniform(*config.location_bounds['lat']),
            'lon': random.uniform(*config.location_bounds['lon'])
        },
        'timestamp': datetime.now()
    }

def build_packet(device_id: int, sensor_data: Dict, config: PacketConfig) -> bytes:
    """Build packet from sensor data"""
    packet = bytearray()
    packet.append(config.STX)
    packet += device_id.to_bytes(2, 'big')
    packet += (32).to_bytes(3, 'big')
    
    # Add sensor data
    packet += sensor_data['temperature'].to_bytes(2, 'big')
    packet += sensor_data['oxygen'].to_bytes(2, 'big')
    packet += sensor_data['water_temperature'].to_bytes(2, 'big')
    
    # Add location (geohash)
    location = sensor_data['location']
    geohash = geohash_encode(location['lat'], location['lon'], precision=config.geohash_precision)
    packet += geohash.encode('ascii')
    
    # Add timestamp
    timestamp = sensor_data['timestamp']
    packet += timestamp.year.to_bytes(2, 'big')
    packet += timestamp.month.to_bytes(1, 'big')
    packet += timestamp.day.to_bytes(1, 'big')
    packet += timestamp.hour.to_bytes(1, 'big')
    packet += timestamp.minute.to_bytes(1, 'big')
    packet += timestamp.second.to_bytes(1, 'big')
    
    # Add checksum
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
