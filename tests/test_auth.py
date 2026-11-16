from app import auth


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
