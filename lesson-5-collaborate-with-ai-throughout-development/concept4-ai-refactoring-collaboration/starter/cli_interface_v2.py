"""
CLI Interface Module - Version 2

Displays reports in terminal with formatting and color.
Refactored version with improved structure and type safety.

Improvements from v1:
- Added type hints for better IDE support and type checking
- Extracted helper methods to reduce code duplication
- Defined class constants for magic values (widths, separators)
- Better separation of concerns with focused helper methods
"""
from typing import Dict, Any


class CLIInterface:
    """Terminal interface for displaying expense reports.

    Uses class constants for formatting widths and separators to maintain
    consistent display across all report types.
    """

    # Display width constants
    REPORT_WIDTH = 50
    LABEL_WIDTH = 20
    AMOUNT_WIDTH = 10

    # Separator characters
    SEPARATOR_HEAVY = "="
    SEPARATOR_LIGHT = "-"
    SEPARATOR_ERROR = "!"

    def display_report(self, report_data: Dict[str, Any]) -> None:
        """Display formatted report to terminal.

        Args:
            report_data: Dictionary containing 'mode', 'data', and 'total' keys.
                        mode: 'summary' or 'monthly'
                        data: dict of category/month to amount
                        total: total amount across all categories/months
        """
        mode = report_data.get('mode', 'unknown')

        if mode == 'summary':
            self._display_formatted_report(
                "EXPENSE SUMMARY BY CATEGORY",
                report_data
            )
        elif mode == 'monthly':
            self._display_formatted_report(
                "MONTHLY EXPENSE TOTALS",
                report_data
            )
        else:
            print(f"\nError: Unknown report mode '{mode}'\n")

    def _display_formatted_report(self, title: str, report_data: Dict[str, Any]) -> None:
        """Display a formatted report with header, data rows, and total.

        Args:
            title: The report title to display in the header
            report_data: Dictionary containing 'data' and 'total' keys
        """
        self._print_header(title)

        data = report_data.get('data', {})
        for label, amount in sorted(data.items()):
            self._print_data_row(label, amount)

        self._print_separator(self.SEPARATOR_LIGHT)
        total = report_data.get('total', 0.0)
        self._print_data_row('TOTAL', total)
        self._print_footer()

    def _print_header(self, title: str) -> None:
        """Print report header with title.

        Args:
            title: The title to display
        """
        print("\n" + self.SEPARATOR_HEAVY * self.REPORT_WIDTH)
        print(f"  {title}")
        print(self.SEPARATOR_HEAVY * self.REPORT_WIDTH)

    def _print_data_row(self, label: str, amount: float) -> None:
        """Print a single data row with label and amount.

        Args:
            label: The row label (category, month, or 'TOTAL')
            amount: The monetary amount to display
        """
        print(f"  {label:{self.LABEL_WIDTH}s} ${amount:>{self.AMOUNT_WIDTH}.2f}")

    def _print_separator(self, char: str) -> None:
        """Print a separator line.

        Args:
            char: The character to use for the separator
        """
        print(char * self.REPORT_WIDTH)

    def _print_footer(self) -> None:
        """Print report footer."""
        print(self.SEPARATOR_HEAVY * self.REPORT_WIDTH + "\n")

    def display_error(self, error: Any) -> None:
        """Display error message to terminal.

        Args:
            error: Error object or string to display
        """
        error_str = str(error)

        if 'file' in error_str.lower() or 'not found' in error_str.lower():
            self._print_error_box("ERROR: File Not Found", error_str)
        elif 'invalid' in error_str.lower() or 'value' in error_str.lower():
            self._print_error_box("ERROR: Invalid Data", error_str)
        else:
            self._print_error_box("ERROR", error_str)

    def _print_error_box(self, title: str, message: str) -> None:
        """Print an error message in a formatted box.

        Args:
            title: The error title (e.g., 'ERROR: File Not Found')
            message: The error message details
        """
        print("\n" + self.SEPARATOR_ERROR * self.REPORT_WIDTH)
        print(f"  {title}")
        print(f"  {message}")
        print(self.SEPARATOR_ERROR * self.REPORT_WIDTH + "\n")
