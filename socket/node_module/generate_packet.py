# node_module/generate_packet.py
import random
import struct

from .geohash_encode import geohash_encode


def generate_packet(device_id: int):
    """
    센서 패킷 생성 예시
    :param device_id: 센서 ID
    :return: bytes
    """
    temp = random.randint(-40, 125)  # 온도
    do = random.randint(0, 6000)     # DO
    wtr_temp = random.randint(0, 1000) # 수온
    lat, lon = 37.5665, 126.9780
    loc_bytes = geohash_encode(lat, lon)

    # 간단한 패킷 구조 예시
    packet = struct.pack(
        '>B H I H H H 10s B B B B B H B',
        36,          # STX, 예시
        device_id,   # ID
        32,          # 길이
        temp,
        do,
        wtr_temp,
        loc_bytes,
        23, 8, 15, 12, 30,  # YYYY-MM-DD HH:MM
        1234,         # 체크섬 예시
        92            # ETX '\'
    )
    return packet
