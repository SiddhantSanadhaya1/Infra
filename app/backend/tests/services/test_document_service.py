"""
Unit tests for src.services.document_service
Tests S3 key building and presigned URL generation.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.services.document_service import (
    _build_s3_key,
    generate_presigned_url,
    generate_download_url,
)


class TestBuildS3Key:
    """Test S3 key building logic"""

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_claim_id(self, mock_uuid):
        """Test S3 key building with claim ID"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "12345678-1234-1234-1234-123456789012")

        result = _build_s3_key(
            file_name="medical_bill.pdf",
            document_type="medical",
            claim_id="claim-123",
            policy_id=None
        )

        assert result == "claims/claim-123/medical/12345678_medical_bill.pdf"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_policy_id(self, mock_uuid):
        """Test S3 key building with policy ID"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "abcdefgh-abcd-abcd-abcd-abcdefghijkl")

        result = _build_s3_key(
            file_name="policy_document.pdf",
            document_type="policy",
            claim_id=None,
            policy_id="policy-456"
        )

        assert result == "policies/policy-456/policy/abcdefgh_policy_document.pdf"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_both_ids_prefers_claim(self, mock_uuid):
        """Test S3 key building when both claim and policy IDs provided (claim takes precedence)"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "99999999-9999-9999-9999-999999999999")

        result = _build_s3_key(
            file_name="document.pdf",
            document_type="receipt",
            claim_id="claim-789",
            policy_id="policy-789"
        )

        assert result == "claims/claim-789/receipt/99999999_document.pdf"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_without_ids(self, mock_uuid):
        """Test S3 key building without claim or policy ID"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

        result = _build_s3_key(
            file_name="general_doc.pdf",
            document_type="general",
            claim_id=None,
            policy_id=None
        )

        assert result == "documents/general/aaaaaaaa_general_doc.pdf"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_spaces_in_filename(self, mock_uuid):
        """Test S3 key building replaces spaces with underscores"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

        result = _build_s3_key(
            file_name="my file with spaces.pdf",
            document_type="invoice",
            claim_id="claim-001"
        )

        assert result == "claims/claim-001/invoice/bbbbbbbb_my_file_with_spaces.pdf"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_multiple_spaces(self, mock_uuid):
        """Test S3 key building with multiple consecutive spaces"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "cccccccc-cccc-cccc-cccc-cccccccccccc")

        result = _build_s3_key(
            file_name="file   with   many   spaces.txt",
            document_type="text",
            policy_id="policy-002"
        )

        assert result == "policies/policy-002/text/cccccccc_file___with___many___spaces.txt"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_empty_filename(self, mock_uuid):
        """Test S3 key building with empty filename"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "dddddddd-dddd-dddd-dddd-dddddddddddd")

        result = _build_s3_key(
            file_name="",
            document_type="empty",
            claim_id="claim-003"
        )

        assert result == "claims/claim-003/empty/dddddddd_"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_special_characters(self, mock_uuid):
        """Test S3 key building with special characters in filename"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")

        result = _build_s3_key(
            file_name="file@#$%.pdf",
            document_type="special",
            claim_id="claim-004"
        )

        assert result == "claims/claim-004/special/eeeeeeee_file@#$%.pdf"

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_uuid_truncation(self, mock_uuid):
        """Test S3 key building uses first 8 characters of UUID"""
        mock_uuid.return_value = MagicMock(__str__=lambda self: "12345678-9012-3456-7890-123456789012")

        result = _build_s3_key(
            file_name="test.pdf",
            document_type="test",
            claim_id="claim-005"
        )

        assert result.startswith("claims/claim-005/test/12345678_")


class TestGeneratePresignedUrl:
    """Test presigned URL generation for uploads"""

    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.s3_client')
    def test_generate_presigned_url_basic(self, mock_s3, mock_build_key):
        """Test basic presigned URL generation"""
        mock_build_key.return_value = "claims/claim-123/medical/abc123_receipt.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned-url"

        url, key = generate_presigned_url(
            file_name="receipt.pdf",
            document_type="medical",
            content_type="application/pdf",
            claim_id="claim-123"
        )

        assert url == "https://s3.aws.com/presigned-url"
        assert key == "claims/claim-123/medical/abc123_receipt.pdf"
        mock_s3.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "insureco-documents",
                "Key": "claims/claim-123/medical/abc123_receipt.pdf",
                "ContentType": "application/pdf",
            },
            ExpiresIn=3600,
            HttpMethod="PUT",
        )

    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.s3_client')
    def test_generate_presigned_url_with_policy_id(self, mock_s3, mock_build_key):
        """Test presigned URL generation with policy ID"""
        mock_build_key.return_value = "policies/policy-456/contract/def456_contract.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned-url-2"

        url, key = generate_presigned_url(
            file_name="contract.pdf",
            document_type="contract",
            content_type="application/pdf",
            policy_id="policy-456"
        )

        assert url == "https://s3.aws.com/presigned-url-2"
        assert key == "policies/policy-456/contract/def456_contract.pdf"

    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.s3_client')
    def test_generate_presigned_url_custom_expiry(self, mock_s3, mock_build_key):
        """Test presigned URL generation with custom expiry"""
        mock_build_key.return_value = "claims/claim-789/photo/ghi789_photo.jpg"
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned-url-3"

        url, key = generate_presigned_url(
            file_name="photo.jpg",
            document_type="photo",
            content_type="image/jpeg",
            claim_id="claim-789",
            expiry_seconds=7200
        )

        assert url == "https://s3.aws.com/presigned-url-3"
        mock_s3.generate_presigned_url.assert_called_once()
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 7200

    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.s3_client')
    def test_generate_presigned_url_different_content_types(self, mock_s3, mock_build_key):
        """Test presigned URL generation with various content types"""
        mock_build_key.return_value = "claims/claim-001/image/img_test.png"
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        # Test image/png
        url, key = generate_presigned_url(
            file_name="test.png",
            document_type="image",
            content_type="image/png",
            claim_id="claim-001"
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["ContentType"] == "image/png"

    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.s3_client')
    def test_generate_presigned_url_no_ids(self, mock_s3, mock_build_key):
        """Test presigned URL generation without claim or policy ID"""
        mock_build_key.return_value = "documents/general/xyz_doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        url, key = generate_presigned_url(
            file_name="doc.pdf",
            document_type="general",
            content_type="application/pdf"
        )

        assert key == "documents/general/xyz_doc.pdf"
        mock_build_key.assert_called_once_with("doc.pdf", "general", None, None)

    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.s3_client')
    def test_generate_presigned_url_minimum_expiry(self, mock_s3, mock_build_key):
        """Test presigned URL generation with minimum expiry"""
        mock_build_key.return_value = "claims/claim-002/doc/doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        url, key = generate_presigned_url(
            file_name="doc.pdf",
            document_type="doc",
            content_type="application/pdf",
            claim_id="claim-002",
            expiry_seconds=60
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 60

    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.s3_client')
    def test_generate_presigned_url_maximum_expiry(self, mock_s3, mock_build_key):
        """Test presigned URL generation with maximum expiry"""
        mock_build_key.return_value = "claims/claim-003/doc/doc.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        url, key = generate_presigned_url(
            file_name="doc.pdf",
            document_type="doc",
            content_type="application/pdf",
            claim_id="claim-003",
            expiry_seconds=604800  # 7 days
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 604800


class TestGenerateDownloadUrl:
    """Test presigned URL generation for downloads"""

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_basic(self, mock_s3):
        """Test basic download URL generation"""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download-url"

        url = generate_download_url("claims/claim-123/medical/receipt.pdf")

        assert url == "https://s3.aws.com/download-url"
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": "insureco-documents",
                "Key": "claims/claim-123/medical/receipt.pdf",
            },
            ExpiresIn=900,
        )

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_custom_expiry(self, mock_s3):
        """Test download URL generation with custom expiry"""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download-url-2"

        url = generate_download_url(
            "policies/policy-456/contract.pdf",
            expiry_seconds=1800
        )

        assert url == "https://s3.aws.com/download-url-2"
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1800

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_long_key(self, mock_s3):
        """Test download URL generation with long S3 key"""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        long_key = "claims/claim-very-long-id-12345/documents/medical/photos/xyz_very_long_filename_with_many_characters.jpg"
        url = generate_download_url(long_key)

        assert url == "https://s3.aws.com/url"
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == long_key

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_minimum_expiry(self, mock_s3):
        """Test download URL generation with minimum expiry"""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        url = generate_download_url("documents/test.pdf", expiry_seconds=60)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 60

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_maximum_expiry(self, mock_s3):
        """Test download URL generation with maximum expiry"""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        url = generate_download_url("documents/test.pdf", expiry_seconds=604800)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 604800

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_special_characters_in_key(self, mock_s3):
        """Test download URL generation with special characters in key"""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/url"

        key_with_special_chars = "claims/claim-123/docs/file%20with%20spaces.pdf"
        url = generate_download_url(key_with_special_chars)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == key_with_special_chars
