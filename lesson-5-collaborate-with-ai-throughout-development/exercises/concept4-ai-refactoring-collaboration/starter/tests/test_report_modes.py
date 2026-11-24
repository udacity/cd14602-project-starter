"""
Unit tests for report mode strategies.

Test coverage:
    - CategorySummaryReport aggregation and formatting
    - MonthlyTotalsReport grouping and formatting
    - TopExpensesReport sorting and limiting
    - Empty dataset handling
    - Edge cases (single transaction, same amounts, etc.)
"""

import unittest
from datetime import date
from decimal import Decimal

from expense_tracker.domain.models import Transaction
from expense_tracker.reports.report_mode import (
    CategorySummaryReport,
    MonthlyTotalsReport,
    TopExpensesReport,
)
from expense_tracker.domain.exceptions import EmptyDatasetError


class TestCategorySummaryReport(unittest.TestCase):
    """Test CategorySummaryReport strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.report = CategorySummaryReport()
        self.sample_transactions = [
            Transaction(date(2025, 1, 15), Decimal('42.50'), 'Food', 'Lunch'),
            Transaction(date(2025, 1, 16), Decimal('120.00'), 'Transport', 'Metro'),
            Transaction(date(2025, 1, 17), Decimal('35.00'), 'Food', 'Groceries'),
        ]

    def test_process_transactions_groups_by_category(self):
        """Test that transactions are grouped by category correctly."""
        output = self.report.process_transactions(self.sample_transactions)

        self.assertIsInstance(output, str)
        self.assertIn('Food', output)
        self.assertIn('77.50', output)       # 42.50 + 35.00, one row for Food
        self.assertIn('120.00', output)
        self.assertIn('197.50', output)      # grand total

    def test_process_empty_transactions_raises_error(self):
        """Test that empty transaction list raises EmptyDatasetError."""
        with self.assertRaises(EmptyDatasetError):
            self.report.process_transactions([])

    def test_get_report_name(self):
        """Test that report name is returned correctly."""
        self.assertEqual(self.report.get_report_name(), 'Category Summary')

    def test_output_format_has_headers(self):
        """Test that output includes proper headers."""
        output = self.report.process_transactions(self.sample_transactions)

        self.assertIn('Category Summary', output)
        self.assertIn('TOTAL', output.upper())

    def test_categories_sorted_by_total(self):
        """Test that categories are sorted by total amount descending."""
        output = self.report.process_transactions(self.sample_transactions)

        # Transport (120.00) comes before Food (77.50)
        self.assertLess(output.index('Transport'), output.index('Food'))


class TestMonthlyTotalsReport(unittest.TestCase):
    """Test MonthlyTotalsReport strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.report = MonthlyTotalsReport()
        self.sample_transactions = [
            Transaction(date(2025, 1, 15), Decimal('100.00'), 'Food', 'Jan expense'),
            Transaction(date(2025, 2, 16), Decimal('200.00'), 'Transport', 'Feb expense'),
            Transaction(date(2025, 1, 20), Decimal('50.00'), 'Food', 'Another Jan'),
        ]

    def test_process_transactions_groups_by_month(self):
        """Test that transactions are grouped by month correctly."""
        output = self.report.process_transactions(self.sample_transactions)

        self.assertIsInstance(output, str)
        self.assertIn('2025-01', output)
        self.assertIn('150.00', output)      # 100.00 + 50.00, one row for January
        self.assertIn('2025-02', output)
        self.assertIn('200.00', output)
        self.assertIn('350.00', output)      # grand total

    def test_process_empty_transactions_raises_error(self):
        """Test that empty transaction list raises EmptyDatasetError."""
        with self.assertRaises(EmptyDatasetError):
            self.report.process_transactions([])

    def test_months_sorted_chronologically(self):
        """Test that months are sorted in chronological order."""
        output = self.report.process_transactions(self.sample_transactions)

        self.assertLess(output.index('2025-01'), output.index('2025-02'))


class TestTopExpensesReport(unittest.TestCase):
    """Test TopExpensesReport strategy."""

    def setUp(self):
        """Set up test fixtures."""
        self.report = TopExpensesReport(top_n=3)
        self.sample_transactions = [
            Transaction(date(2025, 1, 15), Decimal('50.00'), 'Food', 'Expense 1'),
            Transaction(date(2025, 1, 16), Decimal('200.00'), 'Transport', 'Expense 2'),
            Transaction(date(2025, 1, 17), Decimal('100.00'), 'Food', 'Expense 3'),
            Transaction(date(2025, 1, 18), Decimal('75.00'), 'Utilities', 'Expense 4'),
        ]

    def test_process_transactions_shows_top_n(self):
        """Test that only top N expenses are shown."""
        output = self.report.process_transactions(self.sample_transactions)

        self.assertIn('Expense 2', output)
        self.assertIn('Expense 3', output)
        self.assertIn('Expense 4', output)
        self.assertNotIn('Expense 1', output)   # the smallest of four, with top_n=3

    def test_top_expenses_sorted_by_amount(self):
        """Test that expenses are sorted by amount descending."""
        output = self.report.process_transactions(self.sample_transactions)

        self.assertLess(output.index('Expense 2'), output.index('Expense 3'))
        self.assertLess(output.index('Expense 3'), output.index('Expense 4'))

    def test_process_fewer_than_n_transactions(self):
        """Test handling when there are fewer transactions than top_n."""
        output = self.report.process_transactions(self.sample_transactions[:2])

        self.assertIn('Expense 1', output)
        self.assertIn('Expense 2', output)

    def test_invalid_top_n_raises_error(self):
        """Test that invalid top_n values raise ValueError."""
        with self.assertRaises(ValueError):
            TopExpensesReport(top_n=0)
        with self.assertRaises(ValueError):
            TopExpensesReport(top_n=-1)

    def test_get_report_name_includes_n(self):
        """Test that report name includes the top_n value."""
        self.assertIn('5', TopExpensesReport(top_n=5).get_report_name())


if __name__ == '__main__':
    unittest.main()
