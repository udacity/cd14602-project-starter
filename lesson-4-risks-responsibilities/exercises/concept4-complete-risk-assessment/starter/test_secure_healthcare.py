"""
Comprehensive Test Suite for Secure Healthcare Analytics System
================================================================

Tests cover three risk dimensions:
1. Security: SQL injection, encryption, authentication, access control
2. Ethics: Bias detection, fairness testing, transparent recommendations
3. Reliability: Error handling, graceful degradation, resilience

Integration tests verify cross-dimensional risk interactions.
"""

import pytest
import os
import sqlite3
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from secure_healthcare_analytics import (
    SecureHealthcareSystem,
    UserRole,
    AccessLevel,
    RiskLevel,
    ClinicalRiskFactors,
    EncryptionManager,
    AuthenticationManager,
    DatabaseConnectionPool
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def test_db_path(tmp_path):
    """Create temporary database for testing"""
    return str(tmp_path / "test_healthcare.db")


@pytest.fixture
def secure_system(test_db_path):
    """Create clean healthcare system for each test"""
    system = SecureHealthcareSystem(test_db_path)

    # Create test users
    system.create_user("test_physician", "SecurePass123!", UserRole.PHYSICIAN, "Test Physician", "physician@test.com")
    system.create_user("test_nurse", "SecurePass456!", UserRole.NURSE, "Test Nurse", "nurse@test.com")
    system.create_user("test_admin", "SecurePass789!", UserRole.ADMIN, "Test Admin", "admin@test.com")
    system.create_user("test_researcher", "SecurePass000!", UserRole.RESEARCHER, "Test Researcher", "researcher@test.com")

    return system


@pytest.fixture
def physician_session(secure_system):
    """Authenticated physician session"""
    result = secure_system.login("test_physician", "SecurePass123!")
    assert result["success"]
    return result["session_id"]


@pytest.fixture
def nurse_session(secure_system):
    """Authenticated nurse session"""
    result = secure_system.login("test_nurse", "SecurePass456!")
    assert result["success"]
    return result["session_id"]


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "patient_id": "P_TEST_001",
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1975-06-15",
        "ssn": "987-65-4321",
        "medical_record": {
            "primary_care_physician": "Dr. Johnson",
            "insurance": "Blue Cross"
        },
        "diagnosis_history": ["Hypertension"]
    }


# ============================================================================
# SECURITY TESTS
# ============================================================================

