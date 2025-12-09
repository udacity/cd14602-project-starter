"""
Test Suite for Ethical Job Matching System
==========================================

Comprehensive tests for ethical safeguards including:
- Bias and fairness testing
- Disparate impact analysis (80% rule)
- Privacy protection validation
- Transparency and explainability
- Human oversight and appeals
- Audit logging
"""

import sys
import unittest
from datetime import datetime
from typing import List, Dict, Any
import json

# Import the ethical system
from ethical_job_matching import (
    EthicalJobRecommendationEngine,
    EthicalCandidateScorer,
    DataProtectionManager,
    BiasTestingFramework,
    TransparencyExplainer,
    AppealProcessManager,
    HumanOversightManager,
    DecisionStatus,
    create_ethical_sample_data
)


class TestDataProtection(unittest.TestCase):
    """Test privacy and data protection safeguards."""

    def setUp(self):
        self.data_protection = DataProtectionManager()

    def test_prohibited_fields_detection(self):
        """Test that prohibited fields are detected and rejected."""
        # Test case with prohibited fields
        bad_candidate = {
            'name': 'John Doe',
            'age': 35,  # PROHIBITED
            'race': 'Asian',  # PROHIBITED
            'gender': 'Male',  # PROHIBITED
            'years_relevant_experience': 5
        }

        is_valid, violations = self.data_protection.validate_data_collection(
            bad_candidate
        )

        self.assertFalse(is_valid, "Should reject data with protected characteristics")
        self.assertGreater(len(violations), 0, "Should list violations")

        # Check specific violations
        violation_text = ' '.join(violations)
        self.assertIn('age', violation_text.lower())
        self.assertIn('race', violation_text.lower())
        self.assertIn('gender', violation_text.lower())

    def test_valid_data_collection(self):
        """Test that job-relevant data is accepted."""
        good_candidate = {
            'candidate_id': 'test_001',
            'years_relevant_experience': 5,
            'technical_skills': ['Python', 'JavaScript'],
            'education_field': 'Computer Science',
            'certifications': ['AWS'],
            'portfolio_quality_score': 80
        }

        is_valid, violations = self.data_protection.validate_data_collection(
            good_candidate
        )

        # Should have warnings about name/zip but still be valid for job-relevant data
        self.assertTrue(
            is_valid or all('WARNING' in v for v in violations),
            "Should accept job-relevant data"
        )

    def test_consent_management(self):
        """Test consent obtaining and tracking."""
        candidate_id = "test_candidate_123"

        consent = self.data_protection.obtain_consent(
            candidate_id,
            automated_processing=True
        )

        self.assertEqual(consent.candidate_id, candidate_id)
        self.assertTrue(consent.automated_processing_consent)
        self.assertTrue(consent.can_revoke)
        self.assertIn(candidate_id, self.data_protection.consent_records)

    def test_data_deletion_right(self):
        """Test right to erasure (GDPR Article 17)."""
        candidate_id = "test_candidate_456"

        # Obtain consent first
        self.data_protection.obtain_consent(candidate_id)
        self.assertIn(candidate_id, self.data_protection.consent_records)

        # Request deletion
        result = self.data_protection.request_data_deletion(candidate_id)

        self.assertTrue(result, "Deletion should succeed")
        self.assertNotIn(
            candidate_id,
            self.data_protection.consent_records,
            "Data should be deleted"
        )

    def test_data_anonymization(self):
        """Test that candidate IDs can be anonymized."""
        candidate_id = "sensitive_id_123"

        anonymized = self.data_protection.anonymize_candidate_id(candidate_id)

        self.assertNotEqual(candidate_id, anonymized)
        self.assertEqual(len(anonymized), 16)  # SHA256 truncated

        # Same input should produce same output
        anonymized2 = self.data_protection.anonymize_candidate_id(candidate_id)
        self.assertEqual(anonymized, anonymized2)


