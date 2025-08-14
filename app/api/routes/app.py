from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.backends import default_backend
from typing import Optional
from data_science_api.app.models.models import Message
import base64
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def derive_key(key: bytes, salt: Optional[bytes] = None) -> bytes:
    """Derive a 32-byte AES key using PBKDF2 with optional salt."""
    if salt:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend()
        )
        return kdf.derive(key)
    # pad or hash to fit AES-256
    return (key + b'\0' * 32)[:32]  # Null byte padding


def get_cipher(key: bytes, iv: bytes):
    return Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())


def pad_message(data: bytes) -> bytes:
    padder = padding.PKCS7(128).padder()
    return padder.update(data) + padder.finalize()


def unpad_message(data: bytes) -> bytes:
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(data) + unpadder.finalize()


@app.post("/encrypt")
async def encrypt(data: Message):
    try:
        salt = base64.b64decode(data.salt) if data.salt else None
        key = derive_key(data.key.encode(), salt)

        iv = os.urandom(16)
        cipher = get_cipher(key, iv)
        encryptor = cipher.encryptor()

        padded = pad_message(data.message.encode("utf-8"))
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        result = base64.b64encode(iv + ciphertext).decode()
        return {"result": result}
    except HTTPException as e:
        raise HTTPException(
            status_code=400, detail=f"Encryption failed: {str(e)}"
        )


@app.post("/decrypt")
async def decrypt(data: Message):
    try:
        salt = base64.b64decode(data.salt) if data.salt else None
        key = derive_key(data.key.encode(), salt)

        raw = base64.b64decode(data.message)
        iv = raw[:16]
        ciphertext = raw[16:]

        cipher = get_cipher(key, iv)
        decryptor = cipher.decryptor()

        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        plaintext = unpad_message(padded_plaintext).decode("utf-8")

        return {"result": plaintext}
    except HTTPException as e:
        raise HTTPException(
            status_code=400, detail=f"Decryption failed: {str(e)}"
        )
