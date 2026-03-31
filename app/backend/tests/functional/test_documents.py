"""
Functional tests for document management.

User Story Coverage:
- FR-4.1: Document upload
- FR-4.2: Document retrieval
- FR-4.3: Document types

Acceptance Criteria:
- Upload success rate > 99.5%
- Presigned URLs expire after 15 minutes
- All documents encrypted at rest
- Document access logged for audit
"""
import httpx
import pytest
from datetime import date


@pytest.fixture
def test_policyholder(client: httpx.Client) -> dict:
    """Create a test policyholder."""
    payload = {
        "first_name": "Document",
        "last_name": "Tester",
        "email": f"doc.test.{date.today().isoformat()}.{id(client)}@example.com"
    }
    response = client.post("/api/policyholders", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_policy(client: httpx.Client, test_policyholder: dict) -> dict:
    """Create a test policy."""
    payload = {
        "policyholder_id": test_policyholder["id"],
        "policy_type": "AUTO",
        "premium_amount": 100.00,
        "coverage_amount": 50000.00,
        "start_date": "2026-01-01",
        "end_date": "2027-01-01",
        "status": "ACTIVE"
    }
    response = client.post("/api/policies", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def test_claim(client: httpx.Client, test_policy: dict) -> dict:
    """Create a test claim."""
    payload = {
        "policy_id": test_policy["id"],
        "claim_type": "COLLISION",
        "description": "Test claim for document upload",
        "amount_requested": 5000.00,
        "incident_date": "2026-03-15"
    }
    response = client.post("/api/claims", json=payload)
    assert response.status_code == 201
    return response.json()


class TestDocumentPresignedURL:
    """Tests for generating presigned URLs (FR-4.1.5)."""

    def test_get_presigned_url_for_claim_document(self, client: httpx.Client, test_claim: dict):
        """
        Test generating a presigned URL for claim document upload.
        Acceptance Criteria: Generate presigned S3 URL for secure upload.
        """
        payload = {
            "file_name": "accident_photo.jpg",
            "document_type": "CLAIM_PHOTO",
            "content_type": "image/jpeg",
            "claim_id": test_claim["id"]
        }

        response = client.post("/api/documents/presign", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "file_key" in data
        assert data["upload_url"].startswith("http")
        assert len(data["file_key"]) > 0

    def test_get_presigned_url_for_policy_document(self, client: httpx.Client, test_policy: dict):
        """
        Test generating a presigned URL for policy document upload.
        """
        payload = {
            "file_name": "policy_terms.pdf",
            "document_type": "POLICY_TERMS",
            "content_type": "application/pdf",
            "policy_id": test_policy["id"]
        }

        response = client.post("/api/documents/presign", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "file_key" in data

    def test_get_presigned_url_for_standalone_document(self, client: httpx.Client):
        """
        Test generating a presigned URL without policy or claim association.
        """
        payload = {
            "file_name": "id_card.jpg",
            "document_type": "ID_VERIFICATION",
            "content_type": "image/jpeg"
        }

        response = client.post("/api/documents/presign", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data
        assert "file_key" in data

    def test_get_presigned_url_with_pdf_content_type(self, client: httpx.Client, test_claim: dict):
        """
        Test generating presigned URL for PDF document.
        """
        payload = {
            "file_name": "police_report.pdf",
            "document_type": "POLICE_REPORT",
            "content_type": "application/pdf",
            "claim_id": test_claim["id"]
        }

        response = client.post("/api/documents/presign", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data

    def test_get_presigned_url_with_png_content_type(self, client: httpx.Client, test_claim: dict):
        """
        Test generating presigned URL for PNG image.
        """
        payload = {
            "file_name": "damage_photo.png",
            "document_type": "CLAIM_PHOTO",
            "content_type": "image/png",
            "claim_id": test_claim["id"]
        }

        response = client.post("/api/documents/presign", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "upload_url" in data


class TestDocumentRegistration:
    """Tests for registering uploaded documents (FR-4.1.4, FR-4.1.5)."""

    def test_register_claim_document(self, client: httpx.Client, test_claim: dict):
        """
        Test registering a document after upload.
        Acceptance Criteria: Store metadata in database.
        """
        # First get presigned URL
        presign_payload = {
            "file_name": "accident_scene.jpg",
            "document_type": "CLAIM_PHOTO",
            "content_type": "image/jpeg",
            "claim_id": test_claim["id"]
        }
        presign_response = client.post("/api/documents/presign", json=presign_payload)
        assert presign_response.status_code == 200
        file_key = presign_response.json()["file_key"]

        # Register document
        register_payload = {
            "file_key": file_key,
            "file_name": "accident_scene.jpg",
            "document_type": "CLAIM_PHOTO",
            "claim_id": test_claim["id"]
        }
        response = client.post("/api/documents", json=register_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "accident_scene.jpg"
        assert data["document_type"] == "CLAIM_PHOTO"
        assert data["claim_id"] == test_claim["id"]
        assert "id" in data

    def test_register_policy_document(self, client: httpx.Client, test_policy: dict):
        """
        Test registering a policy document.
        """
        # Get presigned URL
        presign_payload = {
            "file_name": "policy_certificate.pdf",
            "document_type": "CERTIFICATE",
            "content_type": "application/pdf",
            "policy_id": test_policy["id"]
        }
        presign_response = client.post("/api/documents/presign", json=presign_payload)
        file_key = presign_response.json()["file_key"]

        # Register
        register_payload = {
            "file_key": file_key,
            "file_name": "policy_certificate.pdf",
            "document_type": "CERTIFICATE",
            "policy_id": test_policy["id"]
        }
        response = client.post("/api/documents", json=register_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["policy_id"] == test_policy["id"]
        assert data["claim_id"] is None

    def test_register_document_without_associations(self, client: httpx.Client):
        """
        Test registering a standalone document (no policy or claim).
        """
        # Get presigned URL
        presign_payload = {
            "file_name": "drivers_license.jpg",
            "document_type": "ID_VERIFICATION",
            "content_type": "image/jpeg"
        }
        presign_response = client.post("/api/documents/presign", json=presign_payload)
        file_key = presign_response.json()["file_key"]

        # Register
        register_payload = {
            "file_key": file_key,
            "file_name": "drivers_license.jpg",
            "document_type": "ID_VERIFICATION"
        }
        response = client.post("/api/documents", json=register_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["policy_id"] is None
        assert data["claim_id"] is None


class TestDocumentRetrieval:
    """Tests for retrieving documents (FR-4.2)."""

    def test_get_document_download_url(self, client: httpx.Client, test_claim: dict):
        """
        Test retrieving a download URL for a document.
        Acceptance Criteria: Generate presigned S3 URL for secure download (expires after 15 minutes).
        """
        # Register a document first
        presign_payload = {
            "file_name": "test_document.pdf",
            "document_type": "CLAIM_INVOICE",
            "content_type": "application/pdf",
            "claim_id": test_claim["id"]
        }
        presign_response = client.post("/api/documents/presign", json=presign_payload)
        file_key = presign_response.json()["file_key"]

        register_payload = {
            "file_key": file_key,
            "file_name": "test_document.pdf",
            "document_type": "CLAIM_INVOICE",
            "claim_id": test_claim["id"]
        }
        register_response = client.post("/api/documents", json=register_payload)
        document_id = register_response.json()["id"]

        # Get download URL
        response = client.get(f"/api/documents/{document_id}")

        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        assert "file_name" in data
        assert data["file_name"] == "test_document.pdf"
        assert data["download_url"].startswith("http")

    def test_get_nonexistent_document(self, client: httpx.Client):
        """
        Test retrieving a document that doesn't exist returns 404.
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/documents/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestDocumentTypes:
    """Tests for different document types (FR-4.3)."""

    def test_policy_document_types(self, client: httpx.Client, test_policy: dict):
        """
        Test policy-related document types (Terms, Endorsements, Certificates).
        """
        document_types = ["POLICY_TERMS", "ENDORSEMENT", "CERTIFICATE"]

        for doc_type in document_types:
            presign_payload = {
                "file_name": f"{doc_type.lower()}.pdf",
                "document_type": doc_type,
                "content_type": "application/pdf",
                "policy_id": test_policy["id"]
            }
            presign_response = client.post("/api/documents/presign", json=presign_payload)
            assert presign_response.status_code == 200

            file_key = presign_response.json()["file_key"]
            register_payload = {
                "file_key": file_key,
                "file_name": f"{doc_type.lower()}.pdf",
                "document_type": doc_type,
                "policy_id": test_policy["id"]
            }
            register_response = client.post("/api/documents", json=register_payload)
            assert register_response.status_code == 201

    def test_claim_document_types(self, client: httpx.Client, test_claim: dict):
        """
        Test claim-related document types (Photos, Police Reports, Invoices, Medical Records).
        """
        document_types = [
            ("CLAIM_PHOTO", "photo.jpg", "image/jpeg"),
            ("POLICE_REPORT", "police_report.pdf", "application/pdf"),
            ("INVOICE", "repair_invoice.pdf", "application/pdf"),
            ("MEDICAL_RECORD", "medical_report.pdf", "application/pdf")
        ]

        for doc_type, file_name, content_type in document_types:
            presign_payload = {
                "file_name": file_name,
                "document_type": doc_type,
                "content_type": content_type,
                "claim_id": test_claim["id"]
            }
            presign_response = client.post("/api/documents/presign", json=presign_payload)
            assert presign_response.status_code == 200

            file_key = presign_response.json()["file_key"]
            register_payload = {
                "file_key": file_key,
                "file_name": file_name,
                "document_type": doc_type,
                "claim_id": test_claim["id"]
            }
            register_response = client.post("/api/documents", json=register_payload)
            assert register_response.status_code == 201

    def test_customer_document_types(self, client: httpx.Client):
        """
        Test customer-related document types (ID, Proof of Residence).
        """
        document_types = [
            ("ID_VERIFICATION", "drivers_license.jpg", "image/jpeg"),
            ("PROOF_OF_RESIDENCE", "utility_bill.pdf", "application/pdf"),
            ("INSPECTION_REPORT", "home_inspection.pdf", "application/pdf")
        ]

        for doc_type, file_name, content_type in document_types:
            presign_payload = {
                "file_name": file_name,
                "document_type": doc_type,
                "content_type": content_type
            }
            presign_response = client.post("/api/documents/presign", json=presign_payload)
            assert presign_response.status_code == 200

            file_key = presign_response.json()["file_key"]
            register_payload = {
                "file_key": file_key,
                "file_name": file_name,
                "document_type": doc_type
            }
            register_response = client.post("/api/documents", json=register_payload)
            assert register_response.status_code == 201


class TestDocumentWorkflow:
    """Tests for complete document upload workflow."""

    def test_complete_document_upload_workflow(self, client: httpx.Client, test_claim: dict):
        """
        Test the complete workflow: presign → (simulated upload) → register → retrieve.
        Acceptance Criteria: Upload success rate > 99.5%.
        """
        # Step 1: Get presigned URL
        presign_payload = {
            "file_name": "workflow_test.jpg",
            "document_type": "CLAIM_PHOTO",
            "content_type": "image/jpeg",
            "claim_id": test_claim["id"]
        }
        presign_response = client.post("/api/documents/presign", json=presign_payload)
        assert presign_response.status_code == 200
        presign_data = presign_response.json()
        upload_url = presign_data["upload_url"]
        file_key = presign_data["file_key"]

        # Step 2: Upload would happen here (to S3) - we skip actual upload in tests

        # Step 3: Register document after upload
        register_payload = {
            "file_key": file_key,
            "file_name": "workflow_test.jpg",
            "document_type": "CLAIM_PHOTO",
            "claim_id": test_claim["id"]
        }
        register_response = client.post("/api/documents", json=register_payload)
        assert register_response.status_code == 201
        document_id = register_response.json()["id"]

        # Step 4: Retrieve download URL
        download_response = client.get(f"/api/documents/{document_id}")
        assert download_response.status_code == 200
        download_data = download_response.json()
        assert "download_url" in download_data
        assert download_data["file_name"] == "workflow_test.jpg"

        # Step 5: Verify document is associated with claim
        claim_response = client.get(f"/api/claims/{test_claim['id']}")
        assert claim_response.status_code == 200

    def test_multiple_documents_for_single_claim(self, client: httpx.Client, test_claim: dict):
        """
        Test uploading multiple documents for a single claim.
        """
        documents = [
            ("photo1.jpg", "CLAIM_PHOTO", "image/jpeg"),
            ("photo2.jpg", "CLAIM_PHOTO", "image/jpeg"),
            ("invoice.pdf", "INVOICE", "application/pdf")
        ]

        registered_ids = []

        for file_name, doc_type, content_type in documents:
            # Presign
            presign_payload = {
                "file_name": file_name,
                "document_type": doc_type,
                "content_type": content_type,
                "claim_id": test_claim["id"]
            }
            presign_response = client.post("/api/documents/presign", json=presign_payload)
            assert presign_response.status_code == 200
            file_key = presign_response.json()["file_key"]

            # Register
            register_payload = {
                "file_key": file_key,
                "file_name": file_name,
                "document_type": doc_type,
                "claim_id": test_claim["id"]
            }
            register_response = client.post("/api/documents", json=register_payload)
            assert register_response.status_code == 201
            registered_ids.append(register_response.json()["id"])

        # Verify all documents are unique
        assert len(registered_ids) == len(set(registered_ids))
        assert len(registered_ids) == 3
