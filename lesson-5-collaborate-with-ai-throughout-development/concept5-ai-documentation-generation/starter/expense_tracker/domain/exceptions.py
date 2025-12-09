"""
Custom exceptions for expense tracker application.

This module defines domain-specific exceptions that provide clear error
context for different failure scenarios. All exceptions inherit from
ExpenseTrackerError to enable consistent error handling.

Example Usage:
    Catching specific errors:
        >>> from expense_tracker.domain.exceptions import DataLoadError, ValidationError
        >>> from expense_tracker.data.transaction_loader import CSVTransactionLoader
        >>>
        >>> loader = CSVTransactionLoader()
        >>> try:
        ...     transactions = loader.load('expenses.csv')
        ... except DataLoadError as e:
        ...     print(f"Cannot load file: {e}")
        ... except ValidationError as e:
        ...     print(f"Invalid data at row {e.row_number}: {e}")

    Catching all application errors:
        >>> from expense_tracker.domain.exceptions import ExpenseTrackerError
        >>> try:
        ...     # ... application code ...
        ...     pass
        ... except ExpenseTrackerError as e:
        ...     # Handle all application-specific errors
        ...     print(f"Application error: {e}")
        ... except Exception as e:
        ...     # Handle unexpected system errors
        ...     print(f"Unexpected error: {e}")

    Raising custom exceptions:
        >>> from expense_tracker.domain.exceptions import InvalidReportTypeError
        >>> available = ['category', 'monthly', 'top']
        >>> requested = 'unknown'
        >>> if requested not in available:
        ...     raise InvalidReportTypeError(requested, available)
        Traceback (most recent call last):
            ...
        InvalidReportTypeError: Unknown report type 'unknown'. Available: category, monthly, top

Exception Hierarchy:
    ExpenseTrackerError (base)
    ├── DataLoadError (file/data source issues)
    ├── ValidationError (data format/content issues)
    ├── InvalidReportTypeError (unknown report requested)
    └── EmptyDatasetError (no data to process)

Design Notes:
    - All exceptions inherit from ExpenseTrackerError for easy catching
    - ValidationError includes optional row_number for debugging
    - InvalidReportTypeError includes available options for user guidance
    - Use specific exceptions (not base ExpenseTrackerError) when raising
"""


class ExpenseTrackerError(Exception):
    """Base exception for all expense tracker errors."""
    pass


class DataLoadError(ExpenseTrackerError):
    """
    Raised when data cannot be loaded from source.

    Examples:
        - File not found
        - File cannot be read (permissions)
        - File is empty
    """
    pass


class ValidationError(ExpenseTrackerError):
    """
    Raised when data fails validation rules.

    Examples:
        - Invalid date format
        - Negative or zero amounts
        - Empty required fields
        - Invalid CSV structure
    """

    def __init__(self, message: str, row_number: int | None = None):
        """
        Initialize validation error.

        Args:
            message: Description of validation failure
            row_number: Optional row number where validation failed
        """
        self.row_number = row_number
        if row_number is not None:
            message = f"Row {row_number}: {message}"
        super().__init__(message)


class InvalidReportTypeError(ExpenseTrackerError):
    """
    Raised when an unknown report type is requested.

    Example:
        >>> raise InvalidReportTypeError('unknown_report', ['category', 'monthly'])
        InvalidReportTypeError: Unknown report type 'unknown_report'.
                                Available: category, monthly
    """

    def __init__(self, report_type: str, available_types: list[str]):
        """
        Initialize invalid report type error.

        Args:
            report_type: The invalid report type requested
            available_types: List of valid report type names
        """
        self.report_type = report_type
        self.available_types = available_types
        message = (
            f"Unknown report type '{report_type}'. "
            f"Available: {', '.join(available_types)}"
        )
        super().__init__(message)


class EmptyDatasetError(ExpenseTrackerError):
    """
    Raised when attempting to generate reports from empty transaction set.

    This can occur when:
        - No transactions loaded from file
        - All transactions filtered out by date/category
    """
    pass
