from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# 서버용 RSA 키 쌍 생성 (서버만 호출해야 함)
def generate_server_keys(private_path='server/private.pem', public_path='server/public.pem'):
    """
    서버용 RSA 키 쌍 생성
    - 서버는 개인키를 보관하고 공개키를 클라이언트에게 제공
    """
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()

    with open(private_path, "wb") as f:
        f.write(private_key)
    with open(public_path, "wb") as f:
        f.write(public_key)

    print(f"서버 키 생성 완료: 개인키({private_path}), 공개키({public_path})")
    return True

# 기존 함수 유지 (하위 호환성)
def generate_and_save_keys(private_path='server/private.pem', public_path='node/public.pem'):
    """
    @deprecated 보안상 권장하지 않음. generate_server_keys() 사용 권장
    """
    print("경고: 이 방식은 보안상 권장하지 않습니다. 서버는 자신의 키만 생성해야 합니다.")
    return generate_server_keys(private_path, public_path)

# 개인 키 로딩 (서버용)
def load_private_key(path='private.pem') -> RSA.RsaKey:
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

# 공개 키 로딩 (클라이언트용)
def load_public_key(path='public.pem') -> RSA.RsaKey:
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

# 암호화 (클라이언트 → 서버)
def encrypt(data: bytes, public_key: RSA.RsaKey) -> bytes:
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)

# 복호화 (서버 수신 시)
def decrypt(ciphertext: bytes, private_key: RSA.RsaKey) -> bytes:
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(ciphertext)

