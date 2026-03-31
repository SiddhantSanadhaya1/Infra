"""
Unit tests for src.services.claims_service
Tests claim number generation, claim validation, and fraud score calculation.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock

from src.services.claims_service import (
    generate_claim_number,
    validate_claim_against_policy,
    calculate_fraud_score,
)


class TestGenerateClaimNumber:
    """Test claim number generation"""

    @patch('src.services.claims_service.datetime')
    @patch('src.services.claims_service.random.choices')
    def test_generate_claim_number_standard(self, mock_choices, mock_datetime):
        """Test claim number generation with standard date"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 14, 30, 0)
        mock_choices.return_value = ['5', '6', '7', '8']

        result = generate_claim_number()

        assert result == "CLM-20260330-5678"
        mock_choices.assert_called_once()

    @patch('src.services.claims_service.datetime')
    @patch('src.services.claims_service.random.choices')
    def test_generate_claim_number_new_year(self, mock_choices, mock_datetime):
        """Test claim number generation on New Year's Day"""
        mock_datetime.utcnow.return_value = datetime(2026, 1, 1, 0, 0, 0)
        mock_choices.return_value = ['0', '0', '0', '1']

        result = generate_claim_number()

        assert result == "CLM-20260101-0001"

    @patch('src.services.claims_service.datetime')
    @patch('src.services.claims_service.random.choices')
    def test_generate_claim_number_year_end(self, mock_choices, mock_datetime):
        """Test claim number generation on year end"""
        mock_datetime.utcnow.return_value = datetime(2026, 12, 31, 23, 59, 59)
        mock_choices.return_value = ['9', '9', '9', '9']

        result = generate_claim_number()

        assert result == "CLM-20261231-9999"


class TestValidateClaimAgainstPolicy:
    """Test claim validation against policy"""

    def create_mock_policy(self, status, start_date, end_date, coverage_amount):
        """Helper to create a mock policy object"""
        policy = MagicMock()
        policy.status = status
        policy.start_date = start_date
        policy.end_date = end_date
        policy.coverage_amount = coverage_amount
        return policy

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_valid(self, mock_datetime):
        """Test validation passes for valid claim"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("50000.00"))

        assert result is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_inactive_policy(self, mock_datetime):
        """Test validation fails for non-ACTIVE policy"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.PENDING,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )
        policy.status.value = "PENDING"

        result = validate_claim_against_policy(policy, Decimal("50000.00"))

        assert result == "Cannot file a claim against a policy with status 'PENDING'. Policy must be ACTIVE."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_expired_policy(self, mock_datetime):
        """Test validation fails for EXPIRED policy"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.EXPIRED,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            coverage_amount=Decimal("100000.00")
        )
        policy.status.value = "EXPIRED"

        result = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert result == "Cannot file a claim against a policy with status 'EXPIRED'. Policy must be ACTIVE."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_cancelled_policy(self, mock_datetime):
        """Test validation fails for CANCELLED policy"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.CANCELLED,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )
        policy.status.value = "CANCELLED"

        result = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert result == "Cannot file a claim against a policy with status 'CANCELLED'. Policy must be ACTIVE."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_before_start_date(self, mock_datetime):
        """Test validation fails when claim filed before policy start"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 3, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert result == "Cannot file a claim before the policy start date."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_after_end_date(self, mock_datetime):
        """Test validation fails when claim filed after policy expiry"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2027, 1, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("10000.00"))

        assert result == "Cannot file a claim against an expired policy."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_zero_amount(self, mock_datetime):
        """Test validation fails for zero claim amount"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("0"))

        assert result == "Claim amount must be greater than zero."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_negative_amount(self, mock_datetime):
        """Test validation fails for negative claim amount"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("-1000.00"))

        assert result == "Claim amount must be greater than zero."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_exceeds_coverage(self, mock_datetime):
        """Test validation fails when claim exceeds coverage amount"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("150000.00"))

        assert result == "Requested amount $150000.00 exceeds the policy coverage amount $100000.00."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_equals_coverage(self, mock_datetime):
        """Test validation passes when claim equals coverage amount"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("100000.00"))

        assert result is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_on_start_date(self, mock_datetime):
        """Test validation passes when claim filed on policy start date"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 1, 1, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("50000.00"))

        assert result is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_on_end_date(self, mock_datetime):
        """Test validation passes when claim filed on policy end date"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 12, 31, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("50000.00"))

        assert result is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_small_amount(self, mock_datetime):
        """Test validation passes for very small claim amount"""
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)

        policy = self.create_mock_policy(
            status=PolicyStatus.ACTIVE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            coverage_amount=Decimal("100000.00")
        )

        result = validate_claim_against_policy(policy, Decimal("0.01"))

        assert result is None


