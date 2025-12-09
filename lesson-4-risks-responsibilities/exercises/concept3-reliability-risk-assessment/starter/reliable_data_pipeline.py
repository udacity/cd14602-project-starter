"""
Reliable Financial Data Processing Pipeline
==========================================

Production-ready financial data pipeline with comprehensive reliability safeguards.
Designed for safety-critical financial systems with strict regulatory compliance.

Key Features:
- Comprehensive input validation
- Fail-safe error handling
- Confidence scoring and human oversight
- Transaction rollback and audit trail
- Circuit breaker pattern
- Real-time monitoring and alerting
- Anomaly detection
"""

import requests
import time
import sqlite3
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
from enum import Enum
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import traceback


# ============================================================================
# CONFIGURATION AND CONSTANTS
# ============================================================================

class TransactionStatus(Enum):
    """Transaction lifecycle states."""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    REQUIRES_REVIEW = "requires_review"


class ErrorCategory(Enum):
    """Categorized errors for better handling and monitoring."""
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    EXTERNAL_API_ERROR = "external_api_error"
    UNKNOWN_ERROR = "unknown_error"


class ConfidenceLevel(Enum):
    """Confidence levels for transaction processing."""
    HIGH = "high"        # > 0.9
    MEDIUM = "medium"    # 0.7 - 0.9
    LOW = "low"          # < 0.7


# Financial validation constants
FINANCIAL_LIMITS = {
    "min_amount": Decimal("0.01"),
    "max_amount": Decimal("1000000.00"),
    "suspicious_threshold": Decimal("50000.00"),
    "max_daily_per_account": Decimal("100000.00"),
}

# API reliability constants
API_CONFIG = {
    "max_retries": 3,
    "retry_backoff_base": 1.0,  # seconds
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 60,  # seconds
    "request_timeout": 10,  # seconds
    "rate_staleness_minutes": 15,
}

# Supported currencies (ISO 4217 codes)
SUPPORTED_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF"}


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class PipelineException(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, category: ErrorCategory, details: Optional[Dict] = None):
        super().__init__(message)
        self.category = category
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class ValidationException(PipelineException):
    """Input validation failed."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.VALIDATION_ERROR, details)


class NetworkException(PipelineException):
    """Network/API communication failed."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.NETWORK_ERROR, details)


class DatabaseException(PipelineException):
    """Database operation failed."""
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, ErrorCategory.DATABASE_ERROR, details)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Transaction:
    """Validated transaction with full context."""
    transaction_id: str
    account_id: str
    amount: Decimal
    currency: str
    status: TransactionStatus
    confidence_score: float
    created_at: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        data = asdict(self)
        data['amount'] = str(self.amount)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class ProcessingResult:
    """Result of transaction processing with full context."""
    transaction_id: str
    status: TransactionStatus
    confidence_score: float
    requires_review: bool
    original_amount: Decimal
    usd_amount: Optional[Decimal]
    currency: str
    errors: List[str]
    warnings: List[str]
    processing_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "transaction_id": self.transaction_id,
            "status": self.status.value,
            "confidence_score": self.confidence_score,
            "requires_review": self.requires_review,
            "original_amount": str(self.original_amount),
            "usd_amount": str(self.usd_amount) if self.usd_amount else None,
            "currency": self.currency,
            "errors": self.errors,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
        }


# ============================================================================
# LOGGING INFRASTRUCTURE
# ============================================================================

class StructuredLogger:
    """Structured logging with correlation IDs and context."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Console handler with JSON formatting
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def _log(self, level: str, message: str, **context):
        """Log structured message with context."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }
        log_entry.update(context)
        getattr(self.logger, level.lower())(json.dumps(log_entry))

    def info(self, message: str, **context):
        self._log("INFO", message, **context)

    def warning(self, message: str, **context):
        self._log("WARNING", message, **context)

    def error(self, message: str, **context):
        self._log("ERROR", message, **context)

    def critical(self, message: str, **context):
        self._log("CRITICAL", message, **context)


# ============================================================================
# CIRCUIT BREAKER PATTERN
# ============================================================================

