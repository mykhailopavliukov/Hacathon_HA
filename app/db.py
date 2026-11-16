"""SQLite storage for the leaderboard (standard library only)."""

import os
import sqlite3
from contextlib import closing

MAX_NAME_LENGTH = 30


def db_path() -> str:
    return os.environ.get("SCORES_DB", "scores.db")


def connect() -> sqlite3.Connection:
    """Open the database, creating the scores table on first use."""
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY,
            player TEXT NOT NULL,
            points INTEGER NOT NULL CHECK (points >= 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def add_score(player: str, points: int) -> None:
    """Save one result. Raises ValueError for an empty or too long name, or negative points."""
    name = player.strip()
    if not 1 <= len(name) <= MAX_NAME_LENGTH:
        raise ValueError(f"Player name must be 1-{MAX_NAME_LENGTH} characters")
    if points < 0:
        raise ValueError("Points cannot be negative")
    # `with conn` commits the insert; `closing` releases the file afterwards.
    with closing(connect()) as conn, conn:
        conn.execute("INSERT INTO scores (player, points) VALUES (?, ?)", (name, points))


def top_scores(limit: int = 10) -> list[dict]:
    """Best results first; for equal points the earlier one ranks higher."""
    with closing(connect()) as conn:
        rows = conn.execute(
            "SELECT player, points, created_at FROM scores ORDER BY points DESC, id LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