class TestCalculateFraudScore:
    """Test fraud score calculation"""

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_low_ratio(self, mock_randint):
        """Test fraud score for low claim-to-coverage ratio"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("10000.00"), Decimal("100000.00"))

        assert score == 20
        mock_randint.assert_called_once_with(5, 40)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_medium_ratio(self, mock_randint):
        """Test fraud score for medium claim-to-coverage ratio (60%)"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("60000.00"), Decimal("100000.00"))

        assert score == 25  # 20 + 5 bonus for >0.5 ratio
        mock_randint.assert_called_once_with(5, 40)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_high_ratio(self, mock_randint):
        """Test fraud score for high claim-to-coverage ratio (80%)"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("80000.00"), Decimal("100000.00"))

        assert score == 35  # 20 + 15 bonus for >0.7 ratio
        mock_randint.assert_called_once_with(5, 40)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_very_high_ratio(self, mock_randint):
        """Test fraud score for very high claim-to-coverage ratio (95%)"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("95000.00"), Decimal("100000.00"))

        assert score == 50  # 20 + 30 bonus for >0.9 ratio
        mock_randint.assert_called_once_with(5, 40)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_exact_coverage(self, mock_randint):
        """Test fraud score when claim equals coverage (100%)"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("100000.00"), Decimal("100000.00"))

        assert score == 50  # 20 + 30 bonus for ratio = 1.0
        mock_randint.assert_called_once_with(5, 40)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_zero_coverage(self, mock_randint):
        """Test fraud score when coverage is zero (edge case)"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("10000.00"), Decimal("0"))

        assert score == 20  # No bonus, only base score
        mock_randint.assert_called_once_with(5, 40)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_capped_at_100(self, mock_randint):
        """Test fraud score is capped at 100"""
        mock_randint.return_value = 40  # Max base score

        score = calculate_fraud_score(Decimal("95000.00"), Decimal("100000.00"))

        assert score == 70  # 40 + 30 = 70, but would be capped at 100 if higher

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_exact_boundary_50_percent(self, mock_randint):
        """Test fraud score at exactly 50% ratio boundary"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("50000.00"), Decimal("100000.00"))

        assert score == 20  # No bonus at exactly 0.5

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_just_over_50_percent(self, mock_randint):
        """Test fraud score just over 50% ratio boundary"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("50000.01"), Decimal("100000.00"))

        assert score == 25  # 20 + 5 bonus for >0.5 ratio

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_exact_boundary_70_percent(self, mock_randint):
        """Test fraud score at exactly 70% ratio boundary"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("70000.00"), Decimal("100000.00"))

        assert score == 25  # 20 + 5, not 15 (needs to be >0.7)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_exact_boundary_90_percent(self, mock_randint):
        """Test fraud score at exactly 90% ratio boundary"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("90000.00"), Decimal("100000.00"))

        assert score == 35  # 20 + 15, not 30 (needs to be >0.9)

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_minimum_base(self, mock_randint):
        """Test fraud score with minimum random base"""
        mock_randint.return_value = 5  # Minimum base score

        score = calculate_fraud_score(Decimal("10000.00"), Decimal("100000.00"))

        assert score == 5

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_maximum_base(self, mock_randint):
        """Test fraud score with maximum random base"""
        mock_randint.return_value = 40  # Maximum base score

        score = calculate_fraud_score(Decimal("10000.00"), Decimal("100000.00"))

        assert score == 40
