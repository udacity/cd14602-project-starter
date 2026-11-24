"""
Integration tests for CLI orchestrator.

Test coverage:
    - Successful report generation
    - Error handling (file not found, invalid report type)
    - Argument parsing
    - Exit codes
"""

import unittest
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from expense_tracker.cli import ExpenseTrackerCLI


class TestExpenseTrackerCLI(unittest.TestCase):
    """Test CLI orchestrator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.cli = ExpenseTrackerCLI()
        self.fixtures_dir = Path(__file__).parent / 'fixtures'
        self.valid_csv = str(self.fixtures_dir / 'valid_expenses.csv')
        self.empty_csv = str(self.fixtures_dir / 'empty.csv')
        self.missing_csv = str(self.fixtures_dir / 'does_not_exist.csv')

    def run_cli(self, args):
        """Run the CLI with args; return (exit code, stdout, stderr)."""
        with patch('sys.stdout', new_callable=StringIO) as out, \
                patch('sys.stderr', new_callable=StringIO) as err:
            code = self.cli.run(args)
        return code, out.getvalue(), err.getvalue()

    def test_run_with_valid_file_returns_zero(self):
        """Test that successful run returns exit code 0."""
        code, _, err = self.run_cli([self.valid_csv])
        self.assertEqual(code, 0, err)

    def test_run_with_nonexistent_file_returns_one(self):
        """Test that file not found returns exit code 1."""
        code, _, _ = self.run_cli([self.missing_csv])
        self.assertEqual(code, 1)

    def test_run_with_invalid_report_type_returns_two(self):
        """Test that invalid report type returns exit code 2."""
        # argparse rejects a report type outside --report's choices and exits with status 2
        with patch('sys.stderr', new_callable=StringIO):
            with self.assertRaises(SystemExit) as ctx:
                self.cli.run([self.valid_csv, '--report', 'weekly'])
        self.assertEqual(ctx.exception.code, 2)

    def test_run_with_empty_dataset_returns_three(self):
        """Test that empty dataset returns exit code 3."""
        code, _, err = self.run_cli([self.empty_csv])
        self.assertEqual(code, 3, err)

    def test_argument_parser_default_report_type(self):
        """Test that default report type is 'category'."""
        args = self.cli.parser.parse_args(['expenses.csv'])
        self.assertEqual(args.report, 'category')

    def test_argument_parser_custom_report_type(self):
        """Test parsing custom report type."""
        args = self.cli.parser.parse_args(['expenses.csv', '--report', 'monthly'])
        self.assertEqual(args.report, 'monthly')

    def test_argument_parser_top_n_flag(self):
        """Test parsing --top-n flag."""
        args = self.cli.parser.parse_args(['expenses.csv', '--report', 'top', '--top-n', '5'])
        self.assertEqual(args.top_n, 5)

    def test_output_displayed_to_stdout(self):
        """Test that report output goes to stdout."""
        code, out, err = self.run_cli([self.valid_csv])
        self.assertEqual(code, 0, err)
        self.assertIn('Food', out)
        self.assertEqual(err, '')

    def test_errors_displayed_to_stderr(self):
        """Test that errors go to stderr."""
        code, out, err = self.run_cli([self.missing_csv])
        self.assertIn('File not found', err)
        self.assertEqual(out, '')


if __name__ == '__main__':
    unittest.main()
