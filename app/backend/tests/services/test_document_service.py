import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from src.services.document_service import (
    _build_s3_key,
    generate_presigned_url,
    generate_download_url,
)


class TestBuildS3Key:
    """Test suite for _build_s3_key function."""

    @patch("src.services.document_service.uuid")
    def test_build_s3_key_with_claim_id(self, mock_uuid):
        """Test S3 key generation with claim ID."""
        mock_uuid.uuid4.return_value = Mock(hex="12345678abcd")
        mock_uuid.uuid4.return_value.__getitem__ = lambda self, key: "12345678"[:key.stop]

        result = _build_s3_key(
            file_name="invoice.pdf",
            document_type="invoice",
            claim_id="claim-123"
        )

        assert result.startswith("claims/claim-123/invoice/")
        assert result.endswith("_invoice.pdf")

    @patch("src.services.document_service.uuid")
    def test_build_s3_key_with_policy_id(self, mock_uuid):
        """Test S3 key generation with policy ID."""
        mock_uuid.uuid4.return_value = Mock(hex="12345678abcd")
        mock_uuid.uuid4.return_value.__getitem__ = lambda self, key: "12345678"[:key.stop]

        result = _build_s3_key(
            file_name="contract.pdf",
            document_type="contract",
            policy_id="policy-456"
        )

        assert result.startswith("policies/policy-456/contract/")
        assert result.endswith("_contract.pdf")

    @patch("src.services.document_service.uuid")
    def test_build_s3_key_without_ids(self, mock_uuid):
        """Test S3 key generation without claim or policy ID."""
        mock_uuid.uuid4.return_value = Mock(hex="12345678abcd")
        mock_uuid.uuid4.return_value.__getitem__ = lambda self, key: "12345678"[:key.stop]

        result = _build_s3_key(
            file_name="document.pdf",
            document_type="general"
        )

        assert result.startswith("documents/general/")
        assert result.endswith("_document.pdf")

    @patch("src.services.document_service.uuid")
    def test_build_s3_key_replaces_spaces(self, mock_uuid):
        """Test that spaces in filename are replaced with underscores."""
        mock_uuid.uuid4.return_value = Mock(hex="12345678abcd")
        mock_uuid.uuid4.return_value.__getitem__ = lambda self, key: "12345678"[:key.stop]

        result = _build_s3_key(
            file_name="my file name.pdf",
            document_type="doc"
        )

        assert "my_file_name.pdf" in result
        assert " " not in result

    @patch("src.services.document_service.uuid")
    def test_build_s3_key_claim_priority_over_policy(self, mock_uuid):
        """Test that claim_id takes priority when both IDs provided."""
        mock_uuid.uuid4.return_value = Mock(hex="12345678abcd")
        mock_uuid.uuid4.return_value.__getitem__ = lambda self, key: "12345678"[:key.stop]

        result = _build_s3_key(
            file_name="doc.pdf",
            document_type="test",
            claim_id="claim-123",
            policy_id="policy-456"
        )

        assert result.startswith("claims/claim-123/")
        assert "policies" not in result

    @patch("src.services.document_service.uuid")
    def test_build_s3_key_unique_prefix(self, mock_uuid):
        """Test that unique ID is included in key."""
        mock_uuid.uuid4.return_value = Mock(hex="12345678abcd")
        mock_uuid.uuid4.return_value.__getitem__ = lambda self, key: "12345678"[:key.stop]

        result = _build_s3_key(file_name="test.pdf", document_type="test")

        # Should contain the 8-char unique ID
        assert "12345678" in result

    @pytest.mark.parametrize("file_name,expected_safe_name", [
        ("simple.pdf", "simple.pdf"),
        ("file with spaces.doc", "file_with_spaces.doc"),
        ("multiple   spaces.txt", "multiple___spaces.txt"),
    ])
    @patch("src.services.document_service.uuid")
    def test_build_s3_key_various_filenames(
        self, mock_uuid, file_name, expected_safe_name
    ):
        """Test S3 key generation with various filenames."""
        mock_uuid.uuid4.return_value = Mock(hex="12345678abcd")
        mock_uuid.uuid4.return_value.__getitem__ = lambda self, key: "12345678"[:key.stop]

        result = _build_s3_key(file_name=file_name, document_type="test")
        assert expected_safe_name in result


