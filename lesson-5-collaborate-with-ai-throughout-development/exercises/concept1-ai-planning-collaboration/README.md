# Concept 1: AI Planning Collaboration

Plan the expense tracker's architecture with an AI assistant before any code exists. The steps are on the
**Exercise: AI Planning Collaboration** page.

## What's here

- `starter/test_planning_process.py`: checks the three planning files you write in `starter/`:
  `architecture_plan.md` (alternatives, trade-offs, the selected architecture, module responsibilities),
  `interfaces.py` (the interfaces, as ABCs or Protocols, with docstrings) and `project_structure.txt` (the folder
  layout, with comments).
- `solution/`: one finished plan: the three files, and the project skeleton it leads to (`expense_tracker/` with the
  interfaces and stubs, and `tests/`, which Exercise 2 makes pass).
- `PROMPTS.md`: the solution video's prompts, matched to this exercise's files.

## Run it

```bash
cd starter
pytest test_planning_process.py -v    # before you start: 5 failed, 9 skipped
```

Write the three files, then run it again until all 14 pass. Then compare with the solution. In the Udacity workspace, the `solution` folder sits next to `starter`:

```bash
cd ../solution
pytest test_planning_process.py -v    # 14 passed
```
