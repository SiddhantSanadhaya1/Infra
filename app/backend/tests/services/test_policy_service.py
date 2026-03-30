import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from src.services.policy_service import (
    generate_policy_number,
    validate_coverage_dates,
    check_policyholder_eligibility,
)


class TestGeneratePolicyNumber:
    """Test suite for generate_policy_number function."""

    def test_generate_policy_number_format(self):
        """Test that policy number matches expected format POL-TYPE-YYYYMMDD-XXXX."""
        policy_type = "AUTO"
        result = generate_policy_number(policy_type)

        parts = result.split("-")
        assert len(parts) == 4
        assert parts[0] == "POL"
        assert parts[1] == "AUTO"
        assert len(parts[2]) == 8  # YYYYMMDD
        assert len(parts[3]) == 4  # 4 digit suffix
        assert parts[3].isdigit()

    def test_generate_policy_number_truncates_long_type(self):
        """Test that policy types longer than 4 chars are truncated."""
        policy_type = "COMMERCIAL"
        result = generate_policy_number(policy_type)

        parts = result.split("-")
        assert parts[1] == "COMM"  # First 4 chars

    def test_generate_policy_number_short_type(self):
        """Test policy number generation with short type code."""
        policy_type = "LI"
        result = generate_policy_number(policy_type)

        parts = result.split("-")
        assert parts[1] == "LI"

    def test_generate_policy_number_lowercase_type(self):
        """Test that lowercase policy type is converted to uppercase."""
        policy_type = "home"
        result = generate_policy_number(policy_type)

        parts = result.split("-")
        assert parts[1] == "HOME"

    @patch("src.services.policy_service.datetime")
    def test_generate_policy_number_date_format(self, mock_datetime):
        """Test that date portion uses correct YYYYMMDD format."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        result = generate_policy_number("AUTO")
        parts = result.split("-")
        assert parts[2] == "20260330"

    def test_generate_policy_number_uniqueness(self):
        """Test that multiple calls generate different suffixes (probabilistic)."""
        policy_type = "AUTO"
        results = [generate_policy_number(policy_type) for _ in range(10)]

        # With 10,000 possible suffixes, all 10 should be unique
        assert len(set(results)) == 10

    def test_generate_policy_number_empty_string(self):
        """Test generation with empty string policy type."""
        result = generate_policy_number("")
        parts = result.split("-")
        assert parts[1] == ""

    @pytest.mark.parametrize("policy_type,expected_prefix", [
        ("AUTO", "AUTO"),
        ("HOME", "HOME"),
        ("LIFE", "LIFE"),
        ("COMMERCIAL", "COMM"),
    ])
    def test_generate_policy_number_various_types(self, policy_type, expected_prefix):
        """Test policy number generation for various policy types."""
        result = generate_policy_number(policy_type)
        parts = result.split("-")
        assert parts[1] == expected_prefix


class TestValidateCoverageDates:
    """Test suite for validate_coverage_dates function."""

    def test_validate_coverage_dates_valid(self):
        """Test validation passes for valid date range."""
        start_date = date.today()
        end_date = start_date + timedelta(days=365)

        result = validate_coverage_dates(start_date, end_date)
        assert result is None

    def test_validate_coverage_dates_end_before_start(self):
        """Test validation fails when end date is before start date."""
        start_date = date.today()
        end_date = start_date - timedelta(days=1)

        result = validate_coverage_dates(start_date, end_date)
        assert result == "Policy end date must be after the start date."

    def test_validate_coverage_dates_end_equals_start(self):
        """Test validation fails when end date equals start date."""
        start_date = date.today()
        end_date = start_date

        result = validate_coverage_dates(start_date, end_date)
        assert result == "Policy end date must be after the start date."

    def test_validate_coverage_dates_past_end_date(self):
        """Test validation fails when end date is in the past."""
        start_date = date.today() - timedelta(days=100)
        end_date = date.today() - timedelta(days=1)

        result = validate_coverage_dates(start_date, end_date)
        assert result == "Policy end date cannot be in the past."

    def test_validate_coverage_dates_exceeds_max_duration(self):
        """Test validation fails when duration exceeds 5 years."""
        start_date = date.today()
        end_date = start_date + timedelta(days=365 * 5 + 1)

        result = validate_coverage_dates(start_date, end_date)
        assert result == "Policy duration cannot exceed 5 years."

    def test_validate_coverage_dates_exactly_5_years(self):
        """Test validation passes for exactly 5 year duration."""
        start_date = date.today()
        end_date = start_date + timedelta(days=365 * 5)

        result = validate_coverage_dates(start_date, end_date)
        assert result is None

    def test_validate_coverage_dates_one_day_duration(self):
        """Test validation passes for minimum valid duration (1 day)."""
        start_date = date.today()
        end_date = start_date + timedelta(days=1)

        result = validate_coverage_dates(start_date, end_date)
        assert result is None

    def test_validate_coverage_dates_future_start(self):
        """Test validation passes for future start date."""
        start_date = date.today() + timedelta(days=30)
        end_date = start_date + timedelta(days=365)

        result = validate_coverage_dates(start_date, end_date)
        assert result is None

    @pytest.mark.parametrize("days_offset", [0, -1, -100])
    def test_validate_coverage_dates_various_past_end_dates(self, days_offset):
        """Test validation for various past end dates."""
        start_date = date.today() + timedelta(days=days_offset - 10)
        end_date = date.today() + timedelta(days=days_offset)

        if days_offset < 0:
            result = validate_coverage_dates(start_date, end_date)
            assert "past" in result.lower() or "after" in result.lower()


class TestCheckPolicyholderEligibility:
    """Test suite for check_policyholder_eligibility function."""

    def test_check_policyholder_eligibility_valid_age(self):
        """Test eligibility check passes for valid age (30 years old)."""
        dob = date.today() - timedelta(days=30 * 365)

        result = check_policyholder_eligibility(dob)
        assert result is None

    def test_check_policyholder_eligibility_none_dob(self):
        """Test eligibility check passes when DOB is None."""
        result = check_policyholder_eligibility(None)
        assert result is None

    def test_check_policyholder_eligibility_under_18(self):
        """Test eligibility fails for person under 18."""
        dob = date.today() - timedelta(days=17 * 365)

        result = check_policyholder_eligibility(dob)
        assert result == "Policyholder must be at least 18 years old."

    def test_check_policyholder_eligibility_exactly_18(self):
        """Test eligibility passes for exactly 18 years old."""
        dob = date.today() - timedelta(days=18 * 365)

        result = check_policyholder_eligibility(dob)
        assert result is None

    def test_check_policyholder_eligibility_over_85(self):
        """Test eligibility fails for person over 85."""
        dob = date.today() - timedelta(days=86 * 365)

        result = check_policyholder_eligibility(dob)
        assert result == "Policyholder age exceeds maximum eligibility threshold for new policies."

    def test_check_policyholder_eligibility_exactly_85(self):
        """Test eligibility passes for exactly 85 years old."""
        dob = date.today() - timedelta(days=85 * 365)

        result = check_policyholder_eligibility(dob)
        assert result is None

    def test_check_policyholder_eligibility_17_years_364_days(self):
        """Test eligibility fails for person just under 18."""
        dob = date.today() - timedelta(days=18 * 365 - 1)

        result = check_policyholder_eligibility(dob)
        assert result == "Policyholder must be at least 18 years old."

    def test_check_policyholder_eligibility_85_years_1_day(self):
        """Test eligibility fails for person just over 85."""
        dob = date.today() - timedelta(days=85 * 365 + 1)

        result = check_policyholder_eligibility(dob)
        assert result == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @pytest.mark.parametrize("age", [18, 25, 50, 65, 85])
    def test_check_policyholder_eligibility_valid_ages(self, age):
        """Test eligibility for various valid ages."""
        dob = date.today() - timedelta(days=age * 365)

        result = check_policyholder_eligibility(dob)
        assert result is None

    @pytest.mark.parametrize("age", [0, 5, 10, 17])
    def test_check_policyholder_eligibility_invalid_young_ages(self, age):
        """Test eligibility fails for ages under 18."""
        dob = date.today() - timedelta(days=age * 365)

        result = check_policyholder_eligibility(dob)
        assert "18 years old" in result

    @pytest.mark.parametrize("age", [86, 90, 100])
    def test_check_policyholder_eligibility_invalid_old_ages(self, age):
        """Test eligibility fails for ages over 85."""
        dob = date.today() - timedelta(days=age * 365)

        result = check_policyholder_eligibility(dob)
        assert "exceeds maximum" in result
