"""
Tests for the file processor with real dependencies.

These tests describe the fixed behaviour. Run them on the starter first: some fail, and each
failing test's docstring says which problem it points at. Fix file_processor.py until they all pass.
clean_dataframe(df) is imported inside the tests that use it, so until it exists only those tests fail.

These tests show:
1. Real libraries that actually exist
2. Proper error handling and logging
3. Specific exception types instead of generic ones
"""

import pytest
import os
import shutil
import tempfile
import json
import pandas as pd
from file_processor import process_uploaded_files


class TestRealDependencies:
    """Tests that verify real libraries are used."""
    
    def test_uses_real_pandas_library(self):
        """Verify that pandas (a real library) is used."""
        # Pandas should be importable and functional
        df = pd.DataFrame({'test': [1, 2, 3]})
        assert len(df) == 3
        assert 'test' in df.columns
    
    def test_uses_standard_library_modules(self):
        """Verify that standard library modules are used."""
        # These should all be available in Python standard library
        import os
        import logging
        
        # os module functionality should work
        assert hasattr(os, 'path')
        assert hasattr(os, 'listdir')
        
        # logging module should be functional
        assert hasattr(logging, 'getLogger')
        assert hasattr(logging, 'info')
    
    def test_no_phantom_library_imports(self):
        """Fails on the starter: it imports the phantom libraries advanced_file_processor and data_cleaner_pro. Passes once fixed."""
        import ast
        import inspect
        import file_processor

        tree = ast.parse(inspect.getsource(file_processor))
        imported = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}

        # Should not import phantom libraries (a comment or docstring may still name them)
        for phantom in ["advanced_file_processor", "data_cleaner_pro"]:
            assert phantom not in imported, f"Should not import phantom library: {phantom}"

class TestImprovedFileProcessing:
    """Tests for improved file processing functionality."""
    
    def setup_method(self):
        """Set up test files for each test."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test CSV file
        self.csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(self.csv_file, 'w') as f:
            f.write("name,age,city\nJohn,25,NYC\nJane,30,LA\n")
        
        # Create test JSON file
        self.json_file = os.path.join(self.temp_dir, "test.json")
        with open(self.json_file, 'w') as f:
            json.dump([
                {"name": "Alice", "age": 28, "city": "Chicago"},
                {"name": "Bob", "age": 35, "city": "Boston"}
            ], f)
    
    def teardown_method(self):
        """Remove the test files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_processes_csv_files_with_pandas(self):
        """Fails on the starter: the mock fallbacks return made-up data instead of the file's. Passes once fixed."""
        result = process_uploaded_files([self.csv_file])
        
        assert len(result) == 1
        df = result[0]
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # Two rows of data
        assert 'name' in df.columns
        assert 'age' in df.columns
        assert 'city' in df.columns
    
    def test_processes_json_files_with_pandas(self):
        """Fails on the starter: the mock fallbacks return made-up data instead of the file's. Passes once fixed."""
        result = process_uploaded_files([self.json_file])
        
        assert len(result) == 1
        df = result[0]
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2  # Two rows of data
        assert 'name' in df.columns
    
    def test_handles_multiple_file_types(self):
        """Test processing multiple file types together."""
        result = process_uploaded_files([self.csv_file, self.json_file])
        
        assert len(result) == 2
        for df in result:
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
    
    def test_nonexistent_file_handling(self):
        """Fails on the starter: a missing file still returns a (mock) result instead of nothing. Passes once fixed."""
        nonexistent_file = os.path.join(self.temp_dir, "does_not_exist.csv")
        
        # Should handle gracefully and return empty list
        result = process_uploaded_files([nonexistent_file])
        assert result == []


