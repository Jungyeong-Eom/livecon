# node_module/rsa_utils.py
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA


def generate_and_save_keys(private_path='private.pem', public_path='public.pem'):
    key = RSA.generate(2048)
    with open(private_path, "wb") as f:
        f.write(key.export_key())
    with open(public_path, "wb") as f:
        f.write(key.publickey().export_key())

def load_private_key(path='private.pem') -> RSA.RsaKey:
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

def load_public_key(path='public.pem') -> RSA.RsaKey:
    with open(path, "rb") as f:
        return RSA.import_key(f.read())

def encrypt(data: bytes, public_key: RSA.RsaKey) -> bytes:
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)

def decrypt(ciphertext: bytes, private_key: RSA.RsaKey) -> bytes:
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(ciphertext)
