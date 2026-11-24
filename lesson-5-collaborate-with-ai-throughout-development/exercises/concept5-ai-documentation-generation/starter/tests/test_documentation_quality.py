"""
Tests to validate documentation quality.
Checks that required documentation exists and meets quality standards.

The README.md and ARCHITECTURE.md tests fail until you write those files
in this exercise folder (the folder that holds main.py).
"""
import pytest
from pathlib import Path
import ast
import re


# The exercise folder: this file sits in its tests/ folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
README = PROJECT_ROOT / 'README.md'
ARCHITECTURE = PROJECT_ROOT / 'ARCHITECTURE.md'
PACKAGE = PROJECT_ROOT / 'expense_tracker'


class TestReadmeQuality:
    """Validate README.md completeness."""

    def test_readme_exists(self):
        """README.md should exist."""
        assert README.exists(), """
        Create README.md with user-facing documentation.

        Should include:
        - Installation instructions
        - Usage examples
        - CSV format specification
        - Troubleshooting guide
        """

    def test_has_installation_section(self):
        """Should have installation instructions."""
        content = README.read_text() if README.exists() else ''
        assert re.search(r'##\s+Installation', content, re.IGNORECASE), """
        Add ## Installation section with setup instructions.
        """

    def test_has_usage_section(self):
        """Should have usage examples."""
        content = README.read_text() if README.exists() else ''
        assert re.search(r'##\s+Usage', content, re.IGNORECASE), """
        Add ## Usage section with examples of how to run the program.
        """

    def test_has_code_examples(self):
        """Should include code examples."""
        content = README.read_text() if README.exists() else ''
        assert '```' in content, """
        Include code examples in ```code blocks```.

        Example:
        ```bash
        python main.py examples/sample_expenses.csv --report category
        ```
        """

    def test_has_substantial_content(self):
        """README should have meaningful content."""
        content = README.read_text() if README.exists() else ''
        assert len(content) > 500, "README seems too brief - aim for comprehensive user guide"


class TestArchitectureDocQuality:
    """Validate ARCHITECTURE.md completeness."""

    def test_architecture_doc_exists(self):
        """ARCHITECTURE.md should exist."""
        assert ARCHITECTURE.exists(), """
        Create ARCHITECTURE.md with developer documentation.

        Should include:
        - Component descriptions
        - Design patterns used
        - Module responsibilities
        - Extension points
        """

    def test_describes_components(self):
        """Should describe system components."""
        content = ARCHITECTURE.read_text().lower() if ARCHITECTURE.exists() else ''
        assert 'component' in content or 'module' in content, """
        Describe the system components/modules and their responsibilities.
        """

    def test_explains_design_patterns(self):
        """Should mention design patterns used."""
        content = ARCHITECTURE.read_text().lower() if ARCHITECTURE.exists() else ''
        assert 'pattern' in content or 'strategy' in content, """
        Explain which design patterns are used (e.g., Strategy pattern for report modes).
        """

    def test_has_substantial_content(self):
        """Architecture doc should have meaningful content."""
        content = ARCHITECTURE.read_text() if ARCHITECTURE.exists() else ''
        assert len(content) > 500, "Architecture doc seems too brief - provide detailed explanation"


class TestSourceCodeDocumentation:
    """Validate that source code modules have docstrings."""

    def test_transaction_loader_has_module_docstring(self):
        """transaction_loader.py should have module-level docstring."""
        module_path = PACKAGE / 'data' / 'transaction_loader.py'
        tree = ast.parse(module_path.read_text())

        assert ast.get_docstring(tree) is not None, """
        Add module-level docstring to expense_tracker/data/transaction_loader.py.

        Example:
        \"\"\"
        Transaction Loader Module

        Provides CSV loading functionality for transaction data.
        Validates required fields and data types.
        \"\"\"
        """

    def test_report_modes_has_module_docstring(self):
        """report_mode.py should have module-level docstring."""
        module_path = PACKAGE / 'reports' / 'report_mode.py'
        tree = ast.parse(module_path.read_text())

        assert ast.get_docstring(tree) is not None, """
        Add module-level docstring to expense_tracker/reports/report_mode.py explaining the strategy pattern.
        """

    def test_classes_have_docstrings(self):
        """Major classes should have docstrings."""
        classes_without_docs = []

        for path in sorted(PACKAGE.rglob('*.py')):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and not ast.get_docstring(node):
                    classes_without_docs.append(f"{path.relative_to(PROJECT_ROOT)}::{node.name}")

        assert len(classes_without_docs) == 0, f"""
        These classes need docstrings: {', '.join(classes_without_docs)}

        Each class should explain its purpose and usage.
        """


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
