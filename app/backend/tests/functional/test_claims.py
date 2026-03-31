"""
Functional tests for claims processing.

User Story Coverage:
- FR-2.1: Claim filing
- FR-2.2: Claim review (adjusters)
- FR-2.3: Fraud detection
- FR-2.4: Claim status tracking
"""
import httpx
import pytest
from datetime import date, timedelta


@pytest.fixture
def test_policyholder(client: httpx.Client) -> dict:
    """Create a test policyholder."""
    payload = {
        "first_name": "Claims",
        "last_name": "Tester",
        "email": f"claims.test.{date.today().isoformat()}.{id(client)}@example.com"
    }
    response = client.post("/api/policyholders", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def active_policy(client: httpx.Client, test_policyholder: dict) -> dict:
    """Create an active policy for claim tests."""
    payload = {
        "policyholder_id": test_policyholder["id"],
        "policy_type": "AUTO",
        "premium_amount": 150.00,
        "coverage_amount": 100000.00,
        "start_date": "2026-01-01",
        "end_date": "2027-01-01",
        "status": "ACTIVE"
    }
    response = client.post("/api/policies", json=payload)
    assert response.status_code == 201
    return response.json()


class TestClaimFiling:
    """Tests for filing claims (FR-2.1)."""

    def test_file_claim_on_active_policy(self, client: httpx.Client, active_policy: dict):
        """
        Test filing a claim on an active policy.
        Acceptance Criteria:
        - Claim filing completes in < 5 seconds
        - Claim number follows format CLM-2026-XXXXXX
        - Status updates sent within 60 seconds
        """
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Rear-ended at intersection on Main St",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }

        response = client.post("/api/claims", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["policy_id"] == active_policy["id"]
        assert data["claim_type"] == "COLLISION"
        assert data["description"] == payload["description"]
        assert data["amount_requested"] == "5000.00"
        assert data["status"] == "SUBMITTED"
        assert data["claim_number"].startswith("CLM-")
        assert data["incident_date"] == payload["incident_date"]
        assert "id" in data
        assert "filed_at" in data

    def test_file_theft_claim(self, client: httpx.Client, active_policy: dict):
        """
        Test filing a theft claim.
        """
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "THEFT",
            "description": "Vehicle stolen from parking lot",
            "amount_requested": 25000.00,
            "incident_date": "2026-03-20"
        }

        response = client.post("/api/claims", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["claim_type"] == "THEFT"
        assert data["status"] == "SUBMITTED"

    def test_file_fire_claim(self, client: httpx.Client, active_policy: dict):
        """
        Test filing a fire damage claim.
        """
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "FIRE",
            "description": "Kitchen fire caused damage to property",
            "amount_requested": 15000.00,
            "incident_date": "2026-03-10"
        }

        response = client.post("/api/claims", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["claim_type"] == "FIRE"

    def test_file_claim_with_amount_exceeding_coverage(self, client: httpx.Client, active_policy: dict):
        """
        Test that filing a claim with amount > coverage fails validation.
        Acceptance Criteria: Validate claim amount ≤ coverage amount.
        """
        # Policy has coverage_amount of 100000.00
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Total loss of vehicle",
            "amount_requested": 150000.00,  # Exceeds coverage
            "incident_date": "2026-03-15"
        }

        response = client.post("/api/claims", json=payload)

        assert response.status_code == 422
        assert "coverage" in response.json()["detail"].lower()

    def test_file_claim_on_nonexistent_policy(self, client: httpx.Client):
        """
        Test filing a claim on a non-existent policy fails.
        """
        fake_policy_id = "00000000-0000-0000-0000-000000000000"
        payload = {
            "policy_id": fake_policy_id,
            "claim_type": "COLLISION",
            "description": "Test claim",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }

        response = client.post("/api/claims", json=payload)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_file_claim_on_pending_policy(self, client: httpx.Client, test_policyholder: dict):
        """
        Test that filing a claim on PENDING policy fails.
        Acceptance Criteria: Validate policy is ACTIVE.
        """
        # Create PENDING policy
        policy_payload = {
            "policyholder_id": test_policyholder["id"],
            "policy_type": "HOME",
            "premium_amount": 200.00,
            "coverage_amount": 300000.00,
            "start_date": "2026-04-01",
            "end_date": "2027-04-01",
            "status": "PENDING"
        }
        policy_response = client.post("/api/policies", json=policy_payload)
        assert policy_response.status_code == 201
        pending_policy_id = policy_response.json()["id"]

        # Attempt to file claim
        claim_payload = {
            "policy_id": pending_policy_id,
            "claim_type": "FIRE",
            "description": "Test claim",
            "amount_requested": 10000.00,
            "incident_date": "2026-03-15"
        }

        response = client.post("/api/claims", json=claim_payload)

        assert response.status_code == 422
        assert "active" in response.json()["detail"].lower()

    def test_file_claim_on_cancelled_policy(self, client: httpx.Client, test_policyholder: dict):
        """
        Test that filing a claim on CANCELLED policy fails.
        """
        # Create and cancel policy
        policy_payload = {
            "policyholder_id": test_policyholder["id"],
            "policy_type": "AUTO",
            "premium_amount": 100.00,
            "coverage_amount": 50000.00,
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
            "status": "CANCELLED"
        }
        policy_response = client.post("/api/policies", json=policy_payload)
        assert policy_response.status_code == 201
        cancelled_policy_id = policy_response.json()["id"]

        # Attempt to file claim
        claim_payload = {
            "policy_id": cancelled_policy_id,
            "claim_type": "COLLISION",
            "description": "Test claim",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }

        response = client.post("/api/claims", json=claim_payload)

        assert response.status_code == 422

    def test_file_claim_with_missing_fields(self, client: httpx.Client, active_policy: dict):
        """
        Test that filing a claim without required fields fails.
        """
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION"
            # Missing description, amount_requested, incident_date
        }

        response = client.post("/api/claims", json=payload)

        assert response.status_code == 422


