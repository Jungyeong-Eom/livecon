# node_module/geohash_encode.py
def geohash_encode(lat: float, lon: float) -> bytes:
    """
    위도/경도를 지오해시 바이트로 변환 (간단 예시)
    """
    # 실제 구현은 패키지 사용 가능, 여기선 더미 예시
    return f"{lat:.5f},{lon:.5f}".encode('utf-8')
