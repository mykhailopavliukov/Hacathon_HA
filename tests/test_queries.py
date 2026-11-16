from app import queries


def test_get_country_returns_row_or_none():
    assert queries.get_country("UKR")["name_en"] == "Ukraine"
    assert queries.get_country("???") is None


def test_get_value_returns_number():
    assert queries.get_value("UKR", "population") > 0


def test_get_rank_counts_from_top_and_bottom(monkeypatch):
    stats = {"AAA": {"x": 30.0}, "BBB": {"x": 20.0}, "CCC": {"x": 10.0}, "DDD": {}}
    monkeypatch.setattr(queries.data, "stats", lambda: stats)
    assert queries.get_rank("AAA", "x") == 1
    assert queries.get_rank("CCC", "x") == 3
    assert queries.get_rank("CCC", "x", from_bottom=True) == 1
    assert queries.get_rank("DDD", "x") is None


def test_get_rank_gives_equal_values_the_same_place(monkeypatch):
    stats = {"AAA": {"x": 5.0}, "BBB": {"x": 5.0}, "CCC": {"x": 1.0}}
    monkeypatch.setattr(queries.data, "stats", lambda: stats)
    assert queries.get_rank("AAA", "x") == queries.get_rank("BBB", "x") == 1
    assert queries.get_rank("CCC", "x") == 3


def test_is_unique_value(monkeypatch):
    stats = {"AAA": {"x": 5.0}, "BBB": {"x": 5.0}, "CCC": {"x": 1.0}, "DDD": {}}
    monkeypatch.setattr(queries.data, "stats", lambda: stats)
    assert queries.is_unique_value("CCC", "x")
    assert not queries.is_unique_value("AAA", "x")
    assert not queries.is_unique_value("DDD", "x")


def test_real_data_ranks_are_in_range():
    assert 1 <= queries.get_rank("UKR", "population") <= 195


def test_get_value_is_none_when_no_data():
    assert queries.get_value("???", "population") is None
    assert queries.get_value("UKR", "no_such_indicator") is None
