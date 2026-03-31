"""
End-to-end workflow tests.

These tests verify complete user journeys across multiple API endpoints,
simulating real-world scenarios from the InsureCo PRD/BRD.
"""
import httpx
import pytest
from datetime import date, timedelta
from decimal import Decimal


class TestPolicyholderOnboardingWorkflow:
    """
    User Story: Sarah purchases auto insurance online (FR-1, FR-3, FR-6).

    Steps:
    1. Get auto insurance quote
    2. Create policyholder account
    3. Purchase policy based on quote
    4. Verify policy is active
    5. Download policy documents
    """

    def test_complete_onboarding_workflow(self, client: httpx.Client):
        """Test complete customer onboarding from quote to active policy."""

        # Step 1: Sarah gets an auto insurance quote
        quote_payload = {
            "driver_age": 32,
            "vehicle_year": 2022,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }
        quote_response = client.post("/api/quotes/auto", json=quote_payload)
        assert quote_response.status_code == 200
        quote_data = quote_response.json()
        annual_premium = Decimal(quote_data["premium_annual"])

        # Step 2: Sarah creates a policyholder account
        policyholder_payload = {
            "first_name": "Sarah",
            "last_name": "Connor",
            "email": f"sarah.connor.{date.today().isoformat()}.{id(client)}@example.com",
            "phone": "+1-555-0100",
            "date_of_birth": "1994-05-15",
            "address": "123 Marketing St, Austin, TX 78701"
        }
        ph_response = client.post("/api/policyholders", json=policyholder_payload)
        assert ph_response.status_code == 201
        policyholder = ph_response.json()

        # Step 3: Sarah purchases AUTO policy
        policy_payload = {
            "policyholder_id": policyholder["id"],
            "policy_type": "AUTO",
            "premium_amount": float(annual_premium),
            "coverage_amount": 100000.00,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=365)).isoformat(),
            "status": "ACTIVE"
        }
        policy_response = client.post("/api/policies", json=policy_payload)
        assert policy_response.status_code == 201
        policy = policy_response.json()
        assert policy["status"] == "ACTIVE"
        assert policy["policy_number"].startswith("AUTO-")

        # Step 4: Verify policy is retrievable
        get_policy_response = client.get(f"/api/policies/{policy['id']}")
        assert get_policy_response.status_code == 200

        # Step 5: Check policy documents endpoint
        docs_response = client.get(f"/api/policies/{policy['id']}/documents")
        assert docs_response.status_code == 200
        assert isinstance(docs_response.json(), list)


class TestClaimFilingWorkflow:
    """
    User Story: Sarah files a claim after a collision (FR-2, FR-4).

    Steps:
    1. Create policyholder and active policy
    2. File claim for collision
    3. Upload accident photos
    4. Track claim status
    5. Adjuster approves claim
    """

    def test_complete_claim_filing_workflow(self, client: httpx.Client):
        """Test complete claim filing and approval workflow."""

        # Setup: Create policyholder and active policy
        ph_payload = {
            "first_name": "Michael",
            "last_name": "Scott",
            "email": f"michael.scott.{date.today().isoformat()}.{id(client)}@example.com"
        }
        ph_response = client.post("/api/policyholders", json=ph_payload)
        policyholder_id = ph_response.json()["id"]

        policy_payload = {
            "policyholder_id": policyholder_id,
            "policy_type": "AUTO",
            "premium_amount": 150.00,
            "coverage_amount": 100000.00,
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
            "status": "ACTIVE"
        }
        policy_response = client.post("/api/policies", json=policy_payload)
        policy = policy_response.json()

        # Step 1: File claim
        claim_payload = {
            "policy_id": policy["id"],
            "claim_type": "COLLISION",
            "description": "Rear-ended at intersection while stopped at red light",
            "amount_requested": 8000.00,
            "incident_date": "2026-03-15"
        }
        claim_response = client.post("/api/claims", json=claim_payload)
        assert claim_response.status_code == 201
        claim = claim_response.json()
        assert claim["status"] == "SUBMITTED"
        assert claim["claim_number"].startswith("CLM-")

        # Step 2: Upload accident photo (presign + register)
        presign_payload = {
            "file_name": "accident_damage.jpg",
            "document_type": "CLAIM_PHOTO",
            "content_type": "image/jpeg",
            "claim_id": claim["id"]
        }
        presign_response = client.post("/api/documents/presign", json=presign_payload)
        assert presign_response.status_code == 200
        file_key = presign_response.json()["file_key"]

        # Register document after "upload"
        register_payload = {
            "file_key": file_key,
            "file_name": "accident_damage.jpg",
            "document_type": "CLAIM_PHOTO",
            "claim_id": claim["id"]
        }
        doc_response = client.post("/api/documents", json=register_payload)
        assert doc_response.status_code == 201

        # Step 3: Update claim to under review
        update_response = client.put(
            f"/api/claims/{claim['id']}",
            json={"status": "UNDER_REVIEW"}
        )
        assert update_response.status_code == 200

        # Step 4: Adjuster approves claim
        approve_payload = {
            "amount_approved": 7500.00,
            "notes": "Approved with deductible adjustment"
        }
        approve_response = client.post(
            f"/api/claims/{claim['id']}/approve",
            json=approve_payload
        )
        assert approve_response.status_code == 200
        approved_claim = approve_response.json()
        assert approved_claim["status"] == "APPROVED"
        assert approved_claim["amount_approved"] == "7500.00"

        # Step 5: Verify final claim status
        final_claim_response = client.get(f"/api/claims/{claim['id']}")
        assert final_claim_response.status_code == 200
        final_claim = final_claim_response.json()
        assert final_claim["status"] == "APPROVED"


