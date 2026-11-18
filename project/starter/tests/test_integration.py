"""Integration tests for terminal sessions and command-line behavior."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from data_loader import load_flashcards
from flashcard import Flashcard
from main import main
import ui
from ui import play_quiz


def answer_sequence(answers: list[str]) -> Iterator[str]:
    """Yield canned answers for a simulated interactive session."""
    yield from answers


def test_full_session_reports_totals_accuracy_and_missed_terms() -> None:
    cards = [
        load_flashcards(Path(__file__).parents[1] / "data" / "python_basics.json")[
            index
        ]
        for index in range(3)
    ]
    answers = iter(answer_sequence(["DEF", "wrong", "for"]))
    output: list[str] = []

    stats = play_quiz(
        cards,
        "sequential",
        input_func=lambda prompt: next(answers),
        output=output.append,
    )

    assert stats.total_questions == 3
    assert stats.accuracy_percentage == pytest.approx(200 / 3)
    assert stats.missed_terms == (cards[1].front,)
    assert any("Total Questions" in line and "3" in line for line in output)
    assert any(
        "Which built-in function returns the length of a list?" in line
        for line in output
    )


def test_adaptive_session_retries_missed_card() -> None:
    cards = [Flashcard("A", "alpha"), Flashcard("B", "beta")]
    answers = iter(["wrong", "beta", "alpha"])
    output: list[str] = []

    stats = play_quiz(
        cards,
        "adaptive",
        input_func=lambda prompt: next(answers),
        output=output.append,
    )

    assert stats.total_questions == 3
    assert stats.accuracy_percentage == pytest.approx(200 / 3)
    assert sum(line.strip() == "Question 3: A" for line in output) == 1


def test_exit_and_interrupt_finish_without_traceback() -> None:
    cards = [Flashcard("A", "alpha")]
    output: list[str] = []

    stats = play_quiz(
        cards,
        "sequential",
        input_func=lambda prompt: "exit",
        output=output.append,
    )
    assert stats.total_questions == 0
    assert any("Missed terms:" in line for line in output)

    def interrupt(prompt: str) -> str:
        raise KeyboardInterrupt

    output.clear()
    stats = play_quiz(cards, "sequential", input_func=interrupt, output=output.append)
    assert stats.total_questions == 0
    assert any("interrupted" in line.lower() for line in output)


def test_feedback_is_colored_in_interactive_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InteractiveTerminal:
        def isatty(self) -> bool:
            return True

    monkeypatch.setattr(ui.sys, "stdout", InteractiveTerminal())

    assert ui._colorize("Correct!", "32") == "\033[32mCorrect!\033[0m"


def test_cli_handles_missing_deck_gracefully(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = main(["--file", str(tmp_path / "missing.json")])
    captured = capsys.readouterr()

    assert result == 2
    assert "Error: file not found" in captured.err
    assert "Traceback" not in captured.err


def test_cli_supports_flags_and_live_stats(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deck = tmp_path / "deck.json"
    deck.write_text('[{"front": "A", "back": "alpha"}]', encoding="utf-8")
    monkeypatch.setattr("builtins.input", lambda prompt: "alpha")
    result = main(["-f", str(deck), "-m", "sequential", "--stats"])
    captured = capsys.readouterr()

    assert result == 0
    assert "Current accuracy: 100.0%" in captured.out
    assert "Quiz Summary" in captured.out
