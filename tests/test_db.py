from contextlib import closing

import pytest

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


def test_top_scores_orders_by_points_then_by_age(scores_db):
    db.add_score("ann", 50)
    db.add_score("bob", 90)
    db.add_score("cat", 50)
    assert [(s["player"], s["points"]) for s in db.top_scores()] == [
        ("bob", 90),
        ("ann", 50),
        ("cat", 50),
    ]


def test_top_scores_respects_limit_and_empty_database(scores_db):
    assert db.top_scores() == []
    for i in range(5):
        db.add_score(f"p{i}", i)
    assert [s["points"] for s in db.top_scores(limit=2)] == [4, 3]


def test_add_score_trims_the_name(scores_db):
    db.add_score("  ann  ", 10)
    assert db.top_scores()[0]["player"] == "ann"


@pytest.mark.parametrize(("name", "points"), [("", 5), ("   ", 5), ("x" * 31, 5), ("ann", -1)])
def test_add_score_rejects_bad_input(scores_db, name, points):
    with pytest.raises(ValueError):
        db.add_score(name, points)
    assert db.top_scores() == []


def test_sql_injection_text_is_stored_as_plain_text(scores_db):
    db.add_score("x'); DROP TABLE scores;--", 1)
    assert db.top_scores()[0]["player"] == "x'); DROP TABLE scores;--"


def test_connect_twice_keeps_existing_table(scores_db):
    with closing(db.connect()) as conn, conn:
        conn.execute("INSERT INTO scores (player, points) VALUES ('a', 5)")
    with closing(db.connect()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0] == 1
