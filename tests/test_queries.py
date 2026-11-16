from app import queries


def test_get_country_returns_row_or_none():
    assert queries.get_country("UKR")["name_en"] == "Ukraine"
    assert queries.get_country("???") is None


def test_get_value_returns_number():
    assert queries.get_value("UKR", "population") > 0


def test_accepted_names_has_both_languages():
    assert queries.accepted_names("UKR") == ["Україна", "Ukraine"]
    assert queries.accepted_names("???") == []


def test_get_value_is_none_when_no_data():
    assert queries.get_value("???", "population") is None
    assert queries.get_value("UKR", "no_such_indicator") is None
