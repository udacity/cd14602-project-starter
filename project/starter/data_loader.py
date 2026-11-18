"""Load and validate flashcard decks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flashcard import Flashcard
from utils.file_handler import FileHandlerError, read_json_file


class FlashcardLoadError(Exception):
    """Raised when a deck is missing, malformed, or invalid."""


def load_flashcards(file_path: str | Path) -> list[Flashcard]:
    """Load a deck in array or ``{"cards": [...]}`` JSON format."""
    try:
        payload = read_json_file(file_path)
    except FileHandlerError as exc:
        raise FlashcardLoadError(str(exc)) from exc

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and "cards" in payload:
        records = payload["cards"]
        if not isinstance(records, list):
            raise FlashcardLoadError("the 'cards' value must be a JSON array")
    else:
        raise FlashcardLoadError(
            "the deck must be a JSON array or an object containing a 'cards' array"
        )

    if not records:
        raise FlashcardLoadError("the deck must contain at least one flashcard")

    cards: list[Flashcard] = []
    for index, record in enumerate(records, start=1):
        cards.append(_parse_card(record, index))
    return cards


def _parse_card(record: Any, index: int) -> Flashcard:
    """Validate one card record and include its position in errors."""
    if not isinstance(record, dict):
        raise FlashcardLoadError(f"card {index} must be a JSON object")

    front = record.get("front")
    back = record.get("back")
    if not isinstance(front, str) or not front.strip():
        raise FlashcardLoadError(f"card {index} must have a non-empty string 'front'")
    if not isinstance(back, str) or not back.strip():
        raise FlashcardLoadError(f"card {index} must have a non-empty string 'back'")

    return Flashcard(front=front.strip(), back=back.strip())