class CircuitBreaker:
    """Circuit breaker to prevent cascade failures."""

    def __init__(self, service_name: str, failure_threshold: int = 5, timeout: int = 60):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        self.logger = StructuredLogger(f"circuit_breaker.{service_name}")

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                self.logger.info(f"Circuit breaker half-open", service=self.service_name)
            else:
                raise NetworkException(
                    f"Circuit breaker open for {self.service_name}",
                    details={"service": self.service_name, "state": self.state}
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.timeout

    def _on_success(self):
        """Handle successful call."""
        if self.state == "half_open":
            self.state = "closed"
            self.failure_count = 0
            self.logger.info(f"Circuit breaker closed", service=self.service_name)

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            self.logger.critical(
                f"Circuit breaker opened",
                service=self.service_name,
                failure_count=self.failure_count
            )


# ============================================================================
# EXTERNAL API CLIENT WITH RELIABILITY SAFEGUARDS
# ============================================================================

class ReliableExternalAPIClient:
    """API client with retry logic, circuit breaker, and validation."""

    def __init__(self, base_url: str = "https://api.financial-service.com"):
        self.base_url = base_url
        self.logger = StructuredLogger("external_api_client")
        self.circuit_breakers = {
            "exchange_rate": CircuitBreaker("exchange_rate_api"),
            "account_validation": CircuitBreaker("account_validation_api"),
        }
        self.session = requests.Session()  # Connection pooling

    def get_exchange_rate(self, currency: str, correlation_id: str) -> Tuple[Decimal, datetime, float]:
        """
        Get exchange rate with validation and reliability safeguards.

        Returns: (rate, timestamp, confidence_score)
        Raises: ValidationException, NetworkException
        """
        # Validate currency
        if currency not in SUPPORTED_CURRENCIES:
            raise ValidationException(
                f"Unsupported currency: {currency}",
                details={"currency": currency, "supported": list(SUPPORTED_CURRENCIES)}
            )

        # USD doesn't need conversion
        if currency == "USD":
            return Decimal("1.0"), datetime.utcnow(), 1.0

        # Use circuit breaker with retry logic
        def _fetch_rate():
            return self._fetch_exchange_rate_with_retry(currency, correlation_id)

        try:
            rate, timestamp, confidence = self.circuit_breakers["exchange_rate"].call(_fetch_rate)

            # Validate rate freshness
            age_minutes = (datetime.utcnow() - timestamp).total_seconds() / 60
            if age_minutes > API_CONFIG["rate_staleness_minutes"]:
                self.logger.warning(
                    "Stale exchange rate detected",
                    correlation_id=correlation_id,
                    currency=currency,
                    age_minutes=age_minutes
                )
                confidence *= 0.7  # Reduce confidence for stale data

            # Validate rate is reasonable
            if not self._validate_exchange_rate(currency, rate):
                self.logger.error(
                    "Exchange rate outside expected range",
                    correlation_id=correlation_id,
                    currency=currency,
                    rate=str(rate)
                )
                confidence *= 0.5

            return rate, timestamp, confidence

        except Exception as e:
            self.logger.error(
                "Failed to get exchange rate",
                correlation_id=correlation_id,
                currency=currency,
                error=str(e)
            )
            raise

    def _fetch_exchange_rate_with_retry(self, currency: str, correlation_id: str) -> Tuple[Decimal, datetime, float]:
        """Fetch exchange rate with exponential backoff retry."""
        last_exception = None

        for attempt in range(API_CONFIG["max_retries"]):
            try:
                url = f"{self.base_url}/rates/{currency}"

                self.logger.info(
                    "Fetching exchange rate",
                    correlation_id=correlation_id,
                    currency=currency,
                    attempt=attempt + 1
                )

                response = self.session.get(
                    url,
                    timeout=API_CONFIG["request_timeout"],
                    headers={"X-Correlation-ID": correlation_id}
                )

                # Check HTTP status
                if response.status_code == 200:
                    data = response.json()

                    # Validate response structure
                    if not all(k in data for k in ["rate", "timestamp"]):
                        raise ValidationException(
                            "Invalid API response structure",
                            details={"response": data}
                        )

                    rate = Decimal(str(data["rate"]))
                    timestamp = datetime.fromisoformat(data["timestamp"])
                    confidence = data.get("confidence", 0.95)

                    return rate, timestamp, confidence

                elif response.status_code in {429, 500, 502, 503, 504}:
                    # Transient errors - retry
                    last_exception = NetworkException(
                        f"API returned {response.status_code}",
                        details={"status_code": response.status_code}
                    )
                else:
                    # Permanent errors - don't retry
                    raise NetworkException(
                        f"API request failed: {response.status_code}",
                        details={"status_code": response.status_code}
                    )

            except requests.exceptions.Timeout:
                last_exception = NetworkException("API request timeout")
            except requests.exceptions.ConnectionError as e:
                last_exception = NetworkException(f"Connection error: {str(e)}")
            except Exception as e:
                last_exception = PipelineException(
                    f"Unexpected error: {str(e)}",
                    ErrorCategory.UNKNOWN_ERROR
                )

            # Exponential backoff before retry
            if attempt < API_CONFIG["max_retries"] - 1:
                backoff = API_CONFIG["retry_backoff_base"] * (2 ** attempt)
                self.logger.warning(
                    "Retrying after backoff",
                    correlation_id=correlation_id,
                    attempt=attempt + 1,
                    backoff_seconds=backoff
                )
                time.sleep(backoff)

        # All retries exhausted
        raise last_exception

    def validate_account(self, account_id: str, correlation_id: str) -> Tuple[bool, float]:
        """
        Validate account with external service.

        Returns: (is_valid, confidence_score)
        """
        def _validate():
            return self._validate_account_with_retry(account_id, correlation_id)

        try:
            return self.circuit_breakers["account_validation"].call(_validate)
        except Exception as e:
            self.logger.error(
                "Account validation failed",
                correlation_id=correlation_id,
                account_id=account_id,
                error=str(e)
            )
            # FAIL-SAFE: On validation failure, require human review
            return False, 0.0

    def _validate_account_with_retry(self, account_id: str, correlation_id: str) -> Tuple[bool, float]:
        """Validate account with retry logic."""
        # Similar retry logic as exchange rate
        # Simplified for brevity - would follow same pattern
        url = f"{self.base_url}/accounts/{account_id}/validate"

        try:
            response = self.session.get(
                url,
                timeout=API_CONFIG["request_timeout"],
                headers={"X-Correlation-ID": correlation_id}
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("valid", False), data.get("confidence", 0.95)
            else:
                # FAIL-SAFE: Unknown status = invalid
                return False, 0.0

        except Exception:
            # FAIL-SAFE: Any error = invalid
            return False, 0.0

    def _validate_exchange_rate(self, currency: str, rate: Decimal) -> bool:
        """Validate exchange rate is within reasonable bounds."""
        # Simplified validation - in production would check historical ranges
        expected_ranges = {
            "EUR": (Decimal("0.8"), Decimal("1.3")),
            "GBP": (Decimal("0.7"), Decimal("1.5")),
            "JPY": (Decimal("100"), Decimal("160")),
            "CAD": (Decimal("1.2"), Decimal("1.5")),
            "AUD": (Decimal("1.3"), Decimal("1.7")),
            "CHF": (Decimal("0.8"), Decimal("1.1")),
        }

        if currency in expected_ranges:
            min_rate, max_rate = expected_ranges[currency]
            return min_rate <= rate <= max_rate

        return True  # Unknown currency, assume valid


# ============================================================================
# INPUT VALIDATION
# ============================================================================

class TransactionValidator:
    """Comprehensive input validation for transactions."""

    def __init__(self):
        self.logger = StructuredLogger("transaction_validator")

    def validate(self, transaction_data: Dict[str, Any], correlation_id: str) -> Transaction:
        """
        Validate transaction data and return validated Transaction object.

        Raises: ValidationException with detailed error information
        """
        errors = []
        warnings = []

        # Check required fields
        required_fields = ["account_id", "amount", "currency"]
        for field in required_fields:
            if field not in transaction_data:
                errors.append(f"Missing required field: {field}")

        if errors:
            raise ValidationException(
                "Missing required fields",
                details={"errors": errors, "correlation_id": correlation_id}
            )

        # Validate account_id
        account_id = transaction_data["account_id"]
        if not isinstance(account_id, str) or not account_id.strip():
            errors.append("account_id must be a non-empty string")
        elif len(account_id) > 50:
            errors.append("account_id exceeds maximum length of 50")
        elif not account_id.startswith("ACC"):
            warnings.append("account_id doesn't follow expected format (ACC...)")

        # Validate amount
        try:
            amount = Decimal(str(transaction_data["amount"]))

            # Check for negative or zero
            if amount <= 0:
                errors.append(f"amount must be positive, got {amount}")

            # Check minimum
            elif amount < FINANCIAL_LIMITS["min_amount"]:
                errors.append(f"amount below minimum {FINANCIAL_LIMITS['min_amount']}")

            # Check maximum
            elif amount > FINANCIAL_LIMITS["max_amount"]:
                errors.append(f"amount exceeds maximum {FINANCIAL_LIMITS['max_amount']}")

            # Check for suspicious amounts
            elif amount > FINANCIAL_LIMITS["suspicious_threshold"]:
                warnings.append(f"Large transaction amount: {amount}")

            # Validate decimal places (max 2 for currency)
            if amount.as_tuple().exponent < -2:
                errors.append("amount has more than 2 decimal places")

        except (InvalidOperation, ValueError, TypeError):
            errors.append(f"amount must be a valid decimal number")
            amount = Decimal("0")

        # Validate currency
        currency = transaction_data.get("currency", "").upper()
        if not currency:
            errors.append("currency is required")
        elif currency not in SUPPORTED_CURRENCIES:
            errors.append(f"Unsupported currency: {currency}. Supported: {SUPPORTED_CURRENCIES}")

        # If there are validation errors, fail fast
        if errors:
            self.logger.warning(
                "Transaction validation failed",
                correlation_id=correlation_id,
                errors=errors,
                warnings=warnings
            )
            raise ValidationException(
                "Transaction validation failed",
                details={"errors": errors, "warnings": warnings}
            )

        # Log warnings but continue
        if warnings:
            self.logger.warning(
                "Transaction validation warnings",
                correlation_id=correlation_id,
                warnings=warnings
            )

        # Create validated transaction object
        transaction = Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=account_id.strip(),
            amount=amount,
            currency=currency,
            status=TransactionStatus.PENDING,
            confidence_score=1.0,
            created_at=datetime.utcnow(),
            metadata={
                "correlation_id": correlation_id,
                "warnings": warnings,
                "original_data": transaction_data,
            }
        )

        self.logger.info(
            "Transaction validated successfully",
            correlation_id=correlation_id,
            transaction_id=transaction.transaction_id,
            warnings_count=len(warnings)
        )

        return transaction


# ============================================================================
# TRANSACTION PROCESSOR WITH RELIABILITY SAFEGUARDS
# ============================================================================

class ReliableTransactionProcessor:
    """Transaction processor with comprehensive reliability safeguards."""

    def __init__(self, database_path: str = "transactions.db"):
        self.database_path = database_path
        self.logger = StructuredLogger("transaction_processor")
        self.validator = TransactionValidator()
        self.api_client = ReliableExternalAPIClient()
        self.setup_database()

    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections with guaranteed cleanup."""
        conn = None
        try:
            conn = sqlite3.connect(self.database_path, timeout=10.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseException(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def setup_database(self):
        """Initialize database with comprehensive schema."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    correlation_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    usd_amount REAL,
                    exchange_rate REAL,
                    status TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    requires_review INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)

            # Audit log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Failed transactions (dead letter queue)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failed_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    original_data TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    error_category TEXT NOT NULL,
                    stack_trace TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0
                )
            """)

            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    labels TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()

        self.logger.info("Database initialized successfully")

    def process_transaction(self, transaction_data: Dict[str, Any]) -> ProcessingResult:
        """
        Process a single transaction with full reliability safeguards.

        This is the main entry point with comprehensive error handling,
        validation, monitoring, and fail-safe mechanisms.
        """
        start_time = time.time()
        correlation_id = str(uuid.uuid4())

        self.logger.info(
            "Starting transaction processing",
            correlation_id=correlation_id,
            data=transaction_data
        )

        transaction = None
        errors = []
        warnings = []
        confidence_score = 1.0

        try:
            # STEP 1: VALIDATION
            transaction = self.validator.validate(transaction_data, correlation_id)
            warnings.extend(transaction.metadata.get("warnings", []))

            self._audit_log(
                transaction.transaction_id,
                correlation_id,
                "VALIDATION_SUCCESS",
                TransactionStatus.VALIDATING
            )

            # STEP 2: ACCOUNT VALIDATION
            is_valid, validation_confidence = self.api_client.validate_account(
                transaction.account_id,
                correlation_id
            )

            confidence_score *= validation_confidence

            if not is_valid:
                # FAIL-SAFE: Invalid account requires review
                return self._create_review_required_result(
                    transaction,
                    "Account validation failed",
                    confidence_score,
                    start_time,
                    warnings
                )

            self._audit_log(
                transaction.transaction_id,
                correlation_id,
                "ACCOUNT_VALIDATED",
                TransactionStatus.PROCESSING
            )

            # STEP 3: CURRENCY CONVERSION (if needed)
            usd_amount = transaction.amount
            exchange_rate = Decimal("1.0")

            if transaction.currency != "USD":
                try:
                    rate, rate_timestamp, rate_confidence = self.api_client.get_exchange_rate(
                        transaction.currency,
                        correlation_id
                    )

                    confidence_score *= rate_confidence
                    exchange_rate = rate
                    usd_amount = transaction.amount * rate

                    # Round to 2 decimal places
                    usd_amount = usd_amount.quantize(Decimal("0.01"))

                    self.logger.info(
                        "Currency converted",
                        correlation_id=correlation_id,
                        transaction_id=transaction.transaction_id,
                        rate=str(rate),
                        usd_amount=str(usd_amount)
                    )

                except Exception as e:
                    # FAIL-SAFE: Currency conversion failure requires review
                    self.logger.error(
                        "Currency conversion failed",
                        correlation_id=correlation_id,
                        transaction_id=transaction.transaction_id,
                        error=str(e)
                    )
                    return self._create_review_required_result(
                        transaction,
                        f"Currency conversion failed: {str(e)}",
                        confidence_score,
                        start_time,
                        warnings
                    )

            # STEP 4: ANOMALY DETECTION
            is_anomalous, anomaly_reason = self._detect_anomalies(
                transaction.account_id,
                usd_amount,
                correlation_id
            )

            if is_anomalous:
                warnings.append(f"Anomaly detected: {anomaly_reason}")
                confidence_score *= 0.6

            # STEP 5: CONFIDENCE CHECK
            # FAIL-SAFE: Low confidence requires human review
            if confidence_score < 0.7:
                return self._create_review_required_result(
                    transaction,
                    f"Low confidence score: {confidence_score:.2f}",
                    confidence_score,
                    start_time,
                    warnings
                )

            # STEP 6: SAVE TO DATABASE (with transaction)
            self._save_transaction(
                transaction,
                usd_amount,
                exchange_rate,
                confidence_score,
                correlation_id
            )

            self._audit_log(
                transaction.transaction_id,
                correlation_id,
                "TRANSACTION_COMPLETED",
                TransactionStatus.COMPLETED
            )

            # STEP 7: RECORD METRICS
            processing_time = (time.time() - start_time) * 1000
            self._record_metric("transaction_processing_duration_ms", processing_time, {
                "status": "success",
                "currency": transaction.currency
            })

            self.logger.info(
                "Transaction processed successfully",
                correlation_id=correlation_id,
                transaction_id=transaction.transaction_id,
                processing_time_ms=processing_time,
                confidence_score=confidence_score
            )

            return ProcessingResult(
                transaction_id=transaction.transaction_id,
                status=TransactionStatus.COMPLETED,
                confidence_score=confidence_score,
                requires_review=False,
                original_amount=transaction.amount,
                usd_amount=usd_amount,
                currency=transaction.currency,
                errors=[],
                warnings=warnings,
                processing_time_ms=processing_time
            )

        except ValidationException as e:
            # Validation errors are user errors, not system failures
            processing_time = (time.time() - start_time) * 1000

            self.logger.warning(
                "Transaction validation failed",
                correlation_id=correlation_id,
                error=str(e),
                details=e.details
            )

            return ProcessingResult(
                transaction_id=transaction.transaction_id if transaction else "unknown",
                status=TransactionStatus.FAILED,
                confidence_score=0.0,
                requires_review=False,
                original_amount=Decimal("0"),
                usd_amount=None,
                currency="",
                errors=[str(e)] + e.details.get("errors", []),
                warnings=[],
                processing_time_ms=processing_time
            )

        except Exception as e:
            # Unexpected errors - log, save to dead letter queue, and fail gracefully
            processing_time = (time.time() - start_time) * 1000

            self.logger.critical(
                "Unexpected error processing transaction",
                correlation_id=correlation_id,
                error=str(e),
                stack_trace=traceback.format_exc()
            )

            # Save to dead letter queue
            self._save_to_dead_letter_queue(
                transaction.transaction_id if transaction else "unknown",
                correlation_id,
                transaction_data,
                e
            )

            self._record_metric("transaction_processing_duration_ms", processing_time, {
                "status": "error",
                "error_type": type(e).__name__
            })

            return ProcessingResult(
                transaction_id=transaction.transaction_id if transaction else "unknown",
                status=TransactionStatus.FAILED,
                confidence_score=0.0,
                requires_review=True,
                original_amount=transaction.amount if transaction else Decimal("0"),
                usd_amount=None,
                currency=transaction.currency if transaction else "",
                errors=[f"System error: {str(e)}"],
                warnings=warnings,
                processing_time_ms=processing_time
            )

    def _create_review_required_result(
        self,
        transaction: Transaction,
        reason: str,
        confidence_score: float,
        start_time: float,
        warnings: List[str]
    ) -> ProcessingResult:
        """Create result for transactions requiring human review."""
        processing_time = (time.time() - start_time) * 1000

        self.logger.warning(
            "Transaction requires human review",
            transaction_id=transaction.transaction_id,
            reason=reason,
            confidence_score=confidence_score
        )

        # Save to review queue
        self._save_for_review(transaction, reason, confidence_score)

        self._audit_log(
            transaction.transaction_id,
            transaction.metadata["correlation_id"],
            "REQUIRES_REVIEW",
            TransactionStatus.REQUIRES_REVIEW,
            {"reason": reason}
        )

        return ProcessingResult(
            transaction_id=transaction.transaction_id,
            status=TransactionStatus.REQUIRES_REVIEW,
            confidence_score=confidence_score,
            requires_review=True,
            original_amount=transaction.amount,
            usd_amount=None,
            currency=transaction.currency,
            errors=[],
            warnings=warnings + [reason],
            processing_time_ms=processing_time
        )

    def _detect_anomalies(
        self,
        account_id: str,
        usd_amount: Decimal,
        correlation_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect anomalous transactions.

        Returns: (is_anomalous, reason)
        """
        # Check for duplicate transactions (same account, similar amount, recent time)
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # Check last 5 minutes for duplicates
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM transactions
                WHERE account_id = ?
                AND ABS(usd_amount - ?) < 0.01
                AND created_at > datetime('now', '-5 minutes')
                AND status = 'completed'
            """, (account_id, float(usd_amount)))

            result = cursor.fetchone()
            if result and result["count"] > 0:
                return True, "Possible duplicate transaction"

            # Check daily transaction limit
            cursor.execute("""
                SELECT SUM(usd_amount) as daily_total
                FROM transactions
                WHERE account_id = ?
                AND DATE(created_at) = DATE('now')
                AND status = 'completed'
            """, (account_id,))

            result = cursor.fetchone()
            daily_total = Decimal(str(result["daily_total"] or 0))

            if daily_total + usd_amount > FINANCIAL_LIMITS["max_daily_per_account"]:
                return True, f"Daily limit exceeded: {daily_total + usd_amount}"

        return False, None

    def _save_transaction(
        self,
        transaction: Transaction,
        usd_amount: Decimal,
        exchange_rate: Decimal,
        confidence_score: float,
        correlation_id: str
    ):
        """Save transaction to database with atomic commit."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO transactions (
                    transaction_id, correlation_id, account_id, amount,
                    currency, usd_amount, exchange_rate, status,
                    confidence_score, requires_review, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.transaction_id,
                correlation_id,
                transaction.account_id,
                float(transaction.amount),
                transaction.currency,
                float(usd_amount),
                float(exchange_rate),
                TransactionStatus.COMPLETED.value,
                confidence_score,
                0,
                json.dumps(transaction.metadata)
            ))

            conn.commit()

    def _save_for_review(self, transaction: Transaction, reason: str, confidence_score: float):
        """Save transaction to review queue."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO transactions (
                    transaction_id, correlation_id, account_id, amount,
                    currency, status, confidence_score, requires_review, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.transaction_id,
                transaction.metadata["correlation_id"],
                transaction.account_id,
                float(transaction.amount),
                transaction.currency,
                TransactionStatus.REQUIRES_REVIEW.value,
                confidence_score,
                1,
                json.dumps({**transaction.metadata, "review_reason": reason})
            ))

            conn.commit()

    def _save_to_dead_letter_queue(
        self,
        transaction_id: str,
        correlation_id: str,
        original_data: Dict[str, Any],
        error: Exception
    ):
        """Save failed transaction to dead letter queue for manual review."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                error_category = error.category.value if isinstance(error, PipelineException) else "unknown_error"

                cursor.execute("""
                    INSERT INTO failed_transactions (
                        transaction_id, correlation_id, original_data,
                        error_message, error_category, stack_trace
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    transaction_id,
                    correlation_id,
                    json.dumps(original_data),
                    str(error),
                    error_category,
                    traceback.format_exc()
                ))

                conn.commit()

        except Exception as e:
            self.logger.critical(
                "Failed to save to dead letter queue",
                correlation_id=correlation_id,
                error=str(e)
            )

    def _audit_log(
        self,
        transaction_id: str,
        correlation_id: str,
        event_type: str,
        status: TransactionStatus,
        details: Optional[Dict] = None
    ):
        """Record audit log entry."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO audit_log (
                        transaction_id, correlation_id, event_type, status, details
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    transaction_id,
                    correlation_id,
                    event_type,
                    status.value,
                    json.dumps(details) if details else None
                ))

                conn.commit()

        except Exception as e:
            self.logger.error(
                "Failed to write audit log",
                correlation_id=correlation_id,
                error=str(e)
            )

    def _record_metric(self, metric_name: str, value: float, labels: Optional[Dict] = None):
        """Record performance metric."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO metrics (metric_name, metric_value, labels)
                    VALUES (?, ?, ?)
                """, (
                    metric_name,
                    value,
                    json.dumps(labels) if labels else None
                ))

                conn.commit()

        except Exception as e:
            self.logger.error("Failed to record metric", error=str(e))

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics."""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()

            # Processing time statistics
            cursor.execute("""
                SELECT
                    AVG(metric_value) as avg_ms,
                    MIN(metric_value) as min_ms,
                    MAX(metric_value) as max_ms
                FROM metrics
                WHERE metric_name = 'transaction_processing_duration_ms'
                AND timestamp > datetime('now', '-1 hour')
            """)

            timing_stats = cursor.fetchone()

            # Transaction status summary
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM transactions
                WHERE created_at > datetime('now', '-1 hour')
                GROUP BY status
            """)

            status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

            # Error rate
            total = sum(status_counts.values())
            failed = status_counts.get(TransactionStatus.FAILED.value, 0)
            error_rate = (failed / total * 100) if total > 0 else 0

            return {
                "timing_stats": {
                    "avg_ms": timing_stats["avg_ms"] if timing_stats else 0,
                    "min_ms": timing_stats["min_ms"] if timing_stats else 0,
                    "max_ms": timing_stats["max_ms"] if timing_stats else 0,
                },
                "status_counts": status_counts,
                "error_rate_percent": error_rate,
                "total_processed": total,
            }


