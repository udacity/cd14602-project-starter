"""
ReportEngine - Orchestrates report generation using pluggable strategies.

This module implements the Facade pattern to coordinate transaction loading
and report processing. It provides a simple interface that hides the complexity
of working with multiple components (loaders and report strategies).
"""

from typing import Any


class ReportEngine:
    """Orchestrates report generation using pluggable strategies."""

    def __init__(self, loader):
        """
        Initialize with a transaction loader.

        Args:
            loader: TransactionLoader instance for loading transaction data
        """
        self.loader = loader

    def generate_report(self, filepath: str, mode) -> Any:
        """
        Generate report from file using specified mode.

        Workflow:
        1. Load transactions from file using loader
        2. Process transactions using mode strategy
        3. Return the mode's result

        Args:
            filepath: Path to the transaction data file
            mode: ReportMode strategy for processing transactions

        Returns:
            Whatever the mode's process_transactions returns
            (the package's report strategies return the report text)

        Raises:
            Any exception the loader or the mode raises, unchanged
            (the package's CSVTransactionLoader raises DataLoadError
            and ValidationError)
        """
        transactions = self.loader.load(filepath)
        report_data = mode.process_transactions(transactions)
        return report_data
