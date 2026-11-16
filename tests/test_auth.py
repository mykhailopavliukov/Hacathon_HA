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
