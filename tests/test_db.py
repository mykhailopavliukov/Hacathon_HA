from contextlib import closing

from app import db


def test_db_path_defaults_and_reads_environment(monkeypatch):
    monkeypatch.delenv("SCORES_DB", raising=False)
    assert db.db_path() == "scores.db"
    monkeypatch.setenv("SCORES_DB", "other.db")
    assert db.db_path() == "other.db"


def test_connect_creates_scores_table(scores_db):
    with closing(db.connect()) as conn:
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(scores)")]
    assert columns == ["id", "player", "points", "created_at"]
    assert scores_db.exists()


def test_connect_twice_keeps_existing_table(scores_db):
    with closing(db.connect()) as conn, conn:
        conn.execute("INSERT INTO scores (player, points) VALUES ('a', 5)")
    with closing(db.connect()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0] == 1
