"""Unit tests for document service module"""
import pytest
from unittest.mock import patch, MagicMock


class TestBuildS3Key:
    """Test S3 key building (private function)"""

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_claim_id(self, mock_uuid):
        """Test S3 key generation for claim document"""
        from src.services.document_service import _build_s3_key

        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key(
            file_name="invoice.pdf",
            document_type="INVOICE",
            claim_id="claim-123"
        )

        assert key.startswith("claims/claim-123/INVOICE/")
        assert "invoice.pdf" in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_with_policy_id(self, mock_uuid):
        """Test S3 key generation for policy document"""
        from src.services.document_service import _build_s3_key

        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key(
            file_name="contract.pdf",
            document_type="CONTRACT",
            policy_id="policy-456"
        )

        assert key.startswith("policies/policy-456/CONTRACT/")
        assert "contract.pdf" in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_without_claim_or_policy(self, mock_uuid):
        """Test S3 key generation without claim or policy"""
        from src.services.document_service import _build_s3_key

        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key(
            file_name="general.pdf",
            document_type="GENERAL"
        )

        assert key.startswith("documents/GENERAL/")
        assert "general.pdf" in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_spaces_replaced(self, mock_uuid):
        """Test S3 key replaces spaces with underscores"""
        from src.services.document_service import _build_s3_key

        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key(
            file_name="my document with spaces.pdf",
            document_type="GENERAL"
        )

        assert "my_document_with_spaces.pdf" in key
        assert " " not in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_unique_prefix(self, mock_uuid):
        """Test S3 key includes unique UUID prefix"""
        from src.services.document_service import _build_s3_key

        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "abcdef12-1234-1234-1234-123456789012"

        key = _build_s3_key(
            file_name="test.pdf",
            document_type="TEST"
        )

        # Should include first 8 chars of UUID
        assert "abcdef12_test.pdf" in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_empty_filename(self, mock_uuid):
        """Test S3 key with empty filename"""
        from src.services.document_service import _build_s3_key

        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key(
            file_name="",
            document_type="TEST"
        )

        # Should still generate key structure
        assert "documents/TEST/" in key

    @patch('src.services.document_service.uuid.uuid4')
    def test_build_s3_key_special_characters(self, mock_uuid):
        """Test S3 key with special characters in filename"""
        from src.services.document_service import _build_s3_key

        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "12345678-1234-1234-1234-123456789012"

        key = _build_s3_key(
            file_name="file@#$%.pdf",
            document_type="TEST"
        )

        # Spaces replaced, special chars preserved
        assert "file@#$%.pdf" in key


