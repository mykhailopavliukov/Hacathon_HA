"""Accounts: password hashing, sign-up, login and session tokens (standard library only)."""

import hashlib
import hmac
import secrets

# scrypt cost: about 16 MB of memory and tens of milliseconds per hash.
_N, _R, _P = 2**14, 8, 1
_SALT_BYTES = 16


def _derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)


def hash_password(password: str) -> str:
    """Return "scrypt$<salt>$<hash>" in hex; the random salt makes equal passwords differ."""
    salt = secrets.token_bytes(_SALT_BYTES)
    return f"scrypt${salt.hex()}${_derive(password, salt).hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_hex, hash_hex = stored.split("$")
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(hash_hex)
    except ValueError:
        return False
    # compare_digest takes the same time wherever the values differ, so timing leaks nothing.
    return hmac.compare_digest(_derive(password, salt), expected)
