from typing import Any

from app import data


def get_country_feature(iso3: str) -> dict[str, Any] | None:
    """Return a GeoJSON Feature for the given iso3 code, or None if missing."""
    if not iso3:
        return None

    target = iso3.strip().upper()
    geojson = data.shapes()
    for feature in geojson.get("features", []):
        props = feature.get("properties") or {}
        code = props.get("iso3") or feature.get("iso3")
        if isinstance(code, str) and code.upper() == target:
            return feature
    return None


def _extract_points(geometry: dict[str, Any]) -> list[tuple[float, float]]:
    """Extract (lat, lon) pairs from Polygon or MultiPolygon GeoJSON geometry."""
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates") or []
    points: list[tuple[float, float]] = []

    if geom_type == "Polygon":
        for ring in coords:
            for lon, lat in ring:
                points.append((float(lat), float(lon)))
    elif geom_type == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                for lon, lat in ring:
                    points.append((float(lat), float(lon)))
    return points


def get_feature_bounds(
    feature: dict[str, Any] | None,
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Return ((min_lat, min_lon), (max_lat, max_lon)), handling antimeridian crossings."""
    if not feature:
        return None

    geometry = feature.get("geometry") or {}
    points = _extract_points(geometry)
    if not points:
        return None

    lats = [p[0] for p in points]
    lons = [p[1] for p in points]

    # Shift negative longitudes by +360 if the country spans across the 180° meridian
    if max(lons) - min(lons) > 180.0:
        lons = [lon + 360.0 if lon < 0 else lon for lon in lons]

    return (min(lats), min(lons)), (max(lats), max(lons))


def get_feature_center(feature: dict[str, Any] | None) -> tuple[float, float] | None:
    """Return normalized (center_lat, center_lon) based on the feature's bounding box."""
    bounds = get_feature_bounds(feature)
    if not bounds:
        return None

    (min_lat, min_lon), (max_lat, max_lon) = bounds
    center_lon = (min_lon + max_lon) / 2.0
    if center_lon > 180.0:
        center_lon -= 360.0
    return (min_lat + max_lat) / 2.0, center_lon
