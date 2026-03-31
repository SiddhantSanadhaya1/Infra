"""
Functional tests for quote calculator.

User Story Coverage:
- FR-3.1: Quote generation (Auto, Home, Life)
- FR-3.2: Quote persistence
- FR-3.3: Quote-to-policy conversion

Acceptance Criteria:
- Quote generation completes in < 2 seconds (p95)
- Quote calculation accuracy validated by actuarial team
"""
import httpx
import pytest
from decimal import Decimal


class TestAutoQuotes:
    """Tests for auto insurance quotes (FR-3.1)."""

    def test_auto_quote_comprehensive_coverage(self, client: httpx.Client):
        """
        Test generating an auto quote with comprehensive coverage.
        """
        payload = {
            "driver_age": 35,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "premium_monthly" in data
        assert "premium_annual" in data
        assert "coverage_details" in data

        # Verify amounts are valid decimals
        monthly = Decimal(data["premium_monthly"])
        annual = Decimal(data["premium_annual"])
        assert monthly > 0
        assert annual > 0
        assert abs(annual - (monthly * 12)) < Decimal("0.50")  # Rounding tolerance

    def test_auto_quote_liability_coverage(self, client: httpx.Client):
        """
        Test that liability coverage is cheaper than comprehensive.
        """
        comprehensive_payload = {
            "driver_age": 35,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }
        liability_payload = {
            "driver_age": 35,
            "vehicle_year": 2022,
            "coverage_type": "LIABILITY",
            "annual_mileage": 12000
        }

        comp_response = client.post("/api/quotes/auto", json=comprehensive_payload)
        liab_response = client.post("/api/quotes/auto", json=liability_payload)

        assert comp_response.status_code == 200
        assert liab_response.status_code == 200

        comp_annual = Decimal(comp_response.json()["premium_annual"])
        liab_annual = Decimal(liab_response.json()["premium_annual"])

        assert liab_annual < comp_annual

    def test_auto_quote_young_driver_higher_premium(self, client: httpx.Client):
        """
        Test that young drivers (< 25) pay higher premiums.
        """
        young_driver = {
            "driver_age": 20,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }
        mature_driver = {
            "driver_age": 40,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }

        young_response = client.post("/api/quotes/auto", json=young_driver)
        mature_response = client.post("/api/quotes/auto", json=mature_driver)

        assert young_response.status_code == 200
        assert mature_response.status_code == 200

        young_annual = Decimal(young_response.json()["premium_annual"])
        mature_annual = Decimal(mature_response.json()["premium_annual"])

        assert young_annual > mature_annual

    def test_auto_quote_older_vehicle_lower_premium(self, client: httpx.Client):
        """
        Test that older vehicles have slightly lower premiums.
        """
        new_vehicle = {
            "driver_age": 35,
            "vehicle_year": 2025,
            "coverage_type": "COLLISION",
            "annual_mileage": 12000
        }
        old_vehicle = {
            "driver_age": 35,
            "vehicle_year": 2010,
            "coverage_type": "COLLISION",
            "annual_mileage": 12000
        }

        new_response = client.post("/api/quotes/auto", json=new_vehicle)
        old_response = client.post("/api/quotes/auto", json=old_vehicle)

        assert new_response.status_code == 200
        assert old_response.status_code == 200

        new_annual = Decimal(new_response.json()["premium_annual"])
        old_annual = Decimal(old_response.json()["premium_annual"])

        assert old_annual < new_annual

    def test_auto_quote_high_mileage_higher_premium(self, client: httpx.Client):
        """
        Test that higher annual mileage results in higher premiums.
        """
        low_mileage = {
            "driver_age": 35,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 5000
        }
        high_mileage = {
            "driver_age": 35,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 30000
        }

        low_response = client.post("/api/quotes/auto", json=low_mileage)
        high_response = client.post("/api/quotes/auto", json=high_mileage)

        assert low_response.status_code == 200
        assert high_response.status_code == 200

        low_annual = Decimal(low_response.json()["premium_annual"])
        high_annual = Decimal(high_response.json()["premium_annual"])

        assert high_annual > low_annual

    def test_auto_quote_with_invalid_driver_age(self, client: httpx.Client):
        """
        Test that invalid driver age fails validation.
        """
        payload = {
            "driver_age": 15,  # Below minimum 16
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 422

    def test_auto_quote_with_invalid_vehicle_year(self, client: httpx.Client):
        """
        Test that invalid vehicle year fails validation.
        """
        payload = {
            "driver_age": 35,
            "vehicle_year": 1985,  # Below minimum 1990
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 422


class TestHomeQuotes:
    """Tests for home insurance quotes (FR-3.1)."""

    def test_home_quote_standard_coverage(self, client: httpx.Client):
        """
        Test generating a home insurance quote.
        """
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
        assert "coverage_details" in data

        monthly = Decimal(data["premium_monthly"])
        annual = Decimal(data["premium_annual"])
        assert monthly > 0
        assert annual > 0

    def test_home_quote_high_risk_location_higher_premium(self, client: httpx.Client):
        """
        Test that high-risk locations have higher premiums.
        """
        low_risk = {
            "home_value": 300000,
            "location_risk": "LOW",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        }
        high_risk = {
            "home_value": 300000,
            "location_risk": "HIGH",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        }

        low_response = client.post("/api/quotes/home", json=low_risk)
        high_response = client.post("/api/quotes/home", json=high_risk)

        assert low_response.status_code == 200
        assert high_response.status_code == 200

        low_annual = Decimal(low_response.json()["premium_annual"])
        high_annual = Decimal(high_response.json()["premium_annual"])

        assert high_annual > low_annual

    def test_home_quote_higher_home_value_higher_premium(self, client: httpx.Client):
        """
        Test that higher home value results in higher premiums.
        """
        low_value = {
            "home_value": 200000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        }
        high_value = {
            "home_value": 500000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        }

        low_response = client.post("/api/quotes/home", json=low_value)
        high_response = client.post("/api/quotes/home", json=high_value)

        assert low_response.status_code == 200
        assert high_response.status_code == 200

        low_annual = Decimal(low_response.json()["premium_annual"])
        high_annual = Decimal(high_response.json()["premium_annual"])

        assert high_annual > low_annual

    def test_home_quote_premium_coverage_higher_than_basic(self, client: httpx.Client):
        """
        Test that premium coverage costs more than basic.
        """
        basic = {
            "home_value": 300000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "BASIC"
        }
        premium = {
            "home_value": 300000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "PREMIUM"
        }

        basic_response = client.post("/api/quotes/home", json=basic)
        premium_response = client.post("/api/quotes/home", json=premium)

        assert basic_response.status_code == 200
        assert premium_response.status_code == 200

        basic_annual = Decimal(basic_response.json()["premium_annual"])
        premium_annual = Decimal(premium_response.json()["premium_annual"])

        assert premium_annual > basic_annual

    def test_home_quote_older_home_higher_premium(self, client: httpx.Client):
        """
        Test that older homes have higher premiums.
        """
        new_home = {
            "home_value": 300000,
            "location_risk": "MEDIUM",
            "home_age_years": 5,
            "coverage_type": "STANDARD"
        }
        old_home = {
            "home_value": 300000,
            "location_risk": "MEDIUM",
            "home_age_years": 50,
            "coverage_type": "STANDARD"
        }

        new_response = client.post("/api/quotes/home", json=new_home)
        old_response = client.post("/api/quotes/home", json=old_home)

        assert new_response.status_code == 200
        assert old_response.status_code == 200

        new_annual = Decimal(new_response.json()["premium_annual"])
        old_annual = Decimal(old_response.json()["premium_annual"])

        assert old_annual > new_annual

    def test_home_quote_with_invalid_home_value(self, client: httpx.Client):
        """
        Test that home value below minimum fails validation.
        """
        payload = {
            "home_value": 40000,  # Below minimum 50000
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 422


class TestLifeQuotes:
    """Tests for life insurance quotes (FR-3.1)."""

    def test_life_quote_standard_coverage(self, client: httpx.Client):
        """
        Test generating a life insurance quote.
        """
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
        assert "coverage_details" in data

        monthly = Decimal(data["premium_monthly"])
        annual = Decimal(data["premium_annual"])
        assert monthly > 0
        assert annual > 0

    def test_life_quote_older_age_higher_premium(self, client: httpx.Client):
        """
        Test that older applicants pay higher premiums.
        """
        young = {
            "age": 25,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }
        old = {
            "age": 60,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }

        young_response = client.post("/api/quotes/life", json=young)
        old_response = client.post("/api/quotes/life", json=old)

        assert young_response.status_code == 200
        assert old_response.status_code == 200

        young_annual = Decimal(young_response.json()["premium_annual"])
        old_annual = Decimal(old_response.json()["premium_annual"])

        assert old_annual > young_annual

    def test_life_quote_better_health_lower_premium(self, client: httpx.Client):
        """
        Test that better health scores result in lower premiums.
        """
        poor_health = {
            "age": 35,
            "health_score": 40,
            "coverage_amount": 500000,
            "term_years": 20
        }
        excellent_health = {
            "age": 35,
            "health_score": 95,
            "coverage_amount": 500000,
            "term_years": 20
        }

        poor_response = client.post("/api/quotes/life", json=poor_health)
        excellent_response = client.post("/api/quotes/life", json=excellent_health)

        assert poor_response.status_code == 200
        assert excellent_response.status_code == 200

        poor_annual = Decimal(poor_response.json()["premium_annual"])
        excellent_annual = Decimal(excellent_response.json()["premium_annual"])

        assert excellent_annual < poor_annual

    def test_life_quote_higher_coverage_higher_premium(self, client: httpx.Client):
        """
        Test that higher coverage amounts result in higher premiums.
        """
        low_coverage = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 250000,
            "term_years": 20
        }
        high_coverage = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 1000000,
            "term_years": 20
        }

        low_response = client.post("/api/quotes/life", json=low_coverage)
        high_response = client.post("/api/quotes/life", json=high_coverage)

        assert low_response.status_code == 200
        assert high_response.status_code == 200

        low_annual = Decimal(low_response.json()["premium_annual"])
        high_annual = Decimal(high_response.json()["premium_annual"])

        assert high_annual > low_annual

    def test_life_quote_longer_term_higher_premium(self, client: httpx.Client):
        """
        Test that longer terms result in higher premiums.
        """
        short_term = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 10
        }
        long_term = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 30
        }

        short_response = client.post("/api/quotes/life", json=short_term)
        long_response = client.post("/api/quotes/life", json=long_term)

        assert short_response.status_code == 200
        assert long_response.status_code == 200

        short_annual = Decimal(short_response.json()["premium_annual"])
        long_annual = Decimal(long_response.json()["premium_annual"])

        assert long_annual > short_annual

    def test_life_quote_with_invalid_age(self, client: httpx.Client):
        """
        Test that age outside valid range fails validation.
        """
        too_young = {
            "age": 17,  # Below minimum 18
            "health_score": 80,
            "coverage_amount": 500000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=too_young)

        assert response.status_code == 422

    def test_life_quote_with_invalid_health_score(self, client: httpx.Client):
        """
        Test that invalid health score fails validation.
        """
        payload = {
            "age": 35,
            "health_score": 0,  # Below minimum 1
            "coverage_amount": 500000,
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 422

    def test_life_quote_with_invalid_coverage_amount(self, client: httpx.Client):
        """
        Test that coverage amount outside valid range fails validation.
        """
        payload = {
            "age": 35,
            "health_score": 80,
            "coverage_amount": 20000,  # Below minimum 50000
            "term_years": 20
        }

        response = client.post("/api/quotes/life", json=payload)

        assert response.status_code == 422


class TestQuoteResponseFormat:
    """Tests for quote response format and calculation accuracy."""

    def test_quote_response_contains_coverage_details(self, client: httpx.Client):
        """
        Test that quote response includes coverage details.
        """
        payload = {
            "driver_age": 35,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }

        response = client.post("/api/quotes/auto", json=payload)

        assert response.status_code == 200
        data = response.json()
        details = data["coverage_details"]
        assert details["driver_age"] == 35
        assert details["vehicle_year"] == 2022
        assert details["coverage_type"] == "COMPREHENSIVE"
        assert details["annual_mileage"] == 12000

    def test_quote_monthly_annual_relationship(self, client: httpx.Client):
        """
        Test that monthly premium × 12 ≈ annual premium.
        """
        payload = {
            "home_value": 300000,
            "location_risk": "MEDIUM",
            "home_age_years": 10,
            "coverage_type": "STANDARD"
        }

        response = client.post("/api/quotes/home", json=payload)

        assert response.status_code == 200
        data = response.json()
        monthly = Decimal(data["premium_monthly"])
        annual = Decimal(data["premium_annual"])

        # Allow small rounding difference
        calculated_annual = monthly * 12
        assert abs(annual - calculated_annual) < Decimal("1.00")
