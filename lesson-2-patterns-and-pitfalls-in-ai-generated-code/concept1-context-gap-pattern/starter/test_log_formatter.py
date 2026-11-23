"""Tests for log_formatter.py.

These tests describe the fixed behaviour. Run them on the starter first: some fail, and each
failing test's docstring says which problem it points at. Fix log_formatter.py until they all pass.
"""

from datetime import datetime

import pytest
from unittest.mock import patch

from log_formatter import format_log_entry, write_to_log_file, send_to_monitoring, update_log_statistics

class TestLogFormatterSolution:
    """Test suite demonstrating complete log functionality preserved"""
    
    def test_timestamp_feature_added(self):
        """Test that timestamp feature was successfully added"""
        result = format_log_entry("INFO", "User logged in")
        
        # Should contain timestamp (the requested feature)
        assert str(datetime.now().year) in result  # Year should be in timestamp
        assert ":" in result[:20]  # Time separator in first part
        assert "[INFO]" in result
        assert "User logged in" in result
    
    def test_user_context_preserved(self):
        """Test that user context functionality was preserved"""
        result = format_log_entry("ERROR", "Login failed", "user123")
        
        assert "(User: user123)" in result
        assert "[ERROR]" in result
        assert "Login failed" in result
    
    def test_log_level_validation_preserved(self):
        """Test that log level validation was preserved"""
        result = format_log_entry("INVALID", "test message")
        
        assert "[INFO]" in result  # Should default to INFO
        assert "test message" in result
    
    @patch('log_formatter.write_to_log_file')
    def test_file_logging_preserved(self, mock_file):
        """Fails on the starter: the AI version no longer calls write_to_log_file(). Passes once fixed."""
        result = format_log_entry("INFO", "Test message")
        
        mock_file.assert_called_once()
    
    @patch('log_formatter.send_to_monitoring')
    def test_monitoring_integration_preserved(self, mock_monitoring):
        """Fails on the starter: the AI version no longer calls send_to_monitoring(). Passes once fixed."""
        result = format_log_entry("ERROR", "Critical issue", "user456")
        
        mock_monitoring.assert_called_once_with("ERROR", "Critical issue", "user456")
    
    @patch('log_formatter.update_log_statistics')
    def test_statistics_tracking_preserved(self, mock_stats):
        """Fails on the starter: the AI version no longer calls update_log_statistics(). Passes once fixed."""
        result = format_log_entry("WARNING", "Disk space low")
        
        mock_stats.assert_called_once_with("WARNING")
    
    @patch('log_formatter.write_to_log_file')
    @patch('log_formatter.send_to_monitoring')
    @patch('log_formatter.update_log_statistics')
    def test_complete_workflow_with_timestamps(self, mock_stats, mock_monitoring, mock_file):
        """Fails on the starter: the AI version dropped the three calls while adding timestamps. Passes once fixed."""
        result = format_log_entry("CRITICAL", "System failure", "admin")
        
        # New feature works (timestamp)
        assert str(datetime.now().year) in result and ":" in result[:20]
        
        # All original features preserved
        mock_file.assert_called_once()
        mock_monitoring.assert_called_once_with("CRITICAL", "System failure", "admin")
        mock_stats.assert_called_once_with("CRITICAL")
        
        # User context preserved
        assert "(User: admin)" in result