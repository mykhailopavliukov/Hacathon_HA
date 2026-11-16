"""Read-only lookups over the datasets loaded in `app.data`."""

from app import data


def get_country(iso3: str) -> dict[str, str] | None:
    return data.countries().get(iso3)


def get_value(iso3: str, indicator: str) -> float | None:
    """None means no data (unknown country, unknown indicator or empty cell)."""
    return data.stats().get(iso3, {}).get(indicator)
