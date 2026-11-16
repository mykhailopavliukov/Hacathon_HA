from app import data


def test_countries_keyed_by_iso3():
    countries = data.countries()
    assert len(countries) == 197
    assert countries["UKR"]["name_en"] == "Ukraine"


def test_stats_cover_known_countries_and_skip_empty_cells():
    stats = data.stats()
    assert set(stats) <= set(data.countries())
    assert "population" in stats["UKR"]
    assert all(isinstance(v, float) for v in stats["UKR"].values())


def test_stats_columns_have_indicator_metadata_except_known_gap():
    columns = {col for row in data.stats().values() for col in row}
    # "vanilla" is in stats.csv but missing from indicators.csv (source data is read-only).
    assert columns - set(data.indicators()) == {"vanilla"}


def test_shapes_have_iso3():
    features = data.shapes()["features"]
    assert features
    assert all("iso3" in f["properties"] for f in features)
