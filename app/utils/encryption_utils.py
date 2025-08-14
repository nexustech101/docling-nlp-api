# app/encryption.py
import os
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.backends import default_backend


def derive_key(key: bytes, salt: bytes = None) -> bytes: # type: ignore
    if salt:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend()
        )
        return kdf.derive(key)
    return (key + b'\0' * 32)[:32]


def get_cipher(key: bytes, iv: bytes):
    return Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())


def pad_message(data: bytes) -> bytes:
    padder = padding.PKCS7(128).padder()
    return padder.update(data) + padder.finalize()


def unpad_message(data: bytes) -> bytes:
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(data) + unpadder.finalize()


def encrypt_message(plaintext: str, key: str, salt_b64: str = None) -> str:  # type: ignore
    salt = base64.b64decode(salt_b64) if salt_b64 else None
    derived_key = derive_key(key.encode(), salt) # type: ignore
    iv = os.urandom(16)
    cipher = get_cipher(derived_key, iv)
    encryptor = cipher.encryptor()
    padded = pad_message(plaintext.encode())
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode()


def decrypt_message(ciphertext_b64: str, key: str, salt_b64: str = None) -> str:  # type: ignore
    salt = base64.b64decode(salt_b64) if salt_b64 else None
    derived_key = derive_key(key.encode(), salt)  # type: ignore
    raw = base64.b64decode(ciphertext_b64)
    iv, ciphertext = raw[:16], raw[16:]
    cipher = get_cipher(derived_key, iv)
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return unpad_message(padded_plaintext).decode()
