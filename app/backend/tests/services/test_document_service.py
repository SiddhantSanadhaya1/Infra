"""
Comprehensive unit tests for document_service module.
Tests S3 key building, presigned URL generation, and download URL generation.
"""
import pytest
from unittest.mock import patch, MagicMock
import uuid

from src.services.document_service import (
    _build_s3_key,
    generate_presigned_url,
    generate_download_url,
)


class TestBuildS3Key:
    """Test S3 key building logic with various scenarios."""

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_with_claim_id(self, mock_uuid):
        """Test S3 key structure when claim_id is provided."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("report.pdf", "medical", claim_id="claim-123")

        assert key.startswith("claims/claim-123/medical/")
        assert "report.pdf" in key
        assert "12345678" in key

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_with_policy_id(self, mock_uuid):
        """Test S3 key structure when policy_id is provided."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("contract.pdf", "policy_document", policy_id="policy-456")

        assert key.startswith("policies/policy-456/policy_document/")
        assert "contract.pdf" in key

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_without_claim_or_policy(self, mock_uuid):
        """Test S3 key structure when neither claim_id nor policy_id is provided."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("general.pdf", "general_document")

        assert key.startswith("documents/general_document/")
        assert "general.pdf" in key

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_replaces_spaces_with_underscores(self, mock_uuid):
        """Test that spaces in filename are replaced with underscores."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("my file name.pdf", "document")

        assert "my_file_name.pdf" in key
        assert " " not in key

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_multiple_spaces(self, mock_uuid):
        """Test filename with multiple consecutive spaces."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("file   with   spaces.pdf", "document")

        assert "file___with___spaces.pdf" in key

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_claim_takes_priority_over_policy(self, mock_uuid):
        """Test that claim_id takes priority when both claim_id and policy_id are provided."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("doc.pdf", "type", claim_id="claim-123", policy_id="policy-456")

        assert key.startswith("claims/claim-123/")
        assert "policies/" not in key

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_empty_filename(self, mock_uuid):
        """Test with empty filename."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("", "document")

        assert key.startswith("documents/document/")
        assert key.endswith("_")

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_special_characters_in_filename(self, mock_uuid):
        """Test filename with special characters."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key("file@#$%.pdf", "document")

        assert "file@#$%.pdf" in key  # Special chars preserved (only spaces replaced)

    @patch("src.services.document_service.uuid.uuid4")
    def test_build_s3_key_unique_prefix_is_8_chars(self, mock_uuid):
        """Test that unique prefix is exactly first 8 chars of UUID."""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "abcdefgh-1234-1234-1234-123456789012"

        key = _build_s3_key("file.pdf", "type")

        assert "abcdefgh_file.pdf" in key


class TestGeneratePresignedUrl:
    """Test presigned URL generation for uploads."""

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_returns_url_and_key(self, mock_s3):
        """Test that function returns both presigned URL and file key."""
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/bucket/key?signature=xyz"

        url, key = generate_presigned_url("file.pdf", "document", "application/pdf")

        assert url == "https://s3.amazonaws.com/bucket/key?signature=xyz"
        assert key.startswith("documents/document/")
        assert "file.pdf" in key

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_calls_s3_with_correct_params(self, mock_s3):
        """Test that S3 client is called with correct parameters."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        generate_presigned_url("test.pdf", "type", "application/pdf")

        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == "put_object"
        assert call_args[1]["Params"]["Bucket"] == "insureco-documents"
        assert call_args[1]["Params"]["ContentType"] == "application/pdf"
        assert call_args[1]["ExpiresIn"] == 3600
        assert call_args[1]["HttpMethod"] == "PUT"

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_with_claim_id(self, mock_s3):
        """Test presigned URL generation with claim_id."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        url, key = generate_presigned_url("file.pdf", "medical", "application/pdf", claim_id="claim-123")

        assert key.startswith("claims/claim-123/medical/")

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_with_policy_id(self, mock_s3):
        """Test presigned URL generation with policy_id."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        url, key = generate_presigned_url("file.pdf", "contract", "application/pdf", policy_id="policy-456")

        assert key.startswith("policies/policy-456/contract/")

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_custom_expiry(self, mock_s3):
        """Test presigned URL generation with custom expiry time."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        generate_presigned_url("file.pdf", "type", "text/plain", expiry_seconds=7200)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 7200

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_default_expiry(self, mock_s3):
        """Test presigned URL generation uses default 3600 seconds."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        generate_presigned_url("file.pdf", "type", "application/pdf")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 3600

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_different_content_types(self, mock_s3):
        """Test presigned URL with various content types."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        content_types = ["image/png", "text/csv", "application/json", "video/mp4"]
        for content_type in content_types:
            generate_presigned_url("file", "type", content_type)
            call_args = mock_s3.generate_presigned_url.call_args
            assert call_args[1]["Params"]["ContentType"] == content_type

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_minimum_expiry(self, mock_s3):
        """Test presigned URL with minimum expiry (boundary)."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        generate_presigned_url("file.pdf", "type", "application/pdf", expiry_seconds=1)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_maximum_expiry(self, mock_s3):
        """Test presigned URL with maximum expiry (7 days)."""
        mock_s3.generate_presigned_url.return_value = "https://presigned-url.com"

        generate_presigned_url("file.pdf", "type", "application/pdf", expiry_seconds=604800)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 604800


class TestGenerateDownloadUrl:
    """Test presigned URL generation for downloads."""

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_returns_url(self, mock_s3):
        """Test that download URL is returned."""
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/download?sig=xyz"

        url = generate_download_url("documents/file.pdf")

        assert url == "https://s3.amazonaws.com/download?sig=xyz"

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_calls_s3_with_correct_params(self, mock_s3):
        """Test that S3 client is called with correct parameters for GET."""
        mock_s3.generate_presigned_url.return_value = "https://download-url.com"

        generate_download_url("path/to/file.pdf")

        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == "get_object"
        assert call_args[1]["Params"]["Bucket"] == "insureco-documents"
        assert call_args[1]["Params"]["Key"] == "path/to/file.pdf"
        assert call_args[1]["ExpiresIn"] == 900

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_default_expiry(self, mock_s3):
        """Test download URL uses default 900 seconds expiry."""
        mock_s3.generate_presigned_url.return_value = "https://download-url.com"

        generate_download_url("file.pdf")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 900

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_custom_expiry(self, mock_s3):
        """Test download URL with custom expiry time."""
        mock_s3.generate_presigned_url.return_value = "https://download-url.com"

        generate_download_url("file.pdf", expiry_seconds=1800)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1800

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_with_nested_path(self, mock_s3):
        """Test download URL generation with nested S3 key path."""
        mock_s3.generate_presigned_url.return_value = "https://download-url.com"

        generate_download_url("claims/claim-123/medical/report.pdf")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == "claims/claim-123/medical/report.pdf"

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_minimum_expiry(self, mock_s3):
        """Test download URL with minimum expiry (boundary)."""
        mock_s3.generate_presigned_url.return_value = "https://download-url.com"

        generate_download_url("file.pdf", expiry_seconds=1)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_empty_key(self, mock_s3):
        """Test download URL with empty file key."""
        mock_s3.generate_presigned_url.return_value = "https://download-url.com"

        generate_download_url("")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == ""

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_special_characters_in_key(self, mock_s3):
        """Test download URL with special characters in key."""
        mock_s3.generate_presigned_url.return_value = "https://download-url.com"

        generate_download_url("path/to/file with spaces & chars.pdf")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == "path/to/file with spaces & chars.pdf"