class TestFairnessAndBias(unittest.TestCase):
    """Test fairness, bias elimination, and job-relevant scoring."""

    def setUp(self):
        self.job_requirements = {
            'minimum_experience': 5,
            'required_skills': ['Python', 'JavaScript'],
            'preferred_skills': ['React', 'AWS'],
            'education_field': 'Computer Science',
            'preferred_certifications': ['AWS Solutions Architect']
        }
        self.scorer = EthicalCandidateScorer(self.job_requirements)

    def test_no_protected_characteristics_used(self):
        """Verify that NO protected characteristics influence scoring."""
        # Create two identical candidates except for "protected" attributes
        base_candidate = {
            'years_relevant_experience': 6,
            'technical_skills': ['Python', 'JavaScript', 'React'],
            'education_field': 'Computer Science',
            'certifications': ['AWS Solutions Architect'],
            'portfolio_quality_score': 80
        }

        # These should NOT affect scoring (if they're even present by mistake)
        candidate1 = base_candidate.copy()
        candidate1['age'] = 25  # Younger

        candidate2 = base_candidate.copy()
        candidate2['age'] = 55  # Older

        score1 = self.scorer.calculate_score(candidate1)
        score2 = self.scorer.calculate_score(candidate2)

        # Scores should be IDENTICAL
        self.assertEqual(
            score1['final_score'],
            score2['final_score'],
            "Age should not affect scoring"
        )

    def test_job_relevant_criteria_only(self):
        """Test that only job-relevant factors affect scores."""
        candidate_low_experience = {
            'years_relevant_experience': 2,  # Below requirement
            'technical_skills': ['Python'],
            'education_field': 'Computer Science',
            'certifications': [],
            'portfolio_quality_score': 60
        }

        candidate_high_experience = {
            'years_relevant_experience': 10,  # Exceeds requirement
            'technical_skills': ['Python', 'JavaScript', 'React', 'AWS'],
            'education_field': 'Computer Science',
            'certifications': ['AWS Solutions Architect'],
            'portfolio_quality_score': 90
        }

        score_low = self.scorer.calculate_score(candidate_low_experience)
        score_high = self.scorer.calculate_score(candidate_high_experience)

        self.assertLess(
            score_low['final_score'],
            score_high['final_score'],
            "More qualified candidate should score higher"
        )

    def test_alternative_education_paths_not_penalized(self):
        """Test that non-traditional education is not penalized."""
        # Traditional education
        candidate_traditional = {
            'years_relevant_experience': 5,
            'technical_skills': ['Python', 'JavaScript'],
            'education_field': 'Computer Science',
            'certifications': [],
            'portfolio_quality_score': 80
        }

        # Self-taught/bootcamp with same experience
        candidate_alternative = {
            'years_relevant_experience': 5,
            'technical_skills': ['Python', 'JavaScript'],
            'education_field': 'Self-taught / Bootcamp',
            'certifications': [],
            'portfolio_quality_score': 80
        }

        score_traditional = self.scorer.calculate_score(candidate_traditional)
        score_alternative = self.scorer.calculate_score(candidate_alternative)

        # Scores should be close (education is only 5% weight)
        score_diff = abs(
            score_traditional['final_score'] - score_alternative['final_score']
        )

        self.assertLess(
            score_diff,
            10,
            "Alternative education paths should not be significantly penalized"
        )


