"""Tests for name_formatter.py.

These tests describe the fixed behaviour. Run them on the starter first: some fail, and each
failing test's docstring says which problem it points at. Fix name_formatter.py until they all pass.
name_formatter is imported inside each test, so while it cannot be imported, every test that needs
it fails with the import error that names the missing library.
"""

import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


class TestNameFormatterSolution:
    """Test suite for name formatter using real dependencies only"""
    
    def test_basic_name_formatting(self):
        """Fails on the starter: name_formatter imports libraries that don't exist. Passes once fixed."""
        from name_formatter import format_user_name
        assert format_user_name("john", "doe") == "John Doe"
        assert format_user_name("jane", "smith") == "Jane Smith"
        assert format_user_name("", "wilson") == "Wilson"
        assert format_user_name("alice", "") == "Alice"
        assert format_user_name("", "") == "Unknown User"
    
    def test_apostrophe_handling(self):
        """Fails on the starter: name_formatter imports libraries that don't exist. Passes once fixed."""
        from name_formatter import format_user_name
        assert format_user_name("sean", "o'connor") == "Sean O'Connor"
        assert format_user_name("d'angelo", "smith") == "D'Angelo Smith"
    
    def test_list_formatting(self):
        """Fails on the starter: name_formatter imports libraries that don't exist. Passes once fixed."""
        from name_formatter import format_names_list
        users = [
            {"first_name": "alice", "last_name": "jones"},
            {"first_name": "bob", "last_name": "o'connor"},
            {"first_name": "", "last_name": "smith"},
            "invalid_entry"  # Should be skipped gracefully
        ]
        
        result = format_names_list(users)
        expected = ["Alice Jones", "Bob O'Connor", "Smith"]
        assert result == expected
    
    def test_uses_only_real_libraries(self):
        """Fails on the starter: the code imports phantom libraries. Passes once fixed."""
    
        with open(os.path.join(HERE, "name_formatter.py"), "r") as f:
            solution_code = f.read()
        
        # Should NOT contain any phantom libraries
        phantom_libraries = [
            "name_formatter_pro",
            "string_utils_plus", 
            "text_optimizer"
        ]
        
        for phantom in phantom_libraries:
            assert phantom not in solution_code, f"Should not use phantom: {phantom}"
    
    def test_no_phantom_methods_used(self):
        """Fails on the starter: the code calls methods of the phantom libraries. Passes once fixed."""
        
        with open(os.path.join(HERE, "name_formatter.py"), "r") as f:
            solution_code = f.read()
        
        # Should use real string methods
        real_methods = [".strip()", ".title()", ".capitalize()"]
        methods_found = sum(1 for method in real_methods if method in solution_code)
        assert methods_found >= 1, "Should use real string methods"
        
        # Should NOT use phantom methods
        phantom_methods = ["super_clean", "smart_title_case", "process_batch"]
        for phantom_method in phantom_methods:
            assert phantom_method not in solution_code, f"Should not use phantom method: {phantom_method}"