class TestMultiPolicyCustomerWorkflow:
    """
    User Story: Agent creates customer with multiple policies (FR-1, FR-6).

    Steps:
    1. Agent creates policyholder
    2. Agent gets quotes for AUTO and HOME
    3. Agent creates AUTO policy
    4. Agent creates HOME policy
    5. Verify customer has multiple policies
    """

    def test_multi_policy_customer_workflow(self, client: httpx.Client):
        """Test customer with multiple insurance policies."""

        # Step 1: Agent creates policyholder
        ph_payload = {
            "first_name": "David",
            "last_name": "Miller",
            "email": f"david.miller.{date.today().isoformat()}.{id(client)}@example.com",
            "phone": "+1-555-0200",
            "date_of_birth": "1980-08-20",
            "address": "789 Suburban Dr, Chicago, IL 60601"
        }
        ph_response = client.post("/api/policyholders", json=ph_payload)
        assert ph_response.status_code == 201
        policyholder = ph_response.json()

        # Step 2: Get AUTO quote
        auto_quote_payload = {
            "driver_age": 46,
            "vehicle_year": 2023,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 15000
        }
        auto_quote_response = client.post("/api/quotes/auto", json=auto_quote_payload)
        assert auto_quote_response.status_code == 200
        auto_premium = Decimal(auto_quote_response.json()["premium_annual"])

        # Step 3: Get HOME quote
        home_quote_payload = {
            "home_value": 450000,
            "location_risk": "LOW",
            "home_age_years": 8,
            "coverage_type": "PREMIUM"
        }
        home_quote_response = client.post("/api/quotes/home", json=home_quote_payload)
        assert home_quote_response.status_code == 200
        home_premium = Decimal(home_quote_response.json()["premium_annual"])

        # Step 4: Create AUTO policy
        auto_policy_payload = {
            "policyholder_id": policyholder["id"],
            "policy_type": "AUTO",
            "premium_amount": float(auto_premium),
            "coverage_amount": 100000.00,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=365)).isoformat(),
            "status": "ACTIVE"
        }
        auto_policy_response = client.post("/api/policies", json=auto_policy_payload)
        assert auto_policy_response.status_code == 201
        auto_policy = auto_policy_response.json()

        # Step 5: Create HOME policy
        home_policy_payload = {
            "policyholder_id": policyholder["id"],
            "policy_type": "HOME",
            "premium_amount": float(home_premium),
            "coverage_amount": 450000.00,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=365)).isoformat(),
            "status": "ACTIVE"
        }
        home_policy_response = client.post("/api/policies", json=home_policy_payload)
        assert home_policy_response.status_code == 201
        home_policy = home_policy_response.json()

        # Step 6: Verify customer has both policies
        policies_response = client.get(f"/api/policies?policyholder_id={policyholder['id']}")
        assert policies_response.status_code == 200
        policies = policies_response.json()
        assert len(policies) >= 2

        policy_types = {p["policy_type"] for p in policies if p["policyholder_id"] == policyholder["id"]}
        assert "AUTO" in policy_types
        assert "HOME" in policy_types