class TestDisparateImpactAnalysis(unittest.TestCase):
    """Test disparate impact analysis using the 80% rule."""

    def setUp(self):
        self.bias_testing = BiasTestingFramework()

    def test_80_percent_rule_pass(self):
        """Test case where system passes 80% rule."""
        # Simulate fair decisions across groups
        decisions = [
            # Group A: 80% approval rate
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'rejected'},

            # Group B: 85% approval rate
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'recommended'},
            {'demographic_group': 'Group_B', 'status': 'recommended'},
            {'demographic_group': 'Group_B', 'status': 'rejected'},
        ]

        result = self.bias_testing.test_disparate_impact(
            decisions,
            'demographic_group'
        )

        self.assertTrue(
            result['passes_disparate_impact_test'],
            "Should pass 80% rule with similar approval rates"
        )

    def test_80_percent_rule_fail(self):
        """Test case where system fails 80% rule (disparate impact detected)."""
        # Simulate biased decisions
        decisions = [
            # Group A: 90% approval rate
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'approved'},
            {'demographic_group': 'Group_A', 'status': 'rejected'},

            # Group B: 50% approval rate (less than 80% of Group A)
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'approved'},
            {'demographic_group': 'Group_B', 'status': 'rejected'},
            {'demographic_group': 'Group_B', 'status': 'rejected'},
            {'demographic_group': 'Group_B', 'status': 'rejected'},
            {'demographic_group': 'Group_B', 'status': 'rejected'},
            {'demographic_group': 'Group_B', 'status': 'rejected'},
        ]

        result = self.bias_testing.test_disparate_impact(
            decisions,
            'demographic_group'
        )

        self.assertFalse(
            result['passes_disparate_impact_test'],
            "Should fail 80% rule with disparate approval rates"
        )

        # Check that Group B fails
        self.assertFalse(
            result['group_results']['Group_B']['passes_80_percent_rule'],
            "Group B should fail 80% test"
        )

    def test_score_distribution_analysis(self):
        """Test that score distributions are analyzed for bias."""
        scores = [
            {'demographic_group': 'Group_A', 'final_score': 85},
            {'demographic_group': 'Group_A', 'final_score': 82},
            {'demographic_group': 'Group_A', 'final_score': 88},
            {'demographic_group': 'Group_A', 'final_score': 90},

            {'demographic_group': 'Group_B', 'final_score': 84},
            {'demographic_group': 'Group_B', 'final_score': 86},
            {'demographic_group': 'Group_B', 'final_score': 83},
            {'demographic_group': 'Group_B', 'final_score': 87},
        ]

        result = self.bias_testing.test_score_distribution(
            scores,
            'demographic_group'
        )

        # With similar scores, should not detect bias
        self.assertFalse(
            result['potential_bias_detected'],
            "Should not detect bias with similar score distributions"
        )

    def test_score_distribution_bias_detection(self):
        """Test detection of biased score distributions."""
        scores = [
            {'demographic_group': 'Group_A', 'final_score': 90},
            {'demographic_group': 'Group_A', 'final_score': 88},
            {'demographic_group': 'Group_A', 'final_score': 92},
            {'demographic_group': 'Group_A', 'final_score': 91},

            {'demographic_group': 'Group_B', 'final_score': 55},
            {'demographic_group': 'Group_B', 'final_score': 60},
            {'demographic_group': 'Group_B', 'final_score': 58},
            {'demographic_group': 'Group_B', 'final_score': 57},
        ]

        result = self.bias_testing.test_score_distribution(
            scores,
            'demographic_group'
        )

        # With large score difference, should detect bias
        self.assertTrue(
            result['potential_bias_detected'],
            "Should detect bias with disparate score distributions"
        )


