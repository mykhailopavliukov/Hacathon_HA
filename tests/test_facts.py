from app import facts


def test_record_facts_for_a_real_country_are_well_formed():
    result = facts.record_facts("CHN")
    assert result
    assert all(f["rank"] <= 10 for f in result)
    assert [f["rank"] for f in result] == sorted(f["rank"] for f in result)
    assert all(f["text"].startswith(f"{f['rank']} ") for f in result)


def test_record_facts_respects_max_rank():
    assert all(f["rank"] == 1 for f in facts.record_facts("CHN", max_rank=1))


def test_record_facts_is_empty_for_unknown_country():
    assert facts.record_facts("???") == []


def test_record_facts_uses_top_and_bottom_templates(monkeypatch):
    indicators = {
        "x": {
            "use_top": "1",
            "use_bottom": "1",
            "template_top": "{rank} top",
            "template_bottom": "{rank} bottom",
        }
    }
    stats = {"AAA": {"x": 3.0}, "BBB": {"x": 2.0}, "CCC": {"x": 1.0}}
    monkeypatch.setattr(facts.data, "indicators", lambda: indicators)
    monkeypatch.setattr(facts.queries.data, "stats", lambda: stats)
    assert [f["text"] for f in facts.record_facts("AAA", max_rank=1)] == ["1 top"]
    assert [f["text"] for f in facts.record_facts("CCC", max_rank=1)] == ["1 bottom"]
    assert facts.record_facts("BBB", max_rank=1) == []
