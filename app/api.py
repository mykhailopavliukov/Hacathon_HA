"""JSON API over the data layer. Mounted in `app.main`."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app import account_api, data, db, hints, queries

router = APIRouter(prefix="/api")
router.include_router(account_api.router)

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


class ScoreIn(BaseModel):
    player: str = Field(min_length=1, max_length=db.MAX_NAME_LENGTH)
    points: int = Field(ge=0)


@router.post("/scores", status_code=201)
def create_score(score: ScoreIn) -> dict[str, str]:
    try:
        db.add_score(score.player, score.points)
    except ValueError as error:  # e.g. a name made only of spaces
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"status": "saved"}


@router.get("/leaderboard")
def read_leaderboard(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
    return db.top_scores(limit)
