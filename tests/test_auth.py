import time
from contextlib import closing

import pytest

from app import auth, db


def test_hash_is_salted_and_hides_the_password():
    first = auth.hash_password("correct horse")
    second = auth.hash_password("correct horse")
    assert first != second
    assert "correct horse" not in first
    assert first.startswith("scrypt$")


def test_verify_password_accepts_only_the_right_password():
    stored = auth.hash_password("correct horse")
    assert auth.verify_password("correct horse", stored)
    assert not auth.verify_password("correct horsE", stored)
    assert not auth.verify_password("", stored)


def test_verify_password_rejects_malformed_hashes():
    for stored in ("", "plain", "scrypt$zz$zz", "a$b", "scrypt$00$00$00"):
        assert not auth.verify_password("x", stored)


# --- sign-up and login -------------------------------------------------------


def test_register_returns_id_and_stores_only_a_hash(scores_db):
    user_id = auth.register("Hlib", "correct horse")
    with closing(db.connect()) as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    assert row["username"] == "Hlib"
    assert "correct horse" not in row["password_hash"]


@pytest.mark.parametrize("second", ["hlib", "HLIB", " Hlib "])
def test_register_rejects_a_taken_name_ignoring_case(scores_db, second):
    auth.register("Hlib", "correct horse")
    with pytest.raises(auth.UsernameTaken):
        auth.register(second, "another password")


def test_register_treats_cyrillic_names_case_insensitively(scores_db):
    auth.register("Гліб", "correct horse")
    with pytest.raises(auth.UsernameTaken):
        auth.register("гліб", "correct horse")


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("ab", "correct horse"),
        ("a" * 31, "correct horse"),
        ("bad name", "correct horse"),
        ("bad;name", "correct horse"),
        ("   ", "correct horse"),
        ("hlib", "short"),
        ("hlib", "x" * 129),
    ],
)
def test_register_rejects_invalid_input(scores_db, username, password):
    with pytest.raises(ValueError):
        auth.register(username, password)
    assert not auth.authenticate(username, password)


def test_authenticate_returns_the_user_for_correct_credentials(scores_db):
    user_id = auth.register("Hlib", "correct horse")
    assert auth.authenticate("Hlib", "correct horse") == {"id": user_id, "username": "Hlib"}
    assert auth.authenticate(" hlib ", "correct horse")["id"] == user_id


def test_authenticate_fails_for_wrong_password_and_unknown_user(scores_db):
    auth.register("Hlib", "correct horse")
    assert auth.authenticate("Hlib", "wrong password") is None
    assert auth.authenticate("nobody", "correct horse") is None


def test_sql_injection_in_login_is_just_a_wrong_name(scores_db):
    auth.register("Hlib", "correct horse")
    assert auth.authenticate("' OR '1'='1", "x") is None


# --- sessions ----------------------------------------------------------------


def test_session_token_identifies_the_user(scores_db):
    user_id = auth.register("Hlib", "correct horse")
    token = auth.create_session(user_id)
    assert auth.get_session_user(token) == {"id": user_id, "username": "Hlib"}


def test_unknown_or_empty_token_is_rejected(scores_db):
    auth.register("Hlib", "correct horse")
    assert auth.get_session_user("not-a-token") is None
    assert auth.get_session_user("") is None


def test_database_stores_only_a_hash_of_the_token(scores_db):
    token = auth.create_session(auth.register("Hlib", "correct horse"))
    with closing(db.connect()) as conn:
        stored = [row["token_hash"] for row in conn.execute("SELECT token_hash FROM sessions")]
    assert stored and token not in stored


def test_session_expires(scores_db, monkeypatch):
    token = auth.create_session(auth.register("Hlib", "correct horse"))
    now = time.time()
    monkeypatch.setattr(auth.time, "time", lambda: now + auth.SESSION_SECONDS - 5)
    assert auth.get_session_user(token) is not None
    monkeypatch.setattr(auth.time, "time", lambda: now + auth.SESSION_SECONDS + 5)
    assert auth.get_session_user(token) is None


def test_delete_session_logs_out_only_that_session(scores_db):
    user_id = auth.register("Hlib", "correct horse")
    first, second = auth.create_session(user_id), auth.create_session(user_id)
    auth.delete_session(first)
    assert auth.get_session_user(first) is None
    assert auth.get_session_user(second) is not None


def test_creating_a_session_removes_expired_ones(scores_db, monkeypatch):
    user_id = auth.register("Hlib", "correct horse")
    auth.create_session(user_id)
    now = time.time()
    monkeypatch.setattr(auth.time, "time", lambda: now + auth.SESSION_SECONDS + 5)
    auth.create_session(user_id)
    with closing(db.connect()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
