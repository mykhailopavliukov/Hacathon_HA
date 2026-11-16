from app import data
from app.facts import Hint, _place, get_hints, playable_countries


def test_known_records():
    texts = {c: " ".join(h.text for h in get_hints(c)) for c in ("BRA", "CIV", "UKR")}
    assert "1-ше місце у світі за виробництвом кави" in texts["BRA"]
    assert "1-ше місце у світі за виробництвом какао" in texts["CIV"]
    assert "2-ге місце у світі за виробництвом соняшнику" in texts["UKR"]


def test_every_playable_country_has_full_ladder():
    for iso3 in playable_countries():
        hints = get_hints(iso3)
        assert len(hints) >= 8, iso3
        assert all(isinstance(h, Hint) and h.text for h in hints)
        assert hints[-1].text.startswith("Столиця"), iso3
        assert sum(h.kind == "map" for h in hints) == 1


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
