"""Tests for src/services/document_service.py"""
import pytest
from unittest.mock import MagicMock, patch

from src.services.document_service import (
    _build_s3_key,
    generate_presigned_url,
    generate_download_url,
)


class TestBuildS3Key:
    """Test _build_s3_key helper function."""

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_claim_id(self, mock_uuid):
        """Test S3 key generation with claim_id."""
        mock_uuid.return_value = MagicMock(hex="abcd1234efgh5678ijkl")
        mock_uuid.return_value.__str__ = lambda self: "abcd1234-efgh-5678-ijkl-90abcdef1234"

        key = _build_s3_key("test_document.pdf", "CLAIM_PROOF", claim_id="claim-123")

        assert key.startswith("claims/claim-123/CLAIM_PROOF/")
        assert "test_document.pdf" in key
        assert key.count("/") == 3

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_policy_id(self, mock_uuid):
        """Test S3 key generation with policy_id."""
        mock_uuid.return_value = MagicMock(hex="abcd1234")
        mock_uuid.return_value.__str__ = lambda self: "abcd1234-efgh-5678-ijkl-90abcdef1234"

        key = _build_s3_key("policy_doc.pdf", "POLICY_TERMS", policy_id="policy-456")

        assert key.startswith("policies/policy-456/POLICY_TERMS/")
        assert "policy_doc.pdf" in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_without_ids(self, mock_uuid):
        """Test S3 key generation without claim_id or policy_id."""
        mock_uuid.return_value = MagicMock(hex="abcd1234")
        mock_uuid.return_value.__str__ = lambda self: "abcd1234-efgh-5678-ijkl-90abcdef1234"

        key = _build_s3_key("general_doc.pdf", "GENERAL")

        assert key.startswith("documents/GENERAL/")
        assert "general_doc.pdf" in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_replaces_spaces(self, mock_uuid):
        """Test that spaces in filename are replaced with underscores."""
        mock_uuid.return_value = MagicMock(hex="abcd1234")
        mock_uuid.return_value.__str__ = lambda self: "abcd1234-efgh-5678-ijkl-90abcdef1234"

        key = _build_s3_key("my test document.pdf", "TEST")

        assert "my_test_document.pdf" in key
        assert " " not in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_empty_filename(self, mock_uuid):
        """Test with empty filename (edge case)."""
        mock_uuid.return_value = MagicMock(hex="abcd1234")
        mock_uuid.return_value.__str__ = lambda self: "abcd1234-efgh-5678-ijkl-90abcdef1234"

        key = _build_s3_key("", "EMPTY_TEST")

        assert "EMPTY_TEST" in key
        # Should still have unique ID prefix
        assert key.count("/") >= 1

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_precedence_claim_over_policy(self, mock_uuid):
        """Test that claim_id takes precedence over policy_id."""
        mock_uuid.return_value = MagicMock(hex="abcd1234")
        mock_uuid.return_value.__str__ = lambda self: "abcd1234-efgh-5678-ijkl-90abcdef1234"

        key = _build_s3_key("doc.pdf", "TYPE", claim_id="claim-1", policy_id="policy-1")

        # Should use claim_id path
        assert key.startswith("claims/claim-1/")
        assert "policies" not in key


class TestGeneratePresignedUrl:
    """Test generate_presigned_url function."""

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_success(self, mock_build_key, mock_s3):
        """Test successful presigned URL generation."""
        mock_build_key.return_value = "test/path/document.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"

        url, key = generate_presigned_url(
            "document.pdf",
            "TEST_TYPE",
            "application/pdf"
        )

        assert url == "https://s3.example.com/presigned"
        assert key == "test/path/document.pdf"
        mock_s3.generate_presigned_url.assert_called_once()

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_with_claim_id(self, mock_build_key, mock_s3):
        """Test presigned URL generation with claim_id."""
        mock_build_key.return_value = "claims/claim-123/PROOF/doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url, key = generate_presigned_url(
            "doc.pdf",
            "PROOF",
            "application/pdf",
            claim_id="claim-123"
        )

        assert "claims/claim-123" in key
        mock_build_key.assert_called_once_with(
            "doc.pdf", "PROOF", "claim-123", None
        )

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_with_custom_expiry(self, mock_build_key, mock_s3):
        """Test presigned URL with custom expiry time."""
        mock_build_key.return_value = "test/doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url, key = generate_presigned_url(
            "doc.pdf",
            "TYPE",
            "application/pdf",
            expiry_seconds=7200
        )

        # Check that ExpiresIn parameter was set correctly
        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs['ExpiresIn'] == 7200

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_default_expiry(self, mock_build_key, mock_s3):
        """Test presigned URL with default expiry time."""
        mock_build_key.return_value = "test/doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url, key = generate_presigned_url("doc.pdf", "TYPE", "application/pdf")

        # Default should be 3600 seconds
        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs['ExpiresIn'] == 3600

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_verify_http_method(self, mock_build_key, mock_s3):
        """Test that PUT method is used for upload URLs."""
        mock_build_key.return_value = "test/doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        generate_presigned_url("doc.pdf", "TYPE", "application/pdf")

        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs['HttpMethod'] == "PUT"

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_verify_params(self, mock_build_key, mock_s3):
        """Test that S3 parameters are set correctly."""
        from src.config.aws import S3_BUCKET_NAME
        mock_build_key.return_value = "test/doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        generate_presigned_url("doc.pdf", "TYPE", "image/jpeg")

        call_args = mock_s3.generate_presigned_url.call_args
        params = call_args[1]['Params']
        assert params['Bucket'] == S3_BUCKET_NAME
        assert params['Key'] == "test/doc.pdf"
        assert params['ContentType'] == "image/jpeg"


class TestGenerateDownloadUrl:
    """Test generate_download_url function."""

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_success(self, mock_s3):
        """Test successful download URL generation."""
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/download"

        url = generate_download_url("test/path/document.pdf")

        assert url == "https://s3.example.com/download"
        mock_s3.generate_presigned_url.assert_called_once()

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_default_expiry(self, mock_s3):
        """Test download URL with default expiry (900 seconds)."""
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url = generate_download_url("test/doc.pdf")

        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs['ExpiresIn'] == 900

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_custom_expiry(self, mock_s3):
        """Test download URL with custom expiry time."""
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url = generate_download_url("test/doc.pdf", expiry_seconds=1800)

        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs['ExpiresIn'] == 1800

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_verify_method(self, mock_s3):
        """Test that get_object method is used."""
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url = generate_download_url("test/doc.pdf")

        # First argument should be "get_object"
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == "get_object"

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_verify_params(self, mock_s3):
        """Test that S3 parameters include bucket and key."""
        from src.config.aws import S3_BUCKET_NAME
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url = generate_download_url("claims/claim-123/doc.pdf")

        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        params = call_kwargs['Params']
        assert params['Bucket'] == S3_BUCKET_NAME
        assert params['Key'] == "claims/claim-123/doc.pdf"

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_with_special_characters(self, mock_s3):
        """Test download URL with special characters in key."""
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url = generate_download_url("test/path/document with spaces & special.pdf")

        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs['Params']['Key'] == "test/path/document with spaces & special.pdf"

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_zero_expiry(self, mock_s3):
        """Test boundary: zero expiry time."""
        mock_s3.generate_presigned_url.return_value = "https://s3.example.com/url"

        url = generate_download_url("test/doc.pdf", expiry_seconds=0)

        call_kwargs = mock_s3.generate_presigned_url.call_args[1]
        assert call_kwargs['ExpiresIn'] == 0