class TestGeneratePresignedUrl:
    """Test suite for generate_presigned_url function."""

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_success(self, mock_s3):
        """Test successful presigned URL generation."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned"

        url, key = generate_presigned_url(
            file_name="test.pdf",
            document_type="invoice",
            content_type="application/pdf"
        )

        assert url == "https://s3.aws.com/presigned"
        assert "documents/invoice/" in key
        assert "test.pdf" in key
        mock_s3.generate_presigned_url.assert_called_once()

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_with_claim_id(self, mock_s3):
        """Test presigned URL generation with claim ID."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned"

        url, key = generate_presigned_url(
            file_name="claim_doc.pdf",
            document_type="evidence",
            content_type="application/pdf",
            claim_id="claim-123"
        )

        assert "claims/claim-123/" in key
        mock_s3.generate_presigned_url.assert_called_once()

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_with_policy_id(self, mock_s3):
        """Test presigned URL generation with policy ID."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned"

        url, key = generate_presigned_url(
            file_name="policy_doc.pdf",
            document_type="contract",
            content_type="application/pdf",
            policy_id="policy-456"
        )

        assert "policies/policy-456/" in key
        mock_s3.generate_presigned_url.assert_called_once()

    @patch("src.services.document_service.s3_client")
    @patch("src.services.document_service.S3_BUCKET_NAME", "test-bucket")
    def test_generate_presigned_url_correct_params(self, mock_s3):
        """Test that correct parameters are passed to S3 client."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned"

        generate_presigned_url(
            file_name="test.pdf",
            document_type="doc",
            content_type="application/pdf",
            expiry_seconds=7200
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == "put_object"
        assert call_args[1]["Params"]["Bucket"] == "test-bucket"
        assert call_args[1]["Params"]["ContentType"] == "application/pdf"
        assert call_args[1]["ExpiresIn"] == 7200
        assert call_args[1]["HttpMethod"] == "PUT"

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_default_expiry(self, mock_s3):
        """Test that default expiry time is used."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned"

        generate_presigned_url(
            file_name="test.pdf",
            document_type="doc",
            content_type="application/pdf"
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 3600  # Default 1 hour

    @patch("src.services.document_service.s3_client")
    def test_generate_presigned_url_custom_expiry(self, mock_s3):
        """Test presigned URL generation with custom expiry."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned"

        generate_presigned_url(
            file_name="test.pdf",
            document_type="doc",
            content_type="application/pdf",
            expiry_seconds=1800
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 1800

    @patch("src.services.document_service.s3_client")
    @pytest.mark.parametrize("content_type", [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/msword",
    ])
    def test_generate_presigned_url_various_content_types(
        self, mock_s3, content_type
    ):
        """Test presigned URL generation with various content types."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/presigned"

        generate_presigned_url(
            file_name="test.file",
            document_type="doc",
            content_type=content_type
        )

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["ContentType"] == content_type


class TestGenerateDownloadUrl:
    """Test suite for generate_download_url function."""

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_success(self, mock_s3):
        """Test successful download URL generation."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download"

        result = generate_download_url("documents/test/file.pdf")

        assert result == "https://s3.aws.com/download"
        mock_s3.generate_presigned_url.assert_called_once()

    @patch("src.services.document_service.s3_client")
    @patch("src.services.document_service.S3_BUCKET_NAME", "download-bucket")
    def test_generate_download_url_correct_params(self, mock_s3):
        """Test that correct parameters are passed to S3 client."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download"
        file_key = "claims/claim-123/invoice/doc.pdf"

        generate_download_url(file_key)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[0][0] == "get_object"
        assert call_args[1]["Params"]["Bucket"] == "download-bucket"
        assert call_args[1]["Params"]["Key"] == file_key

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_default_expiry(self, mock_s3):
        """Test that default expiry time is used."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download"

        generate_download_url("test/file.pdf")

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 900  # Default 15 minutes

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_custom_expiry(self, mock_s3):
        """Test download URL generation with custom expiry."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download"

        generate_download_url("test/file.pdf", expiry_seconds=300)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["ExpiresIn"] == 300

    @patch("src.services.document_service.s3_client")
    @pytest.mark.parametrize("file_key", [
        "documents/test.pdf",
        "claims/claim-123/invoice/file.pdf",
        "policies/policy-456/contract/agreement.docx",
        "claims/claim-789/evidence/photo.jpg",
    ])
    def test_generate_download_url_various_keys(self, mock_s3, file_key):
        """Test download URL generation with various file keys."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download"

        generate_download_url(file_key)

        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == file_key

    @patch("src.services.document_service.s3_client")
    def test_generate_download_url_empty_key(self, mock_s3):
        """Test download URL generation with empty key."""
        mock_s3.generate_presigned_url.return_value = "https://s3.aws.com/download"

        result = generate_download_url("")

        assert result == "https://s3.aws.com/download"
        call_args = mock_s3.generate_presigned_url.call_args
        assert call_args[1]["Params"]["Key"] == ""
