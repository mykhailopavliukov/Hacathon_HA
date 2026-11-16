"""Compare a wrong guess with the secret country, Spotle-style: match, higher or lower."""

from dataclasses import dataclass

from app import data
from app.hints import _humanize


@dataclass(frozen=True)
class Tile:
    label: str
    value: str
    status: str  # "match", "up" (the answer is bigger), "down" (smaller) or "miss"


def compare(guess: str, target: str) -> list[Tile]:
    """Tiles describing the guessed country, coloured by how close it is to the target."""
    countries = data.countries()
    g, t = countries[guess], countries[target]
    return [
        Tile("Регіон", g["region_uk"] or "—", _same(g["region_uk"], t["region_uk"])),
        Tile("Субрегіон", g["subregion_uk"] or "—", _same(g["subregion_uk"], t["subregion_uk"])),
        _number_tile("Населення", _population(guess), _population(target), " осіб"),
        _number_tile("Площа", _area(guess), _area(target), " км²"),
        Tile(
            "Сусід",
            "Так" if guess in t["borders"].split(";") else "Ні",
            "match" if guess in t["borders"].split(";") else "miss",
        ),
    ]


def _same(a: str, b: str) -> str:
    return "match" if a and a == b else "miss"


def _number_tile(label: str, guess: float | None, target: float | None, unit: str) -> Tile:
    if guess is None:
        return Tile(label, "—", "miss")
    value = f"{_humanize(guess)}{unit}"
    if target is None:
        return Tile(label, value, "miss")
    # within 10% counts as a hit: exact equality would almost never happen
    if abs(guess - target) <= 0.1 * target:
        return Tile(label, value, "match")
    return Tile(label, value, "up" if target > guess else "down")


def _population(iso3: str) -> float | None:
    return data.stats().get(iso3, {}).get("population")


def _area(iso3: str) -> float | None:
    area = data.countries()[iso3]["area_km2"]
    return float(area) if area else None
