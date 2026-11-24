"""
Unit tests for CSV transaction loader.

Test coverage:
    - Valid CSV file loading
    - Invalid CSV format handling
    - File not found errors
    - Data validation during loading
    - Empty file handling
"""

import unittest
from pathlib import Path
from datetime import date
from decimal import Decimal

from expense_tracker.data.transaction_loader import CSVTransactionLoader
from expense_tracker.domain.exceptions import DataLoadError, ValidationError
from expense_tracker.domain.models import Transaction


class TestCSVTransactionLoader(unittest.TestCase):
    """Test CSVTransactionLoader implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = CSVTransactionLoader()
        self.fixtures_dir = Path(__file__).parent / 'fixtures'

    def test_load_valid_csv(self):
        """Test loading a valid CSV file."""
        transactions = self.loader.load(str(self.fixtures_dir / 'valid_expenses.csv'))

        self.assertEqual(len(transactions), 6)
        self.assertTrue(all(isinstance(t, Transaction) for t in transactions))
        first = transactions[0]
        self.assertEqual(first.date, date(2025, 1, 15))
        self.assertIsInstance(first.amount, Decimal)
        self.assertEqual(first.amount, Decimal('42.50'))
        # The fixture pads this row's category and description with spaces: they are stripped
        self.assertEqual(first.category, 'Food')
        self.assertEqual(first.description, 'Lunch at cafe')

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading nonexistent file raises DataLoadError."""
        with self.assertRaises(DataLoadError):
            self.loader.load(str(self.fixtures_dir / 'does_not_exist.csv'))

    def test_load_invalid_csv_format_raises_error(self):
        """Test that invalid CSV structure raises ValidationError."""
        # fixtures/invalid_format.csv has no 'description' column
        with self.assertRaises(ValidationError):
            self.loader.load(str(self.fixtures_dir / 'invalid_format.csv'))

    def test_load_invalid_date_format_raises_error(self):
        """Test that invalid date format raises ValidationError."""
        # fixtures/invalid_date.csv: row 3 has the date 15/01/2025
        with self.assertRaises(ValidationError):
            self.loader.load(str(self.fixtures_dir / 'invalid_date.csv'))

    def test_load_negative_amount_raises_error(self):
        """Test that negative amounts raise ValidationError."""
        # fixtures/negative_amount.csv: the first data row (row 2) has the amount -10.00
        with self.assertRaises(ValidationError) as ctx:
            self.loader.load(str(self.fixtures_dir / 'negative_amount.csv'))
        self.assertEqual(ctx.exception.row_number, 2)

    def test_load_empty_file_returns_empty_list(self):
        """Test that empty CSV returns empty transaction list."""
        # fixtures/empty.csv holds the header row and no transactions
        transactions = self.loader.load(str(self.fixtures_dir / 'empty.csv'))
        self.assertEqual(transactions, [])

    def test_validate_source_existing_file(self):
        """Test validate_source returns True for existing file."""
        self.assertTrue(self.loader.validate_source(str(self.fixtures_dir / 'valid_expenses.csv')))

    def test_validate_source_nonexistent_file(self):
        """Test validate_source returns False for nonexistent file."""
        self.assertFalse(self.loader.validate_source(str(self.fixtures_dir / 'does_not_exist.csv')))

    def test_validation_error_includes_row_number(self):
        """Test that validation errors include row context."""
        # The header is row 1, so the bad date in the second data line is row 3
        with self.assertRaises(ValidationError) as ctx:
            self.loader.load(str(self.fixtures_dir / 'invalid_date.csv'))
        self.assertEqual(ctx.exception.row_number, 3)
        self.assertIn('Row 3', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
