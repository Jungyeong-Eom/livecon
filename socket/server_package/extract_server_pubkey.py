#!/usr/bin/env python3
"""
서버 Ed25519 공개키 추출 유틸리티
클라이언트 config.json에 추가할 공개키를 추출합니다.
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from server_module.crypto_manager import CryptoManager

def extract_server_pubkey():
    """서버 Ed25519 공개키 추출"""
    print("=" * 70)
    print("서버 Ed25519 공개키 추출")
    print("=" * 70)

    crypto_manager = CryptoManager()

    # 키 초기화
    if not crypto_manager.initialize_keys():
        print("ERROR: 키 초기화 실패")
        return False

    # 공개키 추출
    pubkey_bytes = crypto_manager.get_server_public_key()
    pubkey_hex = pubkey_bytes.hex()

    print(f"\n✓ 서버 Ed25519 공개키 (32 bytes):")
    print(f"\nHex (클라이언트 config.json에 사용):")
    print(f"{pubkey_hex}")

    print(f"\n" + "=" * 70)
    print("클라이언트 설정 방법:")
    print("=" * 70)
    print(f'\n1. 클라이언트의 config.json 파일을 엽니다.')
    print(f'2. "server" 섹션에 다음을 추가합니다:')
    print(f'\n   "ed25519_pubkey_hex": "{pubkey_hex}"')
    print(f'\n3. 전체 예시:')
    print(f'''
{{
    "server": {{
        "address": "SERVER_IP_ADDRESS",
        "port": 12351,
        "ed25519_pubkey_hex": "{pubkey_hex}"
    }},
    "client": {{
        "device_id": "device001",
        "send_interval": 10
    }}
}}
''')

    print("=" * 70)
    print("⚠️  중요: 이 공개키는 서버 재시작 시 변경됩니다.")
    print("   프로덕션 환경에서는 서버 키를 파일에 저장하고 재사용하세요.")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        extract_server_pubkey()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
