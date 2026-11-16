import pytest

from app.round import Round, normalize


def make_round() -> Round:
    return Round(
        hints=["h1", "h2", "h3", "h4", "h5"],
        accepted_names=["Ukraine", "Україна"],
    )


def test_normalize_ignores_case_spaces_and_punctuation() -> None:
    assert normalize("  УКРАЇНА! ") == normalize("україна")
    assert normalize("Côte  d'Ivoire") == "cote d ivoire"


def test_starts_with_one_hint_and_max_points() -> None:
    rnd = make_round()
    assert rnd.visible_hints == ["h1"]
    assert rnd.points_available == 100


def test_points_drop_with_each_hint() -> None:
    rnd = make_round()
    seen = [rnd.points_available]
    while rnd.reveal_next():
        seen.append(rnd.points_available)
    assert seen == [100, 80, 60, 40, 20]


def test_cannot_reveal_past_last_hint() -> None:
    rnd = make_round()
    for _ in range(10):
        rnd.reveal_next()
    assert rnd.shown == 5
    assert rnd.reveal_next() is False


def test_correct_guess_scores_current_points() -> None:
    rnd = make_round()
    rnd.reveal_next()
    assert rnd.guess("ukraine") is True
    assert rnd.solved
    assert rnd.score == 80


def test_wrong_guess_costs_penalty() -> None:
    rnd = make_round()
    assert rnd.guess("France") is False
    assert rnd.guess("україна") is True
    assert rnd.score == 90


def test_win_never_below_minimum() -> None:
    rnd = make_round()
    for _ in range(4):
        rnd.reveal_next()
    for _ in range(5):
        rnd.guess("wrong")
    rnd.guess("Ukraine")
    assert rnd.score == 10


def test_empty_guess_is_not_a_mistake() -> None:
    rnd = make_round()
    assert rnd.guess("   ") is False
    assert rnd.wrong_guesses == 0


def test_no_changes_after_round_is_over() -> None:
    rnd = make_round()
    rnd.give_up()
    assert rnd.guess("Ukraine") is False
    assert rnd.reveal_next() is False
    assert rnd.score == 0


def test_give_up_does_not_undo_a_win() -> None:
    rnd = make_round()
    rnd.guess("Ukraine")
    rnd.give_up()
    assert rnd.solved and not rnd.gave_up


def test_invalid_round_raises() -> None:
    with pytest.raises(ValueError):
        Round(hints=[], accepted_names=["Ukraine"])
    with pytest.raises(ValueError):
        Round(hints=["h1"], accepted_names=["  "])
