"""
Tests to validate documentation quality.
Checks that required documentation exists and meets quality standards.

The README.md and ARCHITECTURE.md tests fail until you write those files
in this exercise folder (the folder that holds main.py), and the docstring
examples test fails until every example in the package's docstrings runs.
"""
import pytest
from pathlib import Path
import ast
import re
import subprocess
import sys


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
        """Should include code examples that show how to run the tool."""
        content = README.read_text() if README.exists() else ''
        assert '```' in content and 'python main.py' in content, """
        Include code examples in ```code blocks```, with the command that runs the tool (python main.py ...).

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
        """Should describe the real modules."""
        content = ARCHITECTURE.read_text().lower() if ARCHITECTURE.exists() else ''
        modules = ['transaction_loader', 'report_mode', 'report_factory', 'formatters', 'models', 'cli']
        named = [m for m in modules if m in content]
        assert len(named) >= 3, f"""
        Describe the system's modules and their responsibilities, by name: found {named or 'none'} of
        {modules}; name at least 3.
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

    def test_docstring_examples_run(self):
        """Every docstring example should run and show what the code prints."""
        problems, examples = [], {}
        for path in sorted(PACKAGE.rglob('*.py')):
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            # The command learners run, from the exercise folder (examples/sample_expenses.csv resolves there),
            # one process per module so one example's side effects can't reach another module's or these tests
            result = subprocess.run([sys.executable, '-m', 'doctest', '-v', rel], cwd=PROJECT_ROOT,
                                    capture_output=True, text=True)
            tried = re.search(r'^(\d+) tests? in \d+ items?', result.stdout, re.M)
            examples[rel] = int(tried.group(1)) if tried else 0
            for line, source in re.findall(r'^File ".*", line (\d+), in \S+\nFailed example:\n\s+(.*)$',
                                           result.stdout, re.M):
                problems.append(f"{rel}:{line}: {source.strip()[:70]}")
            if result.returncode != 0 and not tried:
                problems.append(f"{rel}: doctest could not run it: {(result.stderr or result.stdout).strip()[-120:]}")

        assert not problems, f"""
        {len(problems)} docstring example(s) don't run as written. From this folder, see one module's in full:
            python -m doctest -v expense_tracker/cli.py
        Fix each so it runs and shows what the code really prints (examples/sample_expenses.csv is a file that exists).

        """ + "\n".join(problems)

        required = ['expense_tracker/data/transaction_loader.py', 'expense_tracker/reports/report_mode.py',
                    'expense_tracker/reports/report_factory.py', 'expense_tracker/cli.py']
        without = [rel for rel in required if not examples.get(rel)]
        assert not without, f"""
        These modules need at least one docstring example that runs: {', '.join(without)}
        """


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
