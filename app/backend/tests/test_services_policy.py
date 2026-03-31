"""Tests for src/services/policy_service.py"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from src.services.policy_service import (
    generate_policy_number,
    validate_coverage_dates,
    check_policyholder_eligibility,
)


class TestGeneratePolicyNumber:
    """Test generate_policy_number function."""

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_format(self, mock_datetime):
        """Test that policy number has correct format."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15, 10, 30, 0)

        policy_number = generate_policy_number("AUTO")

        assert policy_number.startswith("POL-AUTO-20260315-")
        assert len(policy_number.split("-")[-1]) == 4
        assert policy_number.split("-")[-1].isdigit()

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_with_long_type(self, mock_datetime):
        """Test policy number generation with long policy type."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15, 10, 30, 0)

        policy_number = generate_policy_number("COMMERCIAL")

        # Should truncate to 4 characters
        assert "COMM" in policy_number
        assert len(policy_number.split("-")[1]) == 4

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_with_short_type(self, mock_datetime):
        """Test policy number generation with short policy type."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15, 10, 30, 0)

        policy_number = generate_policy_number("CAR")

        assert "CAR" in policy_number

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_with_lowercase(self, mock_datetime):
        """Test that policy type is converted to uppercase."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15, 10, 30, 0)

        policy_number = generate_policy_number("home")

        assert "HOME" in policy_number

    def test_generate_policy_number_uniqueness(self):
        """Test that multiple calls generate different numbers."""
        numbers = [generate_policy_number("AUTO") for _ in range(5)]

        # All numbers should be unique (very high probability due to random suffix)
        assert len(set(numbers)) == 5

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_with_empty_string(self, mock_datetime):
        """Test policy number generation with empty type."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15, 10, 30, 0)

        policy_number = generate_policy_number("")

        assert policy_number.startswith("POL--20260315-")


class TestValidateCoverageDates:
    """Test validate_coverage_dates function with boundary values."""

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_valid_range(self, mock_datetime):
        """Test validation with valid date range."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2026, 4, 1)
        end_date = date(2027, 4, 1)

        error = validate_coverage_dates(start_date, end_date)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_before_start(self, mock_datetime):
        """Test that end date before start date returns error."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2026, 4, 1)
        end_date = date(2026, 3, 1)

        error = validate_coverage_dates(start_date, end_date)

        assert error is not None
        assert "end date must be after the start date" in error

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_equals_start(self, mock_datetime):
        """Test that end date equal to start date returns error."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        same_date = date(2026, 4, 1)

        error = validate_coverage_dates(same_date, same_date)

        assert error is not None
        assert "end date must be after the start date" in error

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_in_past(self, mock_datetime):
        """Test that past end date returns error."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2025, 1, 1)
        end_date = date(2026, 1, 1)

        error = validate_coverage_dates(start_date, end_date)

        assert error is not None
        assert "end date cannot be in the past" in error

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_exactly_today(self, mock_datetime):
        """Test boundary: end date is today."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15, 23, 59, 59)
        start_date = date(2026, 1, 1)
        end_date = date(2026, 3, 15)

        error = validate_coverage_dates(start_date, end_date)

        # Same day should be considered past
        assert error is not None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_one_day_future(self, mock_datetime):
        """Test boundary: end date is tomorrow."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2026, 3, 1)
        end_date = date(2026, 3, 16)

        error = validate_coverage_dates(start_date, end_date)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_exceeds_max_duration(self, mock_datetime):
        """Test that duration over 5 years returns error."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2026, 4, 1)
        end_date = date(2031, 4, 2)  # 5 years + 1 day

        error = validate_coverage_dates(start_date, end_date)

        assert error is not None
        assert "cannot exceed 5 years" in error

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_exactly_max_duration(self, mock_datetime):
        """Test boundary: exactly 5 years duration."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2026, 4, 1)
        end_date = date(2031, 4, 1)  # Exactly 5 years

        error = validate_coverage_dates(start_date, end_date)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_one_day_over_max(self, mock_datetime):
        """Test boundary: 5 years + 1 day."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2026, 4, 1)
        end_date = start_date + timedelta(days=365 * 5 + 1)

        error = validate_coverage_dates(start_date, end_date)

        assert error is not None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_one_year(self, mock_datetime):
        """Test valid one-year policy."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        start_date = date(2026, 4, 1)
        end_date = date(2027, 4, 1)

        error = validate_coverage_dates(start_date, end_date)

        assert error is None


class TestCheckPolicyholderEligibility:
    """Test check_policyholder_eligibility function with boundary values."""

    @patch('src.services.policy_service.datetime')
    def test_eligibility_with_none_date_of_birth(self, mock_datetime):
        """Test that None date of birth is acceptable."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)

        error = check_policyholder_eligibility(None)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_eligibility_age_exactly_18(self, mock_datetime):
        """Test boundary: exactly 18 years old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        # Born exactly 18 years ago
        dob = date(2008, 3, 15)

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_eligibility_age_17_years_364_days(self, mock_datetime):
        """Test boundary: one day under 18."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        # Born 17 years and 364 days ago
        dob = date(2008, 3, 16)

        error = check_policyholder_eligibility(dob)

        assert error is not None
        assert "at least 18 years old" in error

    @patch('src.services.policy_service.datetime')
    def test_eligibility_age_under_18(self, mock_datetime):
        """Test age under 18 returns error."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        dob = date(2010, 1, 1)  # 16 years old

        error = check_policyholder_eligibility(dob)

        assert error is not None
        assert "at least 18 years old" in error

    @patch('src.services.policy_service.datetime')
    def test_eligibility_age_exactly_85(self, mock_datetime):
        """Test boundary: exactly 85 years old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        dob = date(1941, 3, 15)

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_eligibility_age_over_85(self, mock_datetime):
        """Test age over 85 returns error."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        dob = date(1940, 1, 1)  # 86 years old

        error = check_policyholder_eligibility(dob)

        assert error is not None
        assert "exceeds maximum eligibility threshold" in error

    @patch('src.services.policy_service.datetime')
    def test_eligibility_age_86_years(self, mock_datetime):
        """Test boundary: 86 years old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        dob = date(1940, 3, 14)

        error = check_policyholder_eligibility(dob)

        assert error is not None

    @patch('src.services.policy_service.datetime')
    def test_eligibility_age_middle_range(self, mock_datetime):
        """Test valid age in middle of acceptable range."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        dob = date(1980, 5, 20)  # 45-46 years old

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_eligibility_future_date_of_birth(self, mock_datetime):
        """Test with future date of birth (edge case)."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 15)
        dob = date(2027, 1, 1)  # Future date

        error = check_policyholder_eligibility(dob)

        # Negative age, should fail under 18 check
        assert error is not None
        assert "at least 18 years old" in error
