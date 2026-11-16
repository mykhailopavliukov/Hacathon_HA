"""Leaderboard by player: total points over all won rounds."""

from contextlib import closing

from app import db


def top_players(limit: int = 10) -> list[dict]:
    """Players by total points; ties go to whoever reached the board first."""
    with closing(db.connect()) as conn:
        rows = conn.execute(
            "SELECT player, SUM(points) AS total, COUNT(*) AS wins FROM scores"
            " GROUP BY player ORDER BY total DESC, MIN(id) LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
