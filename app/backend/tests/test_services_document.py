"""Unit tests for src.services.document_service module."""
from unittest.mock import MagicMock, patch
import uuid

import pytest

from src.services.document_service import (
    _build_s3_key,
    generate_presigned_url,
    generate_download_url,
)


class TestBuildS3Key:
    """Test S3 key building logic."""

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_with_claim_id(self, mock_uuid):
        """Test S3 key generation for claim document."""
        mock_uuid.return_value = MagicMock(
            __getitem__=lambda self, key: "abcd1234"[:key]
        )
        mock_uuid.return_value.__str__ = lambda self: "abcd1234-5678-90ef-ghij-klmnopqrstuv"

        result = _build_s3_key(
            file_name="accident_photo.jpg",
            document_type="INCIDENT_PHOTO",
            claim_id="claim-123",
        )

        assert result.startswith("claims/claim-123/INCIDENT_PHOTO/")
        assert "accident_photo.jpg" in result

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_with_policy_id(self, mock_uuid):
        """Test S3 key generation for policy document."""
        mock_uuid.return_value = MagicMock(
            __getitem__=lambda self, key: "xyz12345"[:key]
        )
        mock_uuid.return_value.__str__ = lambda self: "xyz12345-abcd-efgh-ijkl-mnopqrstuvwx"

        result = _build_s3_key(
            file_name="policy_doc.pdf",
            document_type="POLICY_DOCUMENT",
            policy_id="policy-456",
        )

        assert result.startswith("policies/policy-456/POLICY_DOCUMENT/")
        assert "policy_doc.pdf" in result

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_without_claim_or_policy(self, mock_uuid):
        """Test S3 key generation for general document."""
        mock_uuid.return_value = MagicMock(
            __getitem__=lambda self, key: "general1"[:key]
        )
        mock_uuid.return_value.__str__ = lambda self: "general1-2345-6789-abcd-efghijklmnop"

        result = _build_s3_key(
            file_name="general_doc.pdf", document_type="GENERAL"
        )

        assert result.startswith("documents/GENERAL/")
        assert "general_doc.pdf" in result

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_replaces_spaces(self, mock_uuid):
        """Test S3 key replaces spaces in filename with underscores."""
        mock_uuid.return_value = MagicMock(
            __getitem__=lambda self, key: "testid12"[:key]
        )
        mock_uuid.return_value.__str__ = lambda self: "testid12-3456-7890-abcd-efghijklmnop"

        result = _build_s3_key(
            file_name="my test file with spaces.pdf",
            document_type="TEST",
            claim_id="claim-789",
        )

        assert "my_test_file_with_spaces.pdf" in result
        assert " " not in result

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_preserves_extension(self, mock_uuid):
        """Test S3 key preserves file extension."""
        mock_uuid.return_value = MagicMock(
            __getitem__=lambda self, key: "fileid99"[:key]
        )
        mock_uuid.return_value.__str__ = lambda self: "fileid99-abcd-efgh-ijkl-mnopqrstuvwx"

        result = _build_s3_key(
            file_name="document.docx", document_type="CONTRACT", policy_id="pol-123"
        )

        assert result.endswith(".docx")

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_claim_takes_precedence(self, mock_uuid):
        """Test S3 key uses claim_id when both claim and policy provided."""
        mock_uuid.return_value = MagicMock(
            __getitem__=lambda self, key: "both1234"[:key]
        )
        mock_uuid.return_value.__str__ = lambda self: "both1234-5678-90ab-cdef-ghijklmnopqr"

        result = _build_s3_key(
            file_name="file.pdf",
            document_type="MIXED",
            claim_id="claim-111",
            policy_id="policy-222",
        )

        assert result.startswith("claims/claim-111/")
        assert "policies/" not in result


