from app.compare import compare


def _by_label(guess: str, target: str) -> dict:
    return {tile.label: tile for tile in compare(guess, target)}


def test_neighbour_in_same_subregion_is_green():
    tiles = _by_label("BLR", "UKR")
    assert tiles["Регіон"].status == "match"
    assert tiles["Субрегіон"].status == "match"
    assert tiles["Сусід"].status == "match"


def test_arrows_point_towards_the_answer():
    tiles = _by_label("MCO", "UKR")
    assert tiles["Населення"].status == "up"
    assert tiles["Площа"].status == "up"
    assert _by_label("CHN", "UKR")["Населення"].status == "down"


def test_far_country_misses():
    tiles = _by_label("BRA", "UKR")
    assert tiles["Регіон"].status == "miss"
    assert tiles["Сусід"].value == "Ні"


def test_same_country_matches_everything_but_neighbour():
    tiles = _by_label("UKR", "UKR")
    assert {t.status for label, t in tiles.items() if label != "Сусід"} == {"match"}
