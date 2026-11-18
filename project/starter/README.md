# Flashcard Quizzer

A lightweight terminal application for practicing JSON flashcard decks. It
supports sequential, shuffled, and adaptive sessions, reports accuracy and
missed terms, and validates decks before the quiz begins.

## Requirements and installation

Python 3.10 or later is recommended. From this directory, create and activate a
virtual environment, then install the project tools:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## Run a quiz

```powershell
python main.py --help
python main.py --mode sequential --file data/glossary.json
python main.py -m random -f data/glossary.json
python main.py -m adaptive -f data/python_basics.json
```

`-f`/`--file` selects the required JSON deck. `-m`/`--mode` accepts
`sequential`, `random`, or `adaptive` and defaults to sequential. `--stats`
prints running accuracy after each answer; a final summary is always shown.
Type `exit` or press Ctrl+C to finish early. Answers are compared
case-insensitively, with surrounding whitespace ignored. Correct/incorrect
feedback is green/red in interactive terminals.

Adaptive mode asks every card once, then retries each missed card once after
the first pass. This prioritizes known misses without allowing an unbounded
loop. The final accuracy counts every answered question, including retries,
and the missed-terms list includes each card front missed at least once.

## Deck format

Both supported JSON shapes contain objects with non-empty string `front` and
`back` fields:

```json
[
  {"front": "API", "back": "Application Programming Interface"}
]
```

```json
{
  "cards": [
    {"front": "API", "back": "Application Programming Interface"}
  ]
}
```

Malformed JSON, unsupported shapes, missing fields, and unreadable/missing files
produce a concise error instead of a traceback.

## Project structure

- `main.py`: argparse entry point and friendly loader-error handling
- `data_loader.py`, `flashcard.py`: deck validation and domain model
- `utils/file_handler.py`: UTF-8 JSON file reading and file errors
- `quiz_engine.py`: quiz strategies, factory, session, and statistics
- `ui.py`: terminal interaction, feedback, and summaries
- `tests/`: loader, strategy, integration, and CLI tests
- `data/`: sample decks in both supported formats
- `docs/`: AI interaction log, report, and design-pattern reference

## Quality checks

```powershell
python -m pytest --cov=. --cov-report=term-missing
python -m pytest --cov=. --cov-report=html
python -m black --check .
python -m flake8 .
python -m mypy .
```

The test suite targets more than 80% coverage. The HTML coverage report is
written to `htmlcov/index.html`.

Measured results for this submission are recorded in
[`docs/quality_report.md`](docs/quality_report.md). The final project report and
the five scoped AI interaction examples are in `docs/final_report.md` and
`docs/ai_edit_log.md`.
