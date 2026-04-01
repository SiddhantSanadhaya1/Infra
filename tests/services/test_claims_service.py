"""Unit tests for claims service module"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch, MagicMock


class TestGenerateClaimNumber:
    """Test claim number generation"""

    @patch('src.services.claims_service.datetime')
    def test_generate_claim_number_format(self, mock_datetime):
        """Test claim number has correct format"""
        from src.services.claims_service import generate_claim_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1, 12, 0, 0)

        claim_number = generate_claim_number()

        # Format: CLM-YYYYMMDD-XXXX
        assert claim_number.startswith("CLM-20260401-")
        assert len(claim_number) == 18  # CLM-20260401-1234
        assert claim_number.split("-")[-1].isdigit()
        assert len(claim_number.split("-")[-1]) == 4

    @patch('src.services.claims_service.datetime')
    def test_generate_claim_number_different_dates(self, mock_datetime):
        """Test claim numbers reflect different dates"""
        from src.services.claims_service import generate_claim_number

        mock_datetime.utcnow.return_value = datetime(2026, 12, 31, 23, 59, 59)

        claim_number = generate_claim_number()

        assert claim_number.startswith("CLM-20261231-")

    @patch('src.services.claims_service.random.choices')
    @patch('src.services.claims_service.datetime')
    def test_generate_claim_number_random_suffix(self, mock_datetime, mock_choices):
        """Test claim number generates 4-digit random suffix"""
        from src.services.claims_service import generate_claim_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)
        mock_choices.return_value = ['5', '6', '7', '8']

        claim_number = generate_claim_number()

        assert claim_number.endswith("5678")


class TestValidateClaimAgainstPolicy:
    """Test claim validation against policy"""

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_valid(self, mock_datetime):
        """Test validation passes for valid claim"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_inactive_policy(self, mock_datetime):
        """Test validation fails for inactive policy"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        policy = MagicMock()
        policy.status = PolicyStatus.CANCELLED
        policy.status.value = "CANCELLED"

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error == "Cannot file a claim against a policy with status 'CANCELLED'. Policy must be ACTIVE."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_expired_policy(self, mock_datetime):
        """Test validation fails for expired policy status"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        policy = MagicMock()
        policy.status = PolicyStatus.EXPIRED
        policy.status.value = "EXPIRED"

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error == "Cannot file a claim against a policy with status 'EXPIRED'. Policy must be ACTIVE."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_pending_policy(self, mock_datetime):
        """Test validation fails for pending policy status"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        policy = MagicMock()
        policy.status = PolicyStatus.PENDING
        policy.status.value = "PENDING"

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error == "Cannot file a claim against a policy with status 'PENDING'. Policy must be ACTIVE."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_before_start_date(self, mock_datetime):
        """Test validation fails for claim before policy start date"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2025, 12, 31)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error == "Cannot file a claim before the policy start date."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_on_start_date(self, mock_datetime):
        """Test validation passes for claim on policy start date"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 1, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_after_end_date(self, mock_datetime):
        """Test validation fails for claim after policy end date"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2027, 1, 2)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error == "Cannot file a claim against an expired policy."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_on_end_date(self, mock_datetime):
        """Test validation passes for claim on policy end date"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2027, 1, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("5000.00"))

        assert error is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_zero_amount(self, mock_datetime):
        """Test validation fails for zero claim amount"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)

        error = validate_claim_against_policy(policy, Decimal("0"))

        assert error == "Claim amount must be greater than zero."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_negative_amount(self, mock_datetime):
        """Test validation fails for negative claim amount"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)

        error = validate_claim_against_policy(policy, Decimal("-1000.00"))

        assert error == "Claim amount must be greater than zero."

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_exceeds_coverage(self, mock_datetime):
        """Test validation fails when claim exceeds coverage amount"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("150000.00"))

        assert "Requested amount $150000.00 exceeds the policy coverage amount $100000.00" in error

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_equals_coverage(self, mock_datetime):
        """Test validation passes when claim equals coverage amount"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("100000.00"))

        assert error is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_just_under_coverage(self, mock_datetime):
        """Test validation passes when claim is just under coverage"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("99999.99"))

        assert error is None

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_just_over_coverage(self, mock_datetime):
        """Test validation fails when claim is just over coverage"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("100000.01"))

        assert "exceeds the policy coverage amount" in error

    @patch('src.services.claims_service.datetime')
    def test_validate_claim_small_amount(self, mock_datetime):
        """Test validation passes for very small claim amount"""
        from src.services.claims_service import validate_claim_against_policy
        from src.config.database import PolicyStatus

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        policy = MagicMock()
        policy.status = PolicyStatus.ACTIVE
        policy.start_date = date(2026, 1, 1)
        policy.end_date = date(2027, 1, 1)
        policy.coverage_amount = Decimal("100000.00")

        error = validate_claim_against_policy(policy, Decimal("0.01"))

        assert error is None


class TestCalculateFraudScore:
    """Test fraud score calculation"""

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_low_ratio(self, mock_randint):
        """Test fraud score for low claim to coverage ratio"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("10000"), Decimal("100000"))

        # Ratio is 0.1, should not add bonus
        assert score == 20

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_medium_ratio(self, mock_randint):
        """Test fraud score for medium claim to coverage ratio (50-70%)"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("60000"), Decimal("100000"))

        # Ratio is 0.6, should add 5
        assert score == 25

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_high_ratio(self, mock_randint):
        """Test fraud score for high claim to coverage ratio (70-90%)"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("80000"), Decimal("100000"))

        # Ratio is 0.8, should add 15
        assert score == 35

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_very_high_ratio(self, mock_randint):
        """Test fraud score for very high claim to coverage ratio (>90%)"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("95000"), Decimal("100000"))

        # Ratio is 0.95, should add 30
        assert score == 50

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_exact_coverage(self, mock_randint):
        """Test fraud score when claim equals coverage (ratio = 1.0)"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("100000"), Decimal("100000"))

        # Ratio is 1.0, should add 30
        assert score == 50

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_zero_coverage(self, mock_randint):
        """Test fraud score with zero coverage (edge case)"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("5000"), Decimal("0"))

        # Zero coverage, no bonus added
        assert score == 20

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_capped_at_100(self, mock_randint):
        """Test fraud score is capped at 100"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 40  # High base score

        score = calculate_fraud_score(Decimal("95000"), Decimal("100000"))

        # 40 + 30 = 70, but max is 100
        assert score <= 100

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_boundary_50_percent(self, mock_randint):
        """Test fraud score at 50% ratio boundary"""
        from src.services.claims_service import calculate_fraud_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("50000"), Decimal("100000"))

        # Ratio is exactly 0.5, should not add bonus (condition is >0.5)
        assert score == 20

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_just_over_50_percent(self, mock_randint):
        """Test fraud score just over 50% ratio"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("50001"), Decimal("100000"))

        # Ratio is 0.50001, should add 5
        assert score == 25

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_boundary_70_percent(self, mock_randint):
        """Test fraud score at 70% ratio boundary"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("70000"), Decimal("100000"))

        # Ratio is exactly 0.7, should not add 15 (condition is >0.7)
        assert score == 25  # Base 20 + 5 for >0.5

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_boundary_90_percent(self, mock_randint):
        """Test fraud score at 90% ratio boundary"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(Decimal("90000"), Decimal("100000"))

        # Ratio is exactly 0.9, should not add 30 (condition is >0.9)
        assert score == 35  # Base 20 + 15 for >0.7

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_minimum_base(self, mock_randint):
        """Test fraud score with minimum base value"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 5  # Minimum base

        score = calculate_fraud_score(Decimal("1000"), Decimal("100000"))

        assert score == 5

    @patch('src.services.claims_service.random.randint')
    def test_calculate_fraud_score_maximum_base(self, mock_randint):
        """Test fraud score with maximum base value"""
        from src.services.claims_service import calculate_fraud_score

        mock_randint.return_value = 40  # Maximum base

        score = calculate_fraud_score(Decimal("1000"), Decimal("100000"))

        assert score == 40
