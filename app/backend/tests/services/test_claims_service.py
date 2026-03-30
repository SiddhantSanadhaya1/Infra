"""
Comprehensive unit tests for claims_service module.
Tests claim number generation, claim validation, and fraud score calculation.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from src.services.claims_service import (
    generate_claim_number,
    validate_claim_against_policy,
    calculate_fraud_score,
)


class TestGenerateClaimNumber:
    """Test claim number generation with various conditions."""

    @patch("src.services.claims_service.datetime")
    def test_generate_claim_number_standard_format(self, mock_datetime):
        """Test that claim number follows CLM-YYYYMMDD-XXXX format."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 15, 45, 0)

        claim_number = generate_claim_number()

        assert claim_number.startswith("CLM-20260330-")
        assert len(claim_number) == 17  # CLM-20260330-XXXX
        assert claim_number[-4:].isdigit()

    @patch("src.services.claims_service.random.choices")
    @patch("src.services.claims_service.datetime")
    def test_generate_claim_number_with_specific_suffix(self, mock_datetime, mock_choices):
        """Test claim number with controlled random suffix."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 15, 45, 0)
        mock_choices.return_value = ['5', '6', '7', '8']

        claim_number = generate_claim_number()

        assert claim_number == "CLM-20260330-5678"

    @patch("src.services.claims_service.datetime")
    def test_generate_claim_number_different_dates(self, mock_datetime):
        """Test that different dates produce different claim numbers."""
        mock_datetime.utcnow.return_value = datetime(2025, 12, 25, 10, 0, 0)

        claim_number = generate_claim_number()

        assert claim_number.startswith("CLM-20251225-")

    @patch("src.services.claims_service.datetime")
    def test_generate_claim_number_uniqueness(self, mock_datetime):
        """Test that multiple calls produce different numbers (probabilistic)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 15, 45, 0)

        numbers = [generate_claim_number() for _ in range(10)]

        # All should start with same date prefix
        assert all(n.startswith("CLM-20260330-") for n in numbers)
        # Likely to have at least some unique suffixes
        assert len(set(numbers)) > 1 or len(numbers) == 1


class TestValidateClaimAgainstPolicy:
    """Test claim validation against policy with various scenarios."""

    def _create_mock_policy(self, status="ACTIVE", start_date=None, end_date=None, coverage_amount=Decimal("100000")):
        """Helper to create a mock policy object."""
        from src.config.database import PolicyStatus

        policy = MagicMock()
        policy.status = PolicyStatus[status]
        policy.start_date = start_date or date(2026, 1, 1)
        policy.end_date = end_date or date(2027, 1, 1)
        policy.coverage_amount = coverage_amount
        return policy

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_valid(self, mock_datetime):
        """Test validation passes for valid claim."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy()
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error is None

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_inactive_status(self, mock_datetime):
        """Test that inactive policy cannot have claims."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy(status="EXPIRED")
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Cannot file a claim against a policy with status 'EXPIRED'. Policy must be ACTIVE."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_cancelled_status(self, mock_datetime):
        """Test that cancelled policy cannot have claims."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy(status="CANCELLED")
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Cannot file a claim against a policy with status 'CANCELLED'. Policy must be ACTIVE."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_pending_status(self, mock_datetime):
        """Test that pending policy cannot have claims."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy(status="PENDING")
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Cannot file a claim against a policy with status 'PENDING'. Policy must be ACTIVE."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_before_start_date(self, mock_datetime):
        """Test that claims cannot be filed before policy start date."""
        mock_datetime.utcnow.return_value = datetime(2025, 12, 31, 12, 0, 0)
        policy = self._create_mock_policy(start_date=date(2026, 1, 1))
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Cannot file a claim before the policy start date."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_on_start_date(self, mock_datetime):
        """Test that claims can be filed on policy start date (boundary)."""
        mock_datetime.utcnow.return_value = datetime(2026, 1, 1, 12, 0, 0)
        policy = self._create_mock_policy(start_date=date(2026, 1, 1))
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error is None

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_after_end_date(self, mock_datetime):
        """Test that claims cannot be filed after policy end date."""
        mock_datetime.utcnow.return_value = datetime(2027, 1, 2, 12, 0, 0)
        policy = self._create_mock_policy(end_date=date(2027, 1, 1))
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Cannot file a claim against an expired policy."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_on_end_date(self, mock_datetime):
        """Test that claims can be filed on policy end date (boundary)."""
        mock_datetime.utcnow.return_value = datetime(2027, 1, 1, 12, 0, 0)
        policy = self._create_mock_policy(end_date=date(2027, 1, 1))
        amount = Decimal("50000")

        error = validate_claim_against_policy(policy, amount)

        assert error is None

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_zero_amount(self, mock_datetime):
        """Test that zero claim amount is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy()
        amount = Decimal("0")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Claim amount must be greater than zero."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_negative_amount(self, mock_datetime):
        """Test that negative claim amount is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy()
        amount = Decimal("-100")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Claim amount must be greater than zero."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_exceeds_coverage(self, mock_datetime):
        """Test that claim amount exceeding coverage is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy(coverage_amount=Decimal("100000"))
        amount = Decimal("150000")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Requested amount $150000 exceeds the policy coverage amount $100000."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_exactly_coverage_amount(self, mock_datetime):
        """Test that claim amount exactly equal to coverage is valid (boundary)."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy(coverage_amount=Decimal("100000"))
        amount = Decimal("100000")

        error = validate_claim_against_policy(policy, amount)

        assert error is None

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_one_cent_over_coverage(self, mock_datetime):
        """Test that claim amount one cent over coverage is invalid (boundary)."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy(coverage_amount=Decimal("100000.00"))
        amount = Decimal("100000.01")

        error = validate_claim_against_policy(policy, amount)

        assert error == "Requested amount $100000.01 exceeds the policy coverage amount $100000.00."

    @patch("src.services.claims_service.datetime")
    def test_validate_claim_against_policy_minimum_valid_amount(self, mock_datetime):
        """Test minimum valid claim amount (0.01)."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 12, 0, 0)
        policy = self._create_mock_policy()
        amount = Decimal("0.01")

        error = validate_claim_against_policy(policy, amount)

        assert error is None


