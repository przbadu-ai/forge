from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload.update({"exp": expire, "type": "access"})
    return str(jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm))


def create_refresh_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload.update({"exp": expire, "type": "refresh"})
    return str(jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm))


def decode_token(token: str) -> dict[str, Any]:
    # Raises JWTError if invalid or expired
    result: dict[str, Any] = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    return result


__all__ = [
    "JWTError",
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
]