class TestClaimRetrieval:
    """Tests for retrieving and listing claims (FR-2.2, FR-2.4)."""

    def test_list_all_claims(self, client: httpx.Client):
        """
        Test listing all claims.
        """
        response = client.get("/api/claims")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_claims_with_pagination(self, client: httpx.Client):
        """
        Test pagination parameters.
        """
        response = client.get("/api/claims?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_filter_claims_by_status(self, client: httpx.Client, active_policy: dict):
        """
        Test filtering claims by status.
        Acceptance Criteria: Filter by status (SUBMITTED, UNDER_REVIEW, etc.).
        """
        # Create claim
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Test claim for filtering",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=payload)
        assert create_response.status_code == 201

        # Filter by SUBMITTED status
        response = client.get("/api/claims?status=SUBMITTED")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for claim in data:
            assert claim["status"] == "SUBMITTED"

    def test_filter_claims_by_policy(self, client: httpx.Client, active_policy: dict):
        """
        Test filtering claims by policy ID.
        """
        # Create claim
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "THEFT",
            "description": "Test claim",
            "amount_requested": 10000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=payload)
        assert create_response.status_code == 201

        # Filter by policy
        response = client.get(f"/api/claims?policy_id={active_policy['id']}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for claim in data:
            assert claim["policy_id"] == active_policy["id"]

    def test_get_claim_by_id(self, client: httpx.Client, active_policy: dict):
        """
        Test retrieving a single claim by ID.
        """
        # Create claim
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "FIRE",
            "description": "Specific claim for retrieval",
            "amount_requested": 7500.00,
            "incident_date": "2026-03-10"
        }
        create_response = client.post("/api/claims", json=payload)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]

        # Retrieve by ID
        response = client.get(f"/api/claims/{claim_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == claim_id
        assert data["claim_type"] == "FIRE"
        assert data["amount_requested"] == "7500.00"

    def test_get_nonexistent_claim(self, client: httpx.Client):
        """
        Test retrieving a claim that doesn't exist returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/claims/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestClaimUpdate:
    """Tests for updating claims."""

    def test_update_claim_description(self, client: httpx.Client, active_policy: dict):
        """
        Test updating claim description and details.
        """
        # Create claim
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Initial description",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=create_payload)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]

        # Update description
        update_payload = {
            "description": "Updated description with more details about the accident"
        }
        response = client.put(f"/api/claims/{claim_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_payload["description"]

    def test_update_claim_status_to_under_review(self, client: httpx.Client, active_policy: dict):
        """
        Test updating claim status to UNDER_REVIEW.
        """
        # Create claim
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "THEFT",
            "description": "Vehicle stolen",
            "amount_requested": 20000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=create_payload)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]

        # Update to UNDER_REVIEW
        update_payload = {"status": "UNDER_REVIEW"}
        response = client.put(f"/api/claims/{claim_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UNDER_REVIEW"

    def test_update_nonexistent_claim(self, client: httpx.Client):
        """
        Test updating a claim that doesn't exist returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_payload = {"description": "Updated"}

        response = client.put(f"/api/claims/{fake_id}", json=update_payload)

        assert response.status_code == 404


class TestClaimApproval:
    """Tests for approving claims (FR-2.2.6)."""

    def test_approve_submitted_claim(self, client: httpx.Client, active_policy: dict):
        """
        Test approving a claim in SUBMITTED status.
        Acceptance Criteria: Approve claim with approved amount.
        """
        # Create claim
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Minor fender bender",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=create_payload)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]

        # Approve claim
        approve_payload = {
            "amount_approved": 4500.00,
            "notes": "Approved with adjustment for depreciation"
        }
        response = client.post(f"/api/claims/{claim_id}/approve", json=approve_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["amount_approved"] == "4500.00"

    def test_approve_under_review_claim(self, client: httpx.Client, active_policy: dict):
        """
        Test approving a claim in UNDER_REVIEW status.
        """
        # Create and update claim to UNDER_REVIEW
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "FIRE",
            "description": "Kitchen fire",
            "amount_requested": 15000.00,
            "incident_date": "2026-03-10"
        }
        create_response = client.post("/api/claims", json=create_payload)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]

        # Update to UNDER_REVIEW
        client.put(f"/api/claims/{claim_id}", json={"status": "UNDER_REVIEW"})

        # Approve
        approve_payload = {"amount_approved": 15000.00}
        response = client.post(f"/api/claims/{claim_id}/approve", json=approve_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"

    def test_approve_already_approved_claim_fails(self, client: httpx.Client, active_policy: dict):
        """
        Test that approving an already approved claim fails.
        """
        # Create and approve claim
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Test claim",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=create_payload)
        claim_id = create_response.json()["id"]

        # First approval
        approve_payload = {"amount_approved": 5000.00}
        response1 = client.post(f"/api/claims/{claim_id}/approve", json=approve_payload)
        assert response1.status_code == 200

        # Second approval attempt
        response2 = client.post(f"/api/claims/{claim_id}/approve", json=approve_payload)

        assert response2.status_code == 422
        assert "cannot approve" in response2.json()["detail"].lower()

    def test_approve_nonexistent_claim(self, client: httpx.Client):
        """
        Test approving a non-existent claim returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        approve_payload = {"amount_approved": 5000.00}

        response = client.post(f"/api/claims/{fake_id}/approve", json=approve_payload)

        assert response.status_code == 404


class TestClaimRejection:
    """Tests for rejecting claims (FR-2.2.7)."""

    def test_reject_submitted_claim(self, client: httpx.Client, active_policy: dict):
        """
        Test rejecting a claim with reason.
        Acceptance Criteria: Deny claim with reason.
        """
        # Create claim
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Test claim",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=create_payload)
        assert create_response.status_code == 201
        claim_id = create_response.json()["id"]

        # Reject claim
        reject_payload = {"reason": "Incident not covered under policy terms"}
        response = client.post(f"/api/claims/{claim_id}/reject", json=reject_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"

    def test_reject_under_review_claim(self, client: httpx.Client, active_policy: dict):
        """
        Test rejecting a claim in UNDER_REVIEW status.
        """
        # Create and update claim
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "THEFT",
            "description": "Test claim",
            "amount_requested": 10000.00,
            "incident_date": "2026-03-15"
        }
        create_response = client.post("/api/claims", json=create_payload)
        claim_id = create_response.json()["id"]

        client.put(f"/api/claims/{claim_id}", json={"status": "UNDER_REVIEW"})

        # Reject
        reject_payload = {"reason": "Insufficient evidence provided"}
        response = client.post(f"/api/claims/{claim_id}/reject", json=reject_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "REJECTED"

    def test_reject_approved_claim_fails(self, client: httpx.Client, active_policy: dict):
        """
        Test that rejecting an already approved claim fails.
        """
        # Create and approve claim
        create_payload = {
            "policy_id": active_policy["id"],
            "claim_type": "FIRE",
            "description": "Test claim",
            "amount_requested": 10000.00,
            "incident_date": "2026-03-10"
        }
        create_response = client.post("/api/claims", json=create_payload)
        claim_id = create_response.json()["id"]

        # Approve
        client.post(f"/api/claims/{claim_id}/approve", json={"amount_approved": 10000.00})

        # Attempt to reject
        reject_payload = {"reason": "Test rejection"}
        response = client.post(f"/api/claims/{claim_id}/reject", json=reject_payload)

        assert response.status_code == 422
        assert "cannot reject" in response.json()["detail"].lower()

    def test_reject_nonexistent_claim(self, client: httpx.Client):
        """
        Test rejecting a non-existent claim returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"
        reject_payload = {"reason": "Test"}

        response = client.post(f"/api/claims/{fake_id}/reject", json=reject_payload)

        assert response.status_code == 404


class TestClaimBusinessRules:
    """Tests for claim business rules and constraints."""

    def test_claim_number_is_unique(self, client: httpx.Client, active_policy: dict):
        """
        Test that each claim gets a unique claim number.
        """
        # Create two claims
        payload1 = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "First claim",
            "amount_requested": 5000.00,
            "incident_date": "2026-03-15"
        }
        payload2 = {
            "policy_id": active_policy["id"],
            "claim_type": "THEFT",
            "description": "Second claim",
            "amount_requested": 10000.00,
            "incident_date": "2026-03-20"
        }

        response1 = client.post("/api/claims", json=payload1)
        response2 = client.post("/api/claims", json=payload2)

        assert response1.status_code == 201
        assert response2.status_code == 201

        claim_number1 = response1.json()["claim_number"]
        claim_number2 = response2.json()["claim_number"]

        assert claim_number1 != claim_number2

    def test_claim_amount_requested_must_be_positive(self, client: httpx.Client, active_policy: dict):
        """
        Test that claim amount must be positive.
        """
        payload = {
            "policy_id": active_policy["id"],
            "claim_type": "COLLISION",
            "description": "Test claim",
            "amount_requested": -1000.00,  # Negative amount
            "incident_date": "2026-03-15"
        }

        response = client.post("/api/claims", json=payload)

        assert response.status_code == 422
