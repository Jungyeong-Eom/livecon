import json

def parse_packet(raw_data):
    try:
        packet = json.loads(raw_data)
        # 최소 필수 체크
        if "device_id" in packet and "sensors" in packet:
            return packet
        else:
            raise ValueError("필수 필드 없음")
    except json.JSONDecodeError:
        raise ValueError("JSON 파싱 실패")
