"""
Comprehensive unit tests for quotes routes.
Tests quote calculation logic for auto, home, and life insurance.
"""
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from src.main import app
from src.routes.quotes import _round_decimal

client = TestClient(app)


class TestRoundDecimal:
    """Test decimal rounding utility function."""

    def test_round_decimal_two_places(self):
        """Test rounding to two decimal places."""
        result = _round_decimal(123.456)

        assert result == Decimal("123.46")

    def test_round_decimal_half_up(self):
        """Test rounding uses ROUND_HALF_UP (rounds 0.5 up)."""
        result = _round_decimal(10.555)

        assert result == Decimal("10.56")

    def test_round_decimal_whole_number(self):
        """Test rounding whole number."""
        result = _round_decimal(100.0)

        assert result == Decimal("100.00")

    def test_round_decimal_zero(self):
        """Test rounding zero."""
        result = _round_decimal(0.0)

        assert result == Decimal("0.00")

    def test_round_decimal_very_small(self):
        """Test rounding very small number."""
        result = _round_decimal(0.001)

        assert result == Decimal("0.00")

    def test_round_decimal_negative(self):
        """Test rounding negative number."""
        result = _round_decimal(-123.456)

        assert result == Decimal("-123.46")


class TestQuoteAuto:
    """Test auto insurance quote calculation."""

    def test_quote_auto_minimum_age_16(self):
        """Test auto quote with minimum age 16."""
        response = client.post("/api/quotes/auto", json={
            "driver_age": 16,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        })

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert float(data["premium_annual"]) > 0

    def test_quote_auto_young_driver_high_premium(self):
        """Test that young drivers (under 25) have higher premiums."""
        response_young = client.post("/api/quotes/auto", json={
            "driver_age": 20,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        response_mature = client.post("/api/quotes/auto", json={
            "driver_age": 40,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        assert response_young.status_code == 200
        assert response_mature.status_code == 200

        premium_young = float(response_young.json()["premium_annual"])
        premium_mature = float(response_mature.json()["premium_annual"])

        assert premium_young > premium_mature

    def test_quote_auto_age_25_boundary(self):
        """Test premium at age 25 boundary."""
        response_24 = client.post("/api/quotes/auto", json={
            "driver_age": 24,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        response_25 = client.post("/api/quotes/auto", json={
            "driver_age": 25,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        premium_24 = float(response_24.json()["premium_annual"])
        premium_25 = float(response_25.json()["premium_annual"])

        # 24 should have age_factor 1.8, 25 should have 1.3
        assert premium_24 > premium_25

    def test_quote_auto_senior_driver(self):
        """Test auto quote for senior driver (over 65)."""
        response = client.post("/api/quotes/auto", json={
            "driver_age": 70,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        assert response.status_code == 200
        # Seniors have age_factor 1.25

    def test_quote_auto_liability_cheapest(self):
        """Test that LIABILITY is cheapest coverage type."""
        ages = [30]
        coverage_types = ["LIABILITY", "COLLISION", "COMPREHENSIVE"]
        premiums = {}

        for cov_type in coverage_types:
            response = client.post("/api/quotes/auto", json={
                "driver_age": 30,
                "vehicle_year": 2020,
                "coverage_type": cov_type,
                "annual_mileage": 12000
            })
            premiums[cov_type] = float(response.json()["premium_annual"])

        assert premiums["LIABILITY"] < premiums["COLLISION"]
        assert premiums["LIABILITY"] < premiums["COMPREHENSIVE"]
        assert premiums["COMPREHENSIVE"] > premiums["COLLISION"]

    def test_quote_auto_old_vehicle_cheaper(self):
        """Test that older vehicles have lower premiums."""
        response_new = client.post("/api/quotes/auto", json={
            "driver_age": 30,
            "vehicle_year": 2025,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        response_old = client.post("/api/quotes/auto", json={
            "driver_age": 30,
            "vehicle_year": 2000,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        premium_new = float(response_new.json()["premium_annual"])
        premium_old = float(response_old.json()["premium_annual"])

        assert premium_new > premium_old

    def test_quote_auto_high_mileage_higher_premium(self):
        """Test that higher mileage results in higher premium."""
        response_low = client.post("/api/quotes/auto", json={
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 5000
        })

        response_high = client.post("/api/quotes/auto", json={
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 50000
        })

        premium_low = float(response_low.json()["premium_annual"])
        premium_high = float(response_high.json()["premium_annual"])

        assert premium_high > premium_low

    def test_quote_auto_monthly_is_annual_divided_by_12(self):
        """Test that monthly premium is annual divided by 12."""
        response = client.post("/api/quotes/auto", json={
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        })

        data = response.json()
        monthly = Decimal(data["premium_monthly"])
        annual = Decimal(data["premium_annual"])

        # Check that monthly * 12 is close to annual (within rounding)
        assert abs(monthly * 12 - annual) < Decimal("0.12")

    def test_quote_auto_coverage_details_included(self):
        """Test that coverage details are returned."""
        response = client.post("/api/quotes/auto", json={
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 15000
        })

        data = response.json()
        assert "coverage_details" in data
        assert data["coverage_details"]["driver_age"] == 30
        assert data["coverage_details"]["vehicle_year"] == 2020
        assert data["coverage_details"]["coverage_type"] == "COMPREHENSIVE"
        assert data["coverage_details"]["annual_mileage"] == 15000

    def test_quote_auto_invalid_age_below_16(self):
        """Test validation error for age below 16."""
        response = client.post("/api/quotes/auto", json={
            "driver_age": 15,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        })

        assert response.status_code == 422

    def test_quote_auto_invalid_age_above_100(self):
        """Test validation error for age above 100."""
        response = client.post("/api/quotes/auto", json={
            "driver_age": 101,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        })

        assert response.status_code == 422


class TestQuoteHome:
    """Test home insurance quote calculation."""

    def test_quote_home_basic_request(self):
        """Test basic home insurance quote."""
        response = client.post("/api/quotes/home", json={
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        })

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert float(data["premium_annual"]) > 0

    def test_quote_home_high_value_higher_premium(self):
        """Test that higher home value results in higher premium."""
        response_low = client.post("/api/quotes/home", json={
            "home_value": 100000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        })

        response_high = client.post("/api/quotes/home", json={
            "home_value": 500000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        })

        premium_low = float(response_low.json()["premium_annual"])
        premium_high = float(response_high.json()["premium_annual"])

        assert premium_high > premium_low

    def test_quote_home_high_risk_location_higher_premium(self):
        """Test that high-risk location has higher premium."""
        response_low = client.post("/api/quotes/home", json={
            "home_value": 200000,
            "location_risk": "LOW",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        })

        response_high = client.post("/api/quotes/home", json={
            "home_value": 200000,
            "location_risk": "HIGH",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        })

        premium_low = float(response_low.json()["premium_annual"])
        premium_high = float(response_high.json()["premium_annual"])

        assert premium_high > premium_low

    def test_quote_home_older_home_higher_premium(self):
        """Test that older homes have higher premiums."""
        response_new = client.post("/api/quotes/home", json={
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 5,
            "coverage_type": "STANDARD"
        })

        response_old = client.post("/api/quotes/home", json={
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 50,
            "coverage_type": "STANDARD"
        })

        premium_new = float(response_new.json()["premium_annual"])
        premium_old = float(response_old.json()["premium_annual"])

        assert premium_old > premium_new

    def test_quote_home_premium_coverage_most_expensive(self):
        """Test that PREMIUM coverage is most expensive."""
        coverage_types = ["BASIC", "STANDARD", "PREMIUM"]
        premiums = {}

        for cov_type in coverage_types:
            response = client.post("/api/quotes/home", json={
                "home_value": 200000,
                "location_risk": "MEDIUM",
                "home_age_years": 10,
                "coverage_type": cov_type
            })
            premiums[cov_type] = float(response.json()["premium_annual"])

        assert premiums["BASIC"] < premiums["STANDARD"]
        assert premiums["STANDARD"] < premiums["PREMIUM"]

    def test_quote_home_minimum_value(self):
        """Test home quote with minimum home value."""
        response = client.post("/api/quotes/home", json={
            "home_value": 50000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "BASIC"
        })

        assert response.status_code == 200

    def test_quote_home_maximum_value(self):
        """Test home quote with maximum home value."""
        response = client.post("/api/quotes/home", json={
            "home_value": 5000000,
            "location_risk": "LOW",
            "home_age_years": 1,
            "coverage_type": "PREMIUM"
        })

        assert response.status_code == 200

    def test_quote_home_invalid_value_too_low(self):
        """Test validation error for home value below minimum."""
        response = client.post("/api/quotes/home", json={
            "home_value": 49999,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        })

        assert response.status_code == 422


class TestQuoteLife:
    """Test life insurance quote calculation."""

    def test_quote_life_basic_request(self):
        """Test basic life insurance quote."""
        response = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        })

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert float(data["premium_annual"]) > 0

    def test_quote_life_older_age_higher_premium(self):
        """Test that older age results in higher premium."""
        response_young = client.post("/api/quotes/life", json={
            "age": 25,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        })

        response_old = client.post("/api/quotes/life", json={
            "age": 65,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        })

        premium_young = float(response_young.json()["premium_annual"])
        premium_old = float(response_old.json()["premium_annual"])

        assert premium_old > premium_young

    def test_quote_life_lower_health_score_higher_premium(self):
        """Test that lower health score results in higher premium."""
        response_healthy = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 95,
            "coverage_amount": 500000,
            "term_years": 20
        })

        response_unhealthy = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 50,
            "coverage_amount": 500000,
            "term_years": 20
        })

        premium_healthy = float(response_healthy.json()["premium_annual"])
        premium_unhealthy = float(response_unhealthy.json()["premium_annual"])

        assert premium_unhealthy > premium_healthy

    def test_quote_life_higher_coverage_higher_premium(self):
        """Test that higher coverage amount results in higher premium."""
        response_low = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 80,
            "coverage_amount": 250000,
            "term_years": 20
        })

        response_high = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 80,
            "coverage_amount": 1000000,
            "term_years": 20
        })

        premium_low = float(response_low.json()["premium_annual"])
        premium_high = float(response_high.json()["premium_annual"])

        assert premium_high > premium_low

    def test_quote_life_longer_term_higher_premium(self):
        """Test that longer term results in higher premium."""
        response_short = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 10
        })

        response_long = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 30
        })

        premium_short = float(response_short.json()["premium_annual"])
        premium_long = float(response_long.json()["premium_annual"])

        assert premium_long > premium_short

    def test_quote_life_minimum_age_18(self):
        """Test life quote with minimum age 18."""
        response = client.post("/api/quotes/life", json={
            "age": 18,
            "health_score": 90,
            "coverage_amount": 100000,
            "term_years": 20
        })

        assert response.status_code == 200

    def test_quote_life_maximum_age_80(self):
        """Test life quote with maximum age 80."""
        response = client.post("/api/quotes/life", json={
            "age": 80,
            "health_score": 70,
            "coverage_amount": 250000,
            "term_years": 10
        })

        assert response.status_code == 200

    def test_quote_life_invalid_age_below_18(self):
        """Test validation error for age below 18."""
        response = client.post("/api/quotes/life", json={
            "age": 17,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        })

        assert response.status_code == 422

    def test_quote_life_invalid_age_above_80(self):
        """Test validation error for age above 80."""
        response = client.post("/api/quotes/life", json={
            "age": 81,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        })

        assert response.status_code == 422

    def test_quote_life_perfect_health_score(self):
        """Test life quote with perfect health score (100)."""
        response = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 100,
            "coverage_amount": 500000,
            "term_years": 20
        })

        assert response.status_code == 200
        # Should have lowest health_factor

    def test_quote_life_minimum_health_score(self):
        """Test life quote with minimum health score (1)."""
        response = client.post("/api/quotes/life", json={
            "age": 35,
            "health_score": 1,
            "coverage_amount": 500000,
            "term_years": 20
        })

        assert response.status_code == 200
        # Should have highest health_factor
