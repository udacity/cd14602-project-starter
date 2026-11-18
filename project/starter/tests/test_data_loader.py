"""Tests for flashcard loading and validation."""

from pathlib import Path

import pytest

from data_loader import FlashcardLoadError, load_flashcards
from flashcard import Flashcard


def test_load_valid_flashcards_array(tmp_path: Path) -> None:
    deck = tmp_path / "deck.json"
    deck.write_text(
        '[{"front": " API ", "back": "Application Programming Interface"}]',
        encoding="utf-8",
    )

    assert load_flashcards(deck) == [
        Flashcard("API", "Application Programming Interface")
    ]


def test_load_valid_flashcards_object(tmp_path: Path) -> None:
    deck = tmp_path / "deck.json"
    deck.write_text(
        '{"cards": [{"front": "Python", "back": "Language"}]}',
        encoding="utf-8",
    )

    assert load_flashcards(deck) == [Flashcard("Python", "Language")]


def test_load_invalid_json(tmp_path: Path) -> None:
    deck = tmp_path / "broken.json"
    deck.write_text('{"cards": [', encoding="utf-8")

    with pytest.raises(FlashcardLoadError, match="invalid JSON"):
        load_flashcards(deck)


def test_load_missing_required_field(tmp_path: Path) -> None:
    deck = tmp_path / "incomplete.json"
    deck.write_text('[{"front": "DNS"}]', encoding="utf-8")

    with pytest.raises(FlashcardLoadError, match="card 1.*'back'"):
        load_flashcards(deck)


def test_load_missing_file_has_helpful_message(tmp_path: Path) -> None:
    with pytest.raises(FlashcardLoadError, match="file not found"):
        load_flashcards(tmp_path / "missing.json")


def test_load_invalid_utf8_has_helpful_message(tmp_path: Path) -> None:
    deck = tmp_path / "not_utf8.json"
    deck.write_bytes(b"\xff")

    with pytest.raises(FlashcardLoadError, match="not valid UTF-8"):
        load_flashcards(deck)


@pytest.mark.parametrize(
    "content, error",
    [
        ('{"cards": "not a list"}', "must be a JSON array"),
        ('{"front": "no cards key"}', "must be a JSON array"),
        ("[]", "at least one flashcard"),
        ('[{"front": "   ", "back": "answer"}]', "non-empty string 'front'"),
        ('[{"front": "term", "back": 42}]', "non-empty string 'back'"),
        ("[null]", "card 1 must be a JSON object"),
    ],
)
def test_load_rejects_invalid_structure(
    tmp_path: Path, content: str, error: str
) -> None:
    deck = tmp_path / "invalid.json"
    deck.write_text(content, encoding="utf-8")

    with pytest.raises(FlashcardLoadError, match=error):
        load_flashcards(deck)
