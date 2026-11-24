# Concept 2: AI Code Generation

**Exercise Goal**: Generate production-quality implementations of the planned `CSVTransactionLoader` and report strategies, so the tests in `tests/` pass.

The starter holds the plan from Exercise 1 as stubs: `expense_tracker/data/transaction_loader.py` and `expense_tracker/reports/report_mode.py` define every class and method with its docstring, and the methods you generate raise `NotImplementedError`. The tests in `tests/test_csv_loader.py` and `tests/test_report_modes.py` define what each one must do.

## Prompt Examples (Adjust as needed)

**Prompt 1** (Generate CSVTransactionLoader):

```xml
<role>
Senior Python developer implementing planned architecture
</role>

<task>
Implement CSVTransactionLoader in expense_tracker/data/transaction_loader.py,
following the interface specification and the docstrings already in the file
</task>

<interface_specification>
from abc import ABC, abstractmethod
from typing import List

from expense_tracker.domain.models import Transaction
from expense_tracker.domain.exceptions import DataLoadError, ValidationError

class TransactionLoader(ABC):
    @abstractmethod
    def load(self, source: str) -> List[Transaction]:
        """Load transactions from the source.

        Returns:
            List of Transaction objects (date: datetime.date, amount: Decimal,
            category: str, description: str), in file order

        Raises:
            DataLoadError: If the file doesn't exist, can't be read, or is empty
            ValidationError: If the CSV is missing a column or a row is invalid
                             (pass row_number=... so the message names the row)
        """

    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """Return True if the file exists and is readable, without loading it."""
</interface_specification>

<requirements>
<functionality>
- Implement CSVTransactionLoader.load and CSVTransactionLoader.validate_source
- CSV format: date,amount,category,description (header row required)
- Validate all four fields are present for each row
- Parse date as YYYY-MM-DD into datetime.date
- Convert amount to Decimal and validate it's positive
- Strip whitespace from all fields
- Provide row-specific error messages for validation failures (the header is row 1)
- A file with only the header row returns an empty list
</functionality>

<error_handling>
- DataLoadError with informative message including the file path
- ValidationError for missing columns with specific column names
- ValidationError for row-level issues, with row_number set
- ValidationError for empty/missing required fields
- ValidationError for invalid amount (not numeric or not positive)
- NO bare except clauses
</error_handling>

<code_quality>
- Keep the module, class and method docstrings already in the file
- Full type hints on all signatures
- Use the class constant REQUIRED_COLUMNS
- Extract validation logic to private helper method
</code_quality>
</requirements>

<constraints>
- Python standard library only (csv, datetime, decimal, pathlib)
- Module should be under 150 lines
- Follow PEP 8 style guide
- No external dependencies
</constraints>
```

**Prompt 2** (Generate ReportMode Strategies):

```xml
<task>
Implement CategorySummaryReport.process_transactions and
MonthlyTotalsReport.process_transactions in expense_tracker/reports/report_mode.py
</task>

<interface_specification>
from abc import ABC, abstractmethod
from typing import List

from expense_tracker.domain.models import Transaction
from expense_tracker.domain.exceptions import EmptyDatasetError

class ReportMode(ABC):
    @abstractmethod
    def process_transactions(self, transactions: List[Transaction]) -> str:
        """Process transactions and return the formatted report as text.

        Raises:
            EmptyDatasetError: If transactions is empty
        """

    @abstractmethod
    def get_report_name(self) -> str:
        """Return name of this report mode."""
</interface_specification>

<requirements>
<strategy_1_category_summary>
- Group transactions by category
- Show total, count and average for each category
- Sort categories by total, highest first
- Start with a "Category Summary Report" title and end with a TOTAL row
</strategy_1_category_summary>

<strategy_2_monthly_totals>
- Group transactions by month (YYYY-MM, from transaction.date)
- Show total, count and average for each month
- Sort months chronologically
- End with a TOTAL row
</strategy_2_monthly_totals>

<both_strategies>
- Raise EmptyDatasetError for an empty transaction list
- Follow Strategy pattern (interchangeable implementations)
- Use Decimal for all money calculations; format amounts with 2 decimals
- Keep the docstrings already in the file
- Use defaultdict or similar for clean grouping logic
</both_strategies>
</requirements>

<code_quality>
- Clear variable names (no abbreviations)
- Each strategy class under 50 lines
</code_quality>
```

**Prompt 3** (Quick Quality Check):

```xml
<task>
Review the generated expense_tracker/data/transaction_loader.py and expense_tracker/reports/report_mode.py
for common AI code generation issues from Lesson 2
</task>

<lesson_2_patterns_to_check>
- Phantom dependencies: Are we importing anything that doesn't exist?
- Over-generic code: Is error handling too broad (bare except)?
- Inconsistent patterns: Do similar operations use similar code?
- Missing edge cases: Empty files, single items, duplicates?
- Type safety: Are type hints complete and accurate?
</lesson_2_patterns_to_check>

<action>
List any issues found. If none, confirm code is ready for testing.
</action>
```

`TopExpensesReport.process_transactions` is still a stub after these prompts: implementing it is yours (its three tests in `tests/test_report_modes.py` fail until you do).
