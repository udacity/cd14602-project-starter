# Flashcard Quizzer: AI-Assisted Development Report

## Executive Summary

The Flashcard Quizzer is a small Python command-line application for practicing
terms from JSON decks. It loads two supported deck shapes, validates their
contents, and offers sequential, shuffled, and adaptive sessions. A quiz ends
with a summary of answered questions, accuracy, and missed terms. The source is
split into a domain model, file and data layers, quiz strategies, and terminal
interaction rather than being concentrated in one entry-point script.

The implementation was directed and reviewed with the Copilot SDK in VS Code.
The development process translated the project brief into scoped requirements,
implemented each layer, added tests around expected behavior, and then used
pytest, coverage, Black, Flake8, and mypy as independent checks. The final suite
passes 25 tests; measured total coverage is 99%, and no formatter, lint, or type
errors remain.

## Project Overview

### Problem and solution

New hires need a quick way to learn internal acronyms and technical vocabulary.
A terminal quizzer is lightweight, requires no service or database, and can use
decks maintained as ordinary JSON. The solution uses only the Python standard
library at runtime. Development tools are installed from the supplied
`requirements.txt`.

The loader accepts either a top-level array of `{ "front": ..., "back": ... }`
records or an object whose `cards` property contains that array. File reading
and JSON decoding live in `utils/file_handler.py`; validation and conversion to
immutable `Flashcard` objects live in `data_loader.py` and `flashcard.py`.
Invalid paths, malformed JSON, unsupported structures, empty decks, and
missing or invalid fields are reported with actionable messages. The command
line reports loader errors without a Python traceback.

### Features and design

The CLI in `main.py` uses `argparse` for the required `-f`/`--file` and
`-m`/`--mode` flags, with `--stats` enabling running accuracy output. The UI in
`ui.py` presents each front, accepts a typed answer, compares it without regard
to case or surrounding whitespace, and gives immediate feedback. ANSI green
and red feedback is used only when output is an interactive terminal. Typing
`exit`, reaching end-of-input, or pressing Ctrl+C ends the session cleanly and
shows the summary.

`quiz_engine.py` implements the Strategy Pattern through `QuizMode`,
`SequentialMode`, `RandomMode`, and `AdaptiveMode`. `QuizModeFactory` maps CLI
mode names to strategy instances. Each mode exposes the same start, next-card,
and answer-recording operations, allowing the session and UI to work without
mode-specific branches. Randomness is injectable so the shuffle behavior can
be tested deterministically.

Adaptive mode asks every card once, then retries each missed card once after
the initial pass. This prioritizes known misses while guaranteeing termination
even if answers remain incorrect. Retries count as questions in the accuracy
denominator, while the missed-terms list includes each card front at most once.
The application currently retains mistakes for the active session only; it
does not persist learner history between launches.

## AI Collaboration Experience

The AI tool used was Copilot SDK in VS Code. Work was divided into bounded
requests for JSON loading, quiz-mode strategies, statistics, terminal
interaction, and quality verification. Each request included expected behavior
and constraints, such as supported schemas, case-insensitive answers, bounded
retries, typed functions, and friendly errors. `docs/ai_edit_log.md` records
five detailed scoped prompts, generated components, review decisions, and
outcomes. The entries are explicitly presented as work instructions derived
from the project brief, not as five separate user chat messages.

AI-generated code was not accepted solely on appearance. Tests exercised the
loader, strategy factory, retry behavior, statistics, CLI flags, and simulated
terminal sessions. The first integration run revealed that the UI's default
input callable was bound too early for the CLI test to substitute input, and
that one assertion did not account for a display newline. Resolving input at
call time made the test seam reliable without changing real terminal use; the
assertion was updated to check the displayed question independent of leading
whitespace. Both failures were caught by the test run and corrected before the
final verification.

## Engineering Practices and Testing

The code separates concerns by module: `main.py` parses arguments and handles
application-level load errors; `utils/file_handler.py` reads JSON;
`data_loader.py` validates records; `flashcard.py` represents domain data;
`quiz_engine.py` owns algorithms and session statistics; and `ui.py` owns
terminal interaction. Functions and methods use Python type hints. Errors are
handled at the boundary where they can be given context rather than hidden by
broad exception handling.

The pytest suite contains 25 tests across loader, mode, and integration files.
It checks both JSON formats, malformed input, missing files and fields,
unsupported structures, mode-factory selection, shuffle and adaptive behavior,
answer normalization, score calculation, early exit, interrupts, and CLI error
messages. The overall coverage command measured 99% (367 of 372 statements);
the six application modules together measured approximately 98% (218 of 223).
The remaining uncovered lines are exceptional operating-system file-read
branches. A generated HTML report is available at `htmlcov/index.html`, and
the tracked result is summarized in `docs/quality_report.md`.

Black's check passed with all 11 Python files unchanged after formatting.
Flake8 completed with no errors, and mypy completed with no type errors. The
Flake8 maximum line length is aligned with Black's 88-character default. The
project README documents installation, CLI use, the adaptive retry policy,
supported deck formats, and quality commands.

## Technical Challenges and Outcomes

The repository includes a Windows-invalid tracked path outside the target
starter directory. A normal checkout could not complete on this Windows
workspace. The repository was therefore checked out sparsely to
`project/starter`, restoring the starter's tracked files without removing its
folder structure. Only files within the requested starter were changed.

A second design issue was ensuring an adaptive game could not continue forever.
The strategy queues each first-pass miss for a single retry after the deck's
first pass. This is a deliberately bounded interpretation of prioritization:
the learner gets another attempt, the game ends predictably, and statistics
remain straightforward. The retry policy and accuracy denominator are
documented in the README and tested.

## Code Metrics and Reflection

The application contains 295 nonblank source lines, 10 classes, and 30
functions or methods across its six application modules. Test coverage,
formatting, linting, and static typing provide measurable checks beyond manual
inspection. The resulting design makes it possible to add another strategy
without moving selection branches into the CLI, while the factory keeps mode
selection in one place.

The main trade-off is that adaptive history is session-local. Persistent
progress, configurable retry limits, spaced repetition, deck authoring
validation, and packaging as an installed console command are reasonable
future enhancements, but were not needed for this lightweight tool. If
persistence is added, the design should specify user identity, storage format,
and how old results affect scheduling before implementation.

The project demonstrates a practical AI-assisted workflow: make requirements
explicit, ask for modular implementation, review edge cases, run tests, and
record evidence. Generated code is useful as a starting point, but boundary
conditions and measurable requirements still need direct tests. Separating
strategies from presentation, and validating data before quiz execution, also
makes the resulting code easier to extend and reason about.

## Conclusion

The completed application satisfies the requested CLI, JSON validation,
sequential/random/adaptive modes, session statistics, and modular architecture.
The test and quality checks passed, and the coverage target was exceeded. The
AI interaction log, user README, final report, and quality summary are included
with the source. Future work can build on the strategy interface without
rewriting the file loader or terminal loop.
