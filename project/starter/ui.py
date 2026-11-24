"""Terminal interaction and presentation for quiz sessions."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence

from flashcard import Flashcard
from quiz_engine import QuizModeFactory, QuizSession, QuizStats

Output = Callable[[str], None]
Input = Callable[[str], str]


def _colorize(message: str, color_code: str) -> str:
    """Add an ANSI color only when standard output is an interactive terminal."""
    if sys.stdout.isatty():
        return f"\033[{color_code}m{message}\033[0m"
    return message


def display_summary(stats: QuizStats, output: Output = print) -> None:
    """Print a final summary table and the terms missed during the session."""
    output("Quiz Summary")
    output("+-----------------+----------+")
    output(f"| {'Total Questions':<15} | {stats.total_questions:>8} |")
    output(f"| {'Accuracy':<15} | {stats.accuracy_percentage:>7.1f}% |")
    output("+-----------------+----------+")
    output("Missed terms:")
    if stats.missed_terms:
        for term in stats.missed_terms:
            output(f"- {term}")
    else:
        output("- None")


def play_quiz(
    cards: Sequence[Flashcard],
    mode_name: str,
    show_live_stats: bool = False,
    input_func: Input | None = None,
    output: Output = print,
) -> QuizStats:
    """Run a quiz, gracefully handling exit commands and terminal interrupts."""
    session = QuizSession(cards, QuizModeFactory.create(mode_name))
    read_answer = input if input_func is None else input_func
    output(f"Starting {mode_name} quiz. Type 'exit' to finish early.")

    try:
        question_number = 0
        while (card := session.next_card()) is not None:
            question_number += 1
            output(f"\nQuestion {question_number}: {card.front}")
            answer = read_answer("Your answer: ")
            if answer.strip().casefold() == "exit":
                output("Quiz ended by user.")
                break

            if session.submit_answer(card, answer):
                output(_colorize("Correct!", "32"))
            else:
                output(_colorize(f"Incorrect. Correct answer: {card.back}", "31"))

            if show_live_stats:
                output(
                    f"Current accuracy: {session.stats.accuracy_percentage:.1f}% "
                    f"({session.stats.total_questions} questions)"
                )
    except (EOFError, KeyboardInterrupt):
        output("\nQuiz interrupted. Showing current results.")

    display_summary(session.stats, output)
    return session.stats
