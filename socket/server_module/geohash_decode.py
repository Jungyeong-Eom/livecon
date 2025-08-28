def geohash_decode(gh_bytes: bytes) -> tuple:
    """Geohash 디코딩 예시 (실제 로직 필요 시 교체)"""
    if len(gh_bytes) != 10:
        raise ValueError("Geohash 길이 오류")
    # 단순 예시: 각 바이트를 좌표로 변환
    lat = int.from_bytes(gh_bytes[:5], 'big') / 1e5
    lon = int.from_bytes(gh_bytes[5:], 'big') / 1e5
    return lat, lon
