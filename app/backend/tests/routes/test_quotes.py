import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from src.main import app
from src.routes.quotes import _round_decimal


client = TestClient(app)


class TestRoundDecimal:
    """Test suite for _round_decimal helper function."""

    def test_round_decimal_two_decimals(self):
        """Test rounding to two decimal places."""
        result = _round_decimal(123.456)
        assert result == Decimal("123.46")

    def test_round_decimal_one_decimal(self):
        """Test rounding with one decimal place."""
        result = _round_decimal(100.5)
        assert result == Decimal("100.50")

    def test_round_decimal_no_decimals(self):
        """Test rounding integer value."""
        result = _round_decimal(100.0)
        assert result == Decimal("100.00")

    def test_round_decimal_round_half_up(self):
        """Test ROUND_HALF_UP rounding mode."""
        result = _round_decimal(10.555)
        assert result == Decimal("10.56")

    def test_round_decimal_round_down(self):
        """Test rounding down."""
        result = _round_decimal(10.554)
        assert result == Decimal("10.55")

    @pytest.mark.parametrize("value,expected", [
        (0.0, Decimal("0.00")),
        (0.005, Decimal("0.01")),
        (999.999, Decimal("1000.00")),
        (12.345, Decimal("12.35")),
    ])
    def test_round_decimal_various_values(self, value, expected):
        """Test rounding various values."""
        result = _round_decimal(value)
        assert result == expected


