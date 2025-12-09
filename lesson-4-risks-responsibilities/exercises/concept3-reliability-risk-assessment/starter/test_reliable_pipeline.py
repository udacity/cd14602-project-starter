"""
Comprehensive Test Suite for Reliable Financial Data Pipeline
============================================================

Tests validate all reliability safeguards including:
- Input validation
- Fail-safe error handling
- Confidence scoring
- Circuit breaker behavior
- Retry logic
- Anomaly detection
- Audit trail
- Dead letter queue
"""

import pytest
import sqlite3
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from reliable_data_pipeline import (
    ReliableTransactionProcessor,
    BatchProcessor,
    TransactionValidator,
    ReliableExternalAPIClient,
    CircuitBreaker,
    TransactionStatus,
    ValidationException,
    NetworkException,
    FINANCIAL_LIMITS,
)


# ============================================================================
# INPUT VALIDATION TESTS
# ============================================================================

class TestInputValidation:
    """Test comprehensive input validation."""

    def setup_method(self):
        self.validator = TransactionValidator()

    def test_valid_transaction(self):
        """Test that valid transactions pass validation."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.50,
            "currency": "USD"
        }

        transaction = self.validator.validate(transaction_data, "test-correlation-id")

        assert transaction.account_id == "ACC123"
        assert transaction.amount == Decimal("100.50")
        assert transaction.currency == "USD"
        assert transaction.status == TransactionStatus.PENDING

    def test_missing_required_fields(self):
        """Test that missing required fields are rejected."""
        test_cases = [
            {},  # All fields missing
            {"account_id": "ACC123"},  # Missing amount and currency
            {"amount": 100.00},  # Missing account_id and currency
            {"account_id": "ACC123", "amount": 100.00},  # Missing currency
        ]

        for transaction_data in test_cases:
            with pytest.raises(ValidationException) as exc_info:
                self.validator.validate(transaction_data, "test-correlation-id")

            assert "Missing required field" in str(exc_info.value)

    def test_negative_amount_rejected(self):
        """Test that negative amounts are rejected."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": -50.00,
            "currency": "USD"
        }

        with pytest.raises(ValidationException) as exc_info:
            self.validator.validate(transaction_data, "test-correlation-id")

        assert "must be positive" in str(exc_info.value)

    def test_zero_amount_rejected(self):
        """Test that zero amounts are rejected."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 0.00,
            "currency": "USD"
        }

        with pytest.raises(ValidationException) as exc_info:
            self.validator.validate(transaction_data, "test-correlation-id")

        assert "must be positive" in str(exc_info.value)

    def test_below_minimum_amount_rejected(self):
        """Test that amounts below minimum are rejected."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 0.001,  # Below 0.01 minimum
            "currency": "USD"
        }

        with pytest.raises(ValidationException) as exc_info:
            self.validator.validate(transaction_data, "test-correlation-id")

        assert "below minimum" in str(exc_info.value)

    def test_above_maximum_amount_rejected(self):
        """Test that amounts above maximum are rejected."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 10000000.00,  # Above 1M maximum
            "currency": "USD"
        }

        with pytest.raises(ValidationException) as exc_info:
            self.validator.validate(transaction_data, "test-correlation-id")

        assert "exceeds maximum" in str(exc_info.value)

    def test_too_many_decimal_places_rejected(self):
        """Test that amounts with more than 2 decimal places are rejected."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.123,  # 3 decimal places
            "currency": "USD"
        }

        with pytest.raises(ValidationException) as exc_info:
            self.validator.validate(transaction_data, "test-correlation-id")

        assert "more than 2 decimal places" in str(exc_info.value)

    def test_unsupported_currency_rejected(self):
        """Test that unsupported currencies are rejected."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "XYZ"  # Invalid currency
        }

        with pytest.raises(ValidationException) as exc_info:
            self.validator.validate(transaction_data, "test-correlation-id")

        assert "Unsupported currency" in str(exc_info.value)

    def test_invalid_amount_type_rejected(self):
        """Test that non-numeric amounts are rejected."""
        test_cases = [
            {"account_id": "ACC123", "amount": "not a number", "currency": "USD"},
            {"account_id": "ACC123", "amount": None, "currency": "USD"},
            {"account_id": "ACC123", "amount": {}, "currency": "USD"},
        ]

        for transaction_data in test_cases:
            with pytest.raises(ValidationException) as exc_info:
                self.validator.validate(transaction_data, "test-correlation-id")

            assert "valid decimal number" in str(exc_info.value)

    def test_empty_account_id_rejected(self):
        """Test that empty account IDs are rejected."""
        transaction_data = {
            "account_id": "",
            "amount": 100.00,
            "currency": "USD"
        }

        with pytest.raises(ValidationException) as exc_info:
            self.validator.validate(transaction_data, "test-correlation-id")

        assert "non-empty string" in str(exc_info.value)

    def test_large_amount_warning(self):
        """Test that large amounts generate warnings but pass validation."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 60000.00,  # Above suspicious threshold
            "currency": "USD"
        }

        transaction = self.validator.validate(transaction_data, "test-correlation-id")

        assert transaction is not None
        warnings = transaction.metadata.get("warnings", [])
        assert any("Large transaction" in w for w in warnings)


