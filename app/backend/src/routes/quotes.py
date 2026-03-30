from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class AutoQuoteRequest(BaseModel):
    driver_age: int = Field(..., ge=16, le=100)
    vehicle_year: int = Field(..., ge=1990, le=2025)
    coverage_type: Literal["LIABILITY", "COLLISION", "COMPREHENSIVE"] = "COMPREHENSIVE"
    annual_mileage: int = Field(12000, ge=1000, le=100000)


class HomeQuoteRequest(BaseModel):
    home_value: Decimal = Field(..., ge=50000, le=5000000)
    location_risk: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    home_age_years: int = Field(10, ge=0, le=150)
    coverage_type: Literal["BASIC", "STANDARD", "PREMIUM"] = "STANDARD"


class LifeQuoteRequest(BaseModel):
    age: int = Field(..., ge=18, le=80)
    health_score: int = Field(..., ge=1, le=100, description="Health score 1-100, 100 being excellent")
    coverage_amount: Decimal = Field(..., ge=50000, le=10000000)
    term_years: int = Field(20, ge=10, le=30)


class QuoteResponse(BaseModel):
    premium_monthly: Decimal
    premium_annual: Decimal
    coverage_details: dict


# ── Quote calculation logic ───────────────────────────────────────────────────

def _round_decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.post("/quotes/auto", response_model=QuoteResponse)
async def quote_auto(payload: AutoQuoteRequest):
    # Base rate per year
    base_rate = 800.0

    # Age factor: young/old drivers pay more
    if payload.driver_age < 25:
        age_factor = 1.8
    elif payload.driver_age < 30:
        age_factor = 1.3
    elif payload.driver_age < 65:
        age_factor = 1.0
    else:
        age_factor = 1.25

    # Vehicle year factor: older vehicles slightly cheaper
    current_year = 2026
    vehicle_age = current_year - payload.vehicle_year
    vehicle_factor = max(0.7, 1.0 - vehicle_age * 0.02)

    # Coverage type factor
    coverage_factors = {
        "LIABILITY": 0.6,
        "COLLISION": 1.0,
        "COMPREHENSIVE": 1.35,
    }
    coverage_factor = coverage_factors[payload.coverage_type]

    # Mileage factor
    mileage_factor = 0.8 + (payload.annual_mileage / 12000) * 0.2

    annual = base_rate * age_factor * vehicle_factor * coverage_factor * mileage_factor
    monthly = annual / 12

    return QuoteResponse(
        premium_monthly=_round_decimal(monthly),
        premium_annual=_round_decimal(annual),
        coverage_details={
            "coverage_type": payload.coverage_type,
            "driver_age": payload.driver_age,
            "vehicle_year": payload.vehicle_year,
            "annual_mileage": payload.annual_mileage,
        },
    )


@router.post("/quotes/home", response_model=QuoteResponse)
async def quote_home(payload: HomeQuoteRequest):
    # Base rate: 0.5% of home value per year
    base_rate = float(payload.home_value) * 0.005

    # Location risk factor
    location_factors = {"LOW": 0.8, "MEDIUM": 1.0, "HIGH": 1.5}
    location_factor = location_factors[payload.location_risk]

    # Home age factor: older homes are slightly more expensive
    age_factor = 1.0 + min(payload.home_age_years * 0.005, 0.25)

    # Coverage type factor
    coverage_factors = {"BASIC": 0.7, "STANDARD": 1.0, "PREMIUM": 1.4}
    coverage_factor = coverage_factors[payload.coverage_type]

    annual = base_rate * location_factor * age_factor * coverage_factor
    monthly = annual / 12

    return QuoteResponse(
        premium_monthly=_round_decimal(monthly),
        premium_annual=_round_decimal(annual),
        coverage_details={
            "home_value": str(payload.home_value),
            "location_risk": payload.location_risk,
            "home_age_years": payload.home_age_years,
            "coverage_type": payload.coverage_type,
        },
    )


@router.post("/quotes/life", response_model=QuoteResponse)
async def quote_life(payload: LifeQuoteRequest):
    # Base rate: 0.3% of coverage per year
    base_rate = float(payload.coverage_amount) * 0.003

    # Age factor: exponential increase with age
    age_factor = 1.0 + ((payload.age - 18) / 62) ** 2 * 3

    # Health score factor: better health = lower premium
    health_factor = 2.0 - (payload.health_score / 100)

    # Term factor: longer term = slightly higher rate
    term_factor = 1.0 + (payload.term_years - 10) * 0.02

    annual = base_rate * age_factor * health_factor * term_factor
    monthly = annual / 12

    return QuoteResponse(
        premium_monthly=_round_decimal(monthly),
        premium_annual=_round_decimal(annual),
        coverage_details={
            "coverage_amount": str(payload.coverage_amount),
            "age": payload.age,
            "health_score": payload.health_score,
            "term_years": payload.term_years,
        },
    )
