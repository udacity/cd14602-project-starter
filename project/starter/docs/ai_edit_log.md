# AI Edit Log

**AI tool:** Copilot SDK in VS Code  
**Project:** Flashcard Quizzer  
**Date:** 2026-11-18

This log records five scoped implementation requests extracted from the project
brief that guided this AI-assisted build. They represent the work instructions
used to implement and review the application, not five separate user chat
messages. The responses, decisions, and verification notes below describe the
actual project changes.

## 1. Load and validate both JSON deck formats

**Context:** The starter includes a top-level array deck and an object containing
a `cards` array. The application must report malformed or invalid input without
exposing a traceback.

**Prompt/Request:** “Implement the data layer for both supplied JSON formats.
Validate that every card is an object with non-empty string `front` and `back`
values. Report a useful file or card-position error for missing files, bad JSON,
unsupported structures, and invalid fields. Keep file reading separate from
deck validation and use type hints.”

**AI response:** Added the `Flashcard` model, `utils/file_handler.py` for UTF-8
JSON reading, and `data_loader.py` for validating either deck shape.

**Review/refinement:** Kept file-system/JSON failures in a dedicated exception
and translated those into `FlashcardLoadError` at the deck boundary. Added
card-index context and rejected empty decks and whitespace-only values. The CLI
prints loader errors to stderr and exits with a nonzero status.

**Reasoning:** Precise error handling keeps invalid-data failures understandable
and avoids masking unrelated programming errors with broad exception handlers.

**Outcome:** Tests cover both valid shapes, malformed JSON, missing files,
missing fields, and malformed card structures.

**Lesson:** Validate data at ingestion so the quiz engine can rely on a
well-formed domain model.

## 2. Implement strategy-based quiz modes and a factory

**Context:** The three modes select questions differently and should be
extendable without putting mode-specific branches into the CLI loop.

**Prompt/Request:** “Create a `QuizMode` abstraction with sequential, random,
and adaptive implementations. Add a factory that maps user-facing mode names to
the corresponding strategy and rejects unknown names.”

**AI response:** Added `QuizMode`, `SequentialMode`, `RandomMode`,
`AdaptiveMode`, and `QuizModeFactory` in `quiz_engine.py`.

**Review/refinement:** The factory is a single responsibility separate from
argument parsing. Random mode accepts an injectable random generator for
repeatable tests. Adaptive mode asks the complete deck once and schedules each
missed card for one retry afterward.

**Reasoning:** The strategy API shares the same `start`, `next_card`, and
`record_answer` contract. A bounded retry is adaptive while still guaranteeing
that a session with unanswered or repeatedly missed cards terminates.

**Outcome:** Factory/type tests cover all modes; a focused adaptive test verifies
first-pass order, retry behavior, and termination.

**Lesson:** An explicit lifecycle makes each strategy testable without knowing
the internals of the user interface.

## 3. Track answers, accuracy, and missed terms

**Context:** Each answer needs immediate comparison and the final summary must
report total questions, accuracy, and terms missed.

**Prompt/Request:** “Add session-level answer checking and statistics. Ignore
case and surrounding whitespace, count all answered questions, report
correct-answer percentage, and list missed terms once even if they are missed
again.”

**AI response:** Added `QuizSession` and `QuizStats` to the quiz engine.

**Review/refinement:** Accuracy is zero for a session with no submitted
answers; adaptive retries count as additional questions. A term appears only
once in the missed list, even if it is missed on its retry.

**Reasoning:** Counting asked-and-answered questions makes the adaptive score
transparent, and unique terms make the summary readable.

**Outcome:** Unit tests cover case-insensitive answers, whitespace trimming,
incorrect answers, unique missed terms, and accuracy calculation.

**Lesson:** Statistics need an explicit denominator and retry policy; without
those definitions, the same session can produce ambiguous accuracy values.

## 4. Build a robust terminal interaction and CLI

**Context:** The application needs mode and file flags, immediate feedback,
colors, an early-exit path, and a graceful Ctrl+C response.

**Prompt/Request:** “Implement a small argparse CLI and terminal interface.
Support `-f`/`--file`, `-m`/`--mode`, and `--stats`; display correct/incorrect
feedback and the final summary. Handle `exit`, EOF, and Ctrl+C without a
traceback.”

**AI response:** Added argument parsing in `main.py` and interaction/reporting
in `ui.py`. `--stats` enables running accuracy output while the final summary is
always shown.

**Review/refinement:** Error messages from deck loading are caught only at the
CLI boundary. The interface accepts injectable input/output callables so tests
can simulate a real session without terminal interaction. ANSI colors are
added only when standard output is a TTY.

**Reasoning:** Narrow exception handling preserves meaningful failures, while
dependency injection makes integration tests deterministic.

**Outcome:** Integration tests exercise completed sessions, early exit,
interrupt handling, flags, live stats, and friendly missing-file output.

**Lesson:** Test seams such as injectable I/O are useful when they keep the
production interaction simple and make behavior observable.

## 5. Verify behavior and project quality

**Context:** The deliverable requires a passing pytest suite, over 80% coverage,
Black formatting, Flake8 cleanliness, and mypy checks.

**Prompt/Request:** “Review the source and tests against the stated requirements.
Run pytest with coverage, Black, Flake8, and mypy. Fix issues caused by the
implementation, and record only measured results.”

**AI response:** Added focused tests for loading, strategies, statistics, and
CLI integration, then ran the specified quality tools and refined any reported
issues.

**Review/refinement:** The first integration run exposed an overly strict
question-output assertion and an input function bound too early for CLI
simulation. The assertion was made insensitive to the display newline, and the
UI now resolves `input` at call time when no test input function is supplied.
After that refinement, all quality checks passed.

**Reasoning:** The quality gate measures distinct concerns: runtime behavior,
formatting, lint, type safety, and the specified coverage threshold.

**Outcome:** The final suite passed 25 tests. Coverage was 99% overall and
approximately 98% across application modules. Black, Flake8, and mypy all
completed successfully; exact commands and results are in `quality_report.md`.

**Lesson:** A successful test suite is necessary but does not replace checking
formatting, typing, lint, or the coverage target independently.

## Summary

- **Scoped implementation requests recorded:** 5
- **AI-generated components:** loader, model, strategy/factory/session, CLI,
  terminal UI, tests, and project documentation
- **Verification:** See `final_report.md` for measured test and quality results.
