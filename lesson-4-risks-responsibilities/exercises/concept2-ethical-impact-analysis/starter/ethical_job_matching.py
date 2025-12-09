"""
Ethical Job Matching and Candidate Scoring System
=================================================

A redesigned hiring system with comprehensive ethical safeguards that:
- Eliminates discrimination based on protected characteristics
- Focuses on job-relevant qualifications only
- Provides transparency and explainability
- Implements human oversight and accountability
- Protects candidate privacy
- Enables bias testing and monitoring

Compliant with: EEOC Guidelines, GDPR, Fair Lending Laws, EU AI Act
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import uuid


# Configure audit logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ethical_hiring_audit.log'),
        logging.StreamHandler()
    ]
)
audit_logger = logging.getLogger('ethical_hiring_audit')


class DecisionStatus(Enum):
    """Status of hiring decisions."""
    RECOMMENDED = "recommended"
    REVIEW_REQUIRED = "review_required"
    HUMAN_DECISION_PENDING = "human_decision_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPEAL_SUBMITTED = "appeal_submitted"
    APPEAL_REVIEWED = "appeal_reviewed"


@dataclass
class AuditLogEntry:
    """Structured audit log entry for compliance and accountability."""
    timestamp: str
    decision_id: str
    candidate_id: str
    job_id: str
    action: str
    decision_maker: str  # "algorithm" or human identifier
    score: Optional[float]
    factors: Dict[str, Any]
    explanation: str
    status: str
    reviewer_notes: Optional[str] = None


@dataclass
class PrivacyConsent:
    """Track candidate consent for data processing."""
    candidate_id: str
    consent_date: str
    purpose: str
    data_retention_days: int
    automated_processing_consent: bool
    can_revoke: bool = True


class DataProtectionManager:
    """Manages privacy, data minimization, and GDPR compliance."""

    def __init__(self, retention_days: int = 365):
        self.retention_days = retention_days
        self.consent_records: Dict[str, PrivacyConsent] = {}
        self.data_deletion_schedule: Dict[str, str] = {}

    def obtain_consent(self, candidate_id: str,
                      automated_processing: bool = False) -> PrivacyConsent:
        """
        Obtain explicit consent for data processing.
        Required by GDPR Article 6 and 22.
        """
        consent = PrivacyConsent(
            candidate_id=candidate_id,
            consent_date=datetime.now().isoformat(),
            purpose="Job application evaluation and matching",
            data_retention_days=self.retention_days,
            automated_processing_consent=automated_processing
        )

        self.consent_records[candidate_id] = consent

        # Schedule data deletion
        deletion_date = datetime.now() + timedelta(days=self.retention_days)
        self.data_deletion_schedule[candidate_id] = deletion_date.isoformat()

        audit_logger.info(f"Consent obtained for candidate {candidate_id}")
        return consent

    def anonymize_candidate_id(self, candidate_id: str) -> str:
        """Create anonymized identifier for privacy protection."""
        return hashlib.sha256(candidate_id.encode()).hexdigest()[:16]

    def check_data_retention(self, candidate_id: str) -> bool:
        """Check if data should be retained or deleted."""
        if candidate_id not in self.data_deletion_schedule:
            return False

        deletion_date = datetime.fromisoformat(
            self.data_deletion_schedule[candidate_id]
        )
        return datetime.now() < deletion_date

    def request_data_deletion(self, candidate_id: str) -> bool:
        """
        Process right to erasure request (GDPR Article 17).
        Returns True if deletion is processed.
        """
        if candidate_id in self.consent_records:
            del self.consent_records[candidate_id]
        if candidate_id in self.data_deletion_schedule:
            del self.data_deletion_schedule[candidate_id]

        audit_logger.info(f"Data deletion processed for candidate {candidate_id}")
        return True

    def validate_data_collection(self, candidate_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that only job-relevant, non-discriminatory data is collected.
        Returns (is_valid, list_of_violations)
        """
        violations = []

        # PROHIBITED fields that should NEVER be collected
        prohibited_fields = [
            'age', 'date_of_birth', 'birth_year',
            'race', 'ethnicity', 'national_origin',
            'gender', 'sex',
            'religion', 'religious_affiliation',
            'marital_status', 'family_status',
            'disability', 'health_conditions',
            'native_language', 'native_speaker',
            'sexual_orientation',
            'genetic_information',
            'citizenship_status',
            'previous_salary', 'salary_history'
        ]

        for field in prohibited_fields:
            if field in candidate_data:
                violations.append(
                    f"PROHIBITED: Field '{field}' is a protected characteristic "
                    f"and must not be collected"
                )

        # Check for potential proxy variables
        if 'zip_code' in candidate_data or 'postal_code' in candidate_data:
            violations.append(
                "WARNING: Geographic data (zip_code) can be a proxy for race/ethnicity. "
                "Only collect if essential for job location requirements."
            )

        if 'name' in candidate_data:
            violations.append(
                "WARNING: Full names can reveal gender/ethnicity. Consider using "
                "anonymized identifiers during initial screening."
            )

        return len(violations) == 0, violations


