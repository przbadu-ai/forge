import pytest
from cryptography.fernet import InvalidToken

from app.core.encryption import decrypt_value, encrypt_value


def test_encrypt_decrypt_roundtrip() -> None:
    """encrypt then decrypt returns original plaintext."""
    original = "my-super-secret-api-key"
    encrypted = encrypt_value(original)
    assert encrypted != original
    assert len(encrypted) > 0
    assert decrypt_value(encrypted) == original


def test_encrypt_produces_different_ciphertext_each_call() -> None:
    """Fernet uses a random IV so each call produces different ciphertext."""
    plaintext = "same-input"
    c1 = encrypt_value(plaintext)
    c2 = encrypt_value(plaintext)
    assert c1 != c2
    # Both still decrypt to original
    assert decrypt_value(c1) == plaintext
    assert decrypt_value(c2) == plaintext


def test_decrypt_invalid_raises() -> None:
    """Decrypting garbage raises InvalidToken."""
    with pytest.raises(InvalidToken):
        decrypt_value("not-valid-fernet-ciphertext")
