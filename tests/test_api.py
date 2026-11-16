import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import router


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_list_countries_returns_short_rows(client):
    response = client.get("/api/countries")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 197
    assert set(rows[0]) == {"iso3", "name_uk", "name_en", "flag"}


def test_search_returns_short_rows(client):
    response = client.get("/api/countries/search", params={"q": "укр"})
    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["iso3"] == "UKR"
    assert set(rows[0]) == {"iso3", "name_uk", "name_en", "flag"}
    assert len(rows) <= 10


def test_search_without_query_is_empty(client):
    assert client.get("/api/countries/search").json() == []


def test_playable_lists_known_country_codes(client):
    response = client.get("/api/countries/playable")
    assert response.status_code == 200
    codes = response.json()
    assert "UKR" in codes
    assert "VAT" not in codes


def test_read_hints_returns_ordered_kind_and_text(client):
    response = client.get("/api/countries/ukr/hints")
    assert response.status_code == 200
    result = response.json()
    assert len(result) >= 8
    assert all(set(h) == {"kind", "text"} for h in result)
    assert result[-1]["text"].startswith("Столиця")


def test_hints_for_unknown_country_is_404(client):
    assert client.get("/api/countries/xyz/hints").status_code == 404


def test_every_playable_country_serves_hints(client):
    for iso3 in client.get("/api/countries/playable").json():
        response = client.get(f"/api/countries/{iso3}/hints")
        assert response.status_code == 200, iso3
        assert response.json(), iso3


def test_leaderboard_starts_empty(client, scores_db):
    assert client.get("/api/leaderboard").json() == []


def test_posted_score_appears_on_leaderboard(client, scores_db):
    response = client.post("/api/scores", json={"player": "Ann", "points": 80})
    assert response.status_code == 201
    client.post("/api/scores", json={"player": "Bob", "points": 95})
    board = client.get("/api/leaderboard").json()
    assert [(row["player"], row["points"]) for row in board] == [("Bob", 95), ("Ann", 80)]


def test_leaderboard_limit(client, scores_db):
    for points in (1, 2, 3):
        client.post("/api/scores", json={"player": "p", "points": points})
    assert len(client.get("/api/leaderboard", params={"limit": 2}).json()) == 2
    assert client.get("/api/leaderboard", params={"limit": 0}).status_code == 422


def test_invalid_scores_are_rejected(client, scores_db):
    bad_bodies = [
        {"player": "", "points": 5},
        {"player": "x" * 31, "points": 5},
        {"player": "ann", "points": -1},
        {"player": "ann"},
        {"player": "ann", "points": "many"},
    ]
    for body in bad_bodies:
        assert client.post("/api/scores", json=body).status_code == 422, body


def test_blank_name_is_rejected_by_the_database_layer(client, scores_db):
    response = client.post("/api/scores", json={"player": "   ", "points": 5})
    assert response.status_code == 422
    assert client.get("/api/leaderboard").json() == []


def test_read_country_is_case_insensitive(client):
    response = client.get("/api/countries/ukr")
    assert response.status_code == 200
    assert response.json()["name_en"] == "Ukraine"


def test_unknown_country_is_404(client):
    assert client.get("/api/countries/xyz").status_code == 404
