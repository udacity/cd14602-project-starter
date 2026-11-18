"""Command-line entry point for the Flashcard Quizzer."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from data_loader import FlashcardLoadError, load_flashcards
from ui import play_quiz


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Practice a flashcard deck in sequential, random, or adaptive mode."
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="Path to a JSON flashcard deck.",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=("sequential", "random", "adaptive"),
        default="sequential",
        help="Question selection strategy (default: sequential).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show a running accuracy summary after each answer.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process status code."""
    args = build_parser().parse_args(argv)
    try:
        cards = load_flashcards(args.file)
    except FlashcardLoadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    play_quiz(cards, args.mode, show_live_stats=args.stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
