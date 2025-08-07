from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# RSA 키 생성 및 PEM 파일 저장
def generate_and_save_keys(private_path='server/private.pem', public_path='node/public.pem'):
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()

    with open(private_path, "wb") as f:
        f.write(private_key)
    with open(public_path, "wb") as f:
        f.write(public_key)

    print(f"키 파일 생성 완료: {private_path}, {public_path}")

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