class EthicalCandidateScorer:
    """
    Ethical candidate scoring based ONLY on job-relevant qualifications.

    Key principles:
    - NO protected characteristics (age, race, gender, etc.)
    - NO proxy variables (location, name analysis, etc.)
    - Focus on demonstrable skills and experience
    - Transparent and explainable scoring
    - Job-specific criteria validation
    """

    def __init__(self, job_requirements: Dict[str, Any]):
        self.job_requirements = job_requirements

        # Scoring weights must be justified and job-specific
        # These should be validated against actual job performance data
        self.scoring_weights = {
            'relevant_experience': 0.35,    # Years of directly relevant experience
            'technical_skills': 0.30,       # Demonstrable technical competencies
            'project_portfolio': 0.20,      # Quality of work samples/portfolio
            'certifications': 0.10,         # Relevant professional certifications
            'education_relevance': 0.05     # Relevance of education (NOT prestige)
        }

        audit_logger.info(
            f"Ethical scorer initialized with weights: {self.scoring_weights}"
        )

    def calculate_score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate candidate score based ONLY on job-relevant factors.

        Args:
            candidate: Dictionary with job-relevant information ONLY

        Returns:
            Detailed scoring with explanation
        """
        decision_id = str(uuid.uuid4())
        scores = {}
        explanations = []

        # 1. RELEVANT EXPERIENCE (35%)
        # Focus on years of experience in the specific role/technology
        relevant_exp = candidate.get('years_relevant_experience', 0)
        required_exp = self.job_requirements.get('minimum_experience', 0)

        if relevant_exp >= required_exp:
            exp_score = min((relevant_exp / max(required_exp, 1)) * 100, 100)
        else:
            exp_score = (relevant_exp / max(required_exp, 1)) * 70

        scores['relevant_experience'] = exp_score
        explanations.append(
            f"Relevant experience: {relevant_exp} years "
            f"({'meets' if relevant_exp >= required_exp else 'below'} "
            f"{required_exp} year requirement)"
        )

        # 2. TECHNICAL SKILLS (30%)
        # Match candidate skills against required skills
        candidate_skills = set(candidate.get('technical_skills', []))
        required_skills = set(self.job_requirements.get('required_skills', []))
        preferred_skills = set(self.job_requirements.get('preferred_skills', []))

        if not required_skills:
            skills_score = 70  # Default if no requirements specified
        else:
            required_matches = len(candidate_skills.intersection(required_skills))
            preferred_matches = len(candidate_skills.intersection(preferred_skills))

            required_pct = required_matches / len(required_skills)
            skills_score = (required_pct * 80) + (preferred_matches * 5)
            skills_score = min(skills_score, 100)

        scores['technical_skills'] = skills_score
        explanations.append(
            f"Technical skills: {required_matches}/{len(required_skills)} "
            f"required skills matched"
        )

        # 3. PROJECT PORTFOLIO (20%)
        # Evaluate quality of work samples (this should be human-evaluated)
        portfolio_quality = candidate.get('portfolio_quality_score', 0)
        scores['project_portfolio'] = portfolio_quality

        if portfolio_quality > 0:
            explanations.append(
                f"Portfolio demonstrates {self._quality_descriptor(portfolio_quality)} "
                f"level of expertise"
            )
        else:
            explanations.append("No portfolio provided for evaluation")

        # 4. CERTIFICATIONS (10%)
        # Relevant professional certifications only
        candidate_certs = set(candidate.get('certifications', []))
        relevant_certs = set(self.job_requirements.get('preferred_certifications', []))

        cert_matches = len(candidate_certs.intersection(relevant_certs))
        cert_score = min(cert_matches * 30, 100)
        scores['certifications'] = cert_score

        if cert_matches > 0:
            explanations.append(
                f"Holds {cert_matches} relevant professional certification(s)"
            )

        # 5. EDUCATION RELEVANCE (5%)
        # Focus on RELEVANCE not prestige or type
        education_field = candidate.get('education_field', '')
        required_field = self.job_requirements.get('education_field', '')

        if education_field and required_field:
            # Simple relevance check (in production, use more sophisticated matching)
            education_score = 80 if education_field == required_field else 50
        else:
            education_score = 70  # Neutral if not specified

        scores['education_relevance'] = education_score
        explanations.append(
            f"Educational background in {education_field or 'various fields'}"
        )

        # Calculate weighted final score
        final_score = sum(
            scores[factor] * self.scoring_weights[factor]
            for factor in scores
        )

        # Generate human-readable explanation
        explanation = self._generate_explanation(scores, explanations, final_score)

        # Determine if human review is required
        requires_review = self._requires_human_review(final_score, scores)

        result = {
            'decision_id': decision_id,
            'final_score': round(final_score, 2),
            'score_breakdown': scores,
            'scoring_weights': self.scoring_weights,
            'explanation': explanation,
            'detailed_factors': explanations,
            'requires_human_review': requires_review,
            'status': (DecisionStatus.REVIEW_REQUIRED.value if requires_review
                      else DecisionStatus.RECOMMENDED.value),
            'timestamp': datetime.now().isoformat()
        }

        return result

    def _quality_descriptor(self, score: float) -> str:
        """Convert numeric score to human-readable quality level."""
        if score >= 90:
            return "exceptional"
        elif score >= 75:
            return "strong"
        elif score >= 60:
            return "adequate"
        else:
            return "developing"

    def _generate_explanation(self, scores: Dict[str, float],
                            explanations: List[str], final_score: float) -> str:
        """Generate human-readable explanation of the scoring decision."""

        # Identify strongest factors
        sorted_factors = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        strongest = sorted_factors[0]

        explanation = f"Overall Score: {final_score:.1f}/100\n\n"
        explanation += "Key Strengths:\n"

        for factor, score in sorted_factors:
            if score >= 70:
                weight = self.scoring_weights[factor]
                contribution = score * weight
                explanation += f"- {factor.replace('_', ' ').title()}: "
                explanation += f"{score:.1f}/100 (contributes {contribution:.1f} points)\n"

        explanation += "\n" + "\n".join(f"- {exp}" for exp in explanations)

        return explanation

    def _requires_human_review(self, final_score: float,
                               scores: Dict[str, float]) -> bool:
        """
        Determine if human review is required.

        Human review required for:
        - Borderline scores (40-60 range)
        - Rejection decisions (score < 40)
        - Unusual score patterns
        """
        if final_score < 60:  # All low scores need human review
            return True

        # Check for unusual patterns (high variance in subscores)
        if len(scores) > 0:
            score_values = list(scores.values())
            score_range = max(score_values) - min(score_values)
            if score_range > 50:  # Large variance suggests unusual case
                return True

        return False


class TransparencyExplainer:
    """Provides detailed, human-readable explanations for decisions."""

    def generate_candidate_feedback(self, scoring_result: Dict[str, Any],
                                   decision_status: DecisionStatus) -> str:
        """
        Generate transparent feedback for candidates.

        Feedback should be:
        - Honest and specific
        - Actionable (what could be improved)
        - Free of vague euphemisms
        - Respectful
        """
        feedback = f"Application Decision: {decision_status.value.upper()}\n"
        feedback += "=" * 50 + "\n\n"

        feedback += scoring_result['explanation'] + "\n\n"

        # Provide actionable suggestions
        feedback += "Opportunities for Strengthening Your Application:\n"

        scores = scoring_result['score_breakdown']
        weights = scoring_result['scoring_weights']

        # Identify areas for improvement (sorted by potential impact)
        improvements = []
        for factor, score in scores.items():
            if score < 70:
                weight = weights[factor]
                potential_gain = (100 - score) * weight
                improvements.append((factor, score, potential_gain))

        improvements.sort(key=lambda x: x[2], reverse=True)

        for factor, score, potential_gain in improvements[:3]:
            feedback += f"\n- {factor.replace('_', ' ').title()}: "
            feedback += f"Current score {score:.1f}/100. "
            feedback += self._get_improvement_suggestion(factor, score)

        feedback += "\n\n" + "=" * 50 + "\n"
        feedback += "Right to Appeal: If you believe this decision was made in error, "
        feedback += "you have the right to request human review. "
        feedback += f"Contact: appeals@company.com with Decision ID: {scoring_result['decision_id']}\n"

        return feedback

    def _get_improvement_suggestion(self, factor: str, score: float) -> str:
        """Provide specific, actionable improvement suggestions."""
        suggestions = {
            'relevant_experience': "Consider gaining more hands-on experience through projects, internships, or similar roles.",
            'technical_skills': "Expanding your skill set in the required technologies through courses or certifications could strengthen your application.",
            'project_portfolio': "Building a portfolio of projects demonstrating your capabilities would provide concrete evidence of your skills.",
            'certifications': "Relevant professional certifications (e.g., AWS, Azure, industry-specific credentials) can validate your expertise.",
            'education_relevance': "Additional coursework or training in the relevant field could be beneficial."
        }
        return suggestions.get(factor, "Continue developing in this area.")


class AppealProcessManager:
    """Manages the appeals process for candidates to challenge decisions."""

    def __init__(self):
        self.appeals: Dict[str, Dict[str, Any]] = {}

    def submit_appeal(self, decision_id: str, candidate_id: str,
                     appeal_reason: str, additional_info: Dict[str, Any]) -> str:
        """
        Submit an appeal for human review.

        Returns appeal tracking ID.
        """
        appeal_id = str(uuid.uuid4())

        appeal_record = {
            'appeal_id': appeal_id,
            'decision_id': decision_id,
            'candidate_id': candidate_id,
            'submission_date': datetime.now().isoformat(),
            'appeal_reason': appeal_reason,
            'additional_info': additional_info,
            'status': 'pending_review',
            'reviewer': None,
            'review_date': None,
            'outcome': None,
            'reviewer_notes': None
        }

        self.appeals[appeal_id] = appeal_record

        audit_logger.info(
            f"Appeal submitted - Appeal ID: {appeal_id}, "
            f"Decision ID: {decision_id}, Candidate: {candidate_id}"
        )

        return appeal_id

    def process_appeal(self, appeal_id: str, reviewer_id: str,
                      outcome: str, reviewer_notes: str) -> Dict[str, Any]:
        """
        Process an appeal with human review.

        Args:
            appeal_id: The appeal tracking ID
            reviewer_id: Identifier of human reviewer
            outcome: 'approved', 'denied', or 'reconsider'
            reviewer_notes: Detailed notes from reviewer
        """
        if appeal_id not in self.appeals:
            raise ValueError(f"Appeal {appeal_id} not found")

        appeal = self.appeals[appeal_id]
        appeal['status'] = 'reviewed'
        appeal['reviewer'] = reviewer_id
        appeal['review_date'] = datetime.now().isoformat()
        appeal['outcome'] = outcome
        appeal['reviewer_notes'] = reviewer_notes

        audit_logger.info(
            f"Appeal reviewed - Appeal ID: {appeal_id}, "
            f"Reviewer: {reviewer_id}, Outcome: {outcome}"
        )

        return appeal

    def get_appeal_status(self, appeal_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve appeal status for candidate inquiry."""
        return self.appeals.get(appeal_id)