# ============================================================================
# BATCH PROCESSOR WITH GRACEFUL DEGRADATION
# ============================================================================

class BatchProcessor:
    """Process multiple transactions with graceful degradation."""

    def __init__(self, processor: ReliableTransactionProcessor):
        self.processor = processor
        self.logger = StructuredLogger("batch_processor")

    def process_batch(
        self,
        transactions: List[Dict[str, Any]],
        fail_fast: bool = False
    ) -> Dict[str, Any]:
        """
        Process batch of transactions with graceful degradation.

        Args:
            transactions: List of transaction data dicts
            fail_fast: If True, stop on first error. If False, continue processing.

        Returns: Batch processing summary
        """
        start_time = time.time()
        batch_id = str(uuid.uuid4())

        self.logger.info(
            "Starting batch processing",
            batch_id=batch_id,
            transaction_count=len(transactions),
            fail_fast=fail_fast
        )

        results = {
            "batch_id": batch_id,
            "successful": 0,
            "failed": 0,
            "requires_review": 0,
            "total": len(transactions),
            "results": [],
            "processing_time_ms": 0,
        }

        for i, transaction_data in enumerate(transactions):
            try:
                result = self.processor.process_transaction(transaction_data)

                results["results"].append(result.to_dict())

                if result.status == TransactionStatus.COMPLETED:
                    results["successful"] += 1
                elif result.status == TransactionStatus.REQUIRES_REVIEW:
                    results["requires_review"] += 1
                else:
                    results["failed"] += 1

                    if fail_fast:
                        self.logger.warning(
                            "Batch processing stopped (fail_fast)",
                            batch_id=batch_id,
                            processed=i + 1,
                            total=len(transactions)
                        )
                        break

            except Exception as e:
                # Should not happen (processor handles all errors), but fail-safe
                self.logger.critical(
                    "Unexpected batch processing error",
                    batch_id=batch_id,
                    transaction_index=i,
                    error=str(e)
                )
                results["failed"] += 1

                if fail_fast:
                    break

        results["processing_time_ms"] = (time.time() - start_time) * 1000

        self.logger.info(
            "Batch processing completed",
            **{k: v for k, v in results.items() if k != "results"}
        )

        return results