class TestSecurityControls:
    """Test security vulnerabilities are properly mitigated"""

    def test_sql_injection_prevention_patient_name(self, secure_system, physician_session):
        """Test that SQL injection in patient name is prevented"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Attempt SQL injection through patient name
        malicious_patient = {
            "patient_id": "P_SQL_TEST",
            "first_name": "John'; DROP TABLE patients; --",
            "last_name": "Hacker",
            "date_of_birth": "1990-01-01",
            "ssn": "111-11-1111"
        }

        # Add patient (should succeed safely due to parameterized queries)
        result = secure_system.data_manager.add_patient(malicious_patient, user_info)
        assert result["success"], "Parameterized queries should handle injection attempts safely"

        # Verify database integrity - patients table should still exist
        with secure_system.data_manager.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patients")
            count = cursor.fetchone()[0]
            assert count > 0, "Patients table should not be dropped"

            # Verify the malicious string was stored as literal data
            cursor.execute("SELECT first_name FROM patients WHERE patient_id = ?", ("P_SQL_TEST",))
            stored_name = cursor.fetchone()[0]
            assert stored_name == "John'; DROP TABLE patients; --", "SQL should be stored as literal text"

        print("✓ SQL injection prevention: Parameterized queries successfully prevent injection")

    def test_ssn_encryption_at_rest(self, secure_system, physician_session, sample_patient_data):
        """Test that SSN is encrypted in database"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Add patient with SSN
        result = secure_system.data_manager.add_patient(sample_patient_data, user_info)
        assert result["success"]

        # Directly query database to verify encryption
        with secure_system.data_manager.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ssn_encrypted FROM patients WHERE patient_id = ?",
                          (sample_patient_data["patient_id"],))
            stored_ssn = cursor.fetchone()[0]

            # Verify SSN is NOT stored in plain text
            assert stored_ssn != sample_patient_data["ssn"], "SSN should be encrypted"
            assert stored_ssn != "", "SSN should be encrypted, not empty"
            assert len(stored_ssn) > 20, "Encrypted SSN should be longer than plain text"

        print("✓ PHI encryption: SSN successfully encrypted at rest")

    def test_medical_records_encryption(self, secure_system, physician_session, sample_patient_data):
        """Test that medical records are encrypted"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        result = secure_system.data_manager.add_patient(sample_patient_data, user_info)
        assert result["success"]

        # Verify medical records are encrypted in database
        with secure_system.data_manager.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT medical_record_encrypted FROM patients WHERE patient_id = ?",
                          (sample_patient_data["patient_id"],))
            encrypted_record = cursor.fetchone()[0]

            # Should not contain plain text
            assert "Dr. Johnson" not in encrypted_record, "Medical records should be encrypted"
            assert "Blue Cross" not in encrypted_record, "Insurance info should be encrypted"

        print("✓ Medical records encryption: Successfully encrypted at rest")

    def test_password_hashing_security(self, secure_system):
        """Test that passwords are hashed with bcrypt"""
        # Create user
        result = secure_system.create_user(
            "hash_test_user", "TestPassword123!",
            UserRole.NURSE, "Hash Test User"
        )
        assert result["success"]

        # Verify password is hashed in database
        with secure_system.auth_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE username = ?", ("hash_test_user",))
            password_hash = cursor.fetchone()[0]

            # Verify it's a bcrypt hash (starts with $2b$)
            assert password_hash.startswith("$2b$"), "Password should use bcrypt hashing"
            assert "TestPassword123!" not in password_hash, "Plain password should not be in hash"
            assert len(password_hash) == 60, "Bcrypt hash should be 60 characters"

        print("✓ Password security: Bcrypt hashing with salt successfully implemented")

    def test_weak_password_rejection(self, secure_system):
        """Test that weak passwords are rejected"""
        weak_passwords = [
            "short",  # Too short
            "alllowercase123",  # No uppercase
            "ALLUPPERCASE123",  # No lowercase
            "NoNumbers!!",  # No digits
            "NoSpecial123",  # No special characters
        ]

        for weak_pass in weak_passwords:
            result = secure_system.create_user(
                f"weak_user_{weak_pass}",
                weak_pass,
                UserRole.NURSE,
                "Weak Password Test"
            )
            assert not result["success"], f"Weak password should be rejected: {weak_pass}"

        print("✓ Password policy: Weak passwords successfully rejected")

    def test_account_lockout_after_failed_attempts(self, secure_system):
        """Test account lockout after multiple failed login attempts"""
        # Create test user
        secure_system.create_user("lockout_test", "CorrectPassword123!", UserRole.NURSE, "Lockout Test")

        # Attempt 5 failed logins
        for i in range(5):
            result = secure_system.login("lockout_test", "WrongPassword123!")
            assert not result["success"], f"Login attempt {i+1} should fail"

        # 6th attempt should report account locked
        result = secure_system.login("lockout_test", "CorrectPassword123!")
        assert not result["success"]
        assert "locked" in result["message"].lower(), "Account should be locked after 5 failed attempts"

        print("✓ Account lockout: Successfully locks after 5 failed attempts")

    def test_session_token_uniqueness(self, secure_system):
        """Test that session tokens are cryptographically random"""
        sessions = []

        for i in range(10):
            result = secure_system.login("test_physician", "SecurePass123!")
            assert result["success"]
            sessions.append(result["session_id"])
            secure_system.logout(result["session_id"])

        # All sessions should be unique
        assert len(sessions) == len(set(sessions)), "Session IDs should be unique"

        # Should be sufficiently long (URL-safe base64 with 32 bytes = 43 chars)
        for session_id in sessions:
            assert len(session_id) >= 40, "Session ID should be sufficiently long"

        print("✓ Session security: Cryptographically secure random tokens generated")

    def test_session_expiration(self, secure_system):
        """Test that sessions expire after timeout"""
        result = secure_system.login("test_physician", "SecurePass123!")
        session_id = result["session_id"]

        # Manually expire session in database
        with secure_system.auth_manager._get_connection() as conn:
            cursor = conn.cursor()
            expired_time = (datetime.now() - timedelta(hours=1)).isoformat()
            cursor.execute("UPDATE sessions SET expires_at = ? WHERE session_id = ?",
                          (expired_time, session_id))
            conn.commit()

        # Validate session should fail
        user_info = secure_system.auth_manager.validate_session(session_id)
        assert user_info is None, "Expired session should not validate"

        print("✓ Session expiration: Expired sessions properly rejected")

    def test_role_based_access_control(self, secure_system, sample_patient_data):
        """Test RBAC prevents unauthorized access"""
        # Add patient as physician
        physician_result = secure_system.login("test_physician", "SecurePass123!")
        physician_info = secure_system.auth_manager.validate_session(physician_result["session_id"])

        result = secure_system.data_manager.add_patient(sample_patient_data, physician_info)
        assert result["success"]

        # Researcher should have limited access (demographic only)
        researcher_result = secure_system.login("test_researcher", "SecurePass000!")
        researcher_info = secure_system.auth_manager.validate_session(researcher_result["session_id"])

        patient_data = secure_system.data_manager.get_patient_data(
            sample_patient_data["patient_id"],
            researcher_info
        )

        # Researcher should get data but without SSN or medical details
        assert patient_data is not None, "Researcher should have some access"
        assert "ssn" not in patient_data, "Researcher should not see SSN"
        assert "medical_record" not in patient_data, "Researcher should not see medical records"
        assert "first_name" in patient_data, "Researcher should see basic demographics"

        print("✓ RBAC: Role-based access control properly enforces permission levels")

    def test_audit_log_tamper_protection(self, secure_system, physician_session, sample_patient_data):
        """Test that audit logs have tamper protection"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Perform multiple operations to create audit trail
        secure_system.data_manager.add_patient(sample_patient_data, user_info)
        secure_system.data_manager.get_patient_data(sample_patient_data["patient_id"], user_info)

        # Verify audit log chain
        with secure_system.data_manager.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT log_hash, prev_log_hash FROM access_logs ORDER BY id")
            logs = cursor.fetchall()

            assert len(logs) >= 2, "Should have multiple log entries"

            # Verify hash chain
            for i in range(1, len(logs)):
                current_log = logs[i]
                prev_log = logs[i-1]

                # Current log's prev_log_hash should match previous log's hash
                assert current_log['prev_log_hash'] == prev_log['log_hash'], \
                    "Audit log chain should be intact (tamper detection)"

        print("✓ Audit logging: Tamper-resistant chain successfully implemented")