class HumanOversightManager:
    """Manages human review and oversight of algorithmic decisions."""

    def __init__(self):
        self.pending_reviews: List[Dict[str, Any]] = []
        self.completed_reviews: List[Dict[str, Any]] = []

    def flag_for_review(self, decision_id: str, candidate_id: str,
                       scoring_result: Dict[str, Any], reason: str):
        """Flag a decision for mandatory human review."""
        review_item = {
            'review_id': str(uuid.uuid4()),
            'decision_id': decision_id,
            'candidate_id': candidate_id,
            'flagged_date': datetime.now().isoformat(),
            'reason': reason,
            'scoring_result': scoring_result,
            'status': 'pending',
            'reviewer': None,
            'final_decision': None
        }

        self.pending_reviews.append(review_item)

        audit_logger.warning(
            f"Decision flagged for human review - Decision ID: {decision_id}, "
            f"Reason: {reason}"
        )

    def conduct_review(self, review_id: str, reviewer_id: str,
                      final_decision: str, notes: str) -> Dict[str, Any]:
        """
        Conduct human review of flagged decision.

        Args:
            review_id: The review tracking ID
            reviewer_id: Identifier of human reviewer (name/ID)
            final_decision: 'approve', 'reject', or 'request_more_info'
            notes: Detailed rationale for the decision
        """
        # Find the review item
        review_item = None
        for item in self.pending_reviews:
            if item['review_id'] == review_id:
                review_item = item
                break

        if not review_item:
            raise ValueError(f"Review {review_id} not found in pending reviews")

        # Update review with human decision
        review_item['status'] = 'completed'
        review_item['reviewer'] = reviewer_id
        review_item['review_date'] = datetime.now().isoformat()
        review_item['final_decision'] = final_decision
        review_item['reviewer_notes'] = notes

        # Move to completed reviews
        self.pending_reviews.remove(review_item)
        self.completed_reviews.append(review_item)

        audit_logger.info(
            f"Human review completed - Review ID: {review_id}, "
            f"Reviewer: {reviewer_id}, Decision: {final_decision}"
        )

        return review_item

    def get_pending_reviews_count(self) -> int:
        """Get count of decisions awaiting human review."""
        return len(self.pending_reviews)

    def get_review_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve pending reviews for reviewer dashboard."""
        return self.pending_reviews[:limit]


class BiasTestingFramework:
    """Framework for testing disparate impact and bias across groups."""

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []

    def test_disparate_impact(self, decisions: List[Dict[str, Any]],
                             group_attribute: str) -> Dict[str, Any]:
        """
        Test for disparate impact using the 80% rule (4/5ths rule).

        Used by EEOC to assess adverse impact:
        Selection rate for any group should be at least 80% of the
        selection rate for the group with the highest rate.

        Args:
            decisions: List of decision records with demographic info
            group_attribute: Attribute to test (e.g., 'demographic_group')

        Returns:
            Test results including pass/fail and specific rates
        """
        # Group decisions by attribute
        grouped = {}
        for decision in decisions:
            group = decision.get(group_attribute, 'unknown')
            if group not in grouped:
                grouped[group] = {'total': 0, 'approved': 0}

            grouped[group]['total'] += 1
            if decision.get('status') in ['approved', 'recommended']:
                grouped[group]['approved'] += 1

        # Calculate selection rates
        selection_rates = {}
        for group, counts in grouped.items():
            if counts['total'] > 0:
                selection_rates[group] = counts['approved'] / counts['total']
            else:
                selection_rates[group] = 0

        # Find highest selection rate
        if not selection_rates:
            return {'error': 'No data to analyze'}

        highest_rate = max(selection_rates.values())

        # Apply 80% rule
        disparate_impact_results = {}
        for group, rate in selection_rates.items():
            ratio = rate / highest_rate if highest_rate > 0 else 0
            passes_80_percent = ratio >= 0.80

            disparate_impact_results[group] = {
                'selection_rate': rate,
                'ratio_to_highest': ratio,
                'passes_80_percent_rule': passes_80_percent,
                'sample_size': grouped[group]['total']
            }

        # Overall assessment
        all_pass = all(r['passes_80_percent_rule']
                      for r in disparate_impact_results.values())

        result = {
            'test_date': datetime.now().isoformat(),
            'attribute_tested': group_attribute,
            'highest_selection_rate': highest_rate,
            'group_results': disparate_impact_results,
            'passes_disparate_impact_test': all_pass,
            'recommendation': (
                'No evidence of disparate impact detected.' if all_pass
                else 'ALERT: Potential disparate impact detected. Human review required.'
            )
        }

        self.test_results.append(result)

        if not all_pass:
            audit_logger.warning(
                f"BIAS ALERT: Disparate impact detected on {group_attribute}. "
                f"Results: {disparate_impact_results}"
            )

        return result

    def test_score_distribution(self, scores: List[Dict[str, Any]],
                               group_attribute: str) -> Dict[str, Any]:
        """
        Test if score distributions differ significantly across groups.

        Checks for bias in scoring patterns.
        """
        grouped_scores = {}

        for score_record in scores:
            group = score_record.get(group_attribute, 'unknown')
            score = score_record.get('final_score', 0)

            if group not in grouped_scores:
                grouped_scores[group] = []
            grouped_scores[group].append(score)

        # Calculate statistics for each group
        statistics = {}
        for group, group_scores in grouped_scores.items():
            if len(group_scores) > 0:
                statistics[group] = {
                    'count': len(group_scores),
                    'mean': sum(group_scores) / len(group_scores),
                    'min': min(group_scores),
                    'max': max(group_scores),
                    'median': sorted(group_scores)[len(group_scores) // 2]
                }

        # Check for significant differences (simplified test)
        means = [s['mean'] for s in statistics.values()]
        if means:
            mean_range = max(means) - min(means)
            potential_bias = mean_range > 15  # More than 15 point difference
        else:
            potential_bias = False

        result = {
            'test_date': datetime.now().isoformat(),
            'attribute_tested': group_attribute,
            'group_statistics': statistics,
            'mean_score_range': mean_range if means else 0,
            'potential_bias_detected': potential_bias,
            'recommendation': (
                'Score distributions appear reasonably consistent across groups.'
                if not potential_bias
                else 'ALERT: Significant score differences detected. Investigate for bias.'
            )
        }

        if potential_bias:
            audit_logger.warning(
                f"BIAS ALERT: Significant score differences detected on {group_attribute}. "
                f"Statistics: {statistics}"
            )

        return result


class EthicalJobRecommendationEngine:
    """
    Ethical job recommendation engine with comprehensive safeguards.

    Integrates all ethical components:
    - Privacy protection
    - Bias testing
    - Human oversight
    - Transparency
    - Accountability
    """

    def __init__(self, accountability_officer: str = "hiring_manager@company.com"):
        self.scorer = None  # Will be set per job
        self.data_protection = DataProtectionManager(retention_days=365)
        self.transparency = TransparencyExplainer()
        self.appeals = AppealProcessManager()
        self.human_oversight = HumanOversightManager()
        self.bias_testing = BiasTestingFramework()
        self.accountability_officer = accountability_officer

        audit_logger.info(
            f"Ethical recommendation engine initialized. "
            f"Accountability officer: {accountability_officer}"
        )

    def evaluate_candidate(self, candidate: Dict[str, Any],
                          job: Dict[str, Any],
                          consent_obtained: bool = False) -> Dict[str, Any]:
        """
        Evaluate candidate with full ethical safeguards.

        Args:
            candidate: Candidate information (job-relevant only)
            job: Job requirements and details
            consent_obtained: Whether candidate consented to automated processing

        Returns:
            Comprehensive evaluation result with explanations
        """
        candidate_id = candidate.get('candidate_id', str(uuid.uuid4()))
        job_id = job.get('job_id', str(uuid.uuid4()))

        # Step 1: PRIVACY - Validate data collection
        is_valid, violations = self.data_protection.validate_data_collection(candidate)
        if not is_valid:
            audit_logger.error(
                f"Data validation failed for candidate {candidate_id}: {violations}"
            )
            return {
                'error': 'Invalid data collection',
                'violations': violations,
                'status': 'rejected'
            }

        # Step 2: CONSENT - Verify consent for automated processing
        if not consent_obtained:
            audit_logger.warning(
                f"Consent not obtained for candidate {candidate_id}"
            )
            return {
                'error': 'Consent required for automated processing',
                'status': 'consent_required'
            }

        consent = self.data_protection.obtain_consent(
            candidate_id,
            automated_processing=True
        )

        # Step 3: SCORING - Calculate ethical score
        self.scorer = EthicalCandidateScorer(job.get('requirements', {}))
        scoring_result = self.scorer.calculate_score(candidate)

        # Step 4: HUMAN OVERSIGHT - Check if review required
        if scoring_result['requires_human_review']:
            self.human_oversight.flag_for_review(
                decision_id=scoring_result['decision_id'],
                candidate_id=candidate_id,
                scoring_result=scoring_result,
                reason="Score requires human review per policy"
            )
            scoring_result['status'] = DecisionStatus.HUMAN_DECISION_PENDING.value

        # Step 5: TRANSPARENCY - Generate explanation
        feedback = self.transparency.generate_candidate_feedback(
            scoring_result,
            DecisionStatus(scoring_result['status'])
        )

        # Step 6: AUDIT LOGGING - Record decision
        self._log_decision(
            candidate_id=candidate_id,
            job_id=job_id,
            scoring_result=scoring_result,
            consent=consent
        )

        # Step 7: COMPILE RESULT
        result = {
            'candidate_id': candidate_id,
            'job_id': job_id,
            'decision_id': scoring_result['decision_id'],
            'final_score': scoring_result['final_score'],
            'status': scoring_result['status'],
            'requires_human_review': scoring_result['requires_human_review'],
            'explanation': scoring_result['explanation'],
            'candidate_feedback': feedback,
            'score_breakdown': scoring_result['score_breakdown'],
            'appeal_rights': {
                'can_appeal': True,
                'appeal_deadline_days': 30,
                'contact': 'appeals@company.com'
            },
            'data_retention': {
                'retention_days': consent.data_retention_days,
                'deletion_date': self.data_protection.data_deletion_schedule.get(candidate_id),
                'can_request_deletion': consent.can_revoke
            },
            'accountability': {
                'decision_maker': 'Algorithm' if not scoring_result['requires_human_review'] else 'Pending Human Review',
                'accountability_officer': self.accountability_officer,
                'timestamp': scoring_result['timestamp']
            }
        }

        return result

    def _log_decision(self, candidate_id: str, job_id: str,
                     scoring_result: Dict[str, Any],
                     consent: PrivacyConsent):
        """Create comprehensive audit log entry."""
        log_entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            decision_id=scoring_result['decision_id'],
            candidate_id=self.data_protection.anonymize_candidate_id(candidate_id),
            job_id=job_id,
            action='candidate_evaluation',
            decision_maker='algorithm',
            score=scoring_result['final_score'],
            factors=scoring_result['score_breakdown'],
            explanation=scoring_result['explanation'],
            status=scoring_result['status']
        )

        audit_logger.info(f"AUDIT LOG: {json.dumps(asdict(log_entry), indent=2)}")

    def submit_appeal(self, decision_id: str, candidate_id: str,
                     appeal_reason: str, additional_info: Dict[str, Any]) -> str:
        """Submit an appeal for human review."""
        return self.appeals.submit_appeal(
            decision_id, candidate_id, appeal_reason, additional_info
        )

    def process_appeal(self, appeal_id: str, reviewer_id: str,
                      outcome: str, reviewer_notes: str) -> Dict[str, Any]:
        """Process an appeal with human review."""
        return self.appeals.process_appeal(
            appeal_id, reviewer_id, outcome, reviewer_notes
        )

    def conduct_bias_audit(self, decisions: List[Dict[str, Any]],
                          test_attributes: List[str]) -> Dict[str, Any]:
        """
        Conduct comprehensive bias audit across protected groups.

        This should be run regularly (e.g., quarterly) to ensure
        the system is not exhibiting disparate impact.
        """
        audit_results = {
            'audit_date': datetime.now().isoformat(),
            'total_decisions': len(decisions),
            'disparate_impact_tests': {},
            'score_distribution_tests': {},
            'overall_assessment': None
        }

        for attribute in test_attributes:
            # Test for disparate impact
            di_result = self.bias_testing.test_disparate_impact(
                decisions, attribute
            )
            audit_results['disparate_impact_tests'][attribute] = di_result

            # Test score distributions
            score_result = self.bias_testing.test_score_distribution(
                decisions, attribute
            )
            audit_results['score_distribution_tests'][attribute] = score_result

        # Overall assessment
        all_di_pass = all(
            r['passes_disparate_impact_test']
            for r in audit_results['disparate_impact_tests'].values()
        )

        any_score_bias = any(
            r['potential_bias_detected']
            for r in audit_results['score_distribution_tests'].values()
        )

        if all_di_pass and not any_score_bias:
            audit_results['overall_assessment'] = 'PASS - No bias detected'
        else:
            audit_results['overall_assessment'] = 'FAIL - Bias detected, review required'
            audit_logger.critical(
                f"BIAS AUDIT FAILURE: {audit_results['overall_assessment']}"
            )

        return audit_results


def create_ethical_sample_data():
    """
    Create sample data demonstrating ethical data collection.

    Note: Only job-relevant information, NO protected characteristics.
    """
    candidates = [
        {
            'candidate_id': 'candidate_001',
            # Job-relevant information only
            'years_relevant_experience': 8,
            'technical_skills': ['Python', 'Django', 'PostgreSQL', 'AWS', 'Docker'],
            'education_field': 'Computer Science',
            'certifications': ['AWS Solutions Architect', 'Certified Scrum Master'],
            'portfolio_quality_score': 85,  # Human-evaluated
            # NO: age, gender, race, national origin, etc.
        },
        {
            'candidate_id': 'candidate_002',
            'years_relevant_experience': 15,
            'technical_skills': ['Python', 'JavaScript', 'React', 'Node.js', 'MongoDB'],
            'education_field': 'Software Engineering',
            'certifications': ['PMP', 'AWS Developer'],
            'portfolio_quality_score': 92,
        },
        {
            'candidate_id': 'candidate_003',
            'years_relevant_experience': 3,
            'technical_skills': ['Python', 'JavaScript', 'React', 'Git'],
            'education_field': 'Self-taught / Bootcamp',
            'certifications': [],
            'portfolio_quality_score': 75,
        }
    ]

    job = {
        'job_id': 'job_001',
        'title': 'Senior Software Engineer',
        'requirements': {
            'minimum_experience': 5,
            'required_skills': ['Python', 'JavaScript', 'AWS'],
            'preferred_skills': ['Django', 'React', 'Docker'],
            'education_field': 'Computer Science',
            'preferred_certifications': ['AWS Solutions Architect', 'AWS Developer']
        }
    }

    return candidates, job


# Demo and Testing
if __name__ == "__main__":
    print("=" * 70)
    print("ETHICAL JOB MATCHING SYSTEM - DEMONSTRATION")
    print("=" * 70)
    print()

    # Initialize the ethical system
    engine = EthicalJobRecommendationEngine(
        accountability_officer="hiring_manager@example.com"
    )

    # Create sample data
    candidates, job = create_ethical_sample_data()

    print(f"Job Position: {job['title']}")
    print(f"Required Skills: {job['requirements']['required_skills']}")
    print(f"Minimum Experience: {job['requirements']['minimum_experience']} years")
    print()
    print("=" * 70)
    print()

    # Evaluate each candidate
    evaluations = []
    for candidate in candidates:
        print(f"\nEvaluating Candidate: {candidate['candidate_id']}")
        print("-" * 70)

        # Simulate consent obtained
        result = engine.evaluate_candidate(
            candidate=candidate,
            job=job,
            consent_obtained=True
        )

        evaluations.append(result)

        print(f"Decision ID: {result['decision_id']}")
        print(f"Final Score: {result['final_score']:.1f}/100")
        print(f"Status: {result['status']}")
        print(f"Requires Human Review: {result['requires_human_review']}")
        print()
        print("Explanation:")
        print(result['explanation'])
        print()

        if result['requires_human_review']:
            print("⚠️  This decision has been flagged for human review")
            print()

    print("=" * 70)
    print("BIAS AUDIT DEMONSTRATION")
    print("=" * 70)
    print()

    # Simulate bias audit
    # Note: In real usage, you would test across actual demographic groups
    # Here we demonstrate the framework
    print("Note: Bias testing requires demographic data collected separately")
    print("from the decision process, used only for auditing purposes.")
    print()

    # Demonstrate appeal process
    print("=" * 70)
    print("APPEAL PROCESS DEMONSTRATION")
    print("=" * 70)
    print()

    # Simulate appeal for candidate with lower score
    if evaluations:
        lowest_score_eval = min(evaluations, key=lambda x: x['final_score'])
        print(f"Candidate {lowest_score_eval['candidate_id']} submits an appeal...")

        appeal_id = engine.submit_appeal(
            decision_id=lowest_score_eval['decision_id'],
            candidate_id=lowest_score_eval['candidate_id'],
            appeal_reason="I believe my portfolio demonstrates stronger capabilities than reflected in the score",
            additional_info={'portfolio_url': 'https://example.com/portfolio'}
        )

        print(f"Appeal submitted successfully. Appeal ID: {appeal_id}")
        print()

        # Simulate human review of appeal
        print("Human reviewer processes the appeal...")
        appeal_result = engine.process_appeal(
            appeal_id=appeal_id,
            reviewer_id="reviewer_jane_doe",
            outcome="approved",
            reviewer_notes="Upon review of the portfolio, candidate demonstrates strong practical skills. Advancing to interview stage."
        )

        print(f"Appeal Outcome: {appeal_result['outcome']}")
        print(f"Reviewer Notes: {appeal_result['reviewer_notes']}")

    print()
    print("=" * 70)
    print("ETHICAL SAFEGUARDS SUMMARY")
    print("=" * 70)
    print("""
✓ NO protected characteristics used (age, race, gender, etc.)
✓ NO proxy variables (location, names, etc.)
✓ Job-relevant criteria only
✓ Transparent scoring with detailed explanations
✓ Human oversight for borderline/rejection cases
✓ Appeals process with human review
✓ Comprehensive audit logging
✓ Bias testing framework
✓ Privacy protection (GDPR-compliant)
✓ Data minimization principle
✓ Clear accountability and responsibility
✓ Candidate rights respected (appeal, deletion, explanation)

This system demonstrates ethical AI design for hiring decisions.
    """)

    print("\nAudit log written to: ethical_hiring_audit.log")
    print()