class TestSpecificErrorHandling:
    """Tests for specific error handling instead of generic exceptions."""
    
    def setup_method(self):
        """A folder for this test's files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Remove the test files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_not_found_error_handling(self):
        """Fails on the starter: a missing file still returns a (mock) result instead of nothing. Passes once fixed."""
        # Non-existent file should be handled specifically
        result = process_uploaded_files(["nonexistent.csv"])
        assert result == []  # Should handle gracefully
    
    def test_pandas_specific_error_handling(self):
        """Test handling of pandas-specific errors."""
        # Create an invalid CSV file
        invalid_csv = os.path.join(self.temp_dir, "invalid.csv")
        
        with open(invalid_csv, 'w') as f:
            f.write("this,is,not\nvalid,csv,format,with,too,many,columns\n")
        
        # Should handle pandas parsing errors gracefully
        result = process_uploaded_files([invalid_csv])
        # Might succeed or fail depending on pandas parsing, but shouldn't crash
        assert isinstance(result, list)
    
    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        # This test might not work on all systems, so we'll skip if needed
        try:
            # Try to create a file we can't read
            no_permission_file = os.path.join(self.temp_dir, "no_permission.csv")
            
            with open(no_permission_file, 'w') as f:
                f.write("test,data\n1,2\n")
            
            # Remove read permission (Unix-like systems)
            if hasattr(os, 'chmod'):
                os.chmod(no_permission_file, 0o000)
                try:
                    result = process_uploaded_files([no_permission_file])
                    assert isinstance(result, list)  # Should handle gracefully
                finally:
                    # Restore permission for cleanup
                    os.chmod(no_permission_file, 0o644)
        except (OSError, PermissionError):
            # Skip this test if we can't manipulate permissions
            pytest.skip("Cannot test permission errors on this system")


class TestDataCleaning:
    """Tests for the data cleaning functionality."""
    
    def test_clean_dataframe_removes_empty_rows(self):
        """Fails on the starter: no clean_dataframe(df), only the phantom clean_dataset. Passes once fixed."""
        from file_processor import clean_dataframe
        df = pd.DataFrame({
            'name': ['Alice', None, 'Bob'],
            'age': [25, None, 30],
            'city': ['NYC', None, 'LA']
        })
        
        cleaned = clean_dataframe(df)
        
        # Should remove the completely empty/null row
        assert len(cleaned) == 2
        assert 'Alice' in cleaned['name'].values
        assert 'Bob' in cleaned['name'].values
    
    def test_clean_dataframe_removes_empty_columns(self):
        """Fails on the starter: no clean_dataframe(df), only the phantom clean_dataset. Passes once fixed."""
        from file_processor import clean_dataframe
        df = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'empty_col': [None, None],
            'age': [25, 30]
        })
        
        cleaned = clean_dataframe(df)
        
        # Should remove the empty column
        assert 'empty_col' not in cleaned.columns
        assert 'name' in cleaned.columns
        assert 'age' in cleaned.columns
    
    def test_clean_dataframe_strips_whitespace(self):
        """Fails on the starter: no clean_dataframe(df), only the phantom clean_dataset. Passes once fixed."""
        from file_processor import clean_dataframe
        df = pd.DataFrame({
            'name': ['  Alice  ', '  Bob  '],
            'city': [' NYC ', ' LA ']
        })
        
        cleaned = clean_dataframe(df)
        
        # Whitespace should be stripped
        assert cleaned['name'].iloc[0] == 'Alice'
        assert cleaned['name'].iloc[1] == 'Bob'
        assert cleaned['city'].iloc[0] == 'NYC'
        assert cleaned['city'].iloc[1] == 'LA'


class TestLoggingInsteadOfPrint:
    """Tests that verify proper logging is used instead of print statements."""
    
    def test_uses_logging_module(self):
        """Fails on the starter: it reports with print() instead of logging. Passes once fixed."""
        import ast
        import inspect
        import file_processor

        # Look inside the module's functions (a demo under `if __name__ == "__main__":` may still print)
        tree = ast.parse(inspect.getsource(file_processor))
        calls = [node for func in ast.walk(tree) if isinstance(func, ast.FunctionDef)
                 for node in ast.walk(func) if isinstance(node, ast.Call)]
        logger_calls = [c for c in calls if isinstance(c.func, ast.Attribute)
                        and isinstance(c.func.value, ast.Name) and c.func.value.id == "logger"]
        print_calls = [c for c in calls if isinstance(c.func, ast.Name) and c.func.id == "print"]

        # Should use logging instead of print
        assert logger_calls, "Should use logger for output"
        # Should not use print for normal operation
        assert not print_calls, f"Should not use print(), found {len(print_calls)} instances"
    
    def test_logging_configuration_exists(self):
        """Fails on the starter: it reports with print() instead of logging. Passes once fixed."""
        import file_processor
        import logging
        import inspect
        
        # Should have logging configuration
        source = inspect.getsource(file_processor)
        assert "logging.basicConfig" in source or "getLogger" in source, "Should configure logging"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))