class TestCalculateFraudScore:
    """Test fraud score calculation with various claim amounts and coverage."""

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_low_ratio(self, mock_random):
        """Test fraud score for low claim to coverage ratio."""
        mock_random.return_value = 20
        claim_amount = Decimal("10000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 20  # Base score only, ratio is 0.1

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_medium_ratio_above_50(self, mock_random):
        """Test fraud score for ratio just above 0.5."""
        mock_random.return_value = 20
        claim_amount = Decimal("51000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 25  # Base 20 + 5 for ratio > 0.5

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_high_ratio_above_70(self, mock_random):
        """Test fraud score for ratio just above 0.7."""
        mock_random.return_value = 20
        claim_amount = Decimal("71000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 35  # Base 20 + 15 for ratio > 0.7

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_very_high_ratio_above_90(self, mock_random):
        """Test fraud score for ratio just above 0.9."""
        mock_random.return_value = 20
        claim_amount = Decimal("91000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 50  # Base 20 + 30 for ratio > 0.9

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_exactly_50_percent(self, mock_random):
        """Test fraud score at exactly 50% ratio (boundary)."""
        mock_random.return_value = 20
        claim_amount = Decimal("50000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 20  # No bonus at exactly 0.5

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_exactly_70_percent(self, mock_random):
        """Test fraud score at exactly 70% ratio (boundary)."""
        mock_random.return_value = 20
        claim_amount = Decimal("70000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 25  # Base + 5, not + 15 (not over 0.7)

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_exactly_90_percent(self, mock_random):
        """Test fraud score at exactly 90% ratio (boundary)."""
        mock_random.return_value = 20
        claim_amount = Decimal("90000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 35  # Base + 15, not + 30 (not over 0.9)

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_100_percent_ratio(self, mock_random):
        """Test fraud score at 100% claim to coverage ratio."""
        mock_random.return_value = 20
        claim_amount = Decimal("100000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 50  # Base 20 + 30 for ratio > 0.9

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_zero_coverage(self, mock_random):
        """Test fraud score when coverage is zero (edge case)."""
        mock_random.return_value = 20
        claim_amount = Decimal("10000")
        coverage_amount = Decimal("0")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 20  # Only base score, no ratio calculation

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_capped_at_100(self, mock_random):
        """Test that fraud score is capped at 100."""
        mock_random.return_value = 80
        claim_amount = Decimal("95000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 100  # Capped at 100 (80 + 30 = 110 -> 100)

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_minimum_base(self, mock_random):
        """Test fraud score with minimum base value."""
        mock_random.return_value = 5
        claim_amount = Decimal("10000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert 5 <= score <= 40

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_maximum_base(self, mock_random):
        """Test fraud score with maximum base value."""
        mock_random.return_value = 40
        claim_amount = Decimal("10000")
        coverage_amount = Decimal("100000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 40

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_small_amounts(self, mock_random):
        """Test fraud score with very small claim and coverage amounts."""
        mock_random.return_value = 20
        claim_amount = Decimal("100")
        coverage_amount = Decimal("1000")

        score = calculate_fraud_score(claim_amount, coverage_amount)

        assert score == 20  # Ratio 0.1, no bonus
