import random
import time
from datetime import datetime

def generate_random_packet() -> bytes:
    STX = 0x24
    ETX = 0x5C
    ID = random.randint(1, 65535)
    TEMP = int(random.uniform(15.0, 35.0) * 10)
    O2 = int(random.uniform(18.0, 25.0) * 100)
    WTR_TEMP = int(random.uniform(15.0, 35.0) * 10)
    LOC = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10)).encode('ascii')
    now = datetime.now()

    packet = bytearray()
    packet.append(STX)
    packet += ID.to_bytes(2, 'big')
    packet += (25).to_bytes(3, 'big')
    packet += TEMP.to_bytes(2, 'big')
    packet += O2.to_bytes(2, 'big')
    packet += WTR_TEMP.to_bytes(2, 'big')
    packet += LOC
    packet += now.year.to_bytes(2, 'big')
    packet += now.month.to_bytes(1, 'big')
    packet += now.day.to_bytes(1, 'big')
    packet += now.hour.to_bytes(1, 'big')
    packet += now.minute.to_bytes(1, 'big')
    packet += now.second.to_bytes(1, 'big')
    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, 'big')
    packet.append(ETX)

    return bytes(packet)
