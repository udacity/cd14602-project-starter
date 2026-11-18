# Quality and Coverage Report

**Run date:** 2026-11-18  
**Python:** 3.12.10  
**Test runner:** pytest 9.2.0

## Results

| Check | Result |
|---|---|
| `python -m pytest --cov=. --cov-report=term-missing` | 25 passed |
| Total measured coverage | 99% (367 of 372 statements) |
| Application module coverage | 98% (218 of 223 statements) |
| `python -m pytest --cov=. --cov-report=html` | 25 passed; HTML generated |
| `python -m black --check .` | Passed; 11 Python files unchanged |
| `python -m flake8 .` | Passed; no lint errors |
| `python -m mypy .` | Passed; no type errors |
| `python main.py --help` | Passed |
| Adaptive example with `exit` input | Passed; displayed summary and exited cleanly |

The HTML report is generated at `htmlcov/index.html` when the coverage command
is run. The project `.gitignore` excludes generated HTML and caches; this
tracked summary preserves the measured submission result.

## Notes

Application modules comprise `main.py`, `flashcard.py`, `data_loader.py`,
`quiz_engine.py`, `ui.py`, and `utils/file_handler.py`. The remaining uncovered
application statements are in exceptional file-read branches, such as
permission and operating-system errors. Normal file-not-found, invalid UTF-8,
malformed JSON, and invalid deck structures are covered by tests.
