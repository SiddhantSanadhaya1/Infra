"""Tests for src/routes/quotes.py"""
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app

client = TestClient(app)


class TestAutoQuote:
    """Test /quotes/auto endpoint with boundary values."""

    def test_auto_quote_valid_request(self):
        """Test valid auto insurance quote request."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert "coverage_details" in data

    def test_auto_quote_minimum_age(self):
        """Test boundary: minimum driver age (16)."""
        payload = {
            "driver_age": 16,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 5000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        # Young drivers should have higher premium due to age_factor
        data = response.json()
        assert float(data["premium_annual"]) > 0

    def test_auto_quote_age_below_minimum(self):
        """Test boundary: age below minimum (15)."""
        payload = {
            "driver_age": 15,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 5000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 422  # Validation error

    def test_auto_quote_maximum_age(self):
        """Test boundary: maximum driver age (100)."""
        payload = {
            "driver_age": 100,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 5000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_auto_quote_age_above_maximum(self):
        """Test boundary: age above maximum (101)."""
        payload = {
            "driver_age": 101,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 5000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 422

    def test_auto_quote_young_driver_premium(self):
        """Test that drivers under 25 have higher premiums."""
        young_payload = {
            "driver_age": 20,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }
        mature_payload = {
            "driver_age": 40,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }

        young_response = client.post("/api/quotes/auto", json=young_payload)
        mature_response = client.post("/api/quotes/auto", json=mature_payload)

        young_premium = float(young_response.json()["premium_annual"])
        mature_premium = float(mature_response.json()["premium_annual"])

        assert young_premium > mature_premium

    def test_auto_quote_oldest_vehicle_year(self):
        """Test boundary: oldest vehicle year (1990)."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 1990,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_auto_quote_newest_vehicle_year(self):
        """Test boundary: newest vehicle year (2025)."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2025,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_auto_quote_liability_coverage(self):
        """Test LIABILITY coverage type."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["coverage_details"]["coverage_type"] == "LIABILITY"

    def test_auto_quote_comprehensive_coverage(self):
        """Test COMPREHENSIVE coverage type."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_auto_quote_minimum_mileage(self):
        """Test boundary: minimum annual mileage (1000)."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 1000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_auto_quote_maximum_mileage(self):
        """Test boundary: maximum annual mileage (100000)."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 100000
        }
        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_auto_quote_premium_calculation_accuracy(self):
        """Test that premium calculation is accurate."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }
        response = client.post("/api/quotes/auto", json=payload)
        data = response.json()

        annual = Decimal(data["premium_annual"])
        monthly = Decimal(data["premium_monthly"])

        # Monthly should be approximately annual / 12
        expected_monthly = (annual / 12).quantize(Decimal("0.01"))
        assert abs(monthly - expected_monthly) <= Decimal("0.01")


class TestHomeQuote:
    """Test /quotes/home endpoint with boundary values."""

    def test_home_quote_valid_request(self):
        """Test valid home insurance quote request."""
        payload = {
            "home_value": 300000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        }
        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data

    def test_home_quote_minimum_value(self):
        """Test boundary: minimum home value (50000)."""
        payload = {
            "home_value": 50000,
            "location_risk": "LOW",
            "home_age_years": 0,
            "coverage_type": "BASIC"
        }
        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200

    def test_home_quote_maximum_value(self):
        """Test boundary: maximum home value (5000000)."""
        payload = {
            "home_value": 5000000,
            "location_risk": "LOW",
            "home_age_years": 0,
            "coverage_type": "BASIC"
        }
        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200

    def test_home_quote_low_risk_location(self):
        """Test LOW risk location."""
        payload = {
            "home_value": 200000,
            "location_risk": "LOW",
            "home_age_years": 5,
            "coverage_type": "STANDARD"
        }
        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["coverage_details"]["location_risk"] == "LOW"

    def test_home_quote_high_risk_location(self):
        """Test HIGH risk location has higher premium."""
        low_risk = {
            "home_value": 200000,
            "location_risk": "LOW",
            "home_age_years": 5,
            "coverage_type": "STANDARD"
        }
        high_risk = {
            "home_value": 200000,
            "location_risk": "HIGH",
            "home_age_years": 5,
            "coverage_type": "STANDARD"
        }

        low_response = client.post("/api/quotes/home", json=low_risk)
        high_response = client.post("/api/quotes/home", json=high_risk)

        low_premium = float(low_response.json()["premium_annual"])
        high_premium = float(high_response.json()["premium_annual"])

        assert high_premium > low_premium

    def test_home_quote_new_home(self):
        """Test boundary: brand new home (0 years)."""
        payload = {
            "home_value": 250000,
            "location_risk": "MEDIUM",
            "home_age_years": 0,
            "coverage_type": "STANDARD"
        }
        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200

    def test_home_quote_maximum_age(self):
        """Test boundary: maximum home age (150 years)."""
        payload = {
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 150,
            "coverage_type": "STANDARD"
        }
        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200

    def test_home_quote_basic_coverage(self):
        """Test BASIC coverage type."""
        payload = {
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "BASIC"
        }
        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200

    def test_home_quote_premium_coverage(self):
        """Test PREMIUM coverage type has higher premium."""
        basic = {
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "BASIC"
        }
        premium = {
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "PREMIUM"
        }

        basic_response = client.post("/api/quotes/home", json=basic)
        premium_response = client.post("/api/quotes/home", json=premium)

        basic_cost = float(basic_response.json()["premium_annual"])
        premium_cost = float(premium_response.json()["premium_annual"])

        assert premium_cost > basic_cost