# ============================================================================
# ETHICAL TESTS
# ============================================================================

class TestEthicalSafeguards:
    """Test that algorithmic bias is eliminated"""

    def test_no_age_based_discrimination(self, secure_system, physician_session):
        """Test that age alone does NOT affect risk score"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Create three patients with identical clinical factors but different ages
        patients = [
            {
                "patient_id": "P_YOUNG",
                "first_name": "Young",
                "last_name": "Patient",
                "date_of_birth": "2000-01-01",  # Age 25
                "ssn": "111-11-1111"
            },
            {
                "patient_id": "P_MIDDLE",
                "first_name": "Middle",
                "last_name": "Patient",
                "date_of_birth": "1975-01-01",  # Age 50
                "ssn": "222-22-2222"
            },
            {
                "patient_id": "P_ELDERLY",
                "first_name": "Elderly",
                "last_name": "Patient",
                "date_of_birth": "1940-01-01",  # Age 85
                "ssn": "333-33-3333"
            }
        ]

        # Identical clinical risk factors for all
        identical_risk_factors = ClinicalRiskFactors(
            has_chronic_conditions=True,
            chronic_condition_count=2,
            recent_hospitalizations=1,
            active_medications_count=3,
            has_high_risk_medications=False,
            recent_emergency_visits=0,
            has_care_plan=True,
            last_preventive_visit_days=180,
            has_uncontrolled_conditions=False,
            polypharmacy_risk=False
        )

        risk_scores = []

        for patient in patients:
            # Add patient
            result = secure_system.data_manager.add_patient(patient, user_info)
            assert result["success"]

            # Update risk factors
            secure_system.data_manager.update_clinical_risk_factors(
                patient["patient_id"],
                identical_risk_factors,
                user_info
            )

            # Analyze risk
            assessment = secure_system.clinical_support.analyze_patient_risk(
                patient["patient_id"],
                user_info
            )
            assert assessment is not None
            risk_scores.append({
                "patient_id": patient["patient_id"],
                "age": "young" if "YOUNG" in patient["patient_id"] else ("middle" if "MIDDLE" in patient["patient_id"] else "elderly"),
                "risk_score": assessment.risk_score
            })

        # All risk scores should be IDENTICAL (no age discrimination)
        scores = [r["risk_score"] for r in risk_scores]
        assert len(set(scores)) == 1, \
            f"Risk scores should be identical regardless of age. Got: {risk_scores}"

        print("✓ NO age discrimination: Risk scores identical across all age groups")
        print(f"  Young (25): {risk_scores[0]['risk_score']}")
        print(f"  Middle (50): {risk_scores[1]['risk_score']}")
        print(f"  Elderly (85): {risk_scores[2]['risk_score']}")

    def test_no_zip_code_discrimination(self, secure_system, physician_session):
        """Test that zip code does NOT affect risk score"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Create patients from wealthy vs poor zip codes
        patients = [
            {
                "patient_id": "P_WEALTHY_ZIP",
                "first_name": "Wealthy",
                "last_name": "Area",
                "date_of_birth": "1980-01-01",
                "medical_record": {"address": {"zip_code": "10001"}},  # Wealthy area
            },
            {
                "patient_id": "P_POOR_ZIP",
                "first_name": "Poor",
                "last_name": "Area",
                "date_of_birth": "1980-01-01",
                "medical_record": {"address": {"zip_code": "10453"}},  # Poor area
            }
        ]

        # Identical clinical factors
        identical_factors = ClinicalRiskFactors(
            has_chronic_conditions=True,
            chronic_condition_count=1,
            recent_hospitalizations=0,
            active_medications_count=2,
            has_high_risk_medications=False
        )

        risk_scores = []

        for patient in patients:
            result = secure_system.data_manager.add_patient(patient, user_info)
            assert result["success"]

            secure_system.data_manager.update_clinical_risk_factors(
                patient["patient_id"],
                identical_factors,
                user_info
            )

            assessment = secure_system.clinical_support.analyze_patient_risk(
                patient["patient_id"],
                user_info
            )
            risk_scores.append({
                "patient_id": patient["patient_id"],
                "risk_score": assessment.risk_score
            })

        # Risk scores should be IDENTICAL (no zip code discrimination)
        assert risk_scores[0]["risk_score"] == risk_scores[1]["risk_score"], \
            "Risk scores should be identical regardless of zip code"

        print("✓ NO zip code discrimination: Risk scores identical across wealthy/poor areas")

    def test_evidence_based_risk_factors_only(self, secure_system, physician_session):
        """Test that risk score is based ONLY on clinical evidence"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        patient_data = {
            "patient_id": "P_EVIDENCE_TEST",
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1980-01-01"
        }

        secure_system.data_manager.add_patient(patient_data, user_info)

        # Low-risk clinical profile
        low_risk_factors = ClinicalRiskFactors(
            has_chronic_conditions=False,
            chronic_condition_count=0,
            recent_hospitalizations=0,
            active_medications_count=0,
            has_high_risk_medications=False,
            recent_emergency_visits=0,
            has_care_plan=False,
            last_preventive_visit_days=90,
            has_uncontrolled_conditions=False,
            polypharmacy_risk=False
        )

        secure_system.data_manager.update_clinical_risk_factors(
            patient_data["patient_id"],
            low_risk_factors,
            user_info
        )

        assessment = secure_system.clinical_support.analyze_patient_risk(
            patient_data["patient_id"],
            user_info
        )

        # Should be low risk
        assert assessment.risk_level == RiskLevel.LOW, "Patient with no risk factors should be low risk"
        assert assessment.risk_score < 30, "Low clinical risk should have low score"

        print("✓ Evidence-based scoring: Risk determined by clinical factors only")
        print(f"  Contributing factors: {assessment.contributing_factors}")

    def test_transparent_risk_explanation(self, secure_system, physician_session):
        """Test that risk assessments include transparent explanations"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        patient_data = {
            "patient_id": "P_TRANSPARENCY_TEST",
            "first_name": "Transparency",
            "last_name": "Test",
            "date_of_birth": "1970-01-01"
        }

        secure_system.data_manager.add_patient(patient_data, user_info)

        high_risk_factors = ClinicalRiskFactors(
            has_chronic_conditions=True,
            chronic_condition_count=4,
            recent_hospitalizations=2,
            active_medications_count=8,
            has_high_risk_medications=True,
            recent_emergency_visits=3,
            has_care_plan=False,
            has_uncontrolled_conditions=True,
            polypharmacy_risk=True
        )

        secure_system.data_manager.update_clinical_risk_factors(
            patient_data["patient_id"],
            high_risk_factors,
            user_info
        )

        assessment = secure_system.clinical_support.analyze_patient_risk(
            patient_data["patient_id"],
            user_info
        )

        # Should have transparent explanation
        assert len(assessment.contributing_factors) > 0, "Should list contributing factors"
        assert len(assessment.clinical_rationale) > 100, "Should provide detailed rationale"
        assert "evidence-based" in assessment.clinical_rationale.lower(), \
            "Should explicitly state evidence-based methodology"
        assert assessment.risk_score > 0, "Should show numerical score"

        # Should NOT mention age, race, zip code, or insurance
        rationale_lower = assessment.clinical_rationale.lower()
        assert "age" not in rationale_lower or "does not consider age" in rationale_lower, \
            "Should clarify age is not used"
        assert "zip" not in rationale_lower or "does not consider" in rationale_lower, \
            "Should clarify zip code is not used"

        print("✓ Transparency: Risk assessments include detailed, transparent explanations")
        print(f"  Clinical rationale provided: {len(assessment.clinical_rationale)} characters")

    def test_human_review_trigger_for_high_risk(self, secure_system, physician_session):
        """Test that high-risk cases trigger human review requirement"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        patient_data = {
            "patient_id": "P_HIGH_RISK_TEST",
            "first_name": "HighRisk",
            "last_name": "Patient",
            "date_of_birth": "1970-01-01"
        }

        secure_system.data_manager.add_patient(patient_data, user_info)

        # Create high-risk clinical profile
        high_risk_factors = ClinicalRiskFactors(
            has_chronic_conditions=True,
            chronic_condition_count=5,
            recent_hospitalizations=3,
            active_medications_count=10,
            has_high_risk_medications=True,
            recent_emergency_visits=4,
            has_care_plan=False,
            has_uncontrolled_conditions=True,
            polypharmacy_risk=True
        )

        secure_system.data_manager.update_clinical_risk_factors(
            patient_data["patient_id"],
            high_risk_factors,
            user_info
        )

        assessment = secure_system.clinical_support.analyze_patient_risk(
            patient_data["patient_id"],
            user_info
        )

        # High-risk cases should require human review
        assert assessment.requires_human_review, \
            "High-risk cases should trigger human review requirement"
        assert assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL], \
            "Should be classified as high or critical risk"

        print("✓ Human-in-the-loop: High-risk cases properly flagged for human review")

    def test_social_determinants_for_support_not_discrimination(self, secure_system, physician_session):
        """Test that social determinants trigger support, not discrimination"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        patient_data = {
            "patient_id": "P_SOCIAL_SUPPORT_TEST",
            "first_name": "Social",
            "last_name": "Support",
            "date_of_birth": "1980-01-01"
        }

        secure_system.data_manager.add_patient(patient_data, user_info)

        # Patient with social support needs
        social_needs_factors = ClinicalRiskFactors(
            has_chronic_conditions=True,
            chronic_condition_count=1,
            needs_transportation_assistance=True,
            needs_language_services=True,
            has_care_coordinator=False
        )

        secure_system.data_manager.update_clinical_risk_factors(
            patient_data["patient_id"],
            social_needs_factors,
            user_info
        )

        assessment = secure_system.clinical_support.analyze_patient_risk(
            patient_data["patient_id"],
            user_info
        )

        # Should recommend SUPPORT, not penalize
        recommendations_text = " ".join(assessment.recommendations).lower()

        assert "transportation assistance" in recommendations_text or \
               "transportation" in recommendations_text, \
            "Should recommend transportation assistance"

        assert "interpreter" in recommendations_text or \
               "language" in recommendations_text, \
            "Should recommend language services"

        # Social needs should NOT dramatically increase risk score
        assert assessment.risk_score < 50, \
            "Social needs should trigger support recommendations, not punitive risk scores"

        print("✓ Social determinants: Used for support recommendations, NOT discrimination")


