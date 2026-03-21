import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_bcrypt_hash() -> None:
    hashed = hash_password("secret")
    assert hashed.startswith("$2b$")


def test_verify_password_correct() -> None:
    hashed = hash_password("secret")
    assert verify_password("secret", hashed) is True


def test_verify_password_wrong() -> None:
    hashed = hash_password("secret")
    assert verify_password("wrong", hashed) is False


def test_create_access_token_has_correct_claims() -> None:
    token = create_access_token({"sub": "1"})
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token_has_correct_claims() -> None:
    token = create_refresh_token({"sub": "1"})
    payload = decode_token(token)
    assert payload["sub"] == "1"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_decode_token_valid() -> None:
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"


def test_decode_token_invalid_raises() -> None:
    with pytest.raises(JWTError):
        decode_token("not-a-valid-token")


def test_decode_token_tampered_raises() -> None:
    token = create_access_token({"sub": "1"})
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(JWTError):
        decode_token(tampered)
