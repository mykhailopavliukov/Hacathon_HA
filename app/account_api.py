"""JSON endpoints for accounts and streaks. Included by `app.api` under /api."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app import auth, streaks

router = APIRouter()


class Credentials(BaseModel):
    # Real rules live in app.auth; these limits only stop huge bodies before they are hashed.
    username: str = Field(max_length=100)
    password: str = Field(max_length=auth.MAX_PASSWORD_LENGTH)


def _bearer_token(authorization: str | None = Header(default=None)) -> str:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Missing bearer token", headers={"WWW-Authenticate": "Bearer"})
    return token


BearerToken = Annotated[str, Depends(_bearer_token)]


def current_user(token: BearerToken) -> dict:
    """Dependency: the logged-in user, or a 401."""
    user = auth.get_session_user(token)
    if user is None:
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})
    return user


CurrentUser = Annotated[dict, Depends(current_user)]


@router.post("/auth/register", status_code=201)
def register(credentials: Credentials) -> dict:
    try:
        user_id = auth.register(credentials.username, credentials.password)
    except auth.UsernameTaken as error:  # before ValueError: it is a subclass
        raise HTTPException(409, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"id": user_id, "username": credentials.username.strip()}


@router.post("/auth/login")
def login(credentials: Credentials) -> dict:
    try:
        user = auth.login(credentials.username, credentials.password)
    except auth.TooManyAttempts as error:
        raise HTTPException(
            429, str(error), headers={"Retry-After": str(auth.LOCKOUT_SECONDS)}
        ) from error
    if user is None:
        # One message for "no such user" and "wrong password", so names cannot be probed.
        raise HTTPException(401, "Wrong username or password")
    return {"token": auth.create_session(user["id"]), "username": user["username"]}


@router.post("/auth/logout", status_code=204)
def logout(token: BearerToken, user: CurrentUser) -> Response:
    auth.delete_session(token)
    return Response(status_code=204)


@router.get("/auth/me")
def me(user: CurrentUser) -> dict:
    return user


class RoundResult(BaseModel):
    solved: bool


@router.get("/streak")
def read_streak(user: CurrentUser) -> dict[str, int]:
    return streaks.get_streak(user["id"])


@router.post("/streak")
def record_round(result: RoundResult, user: CurrentUser) -> dict[str, int]:
    """Report a finished round: solved extends the streak, anything else resets it."""
    return streaks.record_round(user["id"], result.solved)


@router.get("/streaks/top")
def read_top_streaks(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
    return streaks.top_streaks(limit)