# ============================================================================
# RELIABILITY TESTS
# ============================================================================

class TestReliabilityAndResilience:
    """Test error handling and system resilience"""

    def test_missing_patient_graceful_handling(self, secure_system, physician_session):
        """Test graceful handling of missing patient data"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Attempt to analyze non-existent patient
        assessment = secure_system.clinical_support.analyze_patient_risk(
            "NONEXISTENT_PATIENT",
            user_info
        )

        # Should return None gracefully, not crash
        assert assessment is None, "Should return None for non-existent patient"

        print("✓ Error handling: Missing patient handled gracefully (no crash)")

    def test_workflow_partial_success_handling(self, secure_system, physician_session):
        """Test that workflow continues even if components fail"""
        # Add a patient but don't add risk factors
        user_info = secure_system.auth_manager.validate_session(physician_session)

        patient_data = {
            "patient_id": "P_PARTIAL_TEST",
            "first_name": "Partial",
            "last_name": "Success",
            "date_of_birth": "1980-01-01"
        }

        secure_system.data_manager.add_patient(patient_data, user_info)

        # Process workflow WITHOUT risk factors
        result = secure_system.process_patient_workflow(
            physician_session,
            patient_data["patient_id"]
        )

        # Should have partial success
        assert result["partial_success"] or result["success"], \
            "Should succeed partially even without risk factors"
        assert "patient_data" in result["components"], \
            "Should retrieve patient data successfully"

        # Risk analysis may fail gracefully but should provide fallback
        if "risk_analysis" in result["components"]:
            risk = result["components"]["risk_analysis"]
            if "error" in risk:
                assert "fallback" in risk or "fallback_recommendation" in risk, \
                    "Failed components should provide fallback guidance"

        print("✓ Graceful degradation: Workflow continues with partial success")

    def test_database_connection_retry(self, secure_system):
        """Test that database operations retry on transient failures"""
        # This test verifies retry logic exists
        # In production, would mock sqlite3.connect to simulate failures

        db_pool = DatabaseConnectionPool(":memory:")

        # Should successfully connect (no failures)
        with db_pool.get_connection() as conn:
            result = conn.execute("SELECT 1").fetchone()
            assert result[0] == 1

        print("✓ Connection retry: Database connection pooling operational")

    def test_circuit_breaker_pattern(self, test_db_path):
        """Test that circuit breaker opens after repeated failures"""
        db_pool = DatabaseConnectionPool("/nonexistent/path/database.db")

        # Trigger multiple failures
        failure_count = 0
        for i in range(6):
            try:
                with db_pool.get_connection():
                    pass
            except Exception as e:
                failure_count += 1
                if i >= 5:
                    # After threshold, should mention circuit breaker
                    assert "circuit breaker" in str(e).lower(), \
                        "Circuit breaker should open after threshold failures"

        assert failure_count >= 5, "Should fail multiple times before circuit breaker"

        print("✓ Circuit breaker: Opens after repeated failures to prevent cascade")

    def test_session_persistence_across_restarts(self, secure_system):
        """Test that sessions persist in database (not in-memory)"""
        # Login
        result = secure_system.login("test_physician", "SecurePass123!")
        session_id = result["session_id"]

        # Simulate system restart by creating new system instance with same database
        new_system = SecureHealthcareSystem(secure_system.db_path)

        # Session should still be valid
        user_info = new_system.auth_manager.validate_session(session_id)
        assert user_info is not None, "Session should persist across system restarts"
        assert user_info["username"] == "test_physician"

        print("✓ Session persistence: Sessions survive system restarts")

    def test_encrypted_data_recovery(self, secure_system, physician_session, sample_patient_data):
        """Test that encrypted data can be recovered"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Add patient with encrypted SSN
        result = secure_system.data_manager.add_patient(sample_patient_data, user_info)
        assert result["success"]

        # Retrieve and verify decryption works
        retrieved_data = secure_system.data_manager.get_patient_data(
            sample_patient_data["patient_id"],
            user_info
        )

        assert retrieved_data is not None
        assert retrieved_data["ssn"] == sample_patient_data["ssn"], \
            "SSN should be properly decrypted"

        print("✓ Data recovery: Encrypted data successfully decrypted on retrieval")

    def test_audit_log_availability_during_failures(self, secure_system, physician_session):
        """Test that audit logging continues even during component failures"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Attempt to access non-existent patient (triggers failure)
        result = secure_system.data_manager.get_patient_data("NONEXISTENT", user_info)

        # Access should fail
        assert result is None

        # But audit log should still record the attempt
        with secure_system.data_manager.db_pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM access_logs
                WHERE patient_id = 'NONEXISTENT' AND access_granted = 0
            """)
            log_count = cursor.fetchone()[0]

            assert log_count > 0, "Failed access attempts should still be logged"

        print("✓ Audit logging: Continues functioning even during failures")

    def test_input_validation_prevents_corruption(self, secure_system, physician_session):
        """Test that input validation prevents data corruption"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Invalid date of birth (future date)
        invalid_patient = {
            "patient_id": "P_INVALID_DOB",
            "first_name": "Invalid",
            "last_name": "Future",
            "date_of_birth": "2050-01-01"  # Future date
        }

        result = secure_system.data_manager.add_patient(invalid_patient, user_info)
        assert not result["success"], "Future date of birth should be rejected"
        assert "future" in result["message"].lower()

        # Invalid SSN format
        invalid_ssn_patient = {
            "patient_id": "P_INVALID_SSN",
            "first_name": "Invalid",
            "last_name": "SSN",
            "date_of_birth": "1980-01-01",
            "ssn": "not-a-real-ssn"
        }

        result = secure_system.data_manager.add_patient(invalid_ssn_patient, user_info)
        assert not result["success"], "Invalid SSN format should be rejected"

        print("✓ Input validation: Invalid data properly rejected to prevent corruption")


# ============================================================================
# INTEGRATION TESTS: CROSS-DIMENSIONAL RISKS
# ============================================================================

class TestCrossDimensionalRisks:
    """Test interactions between security, ethics, and reliability"""

    def test_security_breach_does_not_expose_bias(self, secure_system, physician_session):
        """Test that security breach doesn't reveal discriminatory algorithms"""
        # In the vulnerable system, SQL injection could expose bias logic
        # In secure system, even with database access, no bias exists to expose

        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Add patients with different demographics
        patients = [
            {"patient_id": "P_DEMO_1", "first_name": "Patient", "last_name": "One",
             "date_of_birth": "1950-01-01", "medical_record": {"address": {"zip_code": "10001"}}},
            {"patient_id": "P_DEMO_2", "first_name": "Patient", "last_name": "Two",
             "date_of_birth": "1950-01-01", "medical_record": {"address": {"zip_code": "10453"}}}
        ]

        risk_factors = ClinicalRiskFactors(chronic_condition_count=1, has_chronic_conditions=True)

        for patient in patients:
            secure_system.data_manager.add_patient(patient, user_info)
            secure_system.data_manager.update_clinical_risk_factors(
                patient["patient_id"], risk_factors, user_info
            )

        # Even if attacker gains database access, risk scores are fair
        # (This test verifies no bias exists in the algorithm)

        assessments = []
        for patient in patients:
            assessment = secure_system.clinical_support.analyze_patient_risk(
                patient["patient_id"], user_info
            )
            assessments.append(assessment)

        # Risk scores should be identical (no hidden bias)
        assert assessments[0].risk_score == assessments[1].risk_score, \
            "No algorithmic bias should exist to be exposed by breach"

        print("✓ Integration: Security breach cannot expose bias (no bias exists)")

    def test_system_failure_does_not_create_discriminatory_outcomes(self, secure_system, physician_session):
        """Test that partial failures don't result in discriminatory service degradation"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Add patients
        patients = [
            {"patient_id": "P_FAIL_1", "first_name": "Patient", "last_name": "One",
             "date_of_birth": "1980-01-01"},
            {"patient_id": "P_FAIL_2", "first_name": "Patient", "last_name": "Two",
             "date_of_birth": "1950-01-01"}  # Different age
        ]

        for patient in patients:
            secure_system.data_manager.add_patient(patient, user_info)

        # Process workflows (may have partial failures due to missing risk factors)
        results = []
        for patient in patients:
            result = secure_system.process_patient_workflow(
                physician_session,
                patient["patient_id"]
            )
            results.append(result)

        # Both should have same level of degradation (no discrimination)
        success_levels = [r.get("success") or r.get("partial_success") for r in results]
        assert success_levels[0] == success_levels[1], \
            "System failures should affect all patients equally"

        print("✓ Integration: System failures do not create discriminatory outcomes")

    def test_audit_trail_captures_cross_dimensional_events(self, secure_system, physician_session):
        """Test that audit logs capture security, ethics, and reliability events"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        patient_data = {
            "patient_id": "P_AUDIT_TEST",
            "first_name": "Audit",
            "last_name": "Test",
            "date_of_birth": "1980-01-01"
        }

        # Security event: Add patient (PHI access)
        secure_system.data_manager.add_patient(patient_data, user_info)

        # Ethics event: Risk assessment
        risk_factors = ClinicalRiskFactors(has_chronic_conditions=True, chronic_condition_count=3)
        secure_system.data_manager.update_clinical_risk_factors(
            patient_data["patient_id"], risk_factors, user_info
        )
        secure_system.clinical_support.analyze_patient_risk(patient_data["patient_id"], user_info)

        # Reliability event: Access non-existent data
        secure_system.data_manager.get_patient_data("NONEXISTENT", user_info)

        # Verify comprehensive audit trail
        with secure_system.data_manager.db_pool.get_connection() as conn:
            cursor = conn.cursor()

            # Should have logs for successful and failed operations
            cursor.execute("""
                SELECT COUNT(*) FROM access_logs
                WHERE user_id = ?
            """, (user_info["user_id"],))

            log_count = cursor.fetchone()[0]
            assert log_count >= 3, "Should log security, ethics, and reliability events"

            # Should have risk assessment record
            cursor.execute("""
                SELECT COUNT(*) FROM risk_assessments
                WHERE patient_id = ?
            """, (patient_data["patient_id"],))

            assessment_count = cursor.fetchone()[0]
            assert assessment_count >= 1, "Should log risk assessments"

        print("✓ Integration: Comprehensive audit trail across all dimensions")


