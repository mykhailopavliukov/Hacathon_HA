"""JSON API over the data layer. Mounted in `app.main`."""

from fastapi import APIRouter, HTTPException

from app import data, queries

router = APIRouter(prefix="/api")


def _require_country(iso3: str) -> dict[str, str]:
    country = queries.get_country(iso3.upper())
    if country is None:
        raise HTTPException(status_code=404, detail=f"Unknown country: {iso3}")
    return country


@router.get("/countries")
def list_countries() -> list[dict[str, str]]:
    keys = ("iso3", "name_uk", "name_en", "flag")
    return [{key: row[key] for key in keys} for row in data.countries().values()]


@router.get("/countries/{iso3}")
def read_country(iso3: str) -> dict[str, str]:
    return _require_country(iso3)
