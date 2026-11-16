from app import data
from app.hints import Hint, _place, get_hints, playable_countries


def test_single_top_record():
    for iso3 in ("BRA", "CIV", "CHN", "UKR"):
        records = [h.text for h in get_hints(iso3) if "місце" in h.text]
        assert len(records) == 1, iso3
        assert records[0].startswith("1-ше"), iso3


def test_base_hints_carry_no_rank():
    population, area, gdp, life = get_hints("BRA")[:4]
    for hint in (population, area, gdp, life):
        assert "місце" not in hint.text


def test_every_playable_country_has_full_ladder():
    for iso3 in playable_countries():
        hints = get_hints(iso3)
        assert len(hints) >= 7, iso3
        assert all(isinstance(h, Hint) and h.text for h in hints)
        assert hints[-1].text.startswith("Столиця"), iso3
        assert sum(h.kind == "map" for h in hints) == 1
        assert sum("місце" in h.text for h in hints) <= 1, iso3


def test_hints_do_not_name_the_country():
    for iso3 in playable_countries():
        name = data.countries()[iso3]["name_uk"]
        assert all(name not in h.text for h in get_hints(iso3)), iso3


def test_countries_without_world_bank_data_are_not_playable():
    assert "VAT" not in playable_countries()
    assert "TWN" not in playable_countries()


def test_ukrainian_ordinals():
    assert [_place(n) for n in (1, 2, 3, 7, 11, 21, 40, 113)] == [
        "1-ше",
        "2-ге",
        "3-тє",
        "7-ме",
        "11-те",
        "21-ше",
        "40-ве",
        "113-те",
    ]
