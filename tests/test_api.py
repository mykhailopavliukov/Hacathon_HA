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


def test_read_country_is_case_insensitive(client):
    response = client.get("/api/countries/ukr")
    assert response.status_code == 200
    assert response.json()["name_en"] == "Ukraine"


def test_unknown_country_is_404(client):
    assert client.get("/api/countries/xyz").status_code == 404
    assert client.get("/api/countries/xyz/facts").status_code == 404


def test_read_facts_respects_max_rank(client):
    response = client.get("/api/countries/UKR/facts", params={"max_rank": 3})
    assert response.status_code == 200
    facts = response.json()
    assert facts
    assert all(f["rank"] <= 3 for f in facts)


def test_read_facts_rejects_bad_max_rank(client):
    assert client.get("/api/countries/UKR/facts", params={"max_rank": 0}).status_code == 422
