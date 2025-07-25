## checksum.py
def checksum(data: bytes):
    if len(data)< 32:
        raise ValueError("Data length is too short for checksum calculation")
    if data[0] != ord('$'):
        raise ValueError("STX error!")
    if data[-1] != ord('\\'):
        raise ValueError("ETX error!")
    chk = sum(data[1:-3])
    chk &= 0xFFFF  
    return chk.to_bytes(2, 'big')