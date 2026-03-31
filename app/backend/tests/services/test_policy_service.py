"""
Unit tests for src.services.policy_service
Tests policy number generation, coverage date validation, and policyholder eligibility checks.
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
    """Test policy number generation"""

    @patch('src.services.policy_service.datetime')
    @patch('src.services.policy_service.random.choices')
    def test_generate_policy_number_auto(self, mock_choices, mock_datetime):
        """Test policy number generation for AUTO type"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        mock_choices.return_value = ['1', '2', '3', '4']

        result = generate_policy_number("AUTO")

        assert result == "POL-AUTO-20260330-1234"
        mock_choices.assert_called_once()

    @patch('src.services.policy_service.datetime')
    @patch('src.services.policy_service.random.choices')
    def test_generate_policy_number_home(self, mock_choices, mock_datetime):
        """Test policy number generation for HOME type"""
        mock_datetime.utcnow.return_value = datetime(2026, 1, 15, 8, 30, 0)
        mock_choices.return_value = ['9', '8', '7', '6']

        result = generate_policy_number("HOME")

        assert result == "POL-HOME-20260115-9876"

    @patch('src.services.policy_service.datetime')
    @patch('src.services.policy_service.random.choices')
    def test_generate_policy_number_long_type(self, mock_choices, mock_datetime):
        """Test policy number generation truncates type to 4 chars"""
        mock_datetime.utcnow.return_value = datetime(2026, 12, 31, 23, 59, 59)
        mock_choices.return_value = ['0', '0', '0', '1']

        result = generate_policy_number("COMMERCIAL")

        assert result == "POL-COMM-20261231-0001"

    @patch('src.services.policy_service.datetime')
    @patch('src.services.policy_service.random.choices')
    def test_generate_policy_number_short_type(self, mock_choices, mock_datetime):
        """Test policy number generation with type shorter than 4 chars"""
        mock_datetime.utcnow.return_value = datetime(2026, 6, 15, 10, 0, 0)
        mock_choices.return_value = ['5', '5', '5', '5']

        result = generate_policy_number("CAR")

        assert result == "POL-CAR-20260615-5555"

    @patch('src.services.policy_service.datetime')
    @patch('src.services.policy_service.random.choices')
    def test_generate_policy_number_lowercase_type(self, mock_choices, mock_datetime):
        """Test policy number generation converts type to uppercase"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)
        mock_choices.return_value = ['1', '2', '3', '4']

        result = generate_policy_number("life")

        assert result == "POL-LIFE-20260330-1234"


class TestValidateCoverageDates:
    """Test coverage date validation"""

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_valid(self, mock_datetime):
        """Test validation passes for valid dates"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2026, 4, 1)
        end = date(2027, 4, 1)

        result = validate_coverage_dates(start, end)

        assert result is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_before_start(self, mock_datetime):
        """Test validation fails when end date is before start date"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2027, 4, 1)
        end = date(2026, 4, 1)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date must be after the start date."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_equals_start(self, mock_datetime):
        """Test validation fails when end date equals start date"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2026, 4, 1)
        end = date(2026, 4, 1)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date must be after the start date."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_in_past(self, mock_datetime):
        """Test validation fails when end date is in the past"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2025, 1, 1)
        end = date(2025, 12, 31)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date cannot be in the past."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_today(self, mock_datetime):
        """Test validation fails when end date is today"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2026, 1, 1)
        end = date(2026, 3, 30)

        result = validate_coverage_dates(start, end)

        assert result == "Policy end date cannot be in the past."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_exceeds_max_duration(self, mock_datetime):
        """Test validation fails when duration exceeds 5 years"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2026, 4, 1)
        end = date(2031, 4, 2)  # 5 years + 1 day

        result = validate_coverage_dates(start, end)

        assert result == "Policy duration cannot exceed 5 years."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_exactly_5_years(self, mock_datetime):
        """Test validation passes for exactly 5 years duration"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2026, 4, 1)
        end = date(2031, 4, 1)  # Exactly 5 years (365 * 5 days)

        result = validate_coverage_dates(start, end)

        assert result is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_one_day_policy(self, mock_datetime):
        """Test validation passes for very short policy duration"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        start = date(2026, 4, 1)
        end = date(2026, 4, 2)  # 1 day policy

        result = validate_coverage_dates(start, end)

        assert result is None


class TestCheckPolicyholderEligibility:
    """Test policyholder eligibility checks"""

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_none_dob(self, mock_datetime):
        """Test eligibility check passes when DOB is None"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        result = check_policyholder_eligibility(None)

        assert result is None

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_valid_age(self, mock_datetime):
        """Test eligibility check passes for valid age (25 years old)"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(2001, 3, 30)  # 25 years old
        result = check_policyholder_eligibility(dob)

        assert result is None

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_exactly_18(self, mock_datetime):
        """Test eligibility check passes for exactly 18 years old"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(2008, 3, 30)  # Exactly 18 years old
        result = check_policyholder_eligibility(dob)

        assert result is None

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_under_18(self, mock_datetime):
        """Test eligibility check fails for under 18"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(2008, 4, 1)  # 17 years, 364 days old
        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder must be at least 18 years old."

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_child(self, mock_datetime):
        """Test eligibility check fails for child (10 years old)"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(2016, 1, 1)  # 10 years old
        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder must be at least 18 years old."

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_exactly_85(self, mock_datetime):
        """Test eligibility check passes for exactly 85 years old"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(1941, 3, 30)  # Exactly 85 years old
        result = check_policyholder_eligibility(dob)

        assert result is None

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_over_85(self, mock_datetime):
        """Test eligibility check fails for over 85"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(1941, 3, 29)  # 85 years and 1 day old
        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_very_old(self, mock_datetime):
        """Test eligibility check fails for very old age (100 years)"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(1926, 1, 1)  # 100 years old
        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_boundary_18_minus_one_day(self, mock_datetime):
        """Test eligibility at 18 year boundary minus one day"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(2008, 3, 31)  # 17 years, 364 days
        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder must be at least 18 years old."

    @patch('src.services.policy_service.datetime')
    def test_check_eligibility_boundary_85_plus_one_day(self, mock_datetime):
        """Test eligibility at 85 year boundary plus one day"""
        mock_datetime.utcnow.return_value = datetime(2026, 3, 30, 12, 0, 0)

        dob = date(1941, 3, 29)  # 85 years and 1 day
        result = check_policyholder_eligibility(dob)

        assert result == "Policyholder age exceeds maximum eligibility threshold for new policies."
