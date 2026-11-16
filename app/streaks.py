"""Win streaks per account: solved rounds in a row, and the best run ever."""

import sqlite3
from contextlib import closing

from app import db


def record_round(user_id: int, solved: bool) -> dict[str, int]:
    """Update the streak after a finished round and return it.

    A solved round extends the current streak (and the best one if beaten); a failed or
    abandoned round resets the current streak to 0. Raises ValueError for an unknown user.
    """
    try:
        with closing(db.connect()) as conn, conn:
            conn.execute("INSERT OR IGNORE INTO streaks (user_id) VALUES (?)", (user_id,))
            if solved:
                # One statement, so two simultaneous requests cannot lose an update.
                conn.execute(
                    "UPDATE streaks SET current = current + 1, best = MAX(best, current + 1)"
                    " WHERE user_id = ?",
                    (user_id,),
                )
            else:
                conn.execute("UPDATE streaks SET current = 0 WHERE user_id = ?", (user_id,))
    except sqlite3.IntegrityError as error:  # the foreign key to users failed
        raise ValueError(f"Unknown user: {user_id}") from error
    return get_streak(user_id)


def get_streak(user_id: int) -> dict[str, int]:
    """Current and best streak; a user who has not played yet has 0 and 0."""
    with closing(db.connect()) as conn:
        row = conn.execute(
            "SELECT current, best FROM streaks WHERE user_id = ?", (user_id,)
        ).fetchone()
    return {"current": 0, "best": 0} if row is None else {"current": row[0], "best": row[1]}


def top_streaks(limit: int = 10) -> list[dict]:
    """Players with the best streaks first; ties go to whoever registered earlier."""
    with closing(db.connect()) as conn:
        rows = conn.execute(
            "SELECT users.username, streaks.best, streaks.current FROM streaks"
            " JOIN users ON users.id = streaks.user_id"
            " WHERE streaks.best > 0"
            " ORDER BY streaks.best DESC, users.id LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