class TestPolicyRenewalWorkflow:
    """
    User Story: Customer renews expiring policy (FR-1.5).

    Steps:
    1. Create policy expiring soon
    2. Get renewal quote
    3. Create new policy for renewal
    4. Update old policy to EXPIRED
    """

    def test_policy_renewal_workflow(self, client: httpx.Client):
        """Test policy renewal process."""

        # Setup: Create policyholder
        ph_payload = {
            "first_name": "Renewal",
            "last_name": "Customer",
            "email": f"renewal.{date.today().isoformat()}.{id(client)}@example.com"
        }
        ph_response = client.post("/api/policyholders", json=ph_payload)
        policyholder_id = ph_response.json()["id"]

        # Step 1: Create policy expiring in 30 days
        expiry_date = date.today() + timedelta(days=30)
        old_policy_payload = {
            "policyholder_id": policyholder_id,
            "policy_type": "AUTO",
            "premium_amount": 120.00,
            "coverage_amount": 75000.00,
            "start_date": (date.today() - timedelta(days=335)).isoformat(),
            "end_date": expiry_date.isoformat(),
            "status": "ACTIVE"
        }
        old_policy_response = client.post("/api/policies", json=old_policy_payload)
        assert old_policy_response.status_code == 201
        old_policy = old_policy_response.json()

        # Step 2: Get renewal quote (may have adjusted premium)
        renewal_quote_payload = {
            "driver_age": 45,
            "vehicle_year": 2023,
            "coverage_type": "COMPREHENSIVE",
            "annual_mileage": 12000
        }
        quote_response = client.post("/api/quotes/auto", json=renewal_quote_payload)
        assert quote_response.status_code == 200
        renewal_premium = Decimal(quote_response.json()["premium_annual"])

        # Step 3: Create new policy (renewal)
        new_policy_payload = {
            "policyholder_id": policyholder_id,
            "policy_type": "AUTO",
            "premium_amount": float(renewal_premium),
            "coverage_amount": 75000.00,
            "start_date": expiry_date.isoformat(),
            "end_date": (expiry_date + timedelta(days=365)).isoformat(),
            "status": "ACTIVE"
        }
        new_policy_response = client.post("/api/policies", json=new_policy_payload)
        assert new_policy_response.status_code == 201
        new_policy = new_policy_response.json()
        assert new_policy["policy_number"] != old_policy["policy_number"]

        # Step 4: Update old policy to EXPIRED
        update_response = client.put(
            f"/api/policies/{old_policy['id']}",
            json={"status": "EXPIRED"}
        )
        assert update_response.status_code == 200
        updated_old_policy = update_response.json()
        assert updated_old_policy["status"] == "EXPIRED"


class TestClaimRejectionWorkflow:
    """
    User Story: Adjuster rejects fraudulent claim (FR-2).

    Steps:
    1. Create policy and file suspicious claim
    2. Adjuster reviews claim
    3. Adjuster rejects claim with reason
    4. Verify claim cannot be approved after rejection
    """

    def test_claim_rejection_workflow(self, client: httpx.Client):
        """Test claim rejection by adjuster."""

        # Setup: Create policyholder and policy
        ph_payload = {
            "first_name": "Suspicious",
            "last_name": "Claimant",
            "email": f"suspicious.{date.today().isoformat()}.{id(client)}@example.com"
        }
        ph_response = client.post("/api/policyholders", json=ph_payload)
        policyholder_id = ph_response.json()["id"]

        policy_payload = {
            "policyholder_id": policyholder_id,
            "policy_type": "AUTO",
            "premium_amount": 100.00,
            "coverage_amount": 50000.00,
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
            "status": "ACTIVE"
        }
        policy_response = client.post("/api/policies", json=policy_payload)
        policy_id = policy_response.json()["id"]

        # Step 1: File suspicious claim (requesting maximum coverage)
        claim_payload = {
            "policy_id": policy_id,
            "claim_type": "THEFT",
            "description": "Vehicle stolen from parking lot, no witnesses",
            "amount_requested": 50000.00,
            "incident_date": "2026-03-15"
        }
        claim_response = client.post("/api/claims", json=claim_payload)
        assert claim_response.status_code == 201
        claim = claim_response.json()

        # Step 2: Adjuster reviews and rejects
        reject_payload = {
            "reason": "Inconsistencies in claim details and police report not filed within required timeframe"
        }
        reject_response = client.post(
            f"/api/claims/{claim['id']}/reject",
            json=reject_payload
        )
        assert reject_response.status_code == 200
        rejected_claim = reject_response.json()
        assert rejected_claim["status"] == "REJECTED"

        # Step 3: Verify claim cannot be approved after rejection
        approve_payload = {"amount_approved": 25000.00}
        approve_response = client.post(
            f"/api/claims/{claim['id']}/approve",
            json=approve_payload
        )
        assert approve_response.status_code == 422
        assert "cannot approve" in approve_response.json()["detail"].lower()


