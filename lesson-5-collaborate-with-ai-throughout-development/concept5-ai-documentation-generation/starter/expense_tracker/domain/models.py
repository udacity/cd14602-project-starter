"""
Domain models for expense tracker application.

This module contains core data structures representing the business domain.
These are immutable, validated data classes that represent the core business
concepts in the expense tracking system.

Example Usage:
    Creating a valid transaction:
        >>> from datetime import date
        >>> from decimal import Decimal
        >>> from expense_tracker.domain.models import Transaction
        >>>
        >>> tx = Transaction(
        ...     date=date(2025, 1, 15),
        ...     amount=Decimal('42.50'),
        ...     category='Food',
        ...     description='Lunch at cafe'
        ... )
        >>> print(f"{tx.description}: ${tx.amount}")
        Lunch at cafe: $42.50

    Validation errors:
        >>> # Invalid: negative amount
        >>> tx = Transaction(
        ...     date=date(2025, 1, 15),
        ...     amount=Decimal('-10.00'),
        ...     category='Food',
        ...     description='Invalid'
        ... )
        Traceback (most recent call last):
            ...
        ValueError: Amount must be positive, got -10.00

        >>> # Invalid: empty category
        >>> tx = Transaction(
        ...     date=date(2025, 1, 15),
        ...     amount=Decimal('42.50'),
        ...     category='',
        ...     description='Invalid'
        ... )
        Traceback (most recent call last):
            ...
        ValueError: Category cannot be empty

    Immutability:
        >>> tx.amount = Decimal('100.00')
        Traceback (most recent call last):
            ...
        dataclasses.FrozenInstanceError: cannot assign to field 'amount'

Key Classes:
    - Transaction: Immutable expense transaction record
    - ValidationResult: Structured validation feedback

Design Notes:
    - All models are frozen dataclasses (immutable by default)
    - Validation occurs in __post_init__ (fails fast on creation)
    - Decimal used for monetary values (not float) for precision
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    """
    Immutable representation of a financial transaction.

    Attributes:
        date: Transaction date
        amount: Transaction amount (positive for expenses)
        category: Expense category (e.g., 'Food', 'Transportation')
        description: Human-readable transaction description

    Example:
        >>> tx = Transaction(
        ...     date=date(2025, 1, 15),
        ...     amount=Decimal('42.50'),
        ...     category='Food',
        ...     description='Lunch at cafe'
        ... )
    """
    date: date
    amount: Decimal
    category: str
    description: str

    def __post_init__(self) -> None:
        """
        Validate transaction data after initialization.

        Raises:
            ValueError: If amount is negative or zero
            ValueError: If category or description is empty
        """
        if self.amount <= 0:
            raise ValueError(f"Amount must be positive, got {self.amount}")

        if not self.category or not self.category.strip():
            raise ValueError("Category cannot be empty")

        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of data validation operation.

    This class encapsulates the outcome of validating data (e.g., CSV rows),
    providing structured feedback including error messages and context.
    Use the factory methods success() and failure() for convenient creation.

    Attributes:
        is_valid: Whether validation passed (True) or failed (False)
        errors: List of validation error messages (empty list if valid)
        row_number: Optional row number for CSV validation context

    Example:
        Creating validation results:
            >>> # Success case
            >>> result = ValidationResult.success()
            >>> assert result.is_valid
            >>> assert result.errors == []

            >>> # Failure case
            >>> result = ValidationResult.failure(
            ...     'Invalid date format',
            ...     'Amount must be positive',
            ...     row_number=5
            ... )
            >>> assert not result.is_valid
            >>> assert len(result.errors) == 2
            >>> print(result.row_number)
            5

        Using in validation logic:
            >>> def validate_row(row_data: dict, row_num: int) -> ValidationResult:
            ...     errors = []
            ...     if not row_data.get('amount'):
            ...         errors.append('Amount is required')
            ...     if errors:
            ...         return ValidationResult.failure(*errors, row_number=row_num)
            ...     return ValidationResult.success()

    See Also:
        - Use with CSVTransactionLoader for row-by-row validation
        - Prefer raising ValidationError for immediate failures (fail-fast)
    """
    is_valid: bool
    errors: list[str]
    row_number: Optional[int] = None

    @classmethod
    def success(cls) -> 'ValidationResult':
        """Create a successful validation result."""
        return cls(is_valid=True, errors=[])

    @classmethod
    def failure(cls, *errors: str, row_number: Optional[int] = None) -> 'ValidationResult':
        """
        Create a failed validation result.

        Args:
            *errors: Variable number of error messages
            row_number: Optional row number for context

        Returns:
            ValidationResult with is_valid=False
        """
        return cls(is_valid=False, errors=list(errors), row_number=row_number)
