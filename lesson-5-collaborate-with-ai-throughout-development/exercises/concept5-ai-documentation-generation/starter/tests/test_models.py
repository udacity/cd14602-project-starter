"""
Unit tests for domain models.

Test coverage:
    - Transaction creation and validation
    - ValidationResult creation and methods
    - Edge cases (empty strings, negative amounts, etc.)
"""

import unittest
from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal

from expense_tracker.domain.models import Transaction, ValidationResult


class TestTransaction(unittest.TestCase):
    """Test Transaction model validation and behavior."""

    def test_valid_transaction_creation(self):
        """Test creating a valid transaction."""
        tx = Transaction(date(2025, 1, 15), Decimal('42.50'), 'Food', 'Lunch at cafe')
        self.assertEqual(tx.date, date(2025, 1, 15))
        self.assertEqual(tx.amount, Decimal('42.50'))
        self.assertEqual(tx.category, 'Food')
        self.assertEqual(tx.description, 'Lunch at cafe')

    def test_negative_amount_raises_error(self):
        """Test that negative amounts are rejected."""
        with self.assertRaises(ValueError):
            Transaction(date(2025, 1, 15), Decimal('-10.00'), 'Food', 'Refund')

    def test_zero_amount_raises_error(self):
        """Test that zero amounts are rejected."""
        with self.assertRaises(ValueError):
            Transaction(date(2025, 1, 15), Decimal('0'), 'Food', 'Free sample')

    def test_empty_category_raises_error(self):
        """Test that empty category is rejected."""
        with self.assertRaises(ValueError):
            Transaction(date(2025, 1, 15), Decimal('10.00'), '   ', 'Lunch')

    def test_empty_description_raises_error(self):
        """Test that empty description is rejected."""
        with self.assertRaises(ValueError):
            Transaction(date(2025, 1, 15), Decimal('10.00'), 'Food', '')

    def test_transaction_immutability(self):
        """Test that Transaction is immutable (frozen dataclass)."""
        tx = Transaction(date(2025, 1, 15), Decimal('42.50'), 'Food', 'Lunch')
        with self.assertRaises(FrozenInstanceError):
            tx.amount = Decimal('1.00')


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult model and factory methods."""

    def test_success_result(self):
        """Test creating successful validation result."""
        result = ValidationResult.success()
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_failure_result(self):
        """Test creating failed validation result."""
        result = ValidationResult.failure('Invalid date format', 'Amount is empty')
        self.assertFalse(result.is_valid)
        self.assertEqual(result.errors, ['Invalid date format', 'Amount is empty'])

    def test_failure_with_row_number(self):
        """Test validation result with row context."""
        result = ValidationResult.failure('Invalid date format', row_number=5)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.row_number, 5)


if __name__ == '__main__':
    unittest.main()
