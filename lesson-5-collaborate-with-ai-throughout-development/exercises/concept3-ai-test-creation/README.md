# Concept 3: AI Test Creation

Generate a test suite for `ReportEngine` with an AI assistant, then make sure the tests check real behaviour. The
steps are on the **Exercise: AI Test Creation** page.

## What's here

- `starter/`: the finished project from Exercise 2, plus:
  - `report_engine.py`: `ReportEngine`, which loads transactions with a loader and passes them to a report mode;
    the module you test;
  - `test_report_engine_EXAMPLES.py`: example tests showing fixtures and mocks;
  - `validate_test_quality.py`: checks the test file you write: at least 2 test classes holding at least 10 tests, at
    least 3 happy-path tests whose names contain `success`, `generate`, `valid`, `happy` or `work`, fixtures, mocks,
    error tests, and docstrings on at least 60% of the tests.
- `solution/`: the same, plus one finished `test_report_engine.py`.
- `PROMPTS.md`: the solution video's prompts, matched to this exercise's files.

## Run it

```bash
cd starter
pytest validate_test_quality.py -v    # before you start: 1 failed (no test file yet), 7 skipped
```

Generate `test_report_engine.py` in `starter/`, then run it and the quality check until both pass:

```bash
pytest test_report_engine.py -v
pytest validate_test_quality.py -v
```

Then compare with the solution. In the Udacity workspace, the `solution` folder sits next to `starter`:

```bash
cd ../solution
pytest test_report_engine.py -v       # 29 passed
pytest validate_test_quality.py -v    # 8 passed
```
