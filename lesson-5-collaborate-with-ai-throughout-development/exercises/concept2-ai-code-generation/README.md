# Concept 2: AI Code Generation

Generate the planned code with an AI assistant, one module at a time, until the tests pass. The steps are on the
**Exercise: AI Code Generation** page.

## What's here

- `starter/`: the project as Exercise 1 planned it. In `expense_tracker/data/transaction_loader.py`,
  `CSVTransactionLoader` is a stub, and in `expense_tracker/reports/report_mode.py` so are the three report
  strategies' `process_transactions` methods: they keep their docstrings and raise `NotImplementedError`. Everything
  else the CLI uses is implemented. `tests/` defines what the stubs must do.
- `solution/`: the same project with the loader and the three strategies implemented.
- `PROMPTS.md`: the solution video's prompts, matched to this exercise's files.

## Run it

```bash
cd starter
pytest tests/ -v    # before you start: 22 failed, 27 passed
```

Generate `CSVTransactionLoader`, then `CategorySummaryReport` and `MonthlyTotalsReport`, running the tests after each.
With those three done, 46 pass and 3 fail: `TopExpensesReport` is yours to implement. When all 49 pass, compare with
the solution:

```bash
cd ../solution
pytest tests/ -v    # 49 passed
python main.py examples/sample_expenses.csv --report category
```
