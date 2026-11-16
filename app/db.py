"""SQLite storage for the leaderboard (standard library only)."""

import os
import sqlite3


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
