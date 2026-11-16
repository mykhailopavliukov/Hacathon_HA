"""JSON API over the data layer. Mounted in `app.main`."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from app import data, hints, queries

router = APIRouter(prefix="/api")

_SHORT_KEYS = ("iso3", "name_uk", "name_en", "flag")


def _short(row: dict[str, str]) -> dict[str, str]:
    return {key: row[key] for key in _SHORT_KEYS}


def _require_country(iso3: str) -> dict[str, str]:
    country = queries.get_country(iso3.upper())
    if country is None:
        raise HTTPException(status_code=404, detail=f"Unknown country: {iso3}")
    return country


@router.get("/countries")
def list_countries() -> list[dict[str, str]]:
    return [_short(row) for row in data.countries().values()]


# "search" and "playable" are declared before "/countries/{iso3}",
# otherwise they would be read as an iso3 code.
@router.get("/countries/search")
def search_countries(q: str = "") -> list[dict[str, str]]:
    return [_short(row) for row in queries.search_countries(q)]


@router.get("/countries/playable")
def list_playable() -> list[str]:
    return hints.playable_countries()


@router.get("/countries/{iso3}")
def read_country(iso3: str) -> dict[str, str]:
    return _require_country(iso3)


@router.get("/countries/{iso3}/hints")
def read_hints(iso3: str) -> list[dict[str, str]]:
    country = _require_country(iso3)
    return [asdict(hint) for hint in hints.get_hints(country["iso3"])]
