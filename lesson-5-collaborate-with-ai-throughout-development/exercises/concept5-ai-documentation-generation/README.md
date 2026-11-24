# Concept 5: AI Documentation Generation

Write the project's documentation with an AI assistant, for each audience, and check it against the code. The steps
are on the **Exercise: AI Documentation Generation** page.

## What's here

- `starter/`: the finished expense tracker, cleaned up after Exercise 4, with no `README.md` or `ARCHITECTURE.md`
  yet. `documentation_requirements.md` lists what each document needs, and
  `tests/test_documentation_quality.py` checks them: the README's Installation and Usage sections and a
  code example with `python main.py`, the architecture document's modules (by name) and design pattern, and that every
  docstring example in the package runs.
- `solution/`: the same project with `README.md` (for users), `ARCHITECTURE.md` (for developers) and improved
  docstrings.
- `PROMPTS.md`: the solution video's prompts, matched to this exercise's files.

## Run it

```bash
cd starter
pytest tests/test_documentation_quality.py -v    # before you start: 10 failed, 3 passed
```

Write `README.md` and `ARCHITECTURE.md` in `starter/` (next to `main.py`) and fix the docstring examples until all 13
pass (`python -m doctest -v expense_tracker/cli.py` runs one module's examples), and check every command and example by
running it. Then compare with the solution. In the Udacity workspace, the `solution` folder sits next to `starter`:

```bash
cd ../solution
pytest tests/ -v    # 62 passed
python main.py examples/sample_expenses.csv --report monthly
```
