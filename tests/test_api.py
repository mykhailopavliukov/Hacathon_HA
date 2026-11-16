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


def test_read_country_is_case_insensitive(client):
    response = client.get("/api/countries/ukr")
    assert response.status_code == 200
    assert response.json()["name_en"] == "Ukraine"


def test_unknown_country_is_404(client):
    assert client.get("/api/countries/xyz").status_code == 404
