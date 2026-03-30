"""Unit tests for src.services.policy_service module."""
from datetime import datetime, date, timedelta
from unittest.mock import patch

import pytest

from src.services.policy_service import (
    generate_policy_number,
    validate_coverage_dates,
    check_policyholder_eligibility,
)


class TestGeneratePolicyNumber:
    """Test policy number generation."""

    @patch("src.services.policy_service.datetime")
    @patch("src.services.policy_service.random.choices")
    def test_generate_policy_number_auto(self, mock_choices, mock_datetime):
        """Test policy number generation for AUTO policy."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 10, 0, 0)
        mock_choices.return_value = ["5", "6", "7", "8"]

        result = generate_policy_number("AUTO")

        assert result == "POL-AUTO-20260330-5678"

    @patch("src.services.policy_service.datetime")
    @patch("src.services.policy_service.random.choices")
    def test_generate_policy_number_home(self, mock_choices, mock_datetime):
        """Test policy number generation for HOME policy."""
        mock_datetime.utcnow.return_value = datetime(2026, 1, 15, 14, 30, 0)
        mock_choices.return_value = ["1", "2", "3", "4"]

        result = generate_policy_number("HOME")

        assert result == "POL-HOME-20260115-1234"

    @patch("src.services.policy_service.datetime")
    @patch("src.services.policy_service.random.choices")
    def test_generate_policy_number_life(self, mock_choices, mock_datetime):
        """Test policy number generation for LIFE policy."""
        mock_datetime.utcnow.return_value = datetime(2025, 12, 31, 23, 59, 0)
        mock_choices.return_value = ["9", "9", "9", "9"]

        result = generate_policy_number("LIFE")

        assert result == "POL-LIFE-20251231-9999"

    @patch("src.services.policy_service.datetime")
    @patch("src.services.policy_service.random.choices")
    def test_generate_policy_number_commercial(self, mock_choices, mock_datetime):
        """Test policy number generation for COMMERCIAL policy."""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 1, 0, 0, 0)
        mock_choices.return_value = ["0", "0", "0", "1"]

        result = generate_policy_number("COMMERCIAL")

        assert result == "POL-COMM-20260601-0001"

    @patch("src.services.policy_service.datetime")
    @patch("src.services.policy_service.random.choices")
    def test_generate_policy_number_truncates_long_type(self, mock_choices, mock_datetime):
        """Test policy number truncates type code to 4 characters."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        mock_choices.return_value = ["1", "1", "1", "1"]

        result = generate_policy_number("VERYLONGTYPE")

        assert result == "POL-VERY-20260330-1111"

    @patch("src.services.policy_service.datetime")
    @patch("src.services.policy_service.random.choices")
    def test_generate_policy_number_short_type(self, mock_choices, mock_datetime):
        """Test policy number handles type code shorter than 4 characters."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        mock_choices.return_value = ["2", "2", "2", "2"]

        result = generate_policy_number("AB")

        assert result == "POL-AB-20260330-2222"

    @patch("src.services.policy_service.datetime")
    @patch("src.services.policy_service.random.choices")
    def test_generate_policy_number_lowercase_type(self, mock_choices, mock_datetime):
        """Test policy number converts type to uppercase."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        mock_choices.return_value = ["3", "3", "3", "3"]

        result = generate_policy_number("auto")

        assert result == "POL-AUTO-20260330-3333"


class TestValidateCoverageDates:
    """Test coverage date validation."""

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_valid_range(self, mock_datetime):
        """Test validation passes for valid date range."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        start = date(2026, 4, 1)
        end = date(2027, 4, 1)

        result = validate_coverage_dates(start, end)

        assert result is None

    def test_validate_coverage_dates_end_before_start(self):
        """Test validation fails when end date is before start date."""
        start = date(2026, 6, 1)
        end = date(2026, 5, 1)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date must be after the start date."

    def test_validate_coverage_dates_end_equals_start(self):
        """Test validation fails when end date equals start date."""
        start = date(2026, 6, 1)
        end = date(2026, 6, 1)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date must be after the start date."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_end_in_past(self, mock_datetime):
        """Test validation fails when end date is in the past."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        start = date(2025, 1, 1)
        end = date(2025, 12, 31)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date cannot be in the past."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_end_today(self, mock_datetime):
        """Test validation fails when end date is today."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        start = date(2025, 3, 30)
        end = date(2026, 3, 30)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date cannot be in the past."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_exceeds_max_duration(self, mock_datetime):
        """Test validation fails when duration exceeds 5 years."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        start = date(2026, 4, 1)
        end = date(2031, 4, 2)  # 5 years + 1 day

        result = validate_coverage_dates(start, end)

        assert result == "Policy duration cannot exceed 5 years."

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_exactly_five_years(self, mock_datetime):
        """Test validation passes for exactly 5 years duration."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        start = date(2026, 4, 1)
        end = date(2031, 4, 1)  # Exactly 5 years

        result = validate_coverage_dates(start, end)

        assert result is None

    @patch("src.services.policy_service.datetime")
    def test_validate_coverage_dates_one_day_policy(self, mock_datetime):
        """Test validation passes for very short policy duration."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        start = date(2026, 4, 1)
        end = date(2026, 4, 2)  # 1 day

        result = validate_coverage_dates(start, end)

        assert result is None


class TestCheckPolicyholderEligibility:
    """Test policyholder age eligibility validation."""

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_valid_age_25(self, mock_datetime):
        """Test eligibility passes for 25-year-old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(2001, 3, 30)  # Exactly 25 years old

        result = check_policyholder_eligibility(dob)

        assert result is None

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_minimum_age_18(self, mock_datetime):
        """Test eligibility passes for exactly 18 years old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(2008, 3, 30)  # Exactly 18 years old

        result = check_policyholder_eligibility(dob)

        assert result is None

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_under_18(self, mock_datetime):
        """Test eligibility fails for under 18 years old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(2008, 4, 1)  # 17 years old

        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder must be at least 18 years old."

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_age_17(self, mock_datetime):
        """Test eligibility fails for 17-year-old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(2009, 3, 30)  # 17 years old

        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder must be at least 18 years old."

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_maximum_age_85(self, mock_datetime):
        """Test eligibility passes for exactly 85 years old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(1941, 3, 30)  # Exactly 85 years old

        result = check_policyholder_eligibility(dob)

        assert result is None

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_over_85(self, mock_datetime):
        """Test eligibility fails for over 85 years old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(1941, 3, 29)  # 85 years and 1 day

        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_age_86(self, mock_datetime):
        """Test eligibility fails for 86-year-old."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(1940, 3, 30)  # 86 years old

        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder age exceeds maximum eligibility threshold for new policies."

    def test_check_eligibility_none_date_of_birth(self):
        """Test eligibility passes when date of birth is None."""
        result = check_policyholder_eligibility(None)

        assert result is None

    @patch("src.services.policy_service.datetime")
    def test_check_eligibility_valid_age_50(self, mock_datetime):
        """Test eligibility passes for middle-aged policyholder."""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30)

        dob = date(1976, 3, 30)  # 50 years old

        result = check_policyholder_eligibility(dob)

        assert result is None
