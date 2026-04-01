"""Unit tests for policy service module"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch


class TestGeneratePolicyNumber:
    """Test policy number generation"""

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_format(self, mock_datetime):
        """Test policy number has correct format"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1, 12, 0, 0)

        policy_number = generate_policy_number("AUTO")

        # Format: POL-{TYPE}-YYYYMMDD-XXXX
        assert policy_number.startswith("POL-AUTO-20260401-")
        assert len(policy_number) == 23  # POL-AUTO-20260401-1234
        assert policy_number.split("-")[-1].isdigit()
        assert len(policy_number.split("-")[-1]) == 4

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_auto_type(self, mock_datetime):
        """Test policy number for AUTO type"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)

        policy_number = generate_policy_number("AUTO")

        assert "POL-AUTO-" in policy_number

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_home_type(self, mock_datetime):
        """Test policy number for HOME type"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)

        policy_number = generate_policy_number("HOME")

        assert "POL-HOME-" in policy_number

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_life_type(self, mock_datetime):
        """Test policy number for LIFE type"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)

        policy_number = generate_policy_number("LIFE")

        assert "POL-LIFE-" in policy_number

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_commercial_type(self, mock_datetime):
        """Test policy number for COMMERCIAL type"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)

        policy_number = generate_policy_number("COMMERCIAL")

        assert "POL-COMM-" in policy_number  # Truncated to 4 chars

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_truncates_long_type(self, mock_datetime):
        """Test policy number truncates type code to 4 characters"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)

        policy_number = generate_policy_number("VERYLONGTYPE")

        assert "POL-VERY-" in policy_number

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_uppercase_conversion(self, mock_datetime):
        """Test policy number converts type to uppercase"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)

        policy_number = generate_policy_number("auto")

        assert "POL-AUTO-" in policy_number

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_different_dates(self, mock_datetime):
        """Test policy numbers reflect different dates"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 12, 31, 23, 59, 59)

        policy_number = generate_policy_number("AUTO")

        assert "POL-AUTO-20261231-" in policy_number

    @patch('src.services.policy_service.random.choices')
    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_random_suffix(self, mock_datetime, mock_choices):
        """Test policy number generates 4-digit random suffix"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)
        mock_choices.return_value = ['7', '2', '9', '1']

        policy_number = generate_policy_number("AUTO")

        assert policy_number.endswith("7291")

    @patch('src.services.policy_service.datetime')
    def test_generate_policy_number_empty_type(self, mock_datetime):
        """Test policy number with empty type string"""
        from src.services.policy_service import generate_policy_number

        mock_datetime.utcnow.return_value = datetime(2026, 4, 1)

        policy_number = generate_policy_number("")

        assert policy_number.startswith("POL--20260401-")


class TestValidateCoverageDates:
    """Test coverage date validation"""

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_valid_future_dates(self, mock_datetime):
        """Test validation passes for valid future dates"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 5, 1)
        end = date(2027, 5, 1)

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_equals_start(self, mock_datetime):
        """Test validation fails when end date equals start date"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 5, 1)
        end = date(2026, 5, 1)

        error = validate_coverage_dates(start, end)

        assert error == "Policy end date must be after the start date."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_before_start(self, mock_datetime):
        """Test validation fails when end date is before start date"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2027, 5, 1)
        end = date(2026, 5, 1)

        error = validate_coverage_dates(start, end)

        assert error == "Policy end date must be after the start date."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_in_past(self, mock_datetime):
        """Test validation fails when end date is in the past"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 1, 1)
        end = date(2026, 3, 31)  # Yesterday

        error = validate_coverage_dates(start, end)

        assert error == "Policy end date cannot be in the past."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_end_is_today(self, mock_datetime):
        """Test validation fails when end date is today"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 1, 1)
        end = date(2026, 4, 1)  # Today

        error = validate_coverage_dates(start, end)

        assert error == "Policy end date cannot be in the past."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_duration_exactly_5_years(self, mock_datetime):
        """Test validation passes for exactly 5 year duration"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 5, 1)
        end = date(2031, 5, 1)  # Exactly 5 years = 1826 days

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_duration_over_5_years(self, mock_datetime):
        """Test validation fails for duration over 5 years"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 5, 1)
        end = date(2031, 5, 2)  # 5 years + 1 day

        error = validate_coverage_dates(start, end)

        assert error == "Policy duration cannot exceed 5 years."

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_duration_just_under_5_years(self, mock_datetime):
        """Test validation passes for duration just under 5 years"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 5, 1)
        end = date(2031, 4, 30)  # Just under 5 years

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_one_day_duration(self, mock_datetime):
        """Test validation passes for minimum valid duration (1 day)"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 5, 1)
        end = date(2026, 5, 2)

        error = validate_coverage_dates(start, end)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_validate_coverage_dates_start_in_past_end_in_future(self, mock_datetime):
        """Test validation allows start date in past if end date is future"""
        from src.services.policy_service import validate_coverage_dates

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        start = date(2026, 1, 1)  # Past
        end = date(2027, 1, 1)    # Future

        error = validate_coverage_dates(start, end)

        # Should pass - only end date must be in future
        assert error is None


class TestCheckPolicyholderEligibility:
    """Test policyholder eligibility check"""

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_none_date_of_birth(self, mock_datetime):
        """Test eligibility returns None when date of birth is None"""
        from src.services.policy_service import check_policyholder_eligibility

        error = check_policyholder_eligibility(None)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_exactly_18_years_old(self, mock_datetime):
        """Test eligibility passes for exactly 18 years old"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(2008, 4, 1)  # Exactly 18 years ago

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_under_18(self, mock_datetime):
        """Test eligibility fails for under 18 years old"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(2008, 4, 2)  # 17 years and 364 days

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder must be at least 18 years old."

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_17_years_old(self, mock_datetime):
        """Test eligibility fails for 17 years old"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(2009, 4, 1)  # 17 years ago

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder must be at least 18 years old."

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_19_years_old(self, mock_datetime):
        """Test eligibility passes for 19 years old"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(2007, 3, 1)  # 19 years ago

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_exactly_85_years_old(self, mock_datetime):
        """Test eligibility passes for exactly 85 years old"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(1941, 4, 1)  # Exactly 85 years ago

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_over_85(self, mock_datetime):
        """Test eligibility fails for over 85 years old"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(1940, 12, 31)  # 85 years and 1 day

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_86_years_old(self, mock_datetime):
        """Test eligibility fails for 86 years old"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(1940, 4, 1)  # 86 years ago

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder age exceeds maximum eligibility threshold for new policies."

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_middle_age(self, mock_datetime):
        """Test eligibility passes for middle-aged person (40 years)"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(1986, 4, 1)  # 40 years ago

        error = check_policyholder_eligibility(dob)

        assert error is None

    @patch('src.services.policy_service.datetime')
    def test_check_policyholder_eligibility_very_old(self, mock_datetime):
        """Test eligibility fails for very old age (100 years)"""
        from src.services.policy_service import check_policyholder_eligibility

        mock_datetime.utcnow.return_value.date.return_value = date(2026, 4, 1)

        dob = date(1926, 4, 1)  # 100 years ago

        error = check_policyholder_eligibility(dob)

        assert error == "Policyholder age exceeds maximum eligibility threshold for new policies."
