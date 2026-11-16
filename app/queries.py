"""Read-only lookups over the datasets loaded in `app.data`."""

from functools import cache

from app import data
from app.round import normalize

SEARCH_LIMIT = 10


def get_country(iso3: str) -> dict[str, str] | None:
    return data.countries().get(iso3)


def get_value(iso3: str, indicator: str) -> float | None:
    """None means no data (unknown country, unknown indicator or empty cell)."""
    return data.stats().get(iso3, {}).get(indicator)


def accepted_names(iso3: str) -> list[str]:
    """Names a player may type to name this country (empty for an unknown code)."""
    country = get_country(iso3)
    return [] if country is None else [country["name_uk"], country["name_en"]]


@cache
def _search_index() -> list[tuple[str, tuple[str, str]]]:
    """(iso3, normalized Ukrainian and English names) for every country, built once."""
    return [
        (iso3, (normalize(row["name_uk"]), normalize(row["name_en"])))
        for iso3, row in data.countries().items()
    ]


def search_countries(query: str, limit: int = SEARCH_LIMIT) -> list[dict[str, str]]:
    """Countries whose name starts with the query, then those that contain it.

    Uses the same `normalize` as answer checking, so typing rules are identical.
    """
    text = normalize(query)
    if not text:
        return []
    starts, contains = [], []
    for iso3, names in _search_index():
        if any(name.startswith(text) for name in names):
            starts.append(iso3)
        elif any(text in name for name in names):
            contains.append(iso3)
    return [data.countries()[iso3] for iso3 in (starts + contains)[:limit]]
