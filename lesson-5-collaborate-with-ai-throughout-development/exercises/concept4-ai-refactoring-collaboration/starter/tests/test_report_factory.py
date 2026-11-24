"""
Unit tests for report factory.

Test coverage:
    - Creating registered report types
    - Invalid report type handling
    - Custom report registration
    - Available types listing
"""

import unittest

from expense_tracker.reports.report_factory import ReportFactory
from expense_tracker.reports.report_mode import (
    ReportMode,
    CategorySummaryReport,
    MonthlyTotalsReport,
    TopExpensesReport,
)
from expense_tracker.domain.exceptions import InvalidReportTypeError


class TestReportFactory(unittest.TestCase):
    """Test ReportFactory functionality."""

    def setUp(self):
        """Save the registry, so a test that registers a report leaves no trace."""
        self.saved_registry = dict(ReportFactory._registry)

    def tearDown(self):
        """Restore the registry."""
        ReportFactory._registry.clear()
        ReportFactory._registry.update(self.saved_registry)

    def test_create_category_report(self):
        """Test creating CategorySummaryReport."""
        self.assertIsInstance(ReportFactory.create_report('category'), CategorySummaryReport)

    def test_create_monthly_report(self):
        """Test creating MonthlyTotalsReport."""
        self.assertIsInstance(ReportFactory.create_report('monthly'), MonthlyTotalsReport)

    def test_create_top_report(self):
        """Test creating TopExpensesReport."""
        self.assertIsInstance(ReportFactory.create_report('top'), TopExpensesReport)

    def test_create_top_report_with_custom_n(self):
        """Test creating TopExpensesReport with custom top_n."""
        report = ReportFactory.create_report('top', top_n=20)
        self.assertIsInstance(report, TopExpensesReport)
        self.assertEqual(report.top_n, 20)

    def test_create_invalid_report_raises_error(self):
        """Test that invalid report type raises InvalidReportTypeError."""
        with self.assertRaises(InvalidReportTypeError) as ctx:
            ReportFactory.create_report('weekly')
        self.assertIn('category', str(ctx.exception))   # the message lists the valid types

    def test_get_available_types(self):
        """Test getting list of available report types."""
        self.assertEqual(ReportFactory.get_available_types(), ['category', 'monthly', 'top'])

    def test_register_custom_report(self):
        """Test registering a custom report type."""
        class CustomReport(ReportMode):
            def process_transactions(self, transactions):
                return 'custom report'

            def get_report_name(self):
                return 'Custom'

        ReportFactory.register_report('custom', CustomReport)
        self.assertIsInstance(ReportFactory.create_report('custom'), CustomReport)
        self.assertIn('custom', ReportFactory.get_available_types())

    def test_register_duplicate_name_raises_error(self):
        """Test that registering duplicate name raises ValueError."""
        with self.assertRaises(ValueError):
            ReportFactory.register_report('category', CategorySummaryReport)

    def test_register_non_reportmode_raises_error(self):
        """Test that registering non-ReportMode class raises TypeError."""
        class NotAReport:
            pass

        with self.assertRaises(TypeError):
            ReportFactory.register_report('not_a_report', NotAReport)
        self.assertNotIn('not_a_report', ReportFactory.get_available_types())


if __name__ == '__main__':
    unittest.main()
