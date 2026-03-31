"""Tests for src/services/claims_service.py"""
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
    """Test generate_claim_number function."""

    @patch('src.services.claims_service.datetime')
    def test_generate_claim_number_format(self, mock_datetime):
        """Test that claim number has correct format."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 31, 14, 30, 0)

        claim_number = generate_claim_number()

        assert claim_number.startswith("CLM-20260331-")
        assert len(claim_number.split("-")[-1]) == 4
        assert claim_number.split("-")[-1].isdigit()

    def test_generate_claim_number_uniqueness(self):
        """Test that multiple calls generate different numbers."""
        numbers = [generate_claim_number() for _ in range(10)]

        # All numbers should be unique (very high probability)
        assert len(set(numbers)) == 10

    @patch('src.services.claims_service.datetime')
    def test_generate_claim_number_different_dates(self, mock_datetime):
        """Test claim numbers on different dates."""
        mock_datetime.utcnow.return_value = datetime(2026, 1, 1, 0, 0, 0)
        num1 = generate_claim_number()

        mock_datetime.utcnow.return_value = datetime(2026, 12, 31, 23, 59, 59)
        num2 = generate_claim_number()

        assert "20260101" in num1
        assert "20261231" in num2


class TestValidateClaimAgainstPolicy:
    """Test validate_claim_against_policy function with boundary values."""

    def _create_mock_policy(self, status, start_date, end_date, coverage_amount):
        """Helper to create mock policy object."""
        from src.config.database import PolicyStatus
        policy = MagicMock()
        policy.status = status
        policy.start_date = start_date
        policy.end_date = end_date
        policy.coverage_amount = coverage_amount
        return policy

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_valid_policy(self, mock_datetime):
        """Test validation with valid active policy."""
        from src.config.database import PolicyStatus
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15)

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert error is None

    def test_validate_claim_policy_not_active(self):
        """Test that non-active policy returns error."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.PENDING,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert error is not None
        assert "PENDING" in error
        assert "must be ACTIVE" in error

    def test_validate_claim_policy_cancelled(self):
        """Test that cancelled policy returns error."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.CANCELLED,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert error is not None
        assert "CANCELLED" in error

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_before_policy_start(self, mock_datetime):
        """Test claim filed before policy start date."""
        from src.config.database import PolicyStatus
        mock_datetime.utcnow.return_value = datetime(2026, 1, 15)

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 2, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert error is not None
        assert "before the policy start date" in error

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_on_policy_start_date(self, mock_datetime):
        """Test boundary: claim on exact policy start date."""
        from src.config.database import PolicyStatus
        mock_datetime.utcnow.return_value = datetime(2026, 1, 1, 0, 0, 0)

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert error is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_after_policy_end(self, mock_datetime):
        """Test claim filed after policy expiration."""
        from src.config.database import PolicyStatus
        mock_datetime.utcnow.return_value = datetime(2027, 1, 1)

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert error is not None
        assert "expired policy" in error

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_on_policy_end_date(self, mock_datetime):
        """Test boundary: claim on exact policy end date."""
        from src.config.database import PolicyStatus
        mock_datetime.utcnow.return_value = datetime(2026, 12, 31, 23, 59, 59)

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert error is None

    def test_validate_claim_zero_amount(self):
        """Test boundary: claim amount is zero."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("0.00"))

        assert error is not None
        assert "greater than zero" in error

    def test_validate_claim_negative_amount(self):
        """Test boundary: negative claim amount."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("-1000.00"))

        assert error is not None
        assert "greater than zero" in error

    def test_validate_claim_exceeds_coverage(self):
        """Test claim amount exceeding coverage."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("60000.00"))

        assert error is not None
        assert "exceeds the policy coverage amount" in error
        assert "60000" in error
        assert "50000" in error

    def test_validate_claim_exactly_coverage_amount(self):
        """Test boundary: claim equals coverage amount."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("50000.00"))

        assert error is None

    def test_validate_claim_one_cent_over_coverage(self):
        """Test boundary: claim one cent over coverage."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("50000.01"))

        assert error is not None

    def test_validate_claim_minimal_valid_amount(self):
        """Test boundary: minimal valid claim amount."""
        from src.config.database import PolicyStatus

        policy = self._create_mock_policy(
            PolicyStatus.ACTIVE,
            date(2026, 1, 1),
            date(2026, 12, 31),
            Decimal("50000.00")
        )

        error = validate_claim_against_policy(policy, Decimal("0.01"))

        assert error is None


class TestCalculateFraudScore:
    """Test calculate_fraud_score function."""

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_low_ratio(self, mock_randint):
        """Test fraud score with low claim-to-coverage ratio."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("10000"), Decimal("100000"))

        # Ratio is 0.1, no additional risk
        assert score == 20

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_medium_ratio(self, mock_randint):
        """Test fraud score with medium ratio (>0.5)."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("60000"), Decimal("100000"))

        # Ratio is 0.6, adds 5 points
        assert score == 25

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_high_ratio(self, mock_randint):
        """Test fraud score with high ratio (>0.7)."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("75000"), Decimal("100000"))

        # Ratio is 0.75, adds 15 points
        assert score == 35

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_very_high_ratio(self, mock_randint):
        """Test fraud score with very high ratio (>0.9)."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("95000"), Decimal("100000"))

        # Ratio is 0.95, adds 30 points
        assert score == 50

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_boundary_90_percent(self, mock_randint):
        """Test boundary: exactly 90% ratio."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("90000"), Decimal("100000"))

        # Exactly 0.9, should not add 30 points
        assert score == 20

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_boundary_91_percent(self, mock_randint):
        """Test boundary: 91% ratio."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("91000"), Decimal("100000"))

        # Over 0.9, adds 30 points
        assert score == 50

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_capped_at_100(self, mock_randint):
        """Test that fraud score is capped at 100."""
        mock_randint.return_value = 80

        score = calculate_fraud_score(Decimal("99000"), Decimal("100000"))

        # 80 + 30 = 110, should be capped at 100
        assert score == 100

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_zero_coverage(self, mock_randint):
        """Test with zero coverage amount (edge case)."""
        mock_randint.return_value = 25

        score = calculate_fraud_score(Decimal("10000"), Decimal("0"))

        # Should not divide by zero, just return base score
        assert score == 25

    @patch('src.services.claims_service.random.randint')
    def test_fraud_score_equal_amounts(self, mock_randint):
        """Test with claim equal to coverage."""
        mock_randint.return_value = 30

        score = calculate_fraud_score(Decimal("50000"), Decimal("50000"))

        # Ratio is 1.0 (>0.9), adds 30
        assert score == 60