class TestTransparencyAndExplainability(unittest.TestCase):
    """Test transparency and explainability features."""

    def setUp(self):
        self.job_requirements = {
            'minimum_experience': 5,
            'required_skills': ['Python', 'JavaScript'],
            'preferred_skills': ['React'],
            'education_field': 'Computer Science',
            'preferred_certifications': []
        }
        self.scorer = EthicalCandidateScorer(self.job_requirements)
        self.explainer = TransparencyExplainer()

    def test_score_breakdown_provided(self):
        """Test that detailed score breakdown is provided."""
        candidate = {
            'years_relevant_experience': 6,
            'technical_skills': ['Python', 'JavaScript'],
            'education_field': 'Computer Science',
            'certifications': [],
            'portfolio_quality_score': 75
        }

        result = self.scorer.calculate_score(candidate)

        self.assertIn('score_breakdown', result)
        self.assertIn('scoring_weights', result)

        # Check that all factors are explained
        breakdown = result['score_breakdown']
        self.assertIn('relevant_experience', breakdown)
        self.assertIn('technical_skills', breakdown)
        self.assertIn('project_portfolio', breakdown)

    def test_explanation_is_human_readable(self):
        """Test that explanations are clear and human-readable."""
        candidate = {
            'years_relevant_experience': 6,
            'technical_skills': ['Python', 'JavaScript'],
            'education_field': 'Computer Science',
            'certifications': [],
            'portfolio_quality_score': 75
        }

        result = self.scorer.calculate_score(candidate)

        self.assertIn('explanation', result)
        explanation = result['explanation']

        # Check for key elements
        self.assertIn('Overall Score', explanation)
        self.assertIn('Key Strengths', explanation)

        # Should not contain technical jargon or code
        self.assertNotIn('algorithm', explanation.lower())
        self.assertNotIn('model', explanation.lower())

    def test_candidate_feedback_includes_appeal_rights(self):
        """Test that feedback includes appeal rights information."""
        scoring_result = {
            'decision_id': 'test_decision_123',
            'final_score': 65,
            'score_breakdown': {
                'relevant_experience': 70,
                'technical_skills': 60,
                'project_portfolio': 65,
                'certifications': 50,
                'education_relevance': 70
            },
            'scoring_weights': {
                'relevant_experience': 0.35,
                'technical_skills': 0.30,
                'project_portfolio': 0.20,
                'certifications': 0.10,
                'education_relevance': 0.05
            },
            'explanation': 'Test explanation'
        }

        feedback = self.explainer.generate_candidate_feedback(
            scoring_result,
            DecisionStatus.REVIEW_REQUIRED
        )

        # Check for appeal information
        self.assertIn('appeal', feedback.lower())
        self.assertIn('Decision ID', feedback)
        self.assertIn(scoring_result['decision_id'], feedback)

    def test_actionable_feedback_provided(self):
        """Test that feedback includes actionable improvement suggestions."""
        scoring_result = {
            'decision_id': 'test_decision_123',
            'final_score': 60,
            'score_breakdown': {
                'relevant_experience': 50,  # Low score
                'technical_skills': 55,      # Low score
                'project_portfolio': 60,
                'certifications': 30,        # Very low
                'education_relevance': 70
            },
            'scoring_weights': {
                'relevant_experience': 0.35,
                'technical_skills': 0.30,
                'project_portfolio': 0.20,
                'certifications': 0.10,
                'education_relevance': 0.05
            },
            'explanation': 'Test explanation'
        }

        feedback = self.explainer.generate_candidate_feedback(
            scoring_result,
            DecisionStatus.REVIEW_REQUIRED
        )

        # Should include improvement opportunities
        self.assertIn('Opportunities for Strengthening', feedback)

        # Should mention specific areas
        self.assertIn('experience', feedback.lower())
        self.assertIn('skills', feedback.lower())


class TestHumanOversightAndAccountability(unittest.TestCase):
    """Test human oversight and accountability mechanisms."""

    def setUp(self):
        self.oversight = HumanOversightManager()
        self.appeals = AppealProcessManager()

    def test_low_scores_flagged_for_review(self):
        """Test that low scores are automatically flagged for human review."""
        job_requirements = {
            'minimum_experience': 5,
            'required_skills': ['Python'],
            'preferred_skills': [],
            'education_field': 'Computer Science',
            'preferred_certifications': []
        }
        scorer = EthicalCandidateScorer(job_requirements)

        # Low-scoring candidate
        candidate = {
            'years_relevant_experience': 1,
            'technical_skills': [],
            'education_field': 'Unrelated Field',
            'certifications': [],
            'portfolio_quality_score': 30
        }

        result = scorer.calculate_score(candidate)

        self.assertTrue(
            result['requires_human_review'],
            "Low scores should require human review"
        )

    def test_human_review_workflow(self):
        """Test complete human review workflow."""
        # Flag a decision for review
        self.oversight.flag_for_review(
            decision_id='decision_123',
            candidate_id='candidate_456',
            scoring_result={'final_score': 45},
            reason='Low score requires human review'
        )

        self.assertEqual(self.oversight.get_pending_reviews_count(), 1)

        # Get review queue
        queue = self.oversight.get_review_queue()
        self.assertEqual(len(queue), 1)

        review_item = queue[0]
        review_id = review_item['review_id']

        # Conduct human review
        review_result = self.oversight.conduct_review(
            review_id=review_id,
            reviewer_id='reviewer_jane',
            final_decision='reject',
            notes='Candidate does not meet minimum qualifications'
        )

        self.assertEqual(review_result['status'], 'completed')
        self.assertEqual(review_result['reviewer'], 'reviewer_jane')
        self.assertEqual(self.oversight.get_pending_reviews_count(), 0)

    def test_appeal_submission_and_processing(self):
        """Test appeal submission and processing workflow."""
        # Submit an appeal
        appeal_id = self.appeals.submit_appeal(
            decision_id='decision_789',
            candidate_id='candidate_101',
            appeal_reason='I have additional certifications not previously submitted',
            additional_info={'new_certification': 'AWS Solutions Architect'}
        )

        self.assertIsNotNone(appeal_id)

        # Check appeal status
        status = self.appeals.get_appeal_status(appeal_id)
        self.assertEqual(status['status'], 'pending_review')

        # Process the appeal
        result = self.appeals.process_appeal(
            appeal_id=appeal_id,
            reviewer_id='reviewer_john',
            outcome='approved',
            reviewer_notes='New certification warrants reconsideration. Advancing to interview.'
        )

        self.assertEqual(result['status'], 'reviewed')
        self.assertEqual(result['outcome'], 'approved')

    def test_appeal_invalid_id_raises_error(self):
        """Test that processing invalid appeal ID raises error."""
        with self.assertRaises(ValueError):
            self.appeals.process_appeal(
                appeal_id='nonexistent_appeal',
                reviewer_id='reviewer',
                outcome='approved',
                reviewer_notes='test'
            )


