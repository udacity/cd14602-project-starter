"""
Abstract interface for loading transaction data.

This module defines the contract for loading transactions from various sources
(CSV files, databases, APIs, etc.) while ensuring validation and error handling.
"""

from abc import ABC, abstractmethod
from typing import List

from expense_tracker.domain.models import Transaction
from expense_tracker.domain.exceptions import DataLoadError, ValidationError  # noqa: F401 (raised by implementations)


class TransactionLoader(ABC):
    """
    Abstract base class for loading and validating transaction data.

    This interface follows the Open/Closed Principle - new data sources can be
    added by creating new implementations without modifying existing code.

    Implementations must:
        1. Load data from source (file, database, API, etc.)
        2. Validate each transaction against business rules
        3. Convert raw data into Transaction objects
        4. Handle errors with appropriate exceptions

    Example implementation:
        >>> class CSVTransactionLoader(TransactionLoader):
        ...     def load(self, source: str) -> List[Transaction]:
        ...         # Read CSV file, parse rows, return transactions
        ...         pass
    """

    @abstractmethod
    def load(self, source: str) -> List[Transaction]:
        """
        Load transactions from specified source.

        This method is responsible for:
            - Opening/connecting to the data source
            - Reading and parsing data
            - Validating each record
            - Creating Transaction objects
            - Closing resources (file handles, connections)

        Args:
            source: Path or identifier for the data source.
                   For file-based loaders: absolute or relative file path
                   For database loaders: connection string or table name
                   For API loaders: endpoint URL

        Returns:
            List of validated Transaction objects in order of appearance.
            Returns empty list if source contains no valid transactions.

        Raises:
            DataLoadError: When source cannot be accessed or read.
                Examples:
                    - File not found
                    - Permission denied
                    - Network connection failure
                    - Empty file

            ValidationError: When data fails validation rules.
                Examples:
                    - Invalid date format (must be ISO 8601: YYYY-MM-DD)
                    - Invalid amount (must be positive decimal)
                    - Missing required fields (date, amount, category, description)
                    - Invalid CSV structure (wrong number of columns)

                Note: Include row_number in ValidationError for easier debugging

        Example:
            >>> loader = CSVTransactionLoader()
            >>> transactions = loader.load('expenses.csv')
            >>> print(f"Loaded {len(transactions)} transactions")
            Loaded 150 transactions

            >>> # Error handling
            >>> try:
            ...     transactions = loader.load('missing.csv')
            ... except DataLoadError as e:
            ...     print(f"Cannot load data: {e}")
            ... except ValidationError as e:
            ...     print(f"Invalid data at row {e.row_number}: {e}")

        Implementation Notes:
            - Use context managers for file/connection handling
            - Validate data before creating Transaction objects
            - Log warnings for skipped rows (if applicable)
            - Consider memory efficiency for large datasets
            - Preserve original transaction order
        """
        pass

    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """
        Check if source is accessible and readable without loading data.

        This method allows pre-flight validation before attempting to load
        large datasets.

        Args:
            source: Path or identifier for the data source

        Returns:
            True if source exists and is readable, False otherwise

        Raises:
            No exceptions - returns False for any access issues

        Example:
            >>> loader = CSVTransactionLoader()
            >>> if loader.validate_source('expenses.csv'):
            ...     transactions = loader.load('expenses.csv')
            ... else:
            ...     print("File not accessible")

        Implementation Notes:
            - Check file existence (for file-based loaders)
            - Check read permissions
            - Check file is not empty (optional)
            - Do NOT load actual data (performance)
        """
        pass


class CSVTransactionLoader(TransactionLoader):
    """
    Loads transactions from CSV files.

    Expected CSV format:
        date,amount,category,description
        2025-01-15,42.50,Food,Lunch at cafe
        2025-01-16,120.00,Transportation,Monthly metro pass

    CSV Requirements:
        - First row must be header (will be skipped)
        - Exactly 4 columns: date, amount, category, description
        - Date format: YYYY-MM-DD (ISO 8601)
        - Amount: Positive decimal number
        - No empty fields

    Example:
        >>> loader = CSVTransactionLoader()
        >>> transactions = loader.load('expenses.csv')
        >>> print(f"Loaded {len(transactions)} transactions")
        Loaded 150 transactions

    Raises:
        DataLoadError: If file cannot be accessed or is empty
        ValidationError: If CSV format or data is invalid
    """

    REQUIRED_COLUMNS = {'date', 'amount', 'category', 'description'}

    def load(self, source: str) -> List[Transaction]:
        """
        Load transactions from CSV file.

        Validates CSV structure and data, then creates Transaction objects.
        Fails fast on first validation error.

        Args:
            source: Path to CSV file (absolute or relative)

        Returns:
            List of validated Transaction objects in file order.
            Returns empty list if file contains only headers.

        Raises:
            DataLoadError: If file not found, cannot be read, or is empty
            ValidationError: If CSV structure invalid or data fails validation

        See base class for additional details.
        """
        raise NotImplementedError(
            "CSVTransactionLoader.load() is a planned stub: generate it in Exercise 2"
        )

    def validate_source(self, source: str) -> bool:
        """
        Check if CSV file is accessible and readable.

        Does not validate CSV content or structure - only checks file access.

        Args:
            source: Path to CSV file

        Returns:
            True if file exists and is readable, False otherwise

        See base class for additional details.
        """
        raise NotImplementedError(
            "CSVTransactionLoader.validate_source() is a planned stub: generate it in Exercise 2"
        )
