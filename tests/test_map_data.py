from app import map_data


def test_get_country_feature_valid_and_case_insensitive() -> None:
    ukr = map_data.get_country_feature("UKR")
    assert ukr is not None
    assert map_data.get_country_feature("ukr") == ukr


def test_get_country_feature_kosovo() -> None:
    # Kosovo uses XKX per dataset rules
    xkx = map_data.get_country_feature("XKX")
    assert xkx is not None


def test_get_country_feature_missing_or_empty() -> None:
    assert map_data.get_country_feature("") is None
    assert map_data.get_country_feature("ZZZ") is None


def test_feature_bounds_and_center_polygon() -> None:
    # GeoJSON uses [lon, lat], output must be (lat, lon)
    fake_feature = {
        "type": "Feature",
        "properties": {"iso3": "TST"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[10.0, 20.0], [30.0, 20.0], [30.0, 40.0], [10.0, 40.0], [10.0, 20.0]]],
        },
    }
    bounds = map_data.get_feature_bounds(fake_feature)
    assert bounds == ((20.0, 10.0), (40.0, 30.0))
    assert map_data.get_feature_center(fake_feature) == (30.0, 20.0)


def test_feature_center_multipolygon_and_empty() -> None:
    multi_feature = {
        "type": "Feature",
        "properties": {"iso3": "MLT"},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 0.0]]],
                [[[8.0, 8.0], [10.0, 8.0], [10.0, 10.0], [8.0, 8.0]]],
            ],
        },
    }
    assert map_data.get_feature_center(multi_feature) == (5.0, 5.0)
    assert map_data.get_feature_center(None) is None
    assert map_data.get_feature_bounds({"geometry": {"type": "Polygon", "coordinates": []}}) is None


def test_feature_bounds_and_center_antimeridian() -> None:
    # Fiji-like geometry crossing the 180° meridian (+178 to -178)
    fiji_like = {
        "type": "Feature",
        "properties": {"iso3": "FJI"},
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[178.0, -18.0], [179.0, -18.0], [179.0, -16.0], [178.0, -18.0]]],
                [[[-179.0, -18.0], [-178.0, -18.0], [-178.0, -16.0], [-179.0, -18.0]]],
            ],
        },
    }
    bounds = map_data.get_feature_bounds(fiji_like)
    assert bounds == ((-18.0, 178.0), (-16.0, 182.0))
    assert map_data.get_feature_center(fiji_like) == (-17.0, 180.0)