class TestQuoteComparisonWorkflow:
    """
    User Story: Customer compares different coverage options (FR-3).

    Steps:
    1. Get LIABILITY quote
    2. Get COLLISION quote
    3. Get COMPREHENSIVE quote
    4. Verify price ordering
    """

    def test_auto_coverage_comparison_workflow(self, client: httpx.Client):
        """Test comparing different auto coverage options."""

        # Common parameters
        base_params = {
            "driver_age": 35,
            "vehicle_year": 2022,
            "annual_mileage": 12000
        }

        # Step 1: Get LIABILITY quote (cheapest)
        liability_payload = {**base_params, "coverage_type": "LIABILITY"}
        liability_response = client.post("/api/quotes/auto", json=liability_payload)
        assert liability_response.status_code == 200
        liability_annual = Decimal(liability_response.json()["premium_annual"])

        # Step 2: Get COLLISION quote (mid-tier)
        collision_payload = {**base_params, "coverage_type": "COLLISION"}
        collision_response = client.post("/api/quotes/auto", json=collision_payload)
        assert collision_response.status_code == 200
        collision_annual = Decimal(collision_response.json()["premium_annual"])

        # Step 3: Get COMPREHENSIVE quote (most expensive)
        comprehensive_payload = {**base_params, "coverage_type": "COMPREHENSIVE"}
        comprehensive_response = client.post("/api/quotes/auto", json=comprehensive_payload)
        assert comprehensive_response.status_code == 200
        comprehensive_annual = Decimal(comprehensive_response.json()["premium_annual"])

        # Step 4: Verify price ordering
        assert liability_annual < collision_annual < comprehensive_annual


class TestDocumentComplianceWorkflow:
    """
    User Story: Claims adjuster reviews claim with multiple documents (FR-4).

    Steps:
    1. File claim
    2. Upload multiple supporting documents
    3. Retrieve all documents for review
    4. Approve claim based on documentation
    """

    def test_claim_documentation_workflow(self, client: httpx.Client):
        """Test complete claim documentation workflow."""

        # Setup: Create policyholder and policy
        ph_payload = {
            "first_name": "Documentation",
            "last_name": "Test",
            "email": f"docs.{date.today().isoformat()}.{id(client)}@example.com"
        }
        ph_response = client.post("/api/policyholders", json=ph_payload)
        policyholder_id = ph_response.json()["id"]

        policy_payload = {
            "policyholder_id": policyholder_id,
            "policy_type": "HOME",
            "premium_amount": 200.00,
            "coverage_amount": 300000.00,
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
            "status": "ACTIVE"
        }
        policy_response = client.post("/api/policies", json=policy_payload)
        policy_id = policy_response.json()["id"]

        # Step 1: File claim
        claim_payload = {
            "policy_id": policy_id,
            "claim_type": "FIRE",
            "description": "Kitchen fire caused by electrical fault",
            "amount_requested": 25000.00,
            "incident_date": "2026-03-10"
        }
        claim_response = client.post("/api/claims", json=claim_payload)
        claim = claim_response.json()

        # Step 2: Upload multiple documents
        documents = [
            ("fire_damage_photo1.jpg", "CLAIM_PHOTO", "image/jpeg"),
            ("fire_damage_photo2.jpg", "CLAIM_PHOTO", "image/jpeg"),
            ("fire_department_report.pdf", "POLICE_REPORT", "application/pdf"),
            ("repair_estimate.pdf", "INVOICE", "application/pdf")
        ]

        document_ids = []
        for file_name, doc_type, content_type in documents:
            # Presign
            presign_payload = {
                "file_name": file_name,
                "document_type": doc_type,
                "content_type": content_type,
                "claim_id": claim["id"]
            }
            presign_response = client.post("/api/documents/presign", json=presign_payload)
            file_key = presign_response.json()["file_key"]

            # Register
            register_payload = {
                "file_key": file_key,
                "file_name": file_name,
                "document_type": doc_type,
                "claim_id": claim["id"]
            }
            register_response = client.post("/api/documents", json=register_payload)
            assert register_response.status_code == 201
            document_ids.append(register_response.json()["id"])

        # Step 3: Adjuster retrieves claim details
        claim_details_response = client.get(f"/api/claims/{claim['id']}")
        assert claim_details_response.status_code == 200

        # Step 4: Verify all documents are accessible
        assert len(document_ids) == 4
        for doc_id in document_ids:
            doc_response = client.get(f"/api/documents/{doc_id}")
            assert doc_response.status_code == 200
            assert "download_url" in doc_response.json()

        # Step 5: Approve claim after reviewing documentation
        approve_payload = {"amount_approved": 24000.00}
        approve_response = client.post(
            f"/api/claims/{claim['id']}/approve",
            json=approve_payload
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["status"] == "APPROVED"