class TestLifeQuote:
    """Test /quotes/life endpoint with boundary values."""

    def test_life_quote_valid_request(self):
        """Test valid life insurance quote request."""
        payload = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data

    def test_life_quote_minimum_age(self):
        """Test boundary: minimum age (18)."""
        payload = {
            "age": 18,
            "health_score": 100,
            "coverage_amount": 100000,
            "term_years": 10
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_life_quote_maximum_age(self):
        """Test boundary: maximum age (80)."""
        payload = {
            "age": 80,
            "health_score": 50,
            "coverage_amount": 100000,
            "term_years": 10
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_life_quote_age_below_minimum(self):
        """Test age below minimum (17)."""
        payload = {
            "age": 17,
            "health_score": 100,
            "coverage_amount": 100000,
            "term_years": 10
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 422

    def test_life_quote_older_age_higher_premium(self):
        """Test that older age results in higher premium."""
        young = {
            "age": 25,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }
        old = {
            "age": 65,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }

        young_response = client.post("/api/quotes/life", json=young)
        old_response = client.post("/api/quotes/life", json=old)

        young_premium = float(young_response.json()["premium_annual"])
        old_premium = float(old_response.json()["premium_annual"])

        assert old_premium > young_premium

    def test_life_quote_minimum_health_score(self):
        """Test boundary: minimum health score (1)."""
        payload = {
            "age": 35,
            "health_score": 1,
            "coverage_amount": 500000,
            "term_years": 20
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_life_quote_maximum_health_score(self):
        """Test boundary: maximum health score (100)."""
        payload = {
            "age": 35,
            "health_score": 100,
            "coverage_amount": 500000,
            "term_years": 20
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_life_quote_better_health_lower_premium(self):
        """Test that better health score results in lower premium."""
        poor_health = {
            "age": 35,
            "health_score": 20,
            "coverage_amount": 500000,
            "term_years": 20
        }
        good_health = {
            "age": 35,
            "health_score": 95,
            "coverage_amount": 500000,
            "term_years": 20
        }

        poor_response = client.post("/api/quotes/life", json=poor_health)
        good_response = client.post("/api/quotes/life", json=good_health)

        poor_premium = float(poor_response.json()["premium_annual"])
        good_premium = float(good_response.json()["premium_annual"])

        assert poor_premium > good_premium

    def test_life_quote_minimum_coverage(self):
        """Test boundary: minimum coverage amount (50000)."""
        payload = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 50000,
            "term_years": 20
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_life_quote_maximum_coverage(self):
        """Test boundary: maximum coverage amount (10000000)."""
        payload = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 10000000,
            "term_years": 20
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_life_quote_minimum_term(self):
        """Test boundary: minimum term years (10)."""
        payload = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 10
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_life_quote_maximum_term(self):
        """Test boundary: maximum term years (30)."""
        payload = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 30
        }
        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
