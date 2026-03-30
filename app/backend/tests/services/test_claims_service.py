import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from src.services.claims_service import (
    generate_claim_number,
    validate_claim_against_policy,
    calculate_fraud_score,
)


class TestGenerateClaimNumber:
    """Test suite for generate_claim_number function."""

    def test_generate_claim_number_format(self):
        """Test that claim number matches expected format CLM-YYYYMMDD-XXXX."""
        result = generate_claim_number()

        parts = result.split("-")
        assert len(parts) == 3
        assert parts[0] == "CLM"
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 4  # 4 digit suffix
        assert parts[2].isdigit()

    @patch("src.services.claims_service.datetime")
    def test_generate_claim_number_date_format(self, mock_datetime):
        """Test that date portion uses correct YYYYMMDD format."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 15, 30, 0)

        result = generate_claim_number()
        parts = result.split("-")
        assert parts[1] == "20260330"

    def test_generate_claim_number_uniqueness(self):
        """Test that multiple calls generate different suffixes (probabilistic)."""
        results = [generate_claim_number() for _ in range(10)]

        # With 10,000 possible suffixes, all 10 should be unique
        assert len(set(results)) == 10

    def test_generate_claim_number_suffix_is_numeric(self):
        """Test that suffix contains only digits."""
        result = generate_claim_number()
        suffix = result.split("-")[2]
        assert suffix.isdigit()
        assert len(suffix) == 4


class TestValidateClaimAgainstPolicy:
    """Test suite for validate_claim_against_policy function."""

    def create_mock_policy(
        self,
        status="ACTIVE",
        start_date=None,
        end_date=None,
        coverage_amount=100000
    ):
        """Helper to create a mock policy object."""
        from src.config.database import PolicyStatus

        policy = Mock()
        policy.status = PolicyStatus[status] if isinstance(status, str) else status
        policy.start_date = start_date or date.today() - timedelta(days=30)
        policy.end_date = end_date or date.today() + timedelta(days=335)
        policy.coverage_amount = Decimal(str(coverage_amount))
        return policy

    def test_validate_claim_valid(self):
        """Test validation passes for a valid claim."""
        policy = self.create_mock_policy()
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert result is None

    def test_validate_claim_inactive_policy(self):
        """Test validation fails for inactive policy."""
        policy = self.create_mock_policy(status="PENDING")
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert "Cannot file a claim against a policy with status 'PENDING'" in result
        assert "Policy must be ACTIVE" in result

    def test_validate_claim_expired_policy(self):
        """Test validation fails for expired policy status."""
        policy = self.create_mock_policy(status="EXPIRED")
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert "EXPIRED" in result

    def test_validate_claim_cancelled_policy(self):
        """Test validation fails for cancelled policy status."""
        policy = self.create_mock_policy(status="CANCELLED")
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert "CANCELLED" in result

    def test_validate_claim_before_start_date(self):
        """Test validation fails when filing before policy start date."""
        start_date = date.today() + timedelta(days=10)
        end_date = start_date + timedelta(days=365)
        policy = self.create_mock_policy(start_date=start_date, end_date=end_date)
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert result == "Cannot file a claim before the policy start date."

    def test_validate_claim_after_end_date(self):
        """Test validation fails when filing after policy expiry."""
        start_date = date.today() - timedelta(days=400)
        end_date = date.today() - timedelta(days=1)
        policy = self.create_mock_policy(start_date=start_date, end_date=end_date)
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert result == "Cannot file a claim against an expired policy."

    def test_validate_claim_on_end_date(self):
        """Test validation passes when filing on policy end date."""
        start_date = date.today() - timedelta(days=365)
        end_date = date.today()
        policy = self.create_mock_policy(start_date=start_date, end_date=end_date)
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert result is None

    def test_validate_claim_zero_amount(self):
        """Test validation fails for zero claim amount."""
        policy = self.create_mock_policy()
        amount = Decimal("0")

        result = validate_claim_against_policy(policy, amount)
        assert result == "Claim amount must be greater than zero."

    def test_validate_claim_negative_amount(self):
        """Test validation fails for negative claim amount."""
        policy = self.create_mock_policy()
        amount = Decimal("-1000.00")

        result = validate_claim_against_policy(policy, amount)
        assert result == "Claim amount must be greater than zero."

    def test_validate_claim_exceeds_coverage(self):
        """Test validation fails when claim exceeds coverage amount."""
        policy = self.create_mock_policy(coverage_amount=50000)
        amount = Decimal("50000.01")

        result = validate_claim_against_policy(policy, amount)
        assert "exceeds the policy coverage amount" in result
        assert "$50000.01" in result
        assert "$50000" in result

    def test_validate_claim_equals_coverage(self):
        """Test validation passes when claim equals coverage amount."""
        policy = self.create_mock_policy(coverage_amount=50000)
        amount = Decimal("50000.00")

        result = validate_claim_against_policy(policy, amount)
        assert result is None

    def test_validate_claim_minimal_valid_amount(self):
        """Test validation passes for minimal positive amount."""
        policy = self.create_mock_policy()
        amount = Decimal("0.01")

        result = validate_claim_against_policy(policy, amount)
        assert result is None

    @pytest.mark.parametrize("status", ["PENDING", "EXPIRED", "CANCELLED"])
    def test_validate_claim_various_invalid_statuses(self, status):
        """Test validation fails for various non-active policy statuses."""
        policy = self.create_mock_policy(status=status)
        amount = Decimal("5000.00")

        result = validate_claim_against_policy(policy, amount)
        assert result is not None
        assert status in result

    @pytest.mark.parametrize("amount", ["1000", "50000", "99999.99"])
    def test_validate_claim_various_valid_amounts(self, amount):
        """Test validation passes for various valid amounts."""
        policy = self.create_mock_policy(coverage_amount=100000)
        claim_amount = Decimal(amount)

        result = validate_claim_against_policy(policy, claim_amount)
        assert result is None


class TestCalculateFraudScore:
    """Test suite for calculate_fraud_score function."""

    def test_calculate_fraud_score_returns_integer(self):
        """Test that fraud score returns an integer."""
        result = calculate_fraud_score(Decimal("10000"), Decimal("100000"))
        assert isinstance(result, int)

    def test_calculate_fraud_score_within_range(self):
        """Test that fraud score is between 0 and 100."""
        result = calculate_fraud_score(Decimal("10000"), Decimal("100000"))
        assert 0 <= result <= 100

    def test_calculate_fraud_score_low_ratio(self):
        """Test fraud score for low claim-to-coverage ratio."""
        # Low ratio (10%) should result in lower score
        scores = [
            calculate_fraud_score(Decimal("10000"), Decimal("100000"))
            for _ in range(10)
        ]
        avg_score = sum(scores) / len(scores)
        assert avg_score < 50  # Should be relatively low

    def test_calculate_fraud_score_high_ratio(self):
        """Test fraud score for high claim-to-coverage ratio (>90%)."""
        # High ratio should add 30 to base score
        scores = [
            calculate_fraud_score(Decimal("95000"), Decimal("100000"))
            for _ in range(10)
        ]
        avg_score = sum(scores) / len(scores)
        assert avg_score > 50  # Should be higher due to 90%+ ratio bonus

    def test_calculate_fraud_score_medium_ratio(self):
        """Test fraud score for medium claim-to-coverage ratio (70-90%)."""
        # Ratio between 70-90% should add 15 to base score
        result = calculate_fraud_score(Decimal("80000"), Decimal("100000"))
        assert 0 <= result <= 100

    def test_calculate_fraud_score_exact_coverage(self):
        """Test fraud score when claiming exact coverage amount."""
        result = calculate_fraud_score(Decimal("100000"), Decimal("100000"))
        # ratio > 0.9, should add 30 to base score
        assert result >= 35  # minimum base (5) + ratio bonus (30)

    def test_calculate_fraud_score_zero_coverage(self):
        """Test fraud score with zero coverage amount (edge case)."""
        result = calculate_fraud_score(Decimal("10000"), Decimal("0"))
        # Should not crash, returns base score only
        assert 0 <= result <= 100

    def test_calculate_fraud_score_zero_claim(self):
        """Test fraud score with zero claim amount."""
        result = calculate_fraud_score(Decimal("0"), Decimal("100000"))
        # ratio = 0, no bonus applied
        assert 5 <= result <= 40  # Just base score

    def test_calculate_fraud_score_max_cap(self):
        """Test that fraud score never exceeds 100."""
        # Even with very high values, should cap at 100
        result = calculate_fraud_score(Decimal("999999"), Decimal("1000000"))
        assert result == 100

    @pytest.mark.parametrize("claim,coverage", [
        (Decimal("10000"), Decimal("100000")),  # 10% ratio
        (Decimal("50000"), Decimal("100000")),  # 50% ratio
        (Decimal("60000"), Decimal("100000")),  # 60% ratio
        (Decimal("75000"), Decimal("100000")),  # 75% ratio
        (Decimal("91000"), Decimal("100000")),  # 91% ratio
    ])
    def test_calculate_fraud_score_various_ratios(self, claim, coverage):
        """Test fraud scores for various claim-to-coverage ratios."""
        result = calculate_fraud_score(claim, coverage)
        assert 0 <= result <= 100

        ratio = float(claim) / float(coverage)
        if ratio > 0.9:
            # Should have higher average score due to bonus
            assert result >= 5  # At minimum base score
        elif ratio > 0.5:
            # Should have some bonus
            assert result >= 5

    def test_calculate_fraud_score_randomness(self):
        """Test that fraud score has random component."""
        scores = [
            calculate_fraud_score(Decimal("50000"), Decimal("100000"))
            for _ in range(20)
        ]
        # Should not all be identical due to randomness
        assert len(set(scores)) > 1

    def test_calculate_fraud_score_small_amounts(self):
        """Test fraud score with small claim and coverage amounts."""
        result = calculate_fraud_score(Decimal("10"), Decimal("100"))
        assert 0 <= result <= 100

    def test_calculate_fraud_score_large_amounts(self):
        """Test fraud score with large claim and coverage amounts."""
        result = calculate_fraud_score(
            Decimal("5000000"),
            Decimal("10000000")
        )
        assert 0 <= result <= 100
