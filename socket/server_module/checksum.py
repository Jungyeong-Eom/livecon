def checksum(data: bytes) -> int:
    """간단한 체크섬 계산 (합계 & 0xFFFF)"""
    return sum(data[:-3]) & 0xFFFF
