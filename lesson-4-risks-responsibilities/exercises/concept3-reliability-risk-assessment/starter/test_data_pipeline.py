"""
Test suite for Financial Data Processing Pipeline
===============================================

These tests demonstrate reliability and resilience issues in the data pipeline.
"""

import pytest
import requests
import sqlite3
from unittest.mock import patch, MagicMock
from data_pipeline import ExternalAPIClient, TransactionProcessor, DataPipelineOrchestrator


class TestReliabilityIssues:
    """Test cases that reveal reliability problems."""
    
    def test_no_retry_logic_for_api_failures(self):
        """Test that API failures aren't retried."""
        client = ExternalAPIClient()
        
        # Mock a temporary network failure
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Network failure")
            
            # Should fail immediately without retry
            try:
                client.get_exchange_rate("EUR")
            except Exception:
                pass  # what matters is how many attempts were made
            
            # One attempt only means no retries
            if mock_get.call_count == 1:
                print("🚨 RELIABILITY ISSUE: No retry logic for temporary API failures")
    
    def test_no_circuit_breaker_for_cascade_failures(self):
        """Test that repeated failures don't trigger circuit breaker."""
        processor = TransactionProcessor()
        
        # Mock the API to always fail
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("API service down")
            
            # Process multiple transactions - should fail all without stopping
            transactions = [
                {"account_id": f"ACC{i:03d}", "amount": 100.0, "currency": "USD"}
                for i in range(10)
            ]
            
            result = processor.process_batch(transactions)
            
            # A circuit breaker would stop calling the API before the last transaction
            last_account = transactions[-1]["account_id"]
            if any(last_account in str(call) for call in mock_get.call_args_list):
                print(f"🚨 RELIABILITY ISSUE: Processed {len(transactions)} transactions despite API being down")
                print(f"   Failed: {result['failed']}, API calls made: {mock_get.call_count}")
    
    def test_no_fallback_for_external_dependencies(self):
        """Test lack of fallback mechanisms when external services fail."""
        client = ExternalAPIClient()
        
        # Mock API failure
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.json.return_value = {"error": "Service unavailable"}
            
            try:
                client.validate_account("ACC123")
            except Exception as e:
                print("🚨 RELIABILITY ISSUE: No fallback when external validation service fails")
                print(f"   Error: {e}")
    
    def test_no_transaction_rollback_on_partial_failures(self):
        """Test that partial failures don't trigger rollbacks."""
        processor = TransactionProcessor()
        
        # Mock database save to fail after validation succeeds
        with patch.object(processor, '_save_transaction') as mock_save:
            mock_save.side_effect = sqlite3.OperationalError("Database locked")
            
            with patch.object(processor.api_client, 'validate_account', return_value=True):
                with patch.object(processor.api_client, 'get_exchange_rate', 
                                return_value={"rate": 1.2}):
                    
                    transaction = {
                        "account_id": "ACC123",
                        "amount": 100.0,
                        "currency": "EUR"
                    }
                    
                    try:
                        processor.process_transaction(transaction)
                    except sqlite3.OperationalError:
                        print("🚨 RELIABILITY ISSUE: No rollback mechanism for partial failures")
                        print("   Validation succeeded but database save failed - no cleanup")
                    except Exception:
                        pass  # the code under test reports the failure its own way
    
    def test_no_connection_pooling_or_resource_management(self):
        """Test that database connections aren't pooled or managed efficiently."""
        processor = TransactionProcessor()
        
        # Process multiple transactions and check connection handling
        transactions = [
            {"account_id": f"ACC{i:03d}", "amount": 100.0, "currency": "USD"}
            for i in range(5)
        ]
        
        # Mock to make calls succeed and count database connections
        with patch.object(processor.api_client, 'validate_account', return_value=True):
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = MagicMock()
                mock_cursor = MagicMock()
                mock_connect.return_value = mock_conn
                mock_conn.cursor.return_value = mock_cursor
                
                processor.process_batch(transactions)  # warm-up: a pool may open its connections here
                warm_up = mock_connect.call_count
                processor.process_batch(transactions)
                opened = mock_connect.call_count - warm_up
                
                # One connection per transaction means no pooling
                if opened >= len(transactions):
                    print(f"🚨 RELIABILITY ISSUE: Database connections not pooled")
                    print(f"   Opened {opened} connections for {len(transactions)} transactions")
                    print(f"   Should use connection pooling for efficiency")
    
    def test_pipeline_fails_completely_on_single_error(self):
        """Test that pipeline doesn't gracefully degrade on errors."""
        pipeline = DataPipelineOrchestrator()
        
        # Mock the processor to fail completely
        with patch.object(pipeline.processor, 'process_batch') as mock_batch:
            mock_batch.side_effect = Exception("Database connection failed")
            
            try:
                pipeline.run_daily_pipeline("demo")
            except Exception as e:
                print("🚨 RELIABILITY ISSUE: Entire pipeline fails on single component error")
                print(f"   Error: {e}")
                print("   No graceful degradation or partial success handling")


class TestBasicFunctionality:
    """Test that basic functionality works when everything is working."""
    
    def test_successful_transaction_processing(self):
        """Test that transaction processing works under normal conditions."""
        processor = TransactionProcessor()
        
        # Mock successful API responses
        with patch.object(processor.api_client, 'validate_account', return_value=True):
            with patch.object(processor.api_client, 'get_exchange_rate', 
                            return_value={"rate": 1.2}):
                
                transaction = {
                    "account_id": "ACC123",
                    "amount": 100.0,
                    "currency": "EUR"
                }
                
                result = processor.process_transaction(transaction)
                
                assert result["status"] == "completed"
                assert result["account_id"] == "ACC123"
                assert "usd_amount" in result
    
    def test_batch_processing_works(self):
        """Test that batch processing works when APIs are available."""
        processor = TransactionProcessor()
        
        # Mock successful API responses
        with patch.object(processor.api_client, 'validate_account', return_value=True):
            with patch.object(processor.api_client, 'get_exchange_rate', 
                            return_value={"rate": 1.0}):
                
                transactions = [
                    {"account_id": "ACC001", "amount": 100.0, "currency": "USD"},
                    {"account_id": "ACC002", "amount": 200.0, "currency": "USD"}
                ]
                
                result = processor.process_batch(transactions)
                
                assert result["successful"] == 2
                assert result["failed"] == 0
    
    def test_pipeline_orchestration(self):
        """Test that pipeline orchestration works with mock data."""
        pipeline = DataPipelineOrchestrator()
        
        # Use demo data source; mock the external API so the test does not wait on the network
        with patch.object(pipeline.processor.api_client, 'validate_account', return_value=True), \
             patch.object(pipeline.processor.api_client, 'get_exchange_rate', return_value={"rate": 1.0}):
            result = pipeline.run_daily_pipeline("demo")
        
        assert "pipeline_status" in result
        assert "duration_seconds" in result
        assert "batch_result" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])