class TestQuoteAuto:
    """Test suite for /quotes/auto endpoint."""

    def test_quote_auto_success(self):
        """Test successful auto quote calculation."""
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
        assert float(data["premium_monthly"]) > 0
        assert float(data["premium_annual"]) > 0

    def test_quote_auto_young_driver(self):
        """Test auto quote for young driver (under 25)."""
        payload = {
            "driver_age": 22,
            "vehicle_year": 2022,
            "coverage_type": "LIABILITY",
            "annual_mileage": 10000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Young drivers pay more (1.8x factor)
        assert float(data["premium_annual"]) > 0

    def test_quote_auto_senior_driver(self):
        """Test auto quote for senior driver (over 65)."""
        payload = {
            "driver_age": 70,
            "vehicle_year": 2020,
            "coverage_type": "COLLISION",
            "annual_mileage": 8000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert float(data["premium_annual"]) > 0

    def test_quote_auto_old_vehicle(self):
        """Test auto quote for older vehicle."""
        payload = {
            "driver_age": 40,
            "vehicle_year": 1995,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        # Older vehicles should be cheaper
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_auto_high_mileage(self):
        """Test auto quote with high annual mileage."""
        payload = {
            "driver_age": 35,
            "vehicle_year": 2021,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 50000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        # High mileage increases premium
        assert float(response.json()["premium_annual"]) > 0

    @pytest.mark.parametrize("coverage_type", [
        "LIABILITY",
        "COLLISION",
        "COMPREHENSIVE"
    ])
    def test_quote_auto_various_coverage_types(self, coverage_type):
        """Test auto quote with various coverage types."""
        payload = {
            "driver_age": 30,
            "vehicle_year": 2020,
            "coverage_type": coverage_type,
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["coverage_details"]["coverage_type"] == coverage_type

    def test_quote_auto_min_age(self):
        """Test auto quote with minimum driver age."""
        payload = {
            "driver_age": 16,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_max_age(self):
        """Test auto quote with maximum driver age."""
        payload = {
            "driver_age": 100,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200

    def test_quote_auto_invalid_age_too_young(self):
        """Test auto quote with invalid age (too young)."""
        payload = {
            "driver_age": 15,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 422  # Validation error

    def test_quote_auto_invalid_age_too_old(self):
        """Test auto quote with invalid age (too old)."""
        payload = {
            "driver_age": 101,
            "vehicle_year": 2020,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 422


class TestQuoteHome:
    """Test suite for /quotes/home endpoint."""

    def test_quote_home_success(self):
        """Test successful home quote calculation."""
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
        assert float(data["premium_monthly"]) > 0
        assert float(data["premium_annual"]) > 0

    def test_quote_home_low_risk_location(self):
        """Test home quote for low-risk location."""
        payload = {
            "home_value": 250000,
            "location_risk": "LOW",
            "home_age_years": 5,
            "coverage_type": "BASIC"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200
        # Low risk should result in lower premium
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_home_high_risk_location(self):
        """Test home quote for high-risk location."""
        payload = {
            "home_value": 400000,
            "location_risk": "HIGH",
            "home_age_years": 50,
            "coverage_type": "PREMIUM"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200
        # High risk should result in higher premium
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_home_new_home(self):
        """Test home quote for brand new home."""
        payload = {
            "home_value": 500000,
            "location_risk": "MEDIUM",
            "home_age_years": 0,
            "coverage_type": "PREMIUM"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_old_home(self):
        """Test home quote for very old home."""
        payload = {
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 100,
            "coverage_type": "STANDARD"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200
        # Older homes should cost more to insure
        assert float(response.json()["premium_annual"]) > 0

    @pytest.mark.parametrize("coverage_type", [
        "BASIC",
        "STANDARD",
        "PREMIUM"
    ])
    def test_quote_home_various_coverage_types(self, coverage_type):
        """Test home quote with various coverage types."""
        payload = {
            "home_value": 300000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": coverage_type
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["coverage_details"]["coverage_type"] == coverage_type

    def test_quote_home_min_value(self):
        """Test home quote with minimum home value."""
        payload = {
            "home_value": 50000,
            "location_risk": "LOW",
            "home_age_years": 30,
            "coverage_type": "BASIC"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200

    def test_quote_home_max_value(self):
        """Test home quote with maximum home value."""
        payload = {
            "home_value": 5000000,
            "location_risk": "HIGH",
            "home_age_years": 1,
            "coverage_type": "PREMIUM"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200


class TestQuoteLife:
    """Test suite for /quotes/life endpoint."""

    def test_quote_life_success(self):
        """Test successful life quote calculation."""
        payload = {
            "age": 30,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert float(data["premium_monthly"]) > 0
        assert float(data["premium_annual"]) > 0

    def test_quote_life_young_age(self):
        """Test life quote for young person."""
        payload = {
            "age": 18,
            "health_score": 95,
            "coverage_amount": 250000,
            "term_years": 10
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        # Young age should result in lower premium
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_life_older_age(self):
        """Test life quote for older person."""
        payload = {
            "age": 75,
            "health_score": 60,
            "coverage_amount": 200000,
            "term_years": 10
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        # Older age should result in higher premium
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_life_excellent_health(self):
        """Test life quote with excellent health score."""
        payload = {
            "age": 40,
            "health_score": 100,
            "coverage_amount": 1000000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        # Excellent health should lower premium
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_life_poor_health(self):
        """Test life quote with poor health score."""
        payload = {
            "age": 50,
            "health_score": 1,
            "coverage_amount": 500000,
            "term_years": 15
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        # Poor health should increase premium
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_life_high_coverage(self):
        """Test life quote with high coverage amount."""
        payload = {
            "age": 35,
            "health_score": 75,
            "coverage_amount": 10000000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        # High coverage should result in higher premium
        assert float(response.json()["premium_annual"]) > 0

    def test_quote_life_short_term(self):
        """Test life quote with minimum term."""
        payload = {
            "age": 30,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 10
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_long_term(self):
        """Test life quote with maximum term."""
        payload = {
            "age": 25,
            "health_score": 90,
            "coverage_amount": 750000,
            "term_years": 30
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200
        # Longer term should result in higher premium
        assert float(response.json()["premium_annual"]) > 0

    @pytest.mark.parametrize("age,health_score", [
        (18, 100),
        (30, 80),
        (50, 50),
        (80, 30),
    ])
    def test_quote_life_various_combinations(self, age, health_score):
        """Test life quote with various age and health combinations."""
        payload = {
            "age": age,
            "health_score": health_score,
            "coverage_amount": 500000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_min_coverage(self):
        """Test life quote with minimum coverage amount."""
        payload = {
            "age": 30,
            "health_score": 80,
            "coverage_amount": 50000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 200

    def test_quote_life_invalid_age_too_young(self):
        """Test life quote with invalid age (too young)."""
        payload = {
            "age": 17,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 422

    def test_quote_life_invalid_age_too_old(self):
        """Test life quote with invalid age (too old)."""
        payload = {
            "age": 81,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 422
