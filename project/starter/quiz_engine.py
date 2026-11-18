"""Quiz strategies, session coordination, and score tracking."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field

from flashcard import Flashcard


class QuizMode(ABC):
    """Strategy interface for selecting and responding to quiz cards."""

    @abstractmethod
    def start(self, cards: Sequence[Flashcard]) -> None:
        """Prepare the strategy for a new deck."""

    @abstractmethod
    def next_card(self) -> Flashcard | None:
        """Return the next card, or ``None`` when the strategy is finished."""

    @abstractmethod
    def record_answer(self, card: Flashcard, is_correct: bool) -> None:
        """Update strategy state after an answer."""


class SequentialMode(QuizMode):
    """Present each card once in its original order."""

    def __init__(self) -> None:
        self._cards: deque[Flashcard] = deque()

    def start(self, cards: Sequence[Flashcard]) -> None:
        self._cards = deque(cards)

    def next_card(self) -> Flashcard | None:
        return self._cards.popleft() if self._cards else None

    def record_answer(self, card: Flashcard, is_correct: bool) -> None:
        return None


class RandomMode(QuizMode):
    """Present each card once in a shuffled order."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self._rng = rng if rng is not None else random.Random()
        self._cards: deque[Flashcard] = deque()

    def start(self, cards: Sequence[Flashcard]) -> None:
        shuffled = list(cards)
        self._rng.shuffle(shuffled)
        self._cards = deque(shuffled)

    def next_card(self) -> Flashcard | None:
        return self._cards.popleft() if self._cards else None

    def record_answer(self, card: Flashcard, is_correct: bool) -> None:
        return None


class AdaptiveMode(QuizMode):
    """Retry missed cards once after the first pass through the deck."""

    def __init__(self) -> None:
        self._cards: deque[Flashcard] = deque()
        self._retries: deque[Flashcard] = deque()
        self._scheduled_ids: set[int] = set()

    def start(self, cards: Sequence[Flashcard]) -> None:
        self._cards = deque(cards)
        self._retries.clear()
        self._scheduled_ids.clear()

    def next_card(self) -> Flashcard | None:
        if self._cards:
            return self._cards.popleft()
        if self._retries:
            return self._retries.popleft()
        return None

    def record_answer(self, card: Flashcard, is_correct: bool) -> None:
        card_id = id(card)
        if not is_correct and card_id not in self._scheduled_ids:
            self._scheduled_ids.add(card_id)
            self._retries.append(card)


class QuizModeFactory:
    """Create a quiz strategy from its command-line name."""

    @staticmethod
    def create(mode_name: str) -> QuizMode:
        """Return the strategy matching ``mode_name``."""
        modes: dict[str, type[QuizMode]] = {
            "sequential": SequentialMode,
            "random": RandomMode,
            "adaptive": AdaptiveMode,
        }
        try:
            return modes[mode_name]()
        except KeyError:
            supported = ", ".join(modes)
            raise ValueError(
                f"unknown quiz mode '{mode_name}'; choose from {supported}"
            ) from None


@dataclass
class QuizStats:
    """Aggregate answers and retain unique terms missed during a session."""

    total_questions: int = 0
    correct_answers: int = 0
    _missed_terms: list[str] = field(default_factory=list)

    @property
    def accuracy_percentage(self) -> float:
        """Return accuracy as a percentage, or zero before any answers."""
        if self.total_questions == 0:
            return 0.0
        return self.correct_answers / self.total_questions * 100

    @property
    def missed_terms(self) -> tuple[str, ...]:
        """Return missed card fronts in the order they were first missed."""
        return tuple(self._missed_terms)

    def record_answer(self, card: Flashcard, is_correct: bool) -> None:
        """Record one answered question."""
        self.total_questions += 1
        if is_correct:
            self.correct_answers += 1
        elif card.front not in self._missed_terms:
            self._missed_terms.append(card.front)


class QuizSession:
    """Coordinate a quiz strategy with answer checking and statistics."""

    def __init__(self, cards: Sequence[Flashcard], mode: QuizMode) -> None:
        if not cards:
            raise ValueError("a quiz session requires at least one flashcard")
        self._mode = mode
        self._mode.start(cards)
        self.stats = QuizStats()

    def next_card(self) -> Flashcard | None:
        """Get the next card selected by this session's strategy."""
        return self._mode.next_card()

    def submit_answer(self, card: Flashcard, answer: str) -> bool:
        """Check an answer case-insensitively and update session state."""
        is_correct = answer.strip().casefold() == card.back.casefold()
        self.stats.record_answer(card, is_correct)
        self._mode.record_answer(card, is_correct)
        return is_correct
