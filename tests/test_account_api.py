import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import auth
from app.api import router


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _register(client, username="Hlib", password="correct horse"):
    return client.post("/api/auth/register", json={"username": username, "password": password})


def _login_headers(client, username="Hlib", password="correct horse") -> dict:
    token = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    ).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_returns_201_without_the_password(client, scores_db):
    response = _register(client)
    assert response.status_code == 201
    assert response.json() == {"id": 1, "username": "Hlib"}


def test_register_duplicate_is_409_and_invalid_input_is_422(client, scores_db):
    _register(client)
    assert _register(client, "hlib").status_code == 409
    assert _register(client, "ab").status_code == 422
    assert _register(client, "someone", "short").status_code == 422
    assert client.post("/api/auth/register", json={"username": "x"}).status_code == 422
    huge = _register(client, "someone", "x" * 100_000)
    assert huge.status_code == 422


def test_login_returns_a_token_that_opens_me(client, scores_db):
    _register(client)
    response = client.post(
        "/api/auth/login", json={"username": "Hlib", "password": "correct horse"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "Hlib"
    me = client.get("/api/auth/me", headers=_login_headers(client))
    assert me.json() == {"id": 1, "username": "Hlib"}


def test_wrong_password_and_unknown_user_look_the_same(client, scores_db):
    _register(client)
    wrong = client.post("/api/auth/login", json={"username": "Hlib", "password": "wrong horse"})
    unknown = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong horse"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_is_locked_after_repeated_failures(client, scores_db):
    _register(client)
    for _ in range(auth.MAX_FAILED_LOGINS):
        client.post("/api/auth/login", json={"username": "Hlib", "password": "wrong horse"})
    locked = client.post("/api/auth/login", json={"username": "Hlib", "password": "correct horse"})
    assert locked.status_code == 429
    assert locked.headers["Retry-After"] == str(auth.LOCKOUT_SECONDS)


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer nope"},
        {"Authorization": "Basic abc"},
        {"Authorization": "Bearer"},
    ],
)
def test_me_requires_a_valid_token(client, scores_db, headers):
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_logout_invalidates_the_token(client, scores_db):
    _register(client)
    headers = _login_headers(client)
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post("/api/auth/logout", headers=headers).status_code == 401
