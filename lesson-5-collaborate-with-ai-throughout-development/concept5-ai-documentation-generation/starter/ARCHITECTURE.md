# Expense Tracker Architecture

## Overview

### System Purpose
The Expense Tracker is a command-line application that generates analytical reports from expense transaction data stored in CSV files. It provides multiple report types (category summaries, monthly trends, top expenses) through a flexible, extensible architecture.

### Key Design Principles

1. **Open/Closed Principle**: The system is open for extension (new report types, data sources) but closed for modification (existing code doesn't need changes).

2. **Dependency Inversion**: High-level modules (CLI, report orchestration) depend on abstractions (ABCs), not concrete implementations.

3. **Single Responsibility**: Each module has one clearly defined purpose:
   - Data loading and validation
   - Report generation strategies
   - CLI orchestration
   - Presentation formatting

4. **Separation of Concerns**: Clear boundaries between layers:
   - **Domain**: Core business logic and models
   - **Data**: Loading and validation
   - **Reports**: Analysis strategies
   - **Presentation**: Output formatting
   - **CLI**: User interface coordination

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Input                           │
│              (CLI: expenses.csv --report category)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   ExpenseTrackerCLI                          │
│               (cli.py - Orchestrator)                        │
│  • Parse arguments                                           │
│  • Coordinate components                                     │
│  • Handle errors                                             │
└─────┬─────────────────────────┬─────────────────────────────┘
      │                         │
      │ 1. Load data           │ 2. Create report
      ▼                         ▼
┌──────────────────┐      ┌─────────────────────┐
│ TransactionLoader│      │   ReportFactory     │
│    (ABC)         │      │  (Factory Pattern)  │
└──────┬───────────┘      └──────┬──────────────┘
       │                         │
       │ implements              │ creates
       ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐
│CSVTransactionLoader │   │    ReportMode       │
│  (data/loader)      │   │      (ABC)          │
│  • Read CSV         │   └──────┬──────────────┘
│  • Validate rows    │          │
│  • Create models    │          │ implements
└──────┬──────────────┘          ▼
       │                   ┌──────────────────────────┐
       │ creates           │ CategorySummaryReport    │
       ▼                   │ MonthlyTotalsReport      │
┌─────────────────┐        │ TopExpensesReport        │
│  Transaction    │        │  (Strategy Pattern)      │
│  (Domain Model) │◄───────┤  • Process transactions  │
└─────────────────┘        │  • Calculate aggregates  │
                           │  • Format output         │
                           └──────┬───────────────────┘
                                  │
                                  │ 3. Generate report
                                  ▼
                           ┌─────────────────────┐
                           │  Formatted Report   │
                           │   (String output)   │
                           └─────────────────────┘
                                  │
                                  ▼
                           ┌─────────────────────┐
                           │  Terminal Display   │
                           └─────────────────────┘

Data Flow:
1. User → CLI → CSVTransactionLoader → Transaction objects
2. CLI → ReportFactory → Specific ReportMode strategy
3. ReportMode → Process transactions → Formatted string → Terminal
```

## Design Patterns

### 1. Strategy Pattern (Report Generation)

**Location**: `expense_tracker/reports/report_mode.py`

**Purpose**: Encapsulate different report algorithms, allowing them to be selected and swapped at runtime without changing client code.

**Implementation**:
```python
# Abstract strategy
class ReportMode(ABC):
    @abstractmethod
    def process_transactions(self, transactions: List[Transaction]) -> str:
        pass

# Concrete strategies
class CategorySummaryReport(ReportMode):
    def process_transactions(self, transactions: List[Transaction]) -> str:
        # Group by category, calculate totals

class MonthlyTotalsReport(ReportMode):
    def process_transactions(self, transactions: List[Transaction]) -> str:
        # Group by month, show trends
```

**Benefits**:
- Add new report types without modifying existing code
- Each report strategy is independently testable
- Strategies can be reused across different interfaces (CLI, web, API)
- Runtime selection based on user input

**Trade-offs**:
- More classes to maintain (acceptable for 3-10 report types)
- Slight overhead from polymorphism (negligible for this use case)

### 2. Factory Pattern (Report Creation)

**Location**: `expense_tracker/reports/report_factory.py`

**Purpose**: Centralize object creation, map string identifiers to concrete classes, and validate report types.

**Implementation**:
```python
class ReportFactory:
    _registry = {
        'category': CategorySummaryReport,
        'monthly': MonthlyTotalsReport,
        'top': TopExpensesReport,
    }

    @classmethod
    def create_report(cls, report_type: str, **kwargs) -> ReportMode:
        if report_type not in cls._registry:
            raise InvalidReportTypeError(report_type, cls.get_available_types())
        return cls._registry[report_type](**kwargs)
```

**Benefits**:
- Single source of truth for available report types
- Easy to add new reports via registration
- Type validation with helpful error messages
- Supports parameterized strategies (e.g., `top_n` for TopExpensesReport)

### 3. Abstract Base Classes (Dependency Inversion)

**Location**:
- `expense_tracker/data/transaction_loader.py` (TransactionLoader ABC)
- `expense_tracker/reports/report_mode.py` (ReportMode ABC)

**Purpose**: Define contracts that implementations must fulfill, enabling dependency inversion and testability.

**Implementation**:
```python
class TransactionLoader(ABC):
    @abstractmethod
    def load(self, source: str) -> List[Transaction]:
        """Load transactions from source."""
        pass

    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """Check if source is accessible."""
        pass
```

**Benefits**:
- High-level code depends on interfaces, not implementations
- Easy to mock for testing (inject fake loaders/reports)
- Enforces contract compliance via abstract methods
- Self-documenting through comprehensive docstrings

### 4. Dependency Injection

**Location**: `expense_tracker/cli.py`

**Purpose**: CLI depends on abstractions (TransactionLoader, ReportMode), not concrete implementations. Dependencies are created and injected at runtime.

**Implementation**:
```python
# CLI creates dependencies but works with abstractions
loader = CSVTransactionLoader()  # Could be DatabaseLoader, APILoader, etc.
transactions = loader.load(file_path)

report = ReportFactory.create_report(report_type)  # Could be any ReportMode
output = report.process_transactions(transactions)
```

**Benefits**:
- Testable (inject mock loaders/reports)
- Flexible (swap implementations without changing CLI)
- Clear separation of concerns

## Module Descriptions

### Domain Layer (`expense_tracker/domain/`)

#### `models.py`
**Purpose**: Core business entities representing the problem domain.

**Key Classes**:
- `Transaction`: Immutable expense transaction with validation
  - Attributes: `date`, `amount`, `category`, `description`
  - Validation: Positive amounts, non-empty fields
  - Immutable via `@dataclass(frozen=True)` for safety

- `ValidationResult`: Structured validation feedback
  - Used internally for complex validation scenarios

**Dependencies**: None (pure domain logic)

**Extension Points**: Add new domain models (e.g., `Budget`, `User`) as needed

#### `exceptions.py`
**Purpose**: Domain-specific exceptions for clear error handling.

**Key Classes**:
- `ExpenseTrackerError`: Base exception for all application errors
- `DataLoadError`: File access, parsing failures
- `ValidationError`: Data integrity violations (with row number context)
- `InvalidReportTypeError`: Unknown report type requested
- `EmptyDatasetError`: No data available for reporting

**Design**: Exception hierarchy enables granular error handling in CLI

### Data Layer (`expense_tracker/data/`)

#### `transaction_loader.py`
**Purpose**: Abstract interface for loading transaction data from various sources.

**Key Classes**:
- `TransactionLoader` (ABC): Contract for data loaders
  - `load(source: str) -> List[Transaction]`: Load and validate data
  - `validate_source(source: str) -> bool`: Pre-flight check

- `CSVTransactionLoader`: CSV file implementation
  - Validates CSV structure (required columns)
  - Parses rows into Transaction objects
  - Comprehensive error handling with row numbers
  - Uses `Decimal` for accurate monetary values

**Public Interface**:
```python
loader = CSVTransactionLoader()
if loader.validate_source('expenses.csv'):
    transactions = loader.load('expenses.csv')
```

**Dependencies**:
- `domain.models.Transaction`: Creates validated transaction objects
- `domain.exceptions`: Raises DataLoadError, ValidationError

**Extension Points**: Implement TransactionLoader for new sources
- `DatabaseTransactionLoader` (SQL queries)
- `APITransactionLoader` (REST endpoints)
- `JSONTransactionLoader` (JSON files)

### Reports Layer (`expense_tracker/reports/`)

#### `report_mode.py`
**Purpose**: Report generation strategies implementing different analytics.

**Key Classes**:
- `ReportMode` (ABC): Strategy interface
  - `process_transactions(transactions) -> str`: Generate formatted report
  - `get_report_name() -> str`: Human-readable report name

- `CategorySummaryReport`: Group by category, show totals/averages
  - Aggregates spending by category
  - Sorted by total (descending)
  - Shows count, total, average per category

- `MonthlyTotalsReport`: Group by month, show trends over time
  - Aggregates spending by month (YYYY-MM format)
  - Chronological ordering
  - Useful for budget tracking

- `TopExpensesReport`: Show N largest individual transactions
  - Configurable top_n parameter (default: 10)
  - Shows full transaction details
  - Useful for identifying outliers

**Public Interface**:
```python
report = CategorySummaryReport()
output = report.process_transactions(transactions)
print(output)
```

**Dependencies**:
- `domain.models.Transaction`: Input data type
- `domain.exceptions.EmptyDatasetError`: Validation

**Extension Points**: New report strategies
- `WeeklySummaryReport`: Weekly spending patterns
- `CategoryTrendsReport`: Category spending over time
- `BudgetComparisonReport`: Actual vs. budget analysis

#### `report_factory.py`
**Purpose**: Centralized report strategy creation and registration.

**Key Classes**:
- `ReportFactory`: Factory with registry pattern
  - `create_report(report_type, **kwargs) -> ReportMode`: Create strategy
  - `get_available_types() -> list[str]`: List available reports
  - `register_report(name, strategy_class)`: Add custom reports

**Public Interface**:
```python
# Standard usage
report = ReportFactory.create_report('category')

# Parameterized creation
report = ReportFactory.create_report('top', top_n=20)

# Extension
ReportFactory.register_report('custom', CustomReport)
```

**Dependencies**:
- `reports.report_mode`: All report strategy classes
- `domain.exceptions.InvalidReportTypeError`: Validation

**Extension Points**: Register custom reports without modifying factory

### Presentation Layer (`expense_tracker/presentation/`)

#### `formatters.py`
**Purpose**: Reusable terminal output formatting utilities.

**Key Functions**:
- `format_currency(amount: Decimal) -> str`: Format monetary values
- `format_header(title: str) -> str`: Report titles with underlines
- `format_separator(width: int, char: str) -> str`: Visual separators
- `truncate_text(text: str, max_length: int) -> str`: Handle long text

**Design**: Pure functions, no state, highly reusable

**Dependencies**: None

**Extension Points**: Add new formatting utilities as needed

### CLI Layer (`expense_tracker/cli.py`)

#### `cli.py`
**Purpose**: Orchestrate all components to fulfill user requests.

**Key Classes**:
- `ExpenseTrackerCLI`: Main application coordinator
  - `_create_argument_parser()`: Configure CLI arguments
  - `run(args) -> int`: Main execution flow with error handling

**Execution Flow**:
1. Parse command-line arguments (file path, report type, options)
2. Validate file exists
3. Create loader and load transactions
4. Validate non-empty dataset
5. Create report strategy via factory
6. Generate and display report
7. Return exit code (0=success, 1-3=various errors)

**Public Interface**:
```python
cli = ExpenseTrackerCLI()
exit_code = cli.run(['expenses.csv', '--report', 'monthly'])
```

**Dependencies**:
- `data.transaction_loader.CSVTransactionLoader`: Data loading
- `reports.report_factory.ReportFactory`: Report creation
- `domain.exceptions`: All exception types for error handling

**Error Handling Strategy**:
- Granular exception catching with specific exit codes
- User-friendly error messages to stderr
- Fail fast with clear feedback

**Extension Points**: Add new CLI arguments for filtering, date ranges, etc.

## Adding New Features

### How to Add a New Report Type

Follow these steps to add a new report strategy (e.g., "Weekly Summary Report"):

#### Step 1: Create Report Strategy Class

Create a new class in `expense_tracker/reports/report_mode.py`:

```python
class WeeklySummaryReport(ReportMode):
    """
    Groups transactions by week and shows totals.

    Shows spending patterns by week (ISO week numbers),
    useful for short-term budget tracking.
    """

    def process_transactions(self, transactions: List[Transaction]) -> str:
        """Generate weekly summary report."""
        if not transactions:
            raise EmptyDatasetError("Cannot generate report from empty transaction list")

        # Group transactions by week
        from collections import defaultdict
        weekly_data = defaultdict(list)

        for transaction in transactions:
            # ISO week format: 2025-W03
            week_key = transaction.date.strftime('%G-W%V')
            weekly_data[week_key].append(transaction.amount)

        # Calculate aggregates
        weekly_stats = {}
        for week, amounts in weekly_data.items():
            weekly_stats[week] = {
                'total': sum(amounts),
                'count': len(amounts),
                'average': sum(amounts) / len(amounts)
            }

        # Sort chronologically
        sorted_weeks = sorted(weekly_stats.items())

        # Format output (similar to MonthlyTotalsReport)
        lines = []
        lines.append("Weekly Summary Report")
        lines.append("=" * 50)
        # ... format table rows ...

        return '\n'.join(lines)

    def get_report_name(self) -> str:
        """Return 'Weekly Summary'."""
        return "Weekly Summary"
```

#### Step 2: Register in Factory

Add to `ReportFactory._registry` in `expense_tracker/reports/report_factory.py`:

```python
_registry: Dict[str, Type[ReportMode]] = {
    'category': CategorySummaryReport,
    'monthly': MonthlyTotalsReport,
    'top': TopExpensesReport,
    'weekly': WeeklySummaryReport,  # Add this line
}
```

#### Step 3: Update CLI Choices

Add to argument parser in `expense_tracker/cli.py`:

```python
parser.add_argument(
    '--report',
    type=str,
    default='category',
    choices=['category', 'monthly', 'top', 'weekly'],  # Add 'weekly'
    help='Type of report to generate (default: category)'
)
```

Also update the epilog documentation:

```python
epilog="""
Available report types:
  category - Summary by expense category
  monthly  - Totals by month
  top      - Largest individual expenses
  weekly   - Totals by week
"""
```

#### Step 4: Add Tests

Create tests in `tests/test_report_modes.py`:

```python
def test_weekly_summary_report():
    """Test weekly aggregation and formatting."""
    from datetime import date
    from decimal import Decimal

    transactions = [
        Transaction(date(2025, 1, 6), Decimal('100'), 'Food', 'Week 1'),
        Transaction(date(2025, 1, 8), Decimal('50'), 'Food', 'Week 1'),
        Transaction(date(2025, 1, 13), Decimal('200'), 'Transport', 'Week 2'),
    ]

    report = WeeklySummaryReport()
    output = report.process_transactions(transactions)

    assert '2025-W01' in output
    assert '2025-W02' in output
    assert '$150.00' in output  # Week 1 total
    assert '$200.00' in output  # Week 2 total
```

#### Step 5: Update Documentation

Update `README.md` examples section to include the new report type.

### How to Add a New Data Source

Follow these steps to add support for JSON files:

#### Step 1: Implement TransactionLoader

Create `expense_tracker/data/json_loader.py`:

```python
import json
from pathlib import Path
from typing import List
from datetime import date
from decimal import Decimal

from expense_tracker.data.transaction_loader import TransactionLoader
from expense_tracker.domain.models import Transaction
from expense_tracker.domain.exceptions import DataLoadError, ValidationError


class JSONTransactionLoader(TransactionLoader):
    """
    Loads transactions from JSON files.

    Expected JSON format:
    {
        "transactions": [
            {
                "date": "2025-01-15",
                "amount": "42.50",
                "category": "Food",
                "description": "Lunch"
            }
        ]
    }
    """

    def load(self, source: str) -> List[Transaction]:
        """Load transactions from JSON file."""
        file_path = Path(source)

        if not file_path.exists():
            raise DataLoadError(f"File not found: {source}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'transactions' not in data:
                raise ValidationError("JSON missing 'transactions' array")

            transactions = []
            for idx, record in enumerate(data['transactions'], start=1):
                transaction = self._validate_and_create(record, idx)
                transactions.append(transaction)

            return transactions

        except json.JSONDecodeError as e:
            raise DataLoadError(f"Invalid JSON in {source}: {e}") from e
        except ValidationError:
            raise
        except Exception as e:
            raise DataLoadError(f"Error reading {source}: {e}") from e

    def validate_source(self, source: str) -> bool:
        """Check if JSON file is accessible."""
        try:
            file_path = Path(source)
            return file_path.exists() and file_path.is_file()
        except Exception:
            return False

    def _validate_and_create(self, record: dict, index: int) -> Transaction:
        """Validate JSON record and create Transaction."""
        # Similar validation logic to CSVTransactionLoader
        # ...
        return Transaction(...)
```

#### Step 2: Update CLI to Support Multiple Formats

Modify `expense_tracker/cli.py` to auto-detect file type:

```python
def _get_loader_for_file(self, file_path: Path) -> TransactionLoader:
    """Select appropriate loader based on file extension."""
    from expense_tracker.data.json_loader import JSONTransactionLoader

    suffix = file_path.suffix.lower()
    if suffix == '.csv':
        return CSVTransactionLoader()
    elif suffix == '.json':
        return JSONTransactionLoader()
    else:
        raise DataLoadError(f"Unsupported file type: {suffix}")

# In run() method:
loader = self._get_loader_for_file(file_path)
transactions = loader.load(str(file_path))
```

#### Step 3: Add Tests

Create `tests/test_json_loader.py` following the pattern in `test_csv_loader.py`.

## Design Decisions

### Why Strategy Pattern for Reports?

**Decision**: Use Strategy pattern instead of a single monolithic report function with conditionals.

**Alternatives Considered**:
1. **Single function with if/elif branches**
   - Violates Open/Closed Principle
   - Difficult to test individual report types
   - Hard to maintain as report types grow

2. **Separate standalone functions**
   - No polymorphism for runtime selection
   - Harder to extend (no interface contract)
   - No consistent error handling

**Rationale**:
- Each report type is complex enough to warrant its own class (50-100 lines)
- New report types are a likely extension point
- Strategy pattern provides clear extension mechanism
- Independent testing and debugging per report type
- Consistent interface enforced by ABC

**Trade-offs Accepted**:
- More classes (minimal overhead for 3-10 report types)
- Slight complexity vs. simple functions (worthwhile for extensibility)

### Why Abstract Base Classes for Interfaces?

**Decision**: Use ABC for TransactionLoader and ReportMode instead of duck typing or protocols.

**Alternatives Considered**:
1. **Duck typing (no explicit interface)**
   - No contract enforcement
   - Harder to understand requirements
   - Runtime errors instead of early validation

2. **Protocol (structural typing)**
   - Works well for simple cases
   - Less explicit for complex contracts
   - No runtime enforcement

**Rationale**:
- ABCs enforce contract compliance at class definition time
- Comprehensive docstrings serve as implementation guide
- Clear error messages when contract violated
- Better IDE support and type checking
- Explicit is better than implicit (Python principle)

**Trade-offs Accepted**:
- Slightly more verbose than duck typing (worthwhile for clarity)
- Requires `from abc import ABC, abstractmethod`

### Why CSV Instead of Database?

**Decision**: Default to CSV files, designed for extensibility to databases.

**Rationale**:
- **Simplicity**: CSV is universal, no database setup required
- **Portability**: CSV files are easily shared, backed up, versioned
- **Low barrier to entry**: Users can create CSV with Excel, scripts, exports
- **Extensible**: TransactionLoader ABC makes database support straightforward
- **Use case fit**: Expense tracking typically involves small datasets (<10K rows)

**When to Add Database Support**:
- Datasets exceed 100K transactions (CSV parsing becomes slow)
- Need concurrent access from multiple users
- Require complex queries (filters, joins, aggregations)
- Need transaction integrity (ACID properties)

**Extension Path**: Implement `DatabaseTransactionLoader` following the same ABC contract.

### Why Not Use External Reporting Library?

**Decision**: Implement custom report generation instead of using pandas, tabulate, or similar.

**Rationale**:
- **Learning**: This is an educational project demonstrating design patterns
- **Control**: Full control over formatting, aggregation logic
- **Simplicity**: No external dependencies (besides standard library)
- **Transparency**: Code is understandable without library-specific knowledge
- **Lightweight**: Small binary size, fast startup

**Trade-offs Accepted**:
- Manual implementation of aggregations (acceptable for simple reports)
- Custom formatting code (minimal, ~50 lines per report)

**When to Reconsider**:
- Need for complex statistical analysis (use pandas)
- Advanced visualizations needed (use matplotlib/plotly)
- Large dataset performance issues (use pandas/dask)

## Testing Strategy

### Test Organization

Tests are organized by module in the `tests/` directory:
- `test_models.py`: Domain model validation
- `test_csv_loader.py`: CSV loading and validation
- `test_report_modes.py`: Report strategy algorithms
- `test_report_factory.py`: Factory creation and registration
- `test_cli.py`: CLI argument parsing and orchestration

### Testing Approach

#### Unit Tests (Primary Strategy)

Each module is tested in isolation using dependency injection and mocking:

```python
# Example: Testing ReportMode without real data loading
def test_category_summary_report():
    # Arrange: Create test data directly
    transactions = [
        Transaction(date(2025, 1, 15), Decimal('42.50'), 'Food', 'Lunch'),
        Transaction(date(2025, 1, 16), Decimal('35.00'), 'Food', 'Dinner'),
    ]

    # Act: Test report strategy in isolation
    report = CategorySummaryReport()
    output = report.process_transactions(transactions)

    # Assert: Verify formatting and calculations
    assert 'Food' in output
    assert '$77.50' in output  # Total
```

#### Mocking Strategy

**What We Mock**:
- File system operations in CLI tests (use temporary files)
- TransactionLoader in CLI tests (inject fake loaders)

**What We Don't Mock**:
- Domain models (Transaction) - use real instances
- Report strategies - test real implementations
- Formatting functions - test actual output

**Rationale**: Mock external dependencies (I/O), test internal logic directly.

#### Test Data Fixtures

Reusable test data in `tests/fixtures/`:
- `sample_expenses.csv`: Valid CSV for integration tests
- `invalid_date.csv`: Test validation error handling
- `empty.csv`: Test empty file handling

### Test Coverage Goals

- **Domain models**: 100% (simple, critical)
- **Data loaders**: 95% (comprehensive validation testing)
- **Report strategies**: 90% (test main logic, edge cases)
- **CLI**: 85% (argument parsing, error handling)

### Running Tests

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/test_report_modes.py

# Run with coverage
pytest --cov=expense_tracker --cov-report=html

# Run with verbose output
pytest -v
```

### Testing New Features

When adding new features, follow this pattern:

1. **Write tests first (TDD approach)**:
   ```python
   def test_new_report_type():
       # Arrange: Create test data
       # Act: Run new report
       # Assert: Verify output
   ```

2. **Test edge cases**:
   - Empty input
   - Single transaction
   - Duplicate values
   - Boundary conditions

3. **Test error handling**:
   - Invalid input types
   - Missing required data
   - Validation failures

4. **Test integration**:
   - End-to-end CLI flow
   - Factory registration
   - Error propagation

## Contributing

When modifying this architecture:

1. **Preserve design patterns**: Don't break Strategy, Factory, or ABC patterns
2. **Maintain separation of concerns**: Keep layers independent
3. **Follow SOLID principles**: Especially Open/Closed and Dependency Inversion
4. **Update this document**: Keep architecture docs synchronized with code
5. **Write tests**: Maintain test coverage above 85%
6. **Document design decisions**: Explain why, not just what

For questions about architectural decisions, see "Design Decisions" section above or consult the development team.
