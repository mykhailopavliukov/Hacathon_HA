"""Read-only lookups over the datasets loaded in `app.data`."""

from app import data


def get_country(iso3: str) -> dict[str, str] | None:
    return data.countries().get(iso3)


def get_value(iso3: str, indicator: str) -> float | None:
    """None means no data (unknown country, unknown indicator or empty cell)."""
    return data.stats().get(iso3, {}).get(indicator)


def get_rank(iso3: str, indicator: str, from_bottom: bool = False) -> int | None:
    """Place of the country among countries that have data (1 = highest, or lowest if from_bottom).

    Countries with equal values share a place. None means the country has no data.
    """
    value = get_value(iso3, indicator)
    if value is None:
        return None
    values = [stat[indicator] for stat in data.stats().values() if indicator in stat]
    better = sum(v < value if from_bottom else v > value for v in values)
    return better + 1


def is_unique_value(iso3: str, indicator: str) -> bool:
    """True if no other country has exactly the same value, so its place is not shared."""
    value = get_value(iso3, indicator)
    values = [stat[indicator] for stat in data.stats().values() if indicator in stat]
    return value is not None and values.count(value) == 1
