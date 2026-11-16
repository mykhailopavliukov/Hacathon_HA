import pytest

from app import auth


@pytest.fixture
def scores_db(tmp_path, monkeypatch):
    """Point the database at a throwaway file."""
    path = tmp_path / "scores.db"
    monkeypatch.setenv("SCORES_DB", str(path))
    return path


@pytest.fixture(autouse=True)
def _clean_login_state():
    """Failed-login counters live in memory; keep tests independent."""
    auth._failed_logins.clear()
    yield
    auth._failed_logins.clear()


@pytest.fixture(autouse=True)
def _cheap_scrypt(monkeypatch):
    """Real scrypt costs 16 MB and tens of ms per hash; tests only need it to be consistent."""
    monkeypatch.setattr(auth, "_N", 2**4)
