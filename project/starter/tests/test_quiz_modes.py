"""Tests for quiz strategies, the factory, and session statistics."""

import random

import pytest

from flashcard import Flashcard
from quiz_engine import (
    AdaptiveMode,
    QuizModeFactory,
    QuizSession,
    RandomMode,
    SequentialMode,
)


def test_quiz_mode_factory() -> None:
    assert isinstance(QuizModeFactory.create("sequential"), SequentialMode)
    assert isinstance(QuizModeFactory.create("random"), RandomMode)
    assert isinstance(QuizModeFactory.create("adaptive"), AdaptiveMode)


def test_factory_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="unknown quiz mode"):
        QuizModeFactory.create("spaced")


def test_sequential_mode_preserves_input_order() -> None:
    cards = [Flashcard("one", "1"), Flashcard("two", "2")]
    mode = SequentialMode()
    mode.start(cards)

    assert mode.next_card() == cards[0]
    assert mode.next_card() == cards[1]
    assert mode.next_card() is None


def test_random_mode_shuffles_without_losing_cards() -> None:
    cards = [Flashcard(str(index), str(index)) for index in range(8)]
    mode = RandomMode(random.Random(4))
    mode.start(cards)
    selected = [mode.next_card() for _ in cards]

    assert sorted(card.front for card in selected if card is not None) == [
        card.front for card in cards
    ]
    assert [card for card in selected if card is not None] != cards
    assert mode.next_card() is None


def test_adaptive_mode_repeats_missed_card_once_after_first_pass() -> None:
    first = Flashcard("first", "1")
    second = Flashcard("second", "2")
    mode = AdaptiveMode()
    mode.start([first, second])

    assert mode.next_card() is first
    mode.record_answer(first, False)
    assert mode.next_card() is second
    assert mode.next_card() is first
    mode.record_answer(first, False)
    assert mode.next_card() is None


def test_session_tracks_case_insensitive_answers_and_missed_terms() -> None:
    cards = [Flashcard("API", "Interface"), Flashcard("DNS", "Name service")]
    session = QuizSession(cards, SequentialMode())

    first = session.next_card()
    assert first is not None
    assert session.submit_answer(first, " interface ")
    second = session.next_card()
    assert second is not None
    assert not session.submit_answer(second, "wrong")

    assert session.stats.total_questions == 2
    assert session.stats.accuracy_percentage == 50.0
    assert session.stats.missed_terms == ("DNS",)


def test_empty_session_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one flashcard"):
        QuizSession([], SequentialMode())
