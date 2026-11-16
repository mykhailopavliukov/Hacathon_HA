"""Accounts: password hashing, sign-up, login and session tokens (standard library only)."""

import hashlib
import hmac
import re
import secrets
import sqlite3
from contextlib import closing
from functools import cache

from app import db

USERNAME_PATTERN = re.compile(r"[\w.-]{3,30}")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

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


class UsernameTaken(ValueError):
    """The username is already registered (names are compared ignoring case)."""


def _clean_credentials(username: str, password: str) -> str:
    """Return the trimmed username, or raise ValueError with a message safe to show the user."""
    name = username.strip()
    if not USERNAME_PATTERN.fullmatch(name):
        raise ValueError("Username must be 3-30 letters, digits, '_', '.' or '-'")
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters")
    return name


def register(username: str, password: str) -> int:
    """Create an account and return its id. Raises UsernameTaken or ValueError."""
    name = _clean_credentials(username, password)
    password_hash = hash_password(password)
    try:
        with closing(db.connect()) as conn, conn:
            cursor = conn.execute(
                "INSERT INTO users (username, username_key, password_hash) VALUES (?, ?, ?)",
                (name, name.casefold(), password_hash),
            )
    except sqlite3.IntegrityError as error:  # the UNIQUE username_key was violated
        raise UsernameTaken(f"Username '{name}' is already taken") from error
    return cursor.lastrowid


@cache
def _dummy_hash() -> str:
    return hash_password("not a real password")


def authenticate(username: str, password: str) -> dict | None:
    """Return {"id", "username"} for correct credentials, otherwise None."""
    with closing(db.connect()) as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username_key = ?",
            (username.strip().casefold(),),
        ).fetchone()
    # An unknown user is checked against a dummy hash, so both failures take the same time.
    password_ok = verify_password(password, row["password_hash"] if row else _dummy_hash())
    if row is None or not password_ok:
        return None
    return {"id": row["id"], "username": row["username"]}