class TestGeneratePresignedUrl:
    """Test presigned URL generation."""

    @patch("src.services.document_service.s3_client")
    @patch("src.services.document_service._build_s3_key")
    def test_generate_presigned_url_for_upload(self, mock_build_key, mock_s3_client):
        """Test presigned URL generation for file upload."""
        mock_build_key.return_value = "claims/claim-123/PHOTO/abc_photo.jpg"
        mock_s3_client.generate_presigned_url.return_value = (
            "https://s3.amazonaws.com/bucket/presigned-url"
        )

        upload_url, file_key = generate_presigned_url(
            file_name="photo.jpg",
            document_type="PHOTO",
            content_type="image/jpeg",
            claim_id="claim-123",
        )

        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "insureco-documents",
                "Key": "claims/claim-123/PHOTO/abc_photo.jpg",
                "ContentType": "image/jpeg",
            },
            ExpiresIn=3600,
            HttpMethod="PUT",
        )
        assert upload_url == "https://s3.amazonaws.com/bucket/presigned-url"
        assert file_key == "claims/claim-123/PHOTO/abc_photo.jpg"

    @patch("src.services.document_service.s3_client")
    @patch("src.services.document_service._build_s3_key")
    def test_generate_presigned_url_custom_expiry(self, mock_build_key, mock_s3_client):
        """Test presigned URL with custom expiry time."""
        mock_build_key.return_value = "documents/TEST/file.pdf"
        mock_s3_client.generate_presigned_url.return_value = "https://s3.url"

        upload_url, file_key = generate_presigned_url(
            file_name="file.pdf",
            document_type="TEST",
            content_type="application/pdf",
            expiry_seconds=7200,
        )

        call_args = mock_s3_client.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 7200

    @patch("src.services.document_service.s3_client")
    @patch("src.services.document_service._build_s3_key")
    def test_generate_presigned_url_with_policy_id(self, mock_build_key, mock_s3_client):
        """Test presigned URL generation with policy ID."""
        mock_build_key.return_value = "policies/pol-456/CONTRACT/contract.pdf"
        mock_s3_client.generate_presigned_url.return_value = "https://s3.url"

        upload_url, file_key = generate_presigned_url(
            file_name="contract.pdf",
            document_type="CONTRACT",
            content_type="application/pdf",
            policy_id="pol-456",
        )

        mock_build_key.assert_called_once_with(
            "contract.pdf", "CONTRACT", None, "pol-456"
        )
        assert file_key == "policies/pol-456/CONTRACT/contract.pdf"

    @patch("src.services.document_service.s3_client")
    @patch("src.services.document_service._build_s3_key")
    def test_generate_presigned_url_default_expiry(self, mock_build_key, mock_s3_client):
        """Test presigned URL uses default expiry of 3600 seconds."""
        mock_build_key.return_value = "documents/test.pdf"
        mock_s3_client.generate_presigned_url.return_value = "https://s3.url"

        upload_url, file_key = generate_presigned_url(
            file_name="test.pdf",
            document_type="TEST",
            content_type="application/pdf",
        )

        call_args = mock_s3_client.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 3600


class TestGenerateDownloadUrl:
    """Test download URL generation."""

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_default_expiry(self, mock_s3_client):
        """Test download URL generation with default expiry."""
        mock_s3_client.generate_presigned_url.return_value = (
            "https://s3.amazonaws.com/bucket/download-url"
        )

        download_url = generate_download_url("claims/claim-123/PHOTO/photo.jpg")

        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": "insureco-documents",
                "Key": "claims/claim-123/PHOTO/photo.jpg",
            },
            ExpiresIn=900,
        )
        assert download_url == "https://s3.amazonaws.com/bucket/download-url"

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_custom_expiry(self, mock_s3_client):
        """Test download URL generation with custom expiry."""
        mock_s3_client.generate_presigned_url.return_value = "https://s3.url"

        download_url = generate_download_url(
            "policies/pol-789/doc.pdf", expiry_seconds=1800
        )

        call_args = mock_s3_client.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1800
        assert call_args[1]["Params"]["Key"] == "policies/pol-789/doc.pdf"

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_with_special_characters(self, mock_s3_client):
        """Test download URL handles file keys with special characters."""
        mock_s3_client.generate_presigned_url.return_value = "https://s3.url"

        download_url = generate_download_url(
            "documents/TEST/my_file-v2 (1).pdf"
        )

        call_args = mock_s3_client.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == "documents/TEST/my_file-v2 (1).pdf"
        assert download_url == "https://s3.url"

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_empty_key(self, mock_s3_client):
        """Test download URL handles empty file key."""
        mock_s3_client.generate_presigned_url.return_value = "https://s3.url"

        download_url = generate_download_url("")

        call_args = mock_s3_client.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == ""