# ============================================================================
# FAIL-SAFE ERROR HANDLING TESTS
# ============================================================================

class TestFailSafeErrorHandling:
    """Test fail-safe error handling and graceful degradation."""

    def setup_method(self):
        self.processor = ReliableTransactionProcessor(":memory:")

    def test_invalid_account_requires_review(self):
        """Test that invalid accounts are flagged for review, not processed."""
        transaction_data = {
            "account_id": "ACC999",
            "amount": 100.00,
            "currency": "USD"
        }

        # Mock API to return invalid
        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (False, 0.0)

            result = self.processor.process_transaction(transaction_data)

            assert result.status == TransactionStatus.REQUIRES_REVIEW
            assert result.requires_review is True
            assert "validation failed" in result.warnings[0].lower()

    def test_currency_conversion_failure_requires_review(self):
        """Test that currency conversion failures require review."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "EUR"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            with patch.object(self.processor.api_client, 'get_exchange_rate') as mock_rate:
                mock_rate.side_effect = NetworkException("API unavailable")

                result = self.processor.process_transaction(transaction_data)

                assert result.status == TransactionStatus.REQUIRES_REVIEW
                assert result.requires_review is True

    def test_low_confidence_requires_review(self):
        """Test that low confidence transactions require review."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "EUR"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            # Low confidence validation
            mock_validate.return_value = (True, 0.5)

            with patch.object(self.processor.api_client, 'get_exchange_rate') as mock_rate:
                # Low confidence rate
                mock_rate.return_value = (Decimal("1.2"), datetime.utcnow(), 0.6)

                result = self.processor.process_transaction(transaction_data)

                # Combined confidence: 0.5 * 0.6 = 0.3 (below 0.7 threshold)
                assert result.status == TransactionStatus.REQUIRES_REVIEW
                assert result.requires_review is True
                assert result.confidence_score < 0.7

    def test_validation_error_fails_gracefully(self):
        """Test that validation errors fail gracefully without crashing."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": -100.00,  # Invalid
            "currency": "USD"
        }

        result = self.processor.process_transaction(transaction_data)

        assert result.status == TransactionStatus.FAILED
        assert len(result.errors) > 0
        assert not result.requires_review  # Validation errors don't need review

    def test_batch_continues_after_failures(self):
        """Test that batch processing continues after individual failures (graceful degradation)."""
        transactions = [
            {"account_id": "ACC001", "amount": 100.00, "currency": "USD"},  # Valid
            {"account_id": "ACC002", "amount": -50.00, "currency": "USD"},  # Invalid
            {"account_id": "ACC003", "amount": 200.00, "currency": "USD"},  # Valid
        ]

        batch_processor = BatchProcessor(self.processor)

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            results = batch_processor.process_batch(transactions, fail_fast=False)

            # Should process all 3, even though one failed
            assert results["total"] == 3
            assert results["successful"] >= 1  # At least one succeeded
            assert results["failed"] >= 1  # At least one failed


# ============================================================================
# CONFIDENCE SCORING AND HUMAN-IN-THE-LOOP TESTS
# ============================================================================

class TestConfidenceScoring:
    """Test confidence scoring and human oversight mechanisms."""

    def setup_method(self):
        self.processor = ReliableTransactionProcessor(":memory:")

    def test_high_confidence_processed_automatically(self):
        """Test that high confidence transactions are processed automatically."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "USD"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            result = self.processor.process_transaction(transaction_data)

            assert result.status == TransactionStatus.COMPLETED
            assert result.confidence_score >= 0.7
            assert not result.requires_review

    def test_medium_confidence_still_processed(self):
        """Test that medium confidence (0.7-0.9) transactions are still processed."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "EUR"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.9)

            with patch.object(self.processor.api_client, 'get_exchange_rate') as mock_rate:
                mock_rate.return_value = (Decimal("1.2"), datetime.utcnow(), 0.8)

                result = self.processor.process_transaction(transaction_data)

                # Combined: 0.9 * 0.8 = 0.72 (above threshold)
                assert result.status == TransactionStatus.COMPLETED
                assert 0.7 <= result.confidence_score < 0.9

    def test_low_confidence_requires_human_review(self):
        """Test that low confidence transactions require human review."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "EUR"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.8)

            with patch.object(self.processor.api_client, 'get_exchange_rate') as mock_rate:
                # Stale rate reduces confidence
                old_timestamp = datetime.utcnow() - timedelta(minutes=30)
                mock_rate.return_value = (Decimal("1.2"), old_timestamp, 0.6)

                result = self.processor.process_transaction(transaction_data)

                # Stale data further reduces confidence
                assert result.status == TransactionStatus.REQUIRES_REVIEW
                assert result.confidence_score < 0.7
                assert result.requires_review

    def test_confidence_score_recorded(self):
        """Test that confidence scores are recorded in database."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "USD"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            result = self.processor.process_transaction(transaction_data)

            # Check database
            with self.processor.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT confidence_score FROM transactions WHERE transaction_id = ?",
                    (result.transaction_id,)
                )
                row = cursor.fetchone()

                assert row is not None
                assert row["confidence_score"] > 0


# ============================================================================
# CIRCUIT BREAKER TESTS
# ============================================================================

class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_closes_initially(self):
        """Test that circuit breaker starts in closed state."""
        cb = CircuitBreaker("test_service", failure_threshold=3)

        assert cb.state == "closed"

    def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure threshold."""
        cb = CircuitBreaker("test_service", failure_threshold=3)

        def failing_func():
            raise Exception("Service down")

        # Trigger 3 failures
        for _ in range(3):
            try:
                cb.call(failing_func)
            except Exception:
                pass

        assert cb.state == "open"

    def test_circuit_prevents_calls_when_open(self):
        """Test that open circuit prevents function calls."""
        cb = CircuitBreaker("test_service", failure_threshold=2)

        def failing_func():
            raise Exception("Service down")

        # Open the circuit
        for _ in range(2):
            try:
                cb.call(failing_func)
            except Exception:
                pass

        assert cb.state == "open"

        # Attempt call with open circuit
        with pytest.raises(NetworkException) as exc_info:
            cb.call(failing_func)

        assert "Circuit breaker open" in str(exc_info.value)

    def test_circuit_half_opens_after_timeout(self):
        """Test that circuit transitions to half-open after timeout."""
        cb = CircuitBreaker("test_service", failure_threshold=2, timeout=0)  # Immediate timeout

        def failing_func():
            raise Exception("Service down")

        # Open the circuit
        for _ in range(2):
            try:
                cb.call(failing_func)
            except Exception:
                pass

        assert cb.state == "open"

        # After timeout, should attempt half-open
        try:
            cb.call(failing_func)
        except Exception:
            pass

        # State should have transitioned through half-open
        assert cb.state in ["half_open", "open"]


