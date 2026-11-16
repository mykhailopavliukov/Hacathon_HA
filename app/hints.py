"""Build the ordered list of hints for a country, from vague to precise."""

from dataclasses import dataclass
from functools import cache

from app import data

MIN_POPULATION_FOR_ANTIRECORD = 1_000_000  # otherwise microstates "win" every bottom list
TOP_N_STEPS = (10, 20, 30)  # widen the top-N until the country has a record
TINY_COUNTRY_KM2 = 10_000  # outline is useless below this, show a point instead


@dataclass(frozen=True)
class Hint:
    kind: str  # "text" or "map"
    text: str


def get_hints(iso3: str) -> list[Hint]:
    """All hints for one country in the order they should be revealed."""
    country = data.countries()[iso3]
    hints = [
        *_size_hints(iso3),
        *_wealth_hints(iso3),
        _best_fact_hint(iso3),
        _region_hint(country),
        _neighbors_hint(country),
        _languages_currency_hint(country),
        _map_hint(country),
        _capital_hint(country),
    ]
    name = country["name_uk"]
    return [Hint(h.kind, h.text.replace(name, "***")) for h in hints if h is not None]


def playable_countries() -> list[str]:
    """Countries that can be the secret answer (they need World Bank data)."""
    return [iso3 for iso3 in data.countries() if "population" in data.stats().get(iso3, {})]


# ---------- rankings ----------


@cache
def _ranking(indicator_id: str, descending: bool) -> dict[str, int]:
    """Rank (1 = first) of every country that has a value for the indicator."""
    stats = data.stats()
    values = {iso3: row[indicator_id] for iso3, row in stats.items() if indicator_id in row}
    if not descending:  # bottom list: only countries big enough to be meaningful
        values = {
            iso3: v
            for iso3, v in values.items()
            if stats[iso3].get("population", 0) >= MIN_POPULATION_FOR_ANTIRECORD
        }
    ordered = sorted(values, key=values.get, reverse=descending)
    return {iso3: place for place, iso3 in enumerate(ordered, start=1)}


@cache
def _lead_over_runner_up(indicator_id: str) -> float:
    """How far the world leader is ahead of the runner-up (1.0 = no lead at all)."""
    values = sorted(
        (row[indicator_id] for row in data.stats().values() if indicator_id in row),
        reverse=True,
    )
    if len(values) < 2 or values[1] <= 0:
        return 1.0
    return values[0] / values[1]


# ---------- hint builders ----------


def _size_hints(iso3: str) -> list[Hint]:
    hints = []
    population = data.stats()[iso3].get("population")
    if population is not None:
        hints.append(Hint("text", f"Населення: {_humanize(population)} осіб"))
    area = data.countries()[iso3]["area_km2"]
    if area:
        hints.append(Hint("text", f"Площа: {_humanize(float(area))} км²"))
    return hints


def _wealth_hints(iso3: str) -> list[Hint]:
    row = data.stats()[iso3]
    hints = []
    if "gdp_pc" in row:
        hints.append(Hint("text", f"ВВП на душу: ${_humanize(row['gdp_pc'])}"))
    if "life_exp" in row:
        hints.append(Hint("text", f"Тривалість життя: {_humanize(row['life_exp'], 1)} років"))
    return hints


def _best_fact_hint(iso3: str) -> Hint | None:
    """The single most striking record: lowest place, then biggest lead over the runner-up."""
    for top_n in TOP_N_STEPS:
        facts = _find_facts(iso3, top_n)
        if facts:
            return Hint("text", min(facts)[2])
    return None


def _find_facts(iso3: str, top_n: int) -> list[tuple[int, float, str]]:
    facts = []
    for ind_id, ind in data.indicators().items():
        if ind["role"] != "fact":
            continue
        value = data.stats()[iso3].get(ind_id)
        if value is None:
            continue
        for descending, flag, template in (
            (True, ind["use_top"], ind["template_top"]),
            (False, ind["use_bottom"], ind["template_bottom"]),
        ):
            if flag != "1" or not template:
                continue
            place = _ranking(ind_id, descending).get(iso3)
            if place is not None and place <= top_n:
                text = template.replace("{rank}", _place(place))
                amount = _humanize(value, int(ind["decimals"]))
                lead = _lead_over_runner_up(ind_id) if place == 1 and descending else 1.0
                phrase = f"{text[0].upper()}{text[1:]} ({amount} {ind['unit_uk']})"
                facts.append((place, -lead, phrase))
    return facts


def _region_hint(country: dict[str, str]) -> Hint | None:
    if not country["region_uk"]:
        return None
    subregion = country["subregion_uk"]
    # "Австралія і Нова Зеландія" would give the answer away
    sub = f", {subregion}" if subregion and country["name_uk"] not in subregion else ""
    return Hint("text", f"Регіон: {country['region_uk']}{sub}")


def _neighbors_hint(country: dict[str, str]) -> Hint:
    count = int(country["neighbors_count"] or 0)
    if count == 0:
        text = "Не має сухопутних сусідів"
    else:
        text = f"Має {count} {_plural(count, 'сусіда', 'сусіди', 'сусідів')} на суходолі"
    if country["landlocked"] == "1":
        text += ", виходу до моря немає"
    return Hint("text", text)


def _languages_currency_hint(country: dict[str, str]) -> Hint | None:
    parts = []
    if country["languages_uk"]:
        parts.append(f"Мови: {country['languages_uk'].replace(';', ',')}")
    if country["currencies_uk"]:
        parts.append(f"валюта: {country['currencies_uk'].replace(';', ',')}")
    return Hint("text", "; ".join(parts)) if parts else None


def _map_hint(country: dict[str, str]) -> Hint:
    tiny = not country["area_km2"] or float(country["area_km2"]) < TINY_COUNTRY_KM2
    if tiny or country["has_shape"] != "1":
        return Hint("map", "Розташування на карті світу")
    return Hint("map", "Контур країни")


def _capital_hint(country: dict[str, str]) -> Hint | None:
    capital = country["capital_uk"]
    return Hint("text", f"Столиця починається на «{capital[0]}»") if capital else None


# ---------- Ukrainian formatting ----------


def _place(n: int) -> str:
    """Ukrainian ordinal: 1-ше, 2-ге, 3-тє, 7-ме, 40-ве, 11-те."""
    if 11 <= n % 100 <= 19:
        return f"{n}-те"
    if n % 100 == 40:
        return f"{n}-ве"
    suffix = {1: "ше", 2: "ге", 3: "тє", 7: "ме", 8: "ме"}.get(n % 10, "те")
    return f"{n}-{suffix}"


def _humanize(value: float, decimals: int = 0) -> str:
    """38 500 000 -> '38,5 млн'; small numbers keep the given decimals."""
    for size, word in ((1e9, "млрд"), (1e6, "млн")):
        if abs(value) >= size:
            return f"{value / size:.1f} {word}".replace(".", ",")
    text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return text


def _plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many
