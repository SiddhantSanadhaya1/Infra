import random
import string
from datetime import datetime
from decimal import Decimal
from typing import Optional


def generate_claim_number() -> str:
    """Generate a unique claim number in the format CLM-YYYYMMDD-XXXX."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"CLM-{date_str}-{suffix}"


def validate_claim_against_policy(policy, amount_requested: Decimal) -> Optional[str]:
    """
    Validate that a claim can be filed against the given policy.
    Returns an error message string if invalid, or None if valid.
    """
    from src.config.database import PolicyStatus

    if policy.status != PolicyStatus.ACTIVE:
        return f"Cannot file a claim against a policy with status '{policy.status.value}'. Policy must be ACTIVE."

    today = datetime.utcnow().date()
    if today < policy.start_date:
        return "Cannot file a claim before the policy start date."

    if today > policy.end_date:
        return "Cannot file a claim against an expired policy."

    if amount_requested <= Decimal("0"):
        return "Claim amount must be greater than zero."

    if amount_requested > policy.coverage_amount:
        return (
            f"Requested amount ${amount_requested} exceeds the policy coverage amount "
            f"${policy.coverage_amount}."
        )

    return None


def calculate_fraud_score(claim_amount: Decimal, coverage_amount: Decimal) -> int:
    """
    Calculate a fraud risk score (0-100) for a claim.
    For demo purposes this uses a simple heuristic + randomness.
    """
    base_score = random.randint(5, 40)

    # Claims that are close to or exceed coverage are higher risk
    if coverage_amount > 0:
        ratio = float(claim_amount) / float(coverage_amount)
        if ratio > 0.9:
            base_score += 30
        elif ratio > 0.7:
            base_score += 15
        elif ratio > 0.5:
            base_score += 5

    return min(100, base_score)
