"""Round state and scoring for the "Guess the country" game.

Pure game logic: no UI and no imports from other app modules.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

MAX_POINTS = 100
WRONG_GUESS_PENALTY = 10
MIN_WIN_POINTS = 10
APOSTROPHES = "'’ʼ`"


def normalize(text: str) -> str:
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    # Dropping combining marks also makes e.g. "й"/"и" and "ї"/"і" equal,
    # which is intentionally lenient for typing on the demo.
    # Apostrophes are removed, not turned into spaces: people often skip them ("Вєтнам").
    no_marks = "".join(
        ch for ch in decomposed if not unicodedata.combining(ch) and ch not in APOSTROPHES
    )
    words = re.sub(r"[^\w\s]", " ", no_marks).split()
    return " ".join(words)


@dataclass
class Round:
    """One game round: hints are ordered from vague to precise."""

    hints: list[str]
    accepted_names: list[str]
    max_points: int = MAX_POINTS
    shown: int = 1
    wrong_guesses: int = 0
    solved: bool = False
    gave_up: bool = False

    def __post_init__(self) -> None:
        if not self.hints:
            raise ValueError("Round needs at least one hint")
        if not any(normalize(name) for name in self.accepted_names):
            raise ValueError("Round needs at least one accepted name")

    @property
    def is_over(self) -> bool:
        return self.solved or self.gave_up

    @property
    def visible_hints(self) -> list[str]:
        """Hints opened so far, in order."""
        return self.hints[: self.shown]

    @property
    def can_reveal(self) -> bool:
        return not self.is_over and self.shown < len(self.hints)

    @property
    def points_available(self) -> int:
        """Points the player would get for a correct answer right now."""
        total = len(self.hints)
        base = self.max_points * (total - self.shown + 1) // total
        penalty = self.wrong_guesses * WRONG_GUESS_PENALTY
        return max(MIN_WIN_POINTS, base - penalty)

    @property
    def score(self) -> int:
        """Final points: zero unless the round was solved."""
        return self.points_available if self.solved else 0

    def reveal_next(self) -> bool:
        """Open the next hint. Returns False if nothing more can be opened."""
        if not self.can_reveal:
            return False
        self.shown += 1
        return True

    def guess(self, text: str) -> bool:
        """Check an answer. Empty input and guesses after the end are ignored."""
        if self.is_over:
            return False
        answer = normalize(text)
        if not answer:
            return False
        if answer in {normalize(name) for name in self.accepted_names}:
            self.solved = True
            return True
        self.wrong_guesses += 1
        return False

    def give_up(self) -> None:
        """End the round without points."""
        if not self.solved:
            self.gave_up = True
