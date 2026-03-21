import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _get_fernet() -> Fernet:
    """Derive a Fernet instance from the application secret key."""
    raw = hashlib.sha256(settings.secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(raw)
    return Fernet(fernet_key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value using Fernet. Returns base64-encoded ciphertext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet-encrypted value back to plaintext."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
