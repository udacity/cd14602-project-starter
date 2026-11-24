# Concept 5: AI Documentation Generation

Write the project's documentation with an AI assistant, for each audience, and check it against the code. The steps
are on the **Exercise: AI Documentation Generation** page.

## What's here

- `starter/`: the finished expense tracker, cleaned up after Exercise 4, with no `README.md` or `ARCHITECTURE.md`
  yet. `documentation_requirements.md` lists what each document needs, and
  `tests/test_documentation_quality.py` checks them.
- `solution/`: the same project with `README.md` (for users), `ARCHITECTURE.md` (for developers) and improved
  docstrings.
- `PROMPTS.md`: the solution video's prompts, matched to this exercise's files.

## Run it

```bash
cd starter
pytest tests/test_documentation_quality.py -v    # before you start: 9 failed, 3 passed
```

Write `README.md` and `ARCHITECTURE.md` in `starter/` (next to `main.py`) until all 12 pass, and check every command
and example in them by running it. Then compare with the solution:

```bash
cd ../solution
pytest tests/ -v    # 61 passed
python main.py examples/sample_expenses.csv --report monthly
```