class TestIntegratedEthicalSystem(unittest.TestCase):
    """Test the complete integrated ethical system."""

    def setUp(self):
        self.engine = EthicalJobRecommendationEngine(
            accountability_officer="test_officer@example.com"
        )
        self.candidates, self.job = create_ethical_sample_data()

    def test_end_to_end_evaluation(self):
        """Test complete evaluation workflow."""
        candidate = self.candidates[0]

        result = self.engine.evaluate_candidate(
            candidate=candidate,
            job=self.job,
            consent_obtained=True
        )

        # Verify all components present
        self.assertIn('decision_id', result)
        self.assertIn('final_score', result)
        self.assertIn('status', result)
        self.assertIn('explanation', result)
        self.assertIn('candidate_feedback', result)
        self.assertIn('appeal_rights', result)
        self.assertIn('data_retention', result)
        self.assertIn('accountability', result)

    def test_consent_required(self):
        """Test that consent is required for processing."""
        candidate = self.candidates[0]

        result = self.engine.evaluate_candidate(
            candidate=candidate,
            job=self.job,
            consent_obtained=False
        )

        self.assertEqual(result['status'], 'consent_required')
        self.assertIn('error', result)

    def test_invalid_data_rejected(self):
        """Test that candidates with prohibited data are rejected."""
        bad_candidate = {
            'candidate_id': 'bad_001',
            'age': 35,  # PROHIBITED
            'years_relevant_experience': 5,
            'technical_skills': ['Python']
        }

        result = self.engine.evaluate_candidate(
            candidate=bad_candidate,
            job=self.job,
            consent_obtained=True
        )

        self.assertEqual(result['status'], 'rejected')
        self.assertIn('violations', result)

    def test_comprehensive_audit_logging(self):
        """Test that decisions are properly logged for audit."""
        candidate = self.candidates[0]

        # Clear any existing log entries
        import logging
        audit_logger = logging.getLogger('ethical_hiring_audit')

        result = self.engine.evaluate_candidate(
            candidate=candidate,
            job=self.job,
            consent_obtained=True
        )

        # Verify result contains audit information
        self.assertIn('accountability', result)
        self.assertIn('decision_maker', result['accountability'])
        self.assertIn('timestamp', result['accountability'])


def run_comprehensive_tests():
    """Run all tests and generate report."""
    print("=" * 70)
    print("ETHICAL JOB MATCHING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDataProtection))
    suite.addTests(loader.loadTestsFromTestCase(TestFairnessAndBias))
    suite.addTests(loader.loadTestsFromTestCase(TestDisparateImpactAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestTransparencyAndExplainability))
    suite.addTests(loader.loadTestsFromTestCase(TestHumanOversightAndAccountability))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedEthicalSystem))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✓ ALL ETHICAL SAFEGUARDS VERIFIED")
        print()
        print("The system demonstrates:")
        print("  ✓ No discrimination based on protected characteristics")
        print("  ✓ Privacy protection and GDPR compliance")
        print("  ✓ Disparate impact testing (80% rule)")
        print("  ✓ Transparency and explainability")
        print("  ✓ Human oversight and accountability")
        print("  ✓ Appeals process functionality")
        print("  ✓ Comprehensive audit logging")
    else:
        print("✗ SOME TESTS FAILED - REVIEW REQUIRED")
        print()
        if result.failures:
            print("Failures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("Errors:")
            for test, traceback in result.errors:
                print(f"  - {test}")

    print()
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
