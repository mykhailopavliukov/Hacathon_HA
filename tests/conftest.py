import pytest


@pytest.fixture
def scores_db(tmp_path, monkeypatch):
    """Point the leaderboard at a throwaway database file."""
    path = tmp_path / "scores.db"
    monkeypatch.setenv("SCORES_DB", str(path))
    return path
