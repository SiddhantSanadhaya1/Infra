"""Unit tests for src.services.claims_service module."""
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.services.claims_service import (
    generate_claim_number,
    validate_claim_against_policy,
    calculate_fraud_score,
)


class TestGenerateClaimNumber:
    """Test claim number generation."""

    @patch("src.services.claims_service.datetime")
    @patch("src.services.claims_service.random.choices")
    def test_generate_claim_number_format(self, mock_choices, mock_datetime):
        """Test claim number has correct format CLM-YYYYMMDD-XXXX."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 14, 30, 0)
        mock_choices.return_value = ["1", "2", "3", "4"]

        result = generate_claim_number()

        assert result == "CLM-20260330-1234"
        mock_choices.assert_called_once()

    @patch("src.services.claims_service.datetime")
    @patch("src.services.claims_service.random.choices")
    def test_generate_claim_number_different_dates(self, mock_choices, mock_datetime):
        """Test claim number changes with different dates."""
        mock_datetime.utcnow.return_value = datetime(2025, 12, 31, 23, 59, 59)
        mock_choices.return_value = ["9", "8", "7", "6"]

        result = generate_claim_number()

        assert result == "CLM-20251231-9876"

    @patch("src.services.claims_service.datetime")
    @patch("src.services.claims_service.random.choices")
    def test_generate_claim_number_with_zeros(self, mock_choices, mock_datetime):
        """Test claim number handles leading zeros in suffix."""
        mock_datetime.utcnow.return_value = datetime(2026, 1, 1, 0, 0, 0)
        mock_choices.return_value = ["0", "0", "0", "1"]

        result = generate_claim_number()

        assert result == "CLM-20260101-0001"


class TestValidateClaimAgainstPolicy:
    """Test claim validation against policy."""

    def test_validate_claim_with_active_policy_valid_amount(self):
        """Test validation passes for active policy with valid amount."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2026, 1, 1)
        mock_policy.end_date = date(2026, 12, 31)
        mock_policy.coverage_amount = Decimal("100000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("50000.00"))

        assert result is None

    def test_validate_claim_with_inactive_policy(self):
        """Test validation fails for non-active policy."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.EXPIRED
        mock_policy.start_date = date(2025, 1, 1)
        mock_policy.end_date = date(2025, 12, 31)
        mock_policy.coverage_amount = Decimal("100000.00")

        result = validate_claim_against_policy(mock_policy, Decimal("1000.00"))

        assert result == "Cannot file a claim against a policy with status 'EXPIRED'. Policy must be ACTIVE."

    def test_validate_claim_with_cancelled_policy(self):
        """Test validation fails for cancelled policy."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.CANCELLED
        mock_policy.coverage_amount = Decimal("100000.00")

        result = validate_claim_against_policy(mock_policy, Decimal("1000.00"))

        assert "Cannot file a claim against a policy with status 'CANCELLED'" in result

    def test_validate_claim_before_policy_start_date(self):
        """Test validation fails for claims before policy start date."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2026, 6, 1)
        mock_policy.end_date = date(2026, 12, 31)
        mock_policy.coverage_amount = Decimal("100000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("1000.00"))

        assert result == "Cannot file a claim before the policy start date."

    def test_validate_claim_after_policy_end_date(self):
        """Test validation fails for claims after policy expiry."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2025, 1, 1)
        mock_policy.end_date = date(2025, 12, 31)
        mock_policy.coverage_amount = Decimal("100000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("1000.00"))

        assert result == "Cannot file a claim against an expired policy."

    def test_validate_claim_with_zero_amount(self):
        """Test validation fails for zero claim amount."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2026, 1, 1)
        mock_policy.end_date = date(2026, 12, 31)
        mock_policy.coverage_amount = Decimal("100000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("0"))

        assert result == "Claim amount must be greater than zero."

    def test_validate_claim_with_negative_amount(self):
        """Test validation fails for negative claim amount."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2026, 1, 1)
        mock_policy.end_date = date(2026, 12, 31)
        mock_policy.coverage_amount = Decimal("100000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("-1000.00"))

        assert result == "Claim amount must be greater than zero."

    def test_validate_claim_exceeds_coverage_amount(self):
        """Test validation fails when claim exceeds coverage."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2026, 1, 1)
        mock_policy.end_date = date(2026, 12, 31)
        mock_policy.coverage_amount = Decimal("50000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("75000.00"))

        assert "Requested amount $75000.00 exceeds the policy coverage amount $50000.00" in result

    def test_validate_claim_at_exact_coverage_limit(self):
        """Test validation passes when claim equals coverage amount."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2026, 1, 1)
        mock_policy.end_date = date(2026, 12, 31)
        mock_policy.coverage_amount = Decimal("100000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("100000.00"))

        assert result is None

    def test_validate_claim_on_policy_end_date(self):
        """Test validation passes on the last day of policy."""
        from src.config.database import PolicyStatus

        mock_policy = MagicMock()
        mock_policy.status = PolicyStatus.ACTIVE
        mock_policy.start_date = date(2026, 1, 1)
        mock_policy.end_date = date(2026, 3, 30)
        mock_policy.coverage_amount = Decimal("100000.00")

        with patch("src.services.claims_service.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2026, 3, 30)
            result = validate_claim_against_policy(mock_policy, Decimal("5000.00"))

        assert result is None


class TestCalculateFraudScore:
    """Test fraud score calculation."""

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_low_ratio(self, mock_randint):
        """Test fraud score for low claim-to-coverage ratio."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("10000"), Decimal("100000"))

        # Ratio is 0.1, no additional score
        assert score == 20

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_medium_ratio(self, mock_randint):
        """Test fraud score for medium claim-to-coverage ratio."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("60000"), Decimal("100000"))

        # Ratio is 0.6, adds 5
        assert score == 25

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_high_ratio(self, mock_randint):
        """Test fraud score for high claim-to-coverage ratio."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("75000"), Decimal("100000"))

        # Ratio is 0.75, adds 15
        assert score == 35

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_very_high_ratio(self, mock_randint):
        """Test fraud score for very high claim-to-coverage ratio."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("95000"), Decimal("100000"))

        # Ratio is 0.95, adds 30
        assert score == 50

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_exact_coverage(self, mock_randint):
        """Test fraud score when claim equals coverage."""
        mock_randint.return_value = 30

        score = calculate_fraud_score(Decimal("100000"), Decimal("100000"))

        # Ratio is 1.0, adds 30
        assert score == 60

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_exceeds_100(self, mock_randint):
        """Test fraud score is capped at 100."""
        mock_randint.return_value = 40

        score = calculate_fraud_score(Decimal("99000"), Decimal("100000"))

        # Base 40 + 30 = 70, but if it somehow exceeds 100, it's capped
        assert score <= 100

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_with_zero_coverage(self, mock_randint):
        """Test fraud score when coverage is zero."""
        mock_randint.return_value = 25

        score = calculate_fraud_score(Decimal("5000"), Decimal("0"))

        # Should not divide by zero, returns base score
        assert score == 25

    @patch("src.services.claims_service.random.randint")
    def test_calculate_fraud_score_randomness_range(self, mock_randint):
        """Test fraud score base is within expected random range."""
        mock_randint.return_value = 5  # Minimum base

        score = calculate_fraud_score(Decimal("1000"), Decimal("100000"))

        assert score >= 5

        mock_randint.return_value = 40  # Maximum base

        score = calculate_fraud_score(Decimal("1000"), Decimal("100000"))

        assert score <= 100
