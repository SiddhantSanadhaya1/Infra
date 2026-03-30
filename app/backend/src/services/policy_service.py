import random
import string
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


def generate_policy_number(policy_type: str) -> str:
    """
    Generate a unique policy number in the format POL-{TYPE}-YYYYMMDD-XXXX.
    Example: POL-AUTO-20260330-7291
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=4))
    type_code = policy_type[:4].upper()
    return f"POL-{type_code}-{date_str}-{suffix}"


def validate_coverage_dates(start_date: date, end_date: date) -> Optional[str]:
    """Return an error message if coverage dates are invalid, else None."""
    today = datetime.utcnow().date()

    if end_date <= start_date:
        return "Policy end date must be after the start date."

    if end_date < today:
        return "Policy end date cannot be in the past."

    max_duration_days = 365 * 5  # 5 years max
    if (end_date - start_date).days > max_duration_days:
        return "Policy duration cannot exceed 5 years."

    return None


def check_policyholder_eligibility(date_of_birth: Optional[date]) -> Optional[str]:
    """
    Verify the policyholder meets minimum age requirements.
    Returns an error message if ineligible, else None.
    """
    if date_of_birth is None:
        return None  # Date of birth not required for all products

    today = datetime.utcnow().date()
    age = (today - date_of_birth).days // 365

    if age < 18:
        return "Policyholder must be at least 18 years old."

    if age > 85:
        return "Policyholder age exceeds maximum eligibility threshold for new policies."

    return None
