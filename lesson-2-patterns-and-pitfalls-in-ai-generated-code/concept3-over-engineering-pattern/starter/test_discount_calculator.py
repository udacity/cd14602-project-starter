"""Tests for discount_calculator.py.

These tests describe the fixed behaviour. Run them on the starter first: some fail, and each
failing test's docstring says which problem it points at. Fix discount_calculator.py until they all pass.
"""

import os

import pytest
from unittest.mock import patch
from discount_calculator import calculate_discount

class TestDiscountCalculator:
    """Test suite for simple, maintainable discount calculation"""
    
    def test_premium_discount_calculation(self):
        """Test premium customer discount"""
        discount = calculate_discount(100.0, "premium")
        assert discount == 15.0  # 15% of 100
    
    def test_regular_discount_calculation(self):
        """Test regular customer discount"""
        discount = calculate_discount(100.0, "regular")
        assert discount == 5.0  # 5% of 100
    
    def test_vip_discount_calculation(self):
        """Test VIP customer discount"""
        discount = calculate_discount(100.0, "vip")
        assert discount == 25.0  # 25% of 100
    
    def test_student_discount_calculation(self):
        """Test student customer discount"""
        discount = calculate_discount(100.0, "student")
        assert discount == 10.0  # 10% of 100
    
    def test_unknown_customer_type_defaults(self):
        """Fails on the starter: an unknown customer type raises ValueError instead of getting the regular 5% rate. Passes once fixed."""
        discount = calculate_discount(100.0, "unknown")
        assert discount == 5.0  # Defaults to regular (5%)
    
    @patch('discount_calculator.logger')
    def test_logging_functionality(self, mock_logger):
        """Test that logging works as requested in original requirement"""
        
        calculate_discount(100.0, "premium")
        
        # Verify logging was called
        assert mock_logger.info.called, "calculate_discount() should log with logger.info()"
        
        # The log message should say which customer type it calculated for
        log_content = " ".join(str(call) for call in mock_logger.info.call_args_list).lower()
        assert "premium" in log_content, "The log message should name the customer type"
    
    def test_edge_cases_handled_simply(self):
        """Fails on the starter: an empty customer type raises ValueError instead of getting the regular 5% rate. Passes once fixed."""
        
        # Zero price
        discount = calculate_discount(0.0, "premium")
        assert discount == 0.0
        
        # Large price
        discount = calculate_discount(10000.0, "regular") 
        assert discount == 500.0  # 5% of 10000
        
        # Edge case customer types
        discount = calculate_discount(100.0, "")
        assert discount == 5.0  # Defaults to regular

class TestSimplicityComparison:
    """Tests that highlight how simple code achieves the same goals"""
    
    def test_equivalent_functionality_simple_vs_complex(self):
        """Fails on the starter: an unknown customer type raises ValueError instead of getting the regular 5% rate. Passes once fixed."""
        
        # Simple implementation (what probably should have been written)
        def simple_discount(price, customer_type):
            rates = {'premium': 0.15, 'regular': 0.05, 'vip': 0.25, 'student': 0.10}
            return price * rates.get(customer_type, 0.05)
        
        # Test cases
        test_cases = [
            (100.0, "premium"),
            (50.0, "regular"), 
            (200.0, "vip"),
            (75.0, "student"),
            (100.0, "unknown")
        ]
        
        for price, customer_type in test_cases:
            simple_result = simple_discount(price, customer_type)
            complex_result = calculate_discount(price, customer_type)
            
            assert simple_result == complex_result, \
                f"Results differ for {customer_type}: simple={simple_result}, complex={complex_result}"
    
    def test_complexity_metrics(self):
        """Fails on the starter: 202 non-blank lines and 10 classes for a request to add logging. Passes once fixed."""
        
        # Count lines of code in the simple version
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "discount_calculator.py"), "r") as f:
            simple_code = f.read()
        
        simple_lines = len([line for line in simple_code.split('\n') if line.strip()])
        
        # The simple version is much more concise 
        assert simple_lines < 50, f"discount_calculator.py has {simple_lines} non-blank lines; the request was only to add logging, so keep it under 50"
        
        # Count number of classes (should be minimal for this simple problem)
        class_count = sum(1 for line in simple_code.splitlines() if line.lstrip().startswith("class "))
        assert class_count == 0, f"discount_calculator.py defines {class_count} classes; a discount lookup with logging needs none"
    
    def test_original_requirement_analysis(self):
        """Analyze what the original request probably was"""
        
        # The user likely asked: "Add logging to the discount calculation function"
        # But AI created an entire enterprise architecture
        
        # The simple requirement was probably:
        # 1. Calculate discount based on customer type
        # 2. Add logging to see what's happening
        
        # Everything else (enums, strategies, factories, caching, statistics) 
        # was likely unnecessary for the actual business requirement
        
        # Test that the simple approach meets the core requirement
        with patch('discount_calculator.logger') as mock_logger:
            calculate_discount(100.0, "premium")
            
            # Logging requirement met with simple approach
            assert mock_logger.info.called
            
        # Discount calculation requirement met
        assert calculate_discount(100.0, "premium") == 15.0