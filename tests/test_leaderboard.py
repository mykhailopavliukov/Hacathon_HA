from app import db
from app.leaderboard import top_players


def test_totals_points_per_player(scores_db):
    db.add_score("sam", 80)
    db.add_score("max", 100)
    db.add_score("sam", 50)
    assert top_players() == [
        {"player": "sam", "total": 130, "wins": 2},
        {"player": "max", "total": 100, "wins": 1},
    ]


def test_ties_go_to_the_earlier_player_and_limit_applies(scores_db):
    db.add_score("first", 40)
    db.add_score("second", 40)
    db.add_score("third", 10)
    assert [row["player"] for row in top_players(limit=2)] == ["first", "second"]


def test_empty_board(scores_db):
    assert top_players() == []
