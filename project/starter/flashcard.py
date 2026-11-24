"""Domain model for a flashcard."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Flashcard:
    """A prompt and its expected answer."""

    front: str
    back: str
