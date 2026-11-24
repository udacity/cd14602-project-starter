# Concept 4: AI Refactoring Collaboration

Refactor `cli_interface_v1.py` with an AI assistant without changing what it does: the tests pass before you start
and must still pass after every change. The steps are on the **Exercise: AI Refactoring Collaboration** page.

## What's here

- `starter/`: the project so far, plus:
  - `cli_interface_v1.py`: a display module that works but repeats its report and error blocks, writes its widths,
    separators and titles as literals, and has no type hints. It is a standalone module: it takes a dictionary
    (`{"mode": ..., "data": ..., "total": ...}`), not the package's report text;
  - `test_cli_interface.py`: its 6 tests. They use `cli_interface_v2.py` once it exists (an import error in it fails them), else v1.
- `solution/`: the same, plus one refactoring: `cli_interface_v2.py` and `refactoring_notes.md`.
- `PROMPTS.md`: the solution video's prompts, matched to this exercise's files.

## Run it

```bash
cd starter
pytest test_cli_interface.py -v    # baseline, against v1: 6 passed
```

Create `cli_interface_v2.py` and run the same command after each change: it must stay at 6 passed, now against v2.
Then compare with the solution. In the Udacity workspace, the `solution` folder sits next to `starter`:

```bash
cd ../solution
pytest test_cli_interface.py -v    # 6 passed, against v2
```
