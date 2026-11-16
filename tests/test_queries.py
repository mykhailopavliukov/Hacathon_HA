from app import queries


def test_get_country_returns_row_or_none():
    assert queries.get_country("UKR")["name_en"] == "Ukraine"
    assert queries.get_country("???") is None


def test_get_value_returns_number():
    assert queries.get_value("UKR", "population") > 0


def test_accepted_names_has_both_languages():
    assert queries.accepted_names("UKR") == ["Україна", "Ukraine"]
    assert queries.accepted_names("???") == []


def test_search_finds_by_ukrainian_and_english_prefix():
    assert queries.search_countries("укр")[0]["iso3"] == "UKR"
    assert "UKR" in [c["iso3"] for c in queries.search_countries("Ukra")]


def test_search_puts_prefix_matches_before_contains_matches():
    iso3s = [c["iso3"] for c in queries.search_countries("guinea")]
    assert iso3s.index("GIN") < iso3s.index("GNQ")  # Guinea before Equatorial Guinea


def test_search_ignores_case_and_extra_spaces():
    assert queries.search_countries("  ПОЛЬ ")[0]["iso3"] == "POL"


def test_search_respects_limit_and_empty_query():
    assert len(queries.search_countries("а", limit=3)) == 3
    assert queries.search_countries("") == []
    assert queries.search_countries("   ") == []
    assert queries.search_countries("zzzzzz") == []


def test_get_value_is_none_when_no_data():
    assert queries.get_value("???", "population") is None
    assert queries.get_value("UKR", "no_such_indicator") is None
