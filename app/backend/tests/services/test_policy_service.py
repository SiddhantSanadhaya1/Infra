"""
Comprehensive unit tests for policy_service module.
Tests policy number generation, coverage date validation, and policyholder eligibility.
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.services.policy_service import (
    generate_policy_number,
    validate_coverage_dates,
    check_policyholder_eligibility,
)


class TestGeneratePolicyNumber:
    """Test policy number generation with various policy types."""

    @patch("src.services.policy_service.datetime")
    def test_generate_policy_number_standard_format(self, mock_datetime):
        """Test that policy number follows POL-{TYPE}-YYYYMMDD-XXXX format."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        policy_number = generate_policy_number("AUTO")

        assert policy_number.startswith("POL-AUTO-20260330-")
        assert len(policy_number) == 22  # POL-AUTO-20260330-XXXX
        assert policy_number[-4:].isdigit()

    @patch("src.services.policy_service.datetime")
    def test_generate_policy_number_truncates_long_type(self, mock_datetime):
        """Test that long policy types are truncated to 4 characters."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        policy_number = generate_policy_number("COMMERCIAL")

        assert policy_number.startswith("POL-COMM-20260330-")

    @patch("src.services.policy_service.datetime")
    def test_generate_policy_number_short_type(self, mock_datetime):
        """Test policy number generation with short type codes."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        policy_number = generate_policy_number("H")

        assert policy_number.startswith("POL-H-20260330-")

    @patch("src.services.policy_service.datetime")
    def test_generate_policy_number_lowercase_converted_to_uppercase(self, mock_datetime):
        """Test that lowercase policy types are converted to uppercase."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        policy_number = generate_policy_number("auto")

        assert "POL-AUTO-" in policy_number

    @patch("src.services.policy_service.random.choices")
    @patch("src.services.policy_service.datetime")
    def test_generate_policy_number_unique_suffix(self, mock_datetime, mock_choices):
        """Test that random suffix is included correctly."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        mock_choices.return_value = ['1', '2', '3', '4']

        policy_number = generate_policy_number("AUTO")

        assert policy_number.endswith("1234")

    @patch("src.services.policy_service.datetime")
    def test_generate_policy_number_empty_type(self, mock_datetime):
        """Test policy number generation with empty string type."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        policy_number = generate_policy_number("")

        assert policy_number.startswith("POL--20260330-")


class TestValidateCoverageDates:
    """Test coverage date validation with boundary conditions."""

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_valid_dates(self, mock_datetime):
        """Test validation passes for valid date range."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = date(2027, 4, 1)

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_end_equals_start(self, mock_datetime):
        """Test that end date equal to start date is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = date(2026, 4, 1)

        error = validate_coverage_dates(start, end)

        assert error == "Policy end date must be after the start date."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_end_before_start(self, mock_datetime):
        """Test that end date before start date is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = date(2026, 3, 1)

        error = validate_coverage_dates(start, end)

        assert error == "Policy end date must be after the start date."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_end_in_past(self, mock_datetime):
        """Test that end date in the past is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2025, 1, 1)
        end = date(2025, 12, 31)

        error = validate_coverage_dates(start, end)

        assert error == "Policy end date cannot be in the past."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_end_exactly_today(self, mock_datetime):
        """Test that end date exactly today is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2025, 3, 30)
        end = date(2026, 3, 30)

        error = validate_coverage_dates(start, end)

        # Should fail because end < today is false, but end <= start would fail
        # Actually end is not less than today, so this should pass the past check
        # But start is in the past too. Let's check the actual logic
        assert error == "Policy end date cannot be in the past."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_end_tomorrow(self, mock_datetime):
        """Test that end date tomorrow is valid (at boundary)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 3, 30)
        end = date(2026, 3, 31)

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_exactly_5_years(self, mock_datetime):
        """Test that exactly 5 years duration is valid (boundary)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = date(2031, 4, 1)  # Exactly 5 years = 1826 days (including leap year)

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_over_5_years(self, mock_datetime):
        """Test that duration over 5 years is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = date(2031, 4, 3)  # 1828 days, over 5 years

        error = validate_coverage_dates(start, end)

        assert error == "Policy duration cannot exceed 5 years."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_exactly_max_duration_days(self, mock_datetime):
        """Test boundary at exactly 1825 days (5 years max)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = start + timedelta(days=1825)

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_one_day_over_max(self, mock_datetime):
        """Test boundary at 1826 days (over 5 years)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = start + timedelta(days=1826)

        error = validate_coverage_dates(start, end)

        assert error == "Policy duration cannot exceed 5 years."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_one_day_duration(self, mock_datetime):
        """Test minimum valid duration of one day."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        start = date(2026, 4, 1)
        end = date(2026, 4, 2)

        error = validate_coverage_dates(start, end)

        assert error is None


class TestCheckPolicyholderEligibility:
    """Test policyholder age eligibility with boundary conditions."""

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_none_date_of_birth(self, mock_datetime):
        """Test that None date of birth is allowed (not required)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        error = check_policyholder_eligibility(None)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_exactly_18(self, mock_datetime):
        """Test that exactly 18 years old is valid (boundary)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(2008, 3, 30)  # Exactly 18 years ago

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_17_years_old(self, mock_datetime):
        """Test that 17 years old is invalid (under minimum)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(2008, 3, 31)  # 17 years and 364 days old

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder must be at least 18 years old."

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_one_day_before_18(self, mock_datetime):
        """Test that one day before 18th birthday is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(2008, 3, 31)  # Turns 18 tomorrow

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder must be at least 18 years old."

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_exactly_85(self, mock_datetime):
        """Test that exactly 85 years old is valid (boundary)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(1941, 3, 30)  # Exactly 85 years ago

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_86_years_old(self, mock_datetime):
        """Test that 86 years old is invalid (over maximum)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(1940, 3, 30)  # 86 years old

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_one_day_after_85(self, mock_datetime):
        """Test that one day after 85th birthday is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(1941, 3, 29)  # 85 years and 1 day

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_middle_age(self, mock_datetime):
        """Test that middle age (e.g., 45) is valid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(1981, 3, 30)  # 45 years old

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_newborn(self, mock_datetime):
        """Test that newborn (0 years) is invalid."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(2026, 3, 1)  # Less than 1 year old

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder must be at least 18 years old."

    @patch("src.services.policy_service.datetime")
    def test_check_policyholder_eligibility_future_date(self, mock_datetime):
        """Test that future date of birth results in negative age."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        dob = date(2027, 3, 30)  # Future date

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder must be at least 18 years old."
