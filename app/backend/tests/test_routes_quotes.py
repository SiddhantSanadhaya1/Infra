"""Unit tests for src.routes.quotes module."""
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.routes.quotes import router


# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestAutoQuote:
    """Test auto insurance quote endpoint."""

    def test_quote_auto_young_driver(self):
        """Test auto quote for young driver (high risk)."""
        payload = {
            "driver_age": 22,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 15000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert float(data["premium_monthly"]) > 0
        assert float(data["premium_annual"]) > float(data["premium_monthly"])

    def test_quote_auto_middle_aged_driver(self):
        """Test auto quote for middle-aged driver (lower risk)."""
        payload = {
            "driver_age": 45,
            "vehicle_year": 2018,
            "coverage_type": "COLLISION",
            "annual_mileage": 12000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Middle-aged drivers should have lower premiums than young drivers
        assert float(data["premium_annual"]) > 0

    def test_quote_auto_senior_driver(self):
        """Test auto quote for senior driver."""
        payload = {
            "driver_age": 70,
            "vehicle_year": 2022,
            "coverage_type": "LIABILITY",
            "annual_mileage": 8000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert float(data["premium_annual"]) > 0

    def test_quote_auto_minimum_age(self):
        """Test auto quote with minimum driver age (16)."""
        payload = {
            "driver_age": 16,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 10000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_maximum_age(self):
        """Test auto quote with maximum driver age (100)."""
        payload = {
            "driver_age": 100,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 5000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_age_below_minimum(self):
        """Test auto quote rejects age below 16."""
        payload = {
            "driver_age": 15,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 10000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 422

    def test_quote_auto_age_above_maximum(self):
        """Test auto quote rejects age above 100."""
        payload = {
            "driver_age": 101,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 10000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 422

    def test_quote_auto_old_vehicle(self):
        """Test auto quote for old vehicle (1990)."""
        payload = {
            "driver_age": 40,
            "vehicle_year": 1990,
            "coverage_type": "LIABILITY",
            "annual_mileage": 10000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_new_vehicle(self):
        """Test auto quote for new vehicle (2025)."""
        payload = {
            "driver_age": 35,
            "vehicle_year": 2025,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_coverage_type_liability(self):
        """Test auto quote for LIABILITY coverage."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200
        # LIABILITY should be cheaper than COMPREHENSIVE
        data = response.json()
        assert data["coverage_details"]["coverage_type"] == "LIABILITY"

    def test_quote_auto_high_mileage(self):
        """Test auto quote for high annual mileage."""
        payload = {
            "driver_age": 35,
            "vehicle_year": 2020,
            "coverage_type": "COLLISION",
            "annual_mileage": 100000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_low_mileage(self):
        """Test auto quote for low annual mileage."""
        payload = {
            "driver_age": 35,
            "vehicle_year": 2020,
            "coverage_type": "COLLISION",
            "annual_mileage": 1000,
        }

        response = client.post("/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_monthly_equals_annual_divided_by_12(self):
        """Test monthly premium is approximately annual divided by 12."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "COLLISION",
            "annual_mileage": 12000,
        }

        response = client.post("/quotes/auto", json=payload)
        data = response.json()

        monthly = float(data["premium_monthly"])
        annual = float(data["premium_annual"])

        # Monthly should be approximately annual / 12 (within rounding)
        assert abs(monthly * 12 - annual) < 1.0


class TestHomeQuote:
    """Test home insurance quote endpoint."""

    def test_quote_home_standard_coverage(self):
        """Test home quote with standard coverage."""
        payload = {
            "home_value": 250000,
            "location_risk": "MEDIUM",
            "home_age_years": 15,
            "coverage_type": "STANDARD",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert float(data["premium_annual"]) > 0

    def test_quote_home_minimum_value(self):
        """Test home quote with minimum home value."""
        payload = {
            "home_value": 50000,
            "location_risk": "LOW",
            "home_age_years": 5,
            "coverage_type": "BASIC",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_maximum_value(self):
        """Test home quote with maximum home value."""
        payload = {
            "home_value": 5000000,
            "location_risk": "LOW",
            "home_age_years": 10,
            "coverage_type": "PREMIUM",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_high_risk_location(self):
        """Test home quote for high-risk location."""
        payload = {
            "home_value": 300000,
            "location_risk": "HIGH",
            "home_age_years": 20,
            "coverage_type": "STANDARD",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_low_risk_location(self):
        """Test home quote for low-risk location."""
        payload = {
            "home_value": 300000,
            "location_risk": "LOW",
            "home_age_years": 5,
            "coverage_type": "STANDARD",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_new_home(self):
        """Test home quote for brand new home (0 years)."""
        payload = {
            "home_value": 400000,
            "location_risk": "MEDIUM",
            "home_age_years": 0,
            "coverage_type": "PREMIUM",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_very_old_home(self):
        """Test home quote for very old home (150 years)."""
        payload = {
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 150,
            "coverage_type": "STANDARD",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_premium_coverage(self):
        """Test home quote with PREMIUM coverage."""
        payload = {
            "home_value": 500000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "PREMIUM",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["coverage_details"]["coverage_type"] == "PREMIUM"

    def test_quote_home_basic_coverage(self):
        """Test home quote with BASIC coverage."""
        payload = {
            "home_value": 150000,
            "location_risk": "LOW",
            "home_age_years": 25,
            "coverage_type": "BASIC",
        }

        response = client.post("/quotes/home", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["coverage_details"]["coverage_type"] == "BASIC"


class TestLifeQuote:
    """Test life insurance quote endpoint."""

    def test_quote_life_young_healthy(self):
        """Test life quote for young, healthy person."""
        payload = {
            "age": 25,
            "health_score": 90,
            "coverage_amount": 500000,
            "term_years": 20,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert float(data["premium_annual"]) > 0

    def test_quote_life_minimum_age(self):
        """Test life quote with minimum age (18)."""
        payload = {
            "age": 18,
            "health_score": 80,
            "coverage_amount": 250000,
            "term_years": 20,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_maximum_age(self):
        """Test life quote with maximum age (80)."""
        payload = {
            "age": 80,
            "health_score": 60,
            "coverage_amount": 100000,
            "term_years": 10,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_age_below_minimum(self):
        """Test life quote rejects age below 18."""
        payload = {
            "age": 17,
            "health_score": 85,
            "coverage_amount": 250000,
            "term_years": 20,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 422

    def test_quote_life_age_above_maximum(self):
        """Test life quote rejects age above 80."""
        payload = {
            "age": 81,
            "health_score": 70,
            "coverage_amount": 100000,
            "term_years": 10,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 422

    def test_quote_life_excellent_health(self):
        """Test life quote for person with excellent health (100)."""
        payload = {
            "age": 40,
            "health_score": 100,
            "coverage_amount": 1000000,
            "term_years": 20,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_poor_health(self):
        """Test life quote for person with poor health (minimum score)."""
        payload = {
            "age": 55,
            "health_score": 1,
            "coverage_amount": 500000,
            "term_years": 15,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_minimum_coverage(self):
        """Test life quote with minimum coverage amount."""
        payload = {
            "age": 30,
            "health_score": 75,
            "coverage_amount": 50000,
            "term_years": 10,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_maximum_coverage(self):
        """Test life quote with maximum coverage amount."""
        payload = {
            "age": 35,
            "health_score": 85,
            "coverage_amount": 10000000,
            "term_years": 20,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_minimum_term(self):
        """Test life quote with minimum term (10 years)."""
        payload = {
            "age": 40,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 10,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_maximum_term(self):
        """Test life quote with maximum term (30 years)."""
        payload = {
            "age": 30,
            "health_score": 90,
            "coverage_amount": 1000000,
            "term_years": 30,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_term_below_minimum(self):
        """Test life quote rejects term below 10 years."""
        payload = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 9,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 422

    def test_quote_life_term_above_maximum(self):
        """Test life quote rejects term above 30 years."""
        payload = {
            "age": 25,
            "health_score": 90,
            "coverage_amount": 1000000,
            "term_years": 31,
        }

        response = client.post("/quotes/life", json=payload)

        assert response.status_code == 422
