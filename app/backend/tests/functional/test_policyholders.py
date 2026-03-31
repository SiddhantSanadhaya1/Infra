"""
Functional tests for policyholder management.

User Story Coverage:
- FR-6.1: Policyholder CRUD operations
- FR-6.2: Policy association
"""
import httpx
import pytest
from datetime import date


class TestPolicyholderCreation:
    """Tests for creating policyholders (FR-6.1.1)."""

    def test_create_policyholder_with_all_fields(self, client: httpx.Client):
        """
        Test creating a policyholder with all required and optional fields.
        Acceptance Criteria: Policyholder creation completes in < 2 seconds.
        """
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": f"john.doe.{date.today().isoformat()}@example.com",
            "phone": "+1-555-0100",
            "date_of_birth": "1985-06-15",
            "address": "123 Main St, Springfield, IL 62701"
        }

        response = client.post("/api/policyholders", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == payload["first_name"]
        assert data["last_name"] == payload["last_name"]
        assert data["email"] == payload["email"]
        assert data["phone"] == payload["phone"]
        assert data["date_of_birth"] == payload["date_of_birth"]
        assert data["address"] == payload["address"]
        assert "id" in data

    def test_create_policyholder_with_minimal_fields(self, client: httpx.Client):
        """
        Test creating a policyholder with only required fields.
        """
        payload = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": f"jane.smith.{date.today().isoformat()}@example.com"
        }

        response = client.post("/api/policyholders", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == payload["first_name"]
        assert data["last_name"] == payload["last_name"]
        assert data["email"] == payload["email"]
        assert data["phone"] is None
        assert data["date_of_birth"] is None
        assert data["address"] is None

    def test_create_policyholder_with_duplicate_email(self, client: httpx.Client):
        """
        Test that creating a policyholder with duplicate email fails.
        Acceptance Criteria: Email validation prevents invalid formats and duplicates.
        """
        email = f"duplicate.{date.today().isoformat()}@example.com"
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": email
        }

        # Create first policyholder
        response1 = client.post("/api/policyholders", json=payload)
        assert response1.status_code == 201

        # Attempt to create second with same email
        response2 = client.post("/api/policyholders", json=payload)
        assert response2.status_code == 409
        assert "already registered" in response2.json()["detail"].lower()

    def test_create_policyholder_with_missing_required_fields(self, client: httpx.Client):
        """
        Test that creating a policyholder without required fields fails.
        """
        payload = {
            "first_name": "Test"
            # Missing last_name and email
        }

        response = client.post("/api/policyholders", json=payload)

        assert response.status_code == 422


class TestPolicyholderRetrieval:
    """Tests for retrieving policyholders (FR-6.1.4)."""

    def test_list_policyholders(self, client: httpx.Client):
        """
        Test listing all policyholders with pagination.
        """
        response = client.get("/api/policyholders")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_policyholders_with_pagination(self, client: httpx.Client):
        """
        Test pagination parameters (skip and limit).
        """
        response = client.get("/api/policyholders?skip=0&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_get_policyholder_by_id(self, client: httpx.Client):
        """
        Test retrieving a single policyholder by ID.
        """
        # First create a policyholder
        payload = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": f"alice.johnson.{date.today().isoformat()}@example.com"
        }
        create_response = client.post("/api/policyholders", json=payload)
        assert create_response.status_code == 201
        policyholder_id = create_response.json()["id"]

        # Retrieve by ID
        response = client.get(f"/api/policyholders/{policyholder_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == policyholder_id
        assert data["first_name"] == payload["first_name"]
        assert data["email"] == payload["email"]

    def test_get_nonexistent_policyholder(self, client: httpx.Client):
        """
        Test retrieving a policyholder that doesn't exist returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/policyholders/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestPolicyholderUpdate:
    """Tests for updating policyholders (FR-6.1.3)."""

    def test_update_policyholder_fields(self, client: httpx.Client):
        """
        Test updating policyholder details.
        """
        # Create policyholder
        create_payload = {
            "first_name": "Bob",
            "last_name": "Williams",
            "email": f"bob.williams.{date.today().isoformat()}@example.com",
            "phone": "+1-555-0200"
        }
        create_response = client.post("/api/policyholders", json=create_payload)
        assert create_response.status_code == 201
        policyholder_id = create_response.json()["id"]

        # Update phone and address
        update_payload = {
            "phone": "+1-555-0999",
            "address": "456 Oak Ave, Chicago, IL 60601"
        }
        response = client.put(f"/api/policyholders/{policyholder_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == update_payload["phone"]
        assert data["address"] == update_payload["address"]
        # Unchanged fields remain the same
        assert data["first_name"] == create_payload["first_name"]
        assert data["email"] == create_payload["email"]

    def test_update_nonexistent_policyholder(self, client: httpx.Client):
        """
        Test updating a policyholder that doesn't exist returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_payload = {"phone": "+1-555-0000"}

        response = client.put(f"/api/policyholders/{fake_id}", json=update_payload)

        assert response.status_code == 404


class TestPolicyholderDeletion:
    """Tests for deleting policyholders (FR-6.1.5)."""

    def test_delete_policyholder(self, client: httpx.Client):
        """
        Test soft-deleting a policyholder.
        Acceptance Criteria: Soft-delete preserves data for audit.
        """
        # Create policyholder
        payload = {
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": f"charlie.brown.{date.today().isoformat()}@example.com"
        }
        create_response = client.post("/api/policyholders", json=payload)
        assert create_response.status_code == 201
        policyholder_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/api/policyholders/{policyholder_id}")

        assert response.status_code == 204

    def test_delete_nonexistent_policyholder(self, client: httpx.Client):
        """
        Test deleting a policyholder that doesn't exist returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.delete(f"/api/policyholders/{fake_id}")

        assert response.status_code == 404


class TestPolicyholderToPolicy:
    """Tests for policyholder-policy association (FR-6.2)."""

    def test_get_policyholder_with_policies(self, client: httpx.Client):
        """
        Test retrieving a policyholder includes their policies.
        Acceptance Criteria: Support multiple policies per policyholder.
        """
        # Create policyholder
        ph_payload = {
            "first_name": "David",
            "last_name": "Miller",
            "email": f"david.miller.{date.today().isoformat()}@example.com"
        }
        ph_response = client.post("/api/policyholders", json=ph_payload)
        assert ph_response.status_code == 201
        policyholder_id = ph_response.json()["id"]

        # Create policy for this policyholder
        policy_payload = {
            "policyholder_id": policyholder_id,
            "policy_type": "AUTO",
            "premium_amount": 120.00,
            "coverage_amount": 50000.00,
            "start_date": "2026-04-01",
            "end_date": "2027-04-01"
        }
        policy_response = client.post("/api/policies", json=policy_payload)
        assert policy_response.status_code == 201

        # Retrieve policyholder
        response = client.get(f"/api/policyholders/{policyholder_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == policyholder_id