# ============================================================================
# RETRY LOGIC TESTS
# ============================================================================

class TestRetryLogic:
    """Test retry logic with exponential backoff."""

    def setup_method(self):
        self.client = ReliableExternalAPIClient()

    def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries."""
        with patch('requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "rate": 1.2,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": 0.95
            }
            mock_get.return_value = mock_response

            rate, timestamp, confidence = self.client._fetch_exchange_rate_with_retry(
                "EUR",
                "test-correlation-id"
            )

            # Should only call once (no retries)
            assert mock_get.call_count == 1
            assert rate == Decimal("1.2")

    def test_transient_error_triggers_retry(self):
        """Test that transient errors trigger retries."""
        with patch('requests.Session.get') as mock_get:
            # First call fails, second succeeds
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 503

            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "rate": 1.2,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": 0.95
            }

            mock_get.side_effect = [mock_response_fail, mock_response_success]

            with patch('time.sleep'):  # Mock sleep to speed up test
                rate, timestamp, confidence = self.client._fetch_exchange_rate_with_retry(
                    "EUR",
                    "test-correlation-id"
                )

            # Should call twice (1 original + 1 retry)
            assert mock_get.call_count == 2

    def test_permanent_error_no_retry(self):
        """Test that permanent errors don't trigger retries."""
        with patch('requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            with pytest.raises(NetworkException):
                self.client._fetch_exchange_rate_with_retry(
                    "EUR",
                    "test-correlation-id"
                )

            # Should only call once (no retries for 404)
            assert mock_get.call_count == 1

    def test_all_retries_exhausted(self):
        """Test behavior when all retries are exhausted."""
        with patch('requests.Session.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 503
            mock_get.return_value = mock_response

            with patch('time.sleep'):  # Mock sleep
                with pytest.raises(NetworkException):
                    self.client._fetch_exchange_rate_with_retry(
                        "EUR",
                        "test-correlation-id"
                    )

            # Should call 3 times (max retries)
            assert mock_get.call_count == 3


# ============================================================================
# ANOMALY DETECTION TESTS
# ============================================================================

class TestAnomalyDetection:
    """Test anomaly detection mechanisms."""

    def setup_method(self):
        self.processor = ReliableTransactionProcessor(":memory:")

    def test_duplicate_transaction_detected(self):
        """Test that duplicate transactions are detected."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "USD"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            # Process first transaction
            result1 = self.processor.process_transaction(transaction_data)
            assert result1.status == TransactionStatus.COMPLETED

            # Process duplicate
            result2 = self.processor.process_transaction(transaction_data)

            # Should be flagged for review due to duplicate detection
            assert result2.status == TransactionStatus.REQUIRES_REVIEW
            assert any("duplicate" in w.lower() for w in result2.warnings)

    def test_daily_limit_exceeded_detected(self):
        """Test that daily limit violations are detected."""
        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            # Process transactions up to near limit
            for i in range(3):
                transaction_data = {
                    "account_id": "ACC123",
                    "amount": 30000.00,
                    "currency": "USD"
                }
                result = self.processor.process_transaction(transaction_data)

            # Process one more that exceeds limit
            transaction_data = {
                "account_id": "ACC123",
                "amount": 15000.00,
                "currency": "USD"
            }
            result = self.processor.process_transaction(transaction_data)

            # Should be flagged for review
            assert result.status == TransactionStatus.REQUIRES_REVIEW
            assert any("limit" in w.lower() for w in result.warnings)


# ============================================================================
# AUDIT TRAIL TESTS
# ============================================================================

class TestAuditTrail:
    """Test audit trail and logging."""

    def setup_method(self):
        self.processor = ReliableTransactionProcessor(":memory:")

    def test_audit_log_created(self):
        """Test that audit log entries are created."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "USD"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            result = self.processor.process_transaction(transaction_data)

            # Check audit log
            with self.processor.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM audit_log WHERE transaction_id = ?",
                    (result.transaction_id,)
                )
                row = cursor.fetchone()

                # Should have multiple audit entries (validation, processing, completion)
                assert row["count"] > 0

    def test_failed_transaction_in_dead_letter_queue(self):
        """Test that failed transactions are saved to dead letter queue."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "EUR"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            with patch.object(self.processor.api_client, 'get_exchange_rate') as mock_rate:
                # Cause unexpected error
                mock_rate.side_effect = Exception("Unexpected error")

                result = self.processor.process_transaction(transaction_data)

                # Check dead letter queue
                with self.processor.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT COUNT(*) as count FROM failed_transactions WHERE transaction_id = ?",
                        (result.transaction_id,)
                    )
                    row = cursor.fetchone()

                    assert row["count"] > 0


# ============================================================================
# MONITORING AND METRICS TESTS
# ============================================================================

class TestMonitoringMetrics:
    """Test monitoring and metrics collection."""

    def setup_method(self):
        self.processor = ReliableTransactionProcessor(":memory:")

    def test_metrics_recorded(self):
        """Test that performance metrics are recorded."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "USD"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            self.processor.process_transaction(transaction_data)

            # Check metrics
            with self.processor.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) as count FROM metrics WHERE metric_name = ?",
                    ("transaction_processing_duration_ms",)
                )
                row = cursor.fetchone()

                assert row["count"] > 0

    def test_metrics_summary(self):
        """Test metrics summary generation."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "USD"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            # Process some transactions
            for _ in range(3):
                self.processor.process_transaction(transaction_data)

            metrics = self.processor.get_metrics_summary()

            assert "timing_stats" in metrics
            assert "status_counts" in metrics
            assert "error_rate_percent" in metrics
            assert metrics["total_processed"] >= 3


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""

    def setup_method(self):
        self.processor = ReliableTransactionProcessor(":memory:")
        self.batch_processor = BatchProcessor(self.processor)

    def test_complete_successful_transaction_flow(self):
        """Test complete flow for successful transaction."""
        transaction_data = {
            "account_id": "ACC123",
            "amount": 100.00,
            "currency": "USD"
        }

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            result = self.processor.process_transaction(transaction_data)

            # Verify result
            assert result.status == TransactionStatus.COMPLETED
            assert result.confidence_score >= 0.7
            assert not result.requires_review
            assert len(result.errors) == 0

            # Verify database
            with self.processor.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM transactions WHERE transaction_id = ?",
                    (result.transaction_id,)
                )
                row = cursor.fetchone()

                assert row is not None
                assert row["status"] == TransactionStatus.COMPLETED.value

    def test_batch_processing_mixed_results(self):
        """Test batch processing with mix of success, failure, and review."""
        transactions = [
            {"account_id": "ACC001", "amount": 100.00, "currency": "USD"},  # Success
            {"account_id": "ACC002", "amount": -50.00, "currency": "USD"},  # Fail (validation)
            {"account_id": "ACC003", "amount": 200.00, "currency": "EUR"},  # Success or review
        ]

        with patch.object(self.processor.api_client, 'validate_account') as mock_validate:
            mock_validate.return_value = (True, 0.95)

            with patch.object(self.processor.api_client, 'get_exchange_rate') as mock_rate:
                mock_rate.return_value = (Decimal("1.2"), datetime.utcnow(), 0.9)

                results = self.batch_processor.process_batch(transactions, fail_fast=False)

                # Verify all processed
                assert results["total"] == 3
                assert results["successful"] >= 1
                assert results["failed"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