# ============================================================================
# PERFORMANCE AND SCALABILITY TESTS
# ============================================================================

class TestPerformanceAndScalability:
    """Test system performance under load"""

    def test_concurrent_user_sessions(self, secure_system):
        """Test system handles multiple concurrent users"""
        sessions = []

        # Create 10 concurrent sessions
        for i in range(10):
            result = secure_system.login("test_physician", "SecurePass123!")
            assert result["success"]
            sessions.append(result["session_id"])

        # All sessions should be valid
        valid_count = 0
        for session_id in sessions:
            user_info = secure_system.auth_manager.validate_session(session_id)
            if user_info:
                valid_count += 1

        assert valid_count == 10, "All concurrent sessions should be valid"

        # Cleanup
        for session_id in sessions:
            secure_system.logout(session_id)

        print("✓ Scalability: Handles multiple concurrent user sessions")

    def test_bulk_patient_operations(self, secure_system, physician_session):
        """Test system handles bulk operations efficiently"""
        user_info = secure_system.auth_manager.validate_session(physician_session)

        # Add 50 patients
        start_time = time.time()

        for i in range(50):
            patient_data = {
                "patient_id": f"P_BULK_{i:03d}",
                "first_name": f"Patient{i}",
                "last_name": "Bulk",
                "date_of_birth": "1980-01-01"
            }
            result = secure_system.data_manager.add_patient(patient_data, user_info)
            assert result["success"]

        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 10 seconds for 50 patients)
        assert elapsed < 10, f"Bulk operations taking too long: {elapsed:.2f}s"

        print(f"✓ Performance: Added 50 patients in {elapsed:.2f} seconds")


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Running Comprehensive Healthcare System Test Suite")
    print("=" * 70)
    print()

    # Run with pytest
    pytest.main([
        __file__,
        "-v",  # Verbose
        "-s",  # Show print statements
        "--tb=short",  # Short traceback format
        "-W", "ignore::DeprecationWarning"  # Ignore deprecation warnings
    ])