class TestGeneratePresignedUrl:
    """Test presigned URL generation"""

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_basic(self, mock_build_key, mock_s3):
        """Test basic presigned URL generation"""
        from src.services.document_service import generate_presigned_url

        mock_build_key.return_value = "claims/claim-123/INVOICE/abc_invoice.pdf"
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned-url"

        url, key = generate_presigned_url(
            file_name="invoice.pdf",
            document_type="INVOICE",
            content_type="application/pdf"
        )

        assert url == "https://s3.amazonaws.com/presigned-url"
        assert key == "claims/claim-123/INVOICE/abc_invoice.pdf"

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    @patch('src.services.document_service.S3_BUCKET_NAME', 'test-bucket')
    def test_generate_presigned_url_with_claim_id(self, mock_build_key, mock_s3):
        """Test presigned URL generation with claim_id"""
        from src.services.document_service import generate_presigned_url

        mock_build_key.return_value = "claims/claim-123/PHOTO/abc_photo.jpg"
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"

        url, key = generate_presigned_url(
            file_name="photo.jpg",
            document_type="PHOTO",
            content_type="image/jpeg",
            claim_id="claim-123"
        )

        mock_build_key.assert_called_once_with(
            "photo.jpg",
            "PHOTO",
            claim_id="claim-123",
            policy_id=None
        )
        mock_s3.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "test-bucket",
                "Key": "claims/claim-123/PHOTO/abc_photo.jpg",
                "ContentType": "image/jpeg",
            },
            ExpiresIn=3600,
            HttpMethod="PUT",
        )

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_with_policy_id(self, mock_build_key, mock_s3):
        """Test presigned URL generation with policy_id"""
        from src.services.document_service import generate_presigned_url

        mock_build_key.return_value = "policies/policy-456/CONTRACT/abc_contract.pdf"
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"

        url, key = generate_presigned_url(
            file_name="contract.pdf",
            document_type="CONTRACT",
            content_type="application/pdf",
            policy_id="policy-456"
        )

        mock_build_key.assert_called_once_with(
            "contract.pdf",
            "CONTRACT",
            claim_id=None,
            policy_id="policy-456"
        )

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_custom_expiry(self, mock_build_key, mock_s3):
        """Test presigned URL with custom expiry time"""
        from src.services.document_service import generate_presigned_url

        mock_build_key.return_value = "documents/TEST/abc_test.pdf"
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"

        url, key = generate_presigned_url(
            file_name="test.pdf",
            document_type="TEST",
            content_type="application/pdf",
            expiry_seconds=7200
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 7200

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_minimum_expiry(self, mock_build_key, mock_s3):
        """Test presigned URL with minimum expiry (1 second)"""
        from src.services.document_service import generate_presigned_url

        mock_build_key.return_value = "documents/TEST/abc_test.pdf"
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"

        url, key = generate_presigned_url(
            file_name="test.pdf",
            document_type="TEST",
            content_type="application/pdf",
            expiry_seconds=1
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_maximum_expiry(self, mock_build_key, mock_s3):
        """Test presigned URL with very long expiry (1 week)"""
        from src.services.document_service import generate_presigned_url

        mock_build_key.return_value = "documents/TEST/abc_test.pdf"
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"

        url, key = generate_presigned_url(
            file_name="test.pdf",
            document_type="TEST",
            content_type="application/pdf",
            expiry_seconds=604800  # 1 week
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 604800

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service._build_s3_key')
    def test_generate_presigned_url_different_content_types(self, mock_build_key, mock_s3):
        """Test presigned URL with different content types"""
        from src.services.document_service import generate_presigned_url

        test_cases = [
            ("image.jpg", "image/jpeg"),
            ("doc.pdf", "application/pdf"),
            ("file.txt", "text/plain"),
            ("data.json", "application/json"),
            ("sheet.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ]

        for filename, content_type in test_cases:
            mock_build_key.return_value = f"documents/TEST/abc_{filename}"
            mock_s3.generate_presigned_url.return_value = "https://presigned.url"

            generate_presigned_url(
                file_name=filename,
                document_type="TEST",
                content_type=content_type
            )

            call_args = mock_s3.generate_presigned_url.call_args
            assert call_args[1]["Params"]["ContentType"] == content_type


class TestGenerateDownloadUrl:
    """Test download URL generation"""

    @patch('src.services.document_service.s3_client')
    @patch('src.services.document_service.S3_BUCKET_NAME', 'test-bucket')
    def test_generate_download_url_basic(self, mock_s3):
        """Test basic download URL generation"""
        from src.services.document_service import generate_download_url

        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/download-url"

        url = generate_download_url("claims/claim-123/INVOICE/abc_invoice.pdf")

        assert url == "https://s3.amazonaws.com/download-url"
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={
                "Bucket": "test-bucket",
                "Key": "claims/claim-123/INVOICE/abc_invoice.pdf",
            },
            ExpiresIn=900,
        )

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_custom_expiry(self, mock_s3):
        """Test download URL with custom expiry"""
        from src.services.document_service import generate_download_url

        mock_s3.generate_presigned_url.return_value = "https://download.url"

        url = generate_download_url("test/file.pdf", expiry_seconds=1800)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1800

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_minimum_expiry(self, mock_s3):
        """Test download URL with minimum expiry (1 second)"""
        from src.services.document_service import generate_download_url

        mock_s3.generate_presigned_url.return_value = "https://download.url"

        url = generate_download_url("test/file.pdf", expiry_seconds=1)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_maximum_expiry(self, mock_s3):
        """Test download URL with very long expiry"""
        from src.services.document_service import generate_download_url

        mock_s3.generate_presigned_url.return_value = "https://download.url"

        url = generate_download_url("test/file.pdf", expiry_seconds=86400)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 86400

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_nested_key(self, mock_s3):
        """Test download URL with deeply nested S3 key"""
        from src.services.document_service import generate_download_url

        mock_s3.generate_presigned_url.return_value = "https://download.url"

        url = generate_download_url("level1/level2/level3/file.pdf")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == "level1/level2/level3/file.pdf"

    @patch('src.services.document_service.s3_client')
    def test_generate_download_url_empty_key(self, mock_s3):
        """Test download URL with empty key"""
        from src.services.document_service import generate_download_url

        mock_s3.generate_presigned_url.return_value = "https://download.url"

        url = generate_download_url("")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == ""
