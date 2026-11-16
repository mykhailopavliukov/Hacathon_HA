import pytest

from app import auth, streaks


@pytest.fixture
def user_id(scores_db):
    return auth.register("Hlib", "correct horse")


def test_new_user_has_no_streak(user_id):
    assert streaks.get_streak(user_id) == {"current": 0, "best": 0}


def test_solved_rounds_extend_the_streak(user_id):
    for _ in range(3):
        result = streaks.record_round(user_id, solved=True)
    assert result == {"current": 3, "best": 3}
    assert streaks.get_streak(user_id) == {"current": 3, "best": 3}


def test_a_failed_round_resets_current_but_keeps_best(user_id):
    for _ in range(4):
        streaks.record_round(user_id, solved=True)
    assert streaks.record_round(user_id, solved=False) == {"current": 0, "best": 4}


def test_best_only_grows_when_beaten(user_id):
    for _ in range(3):
        streaks.record_round(user_id, solved=True)
    streaks.record_round(user_id, solved=False)
    for _ in range(2):
        result = streaks.record_round(user_id, solved=True)
    assert result == {"current": 2, "best": 3}
    result = streaks.record_round(user_id, solved=True)
    assert result == {"current": 3, "best": 3}
    result = streaks.record_round(user_id, solved=True)
    assert result == {"current": 4, "best": 4}


def test_failing_first_creates_a_zero_streak(user_id):
    assert streaks.record_round(user_id, solved=False) == {"current": 0, "best": 0}


def test_streaks_are_separate_per_user(user_id):
    other = auth.register("Sam", "another horse")
    streaks.record_round(user_id, solved=True)
    assert streaks.get_streak(other) == {"current": 0, "best": 0}


def test_unknown_user_is_rejected(scores_db):
    with pytest.raises(ValueError):
        streaks.record_round(999, solved=True)


def test_top_streaks_ranks_by_best_and_skips_players_without_wins(user_id):
    sam = auth.register("Sam", "another horse")
    auth.register("Ann", "third horse")  # never played
    for _ in range(2):
        streaks.record_round(user_id, solved=True)
    for _ in range(3):
        streaks.record_round(sam, solved=True)
    streaks.record_round(sam, solved=False)
    assert streaks.top_streaks() == [
        {"username": "Sam", "best": 3, "current": 0},
        {"username": "Hlib", "best": 2, "current": 2},
    ]


def test_top_streaks_respects_limit(user_id):
    sam = auth.register("Sam", "another horse")
    streaks.record_round(user_id, solved=True)
    streaks.record_round(sam, solved=True)
    assert len(streaks.top_streaks(limit=1)) == 1
    assert streaks.top_streaks(limit=1)[0]["username"] == "Hlib"  # tie: registered first