# ============================================================================
# DEMO USAGE
# ============================================================================

def demo_reliable_pipeline():
    """Demonstrate the reliable pipeline with various scenarios."""
    print("=" * 70)
    print("RELIABLE FINANCIAL DATA PROCESSING PIPELINE")
    print("=" * 70)

    processor = ReliableTransactionProcessor()
    batch_processor = BatchProcessor(processor)

    # Test scenarios
    test_transactions = [
        # Valid transaction
        {"account_id": "ACC001", "amount": 100.50, "currency": "USD"},

        # Valid with currency conversion
        {"account_id": "ACC002", "amount": 75.25, "currency": "EUR"},

        # Large amount (warning)
        {"account_id": "ACC003", "amount": 55000.00, "currency": "USD"},

        # Invalid: missing field
        {"account_id": "ACC004", "amount": 100.00},

        # Invalid: negative amount
        {"account_id": "ACC005", "amount": -50.00, "currency": "USD"},

        # Invalid: unsupported currency
        {"account_id": "ACC006", "amount": 100.00, "currency": "XYZ"},

        # Valid
        {"account_id": "ACC007", "amount": 200.00, "currency": "GBP"},
    ]

    print("\nProcessing batch of test transactions...")
    print("-" * 70)

    results = batch_processor.process_batch(test_transactions, fail_fast=False)

    print(f"\nBatch ID: {results['batch_id']}")
    print(f"Total: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print(f"Requires Review: {results['requires_review']}")
    print(f"Processing Time: {results['processing_time_ms']:.2f}ms")

    print("\nDetailed Results:")
    print("-" * 70)

    for i, result in enumerate(results["results"], 1):
        print(f"\n{i}. Transaction {result['transaction_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Confidence: {result['confidence_score']:.2f}")
        print(f"   Requires Review: {result['requires_review']}")

        if result['errors']:
            print(f"   Errors: {result['errors']}")
        if result['warnings']:
            print(f"   Warnings: {result['warnings']}")

        if result['status'] == 'completed':
            print(f"   Amount: {result['original_amount']} {result['currency']}")
            print(f"   USD Amount: {result['usd_amount']}")

    # Get metrics
    print("\n" + "=" * 70)
    print("SYSTEM METRICS")
    print("=" * 70)

    metrics = processor.get_metrics_summary()
    print(f"\nProcessing Time Statistics:")
    print(f"  Average: {metrics['timing_stats']['avg_ms']:.2f}ms")
    print(f"  Min: {metrics['timing_stats']['min_ms']:.2f}ms")
    print(f"  Max: {metrics['timing_stats']['max_ms']:.2f}ms")

    print(f"\nStatus Summary:")
    for status, count in metrics['status_counts'].items():
        print(f"  {status}: {count}")

    print(f"\nError Rate: {metrics['error_rate_percent']:.1f}%")

    print("\n" + "=" * 70)
    print("RELIABILITY SAFEGUARDS DEMONSTRATED")
    print("=" * 70)
    print("\n✓ Comprehensive input validation")
    print("✓ Fail-safe error handling")
    print("✓ Confidence scoring")
    print("✓ Human-in-the-loop for low confidence")
    print("✓ Anomaly detection")
    print("✓ Audit trail")
    print("✓ Dead letter queue for failures")
    print("✓ Structured logging")
    print("✓ Performance metrics")
    print("✓ Graceful degradation")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    demo_reliable_pipeline()
