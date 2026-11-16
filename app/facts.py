"""Record facts about a country, built from the phrase templates in indicators.csv."""

from app import data, queries

# (counting from the bottom?, flag column, template column) for the two kinds of records
_RECORD_KINDS = (
    (False, "use_top", "template_top"),
    (True, "use_bottom", "template_bottom"),
)


def record_facts(iso3: str, max_rank: int = 10) -> list[dict]:
    """Facts where the country is within `max_rank` places from the top or the bottom.

    Each fact is {"indicator", "from_bottom", "rank", "text"}. Sorted by rank, most striking first.
    Shared places are skipped, because "1st place" would be untrue when several countries tie.
    """
    facts = []
    for indicator, meta in data.indicators().items():
        for from_bottom, flag, template in _RECORD_KINDS:
            if meta[flag] != "1":
                continue
            rank = queries.get_rank(iso3, indicator, from_bottom)
            if rank is None or rank > max_rank or not queries.is_unique_value(iso3, indicator):
                continue
            facts.append(
                {
                    "indicator": indicator,
                    "from_bottom": from_bottom,
                    "rank": rank,
                    "text": meta[template].format(rank=rank),
                }
            )
    return sorted(facts, key=lambda fact: fact["rank"])
