"""Load the read-only datasets from `data/` once and keep them in memory."""

import csv
import json
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _read_csv(name: str) -> list[dict[str, str]]:
    with (DATA_DIR / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@cache
def countries() -> dict[str, dict[str, str]]:
    """Countries keyed by iso3."""
    return {row["iso3"]: row for row in _read_csv("countries.csv")}


@cache
def indicators() -> dict[str, dict[str, str]]:
    """Indicator metadata keyed by indicator id."""
    return {row["id"]: row for row in _read_csv("indicators.csv")}


@cache
def stats() -> dict[str, dict[str, float]]:
    """Indicator values keyed by iso3, then indicator id. Empty cells are omitted."""
    result: dict[str, dict[str, float]] = {}
    for row in _read_csv("stats.csv"):
        iso3 = row.pop("iso3")
        result[iso3] = {k: float(v) for k, v in row.items() if v != ""}
    return result


@cache
def shapes() -> dict:
    """Country outlines as a GeoJSON FeatureCollection (feature property: iso3)."""
    with (DATA_DIR / "shapes.geojson").open(encoding="utf-8") as f:
        return json.load(f)
