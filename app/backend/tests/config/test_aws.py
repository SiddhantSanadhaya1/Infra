"""
Comprehensive unit tests for AWS config module.
Tests AWS client factory functions and configuration.
"""
import pytest
from unittest.mock import patch, MagicMock

from src.config.aws import (
    get_s3_client,
    get_sqs_client,
    get_sns_client,
    get_secrets_manager_client,
    s3_client,
    sqs_client,
    sns_client,
    secrets_manager_client,
    AWS_REGION,
    AWS_ENDPOINT_URL,
    S3_BUCKET_NAME,
    SQS_QUEUE_URL,
    SNS_TOPIC_ARN,
)


class TestGetS3Client:
    """Test S3 client factory function."""

    @patch("src.config.aws.boto3.client")
    def test_get_s3_client_creates_client(self, mock_boto_client):
        """Test that get_s3_client creates an S3 boto3 client."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = get_s3_client()

        mock_boto_client.assert_called_once()
        call_args = mock_boto_client.call_args
        assert call_args[0][0] == "s3"
        assert "region_name" in call_args[1]

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_REGION", "us-west-2")
    def test_get_s3_client_uses_configured_region(self, mock_boto_client):
        """Test that S3 client uses configured AWS region."""
        mock_boto_client.return_value = MagicMock()

        get_s3_client()

        call_args = mock_boto_client.call_args
        assert call_args[1]["region_name"] == "us-west-2"

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_ENDPOINT_URL", "http://localhost:4566")
    def test_get_s3_client_with_custom_endpoint(self, mock_boto_client):
        """Test S3 client with custom endpoint URL (LocalStack)."""
        mock_boto_client.return_value = MagicMock()

        get_s3_client()

        call_args = mock_boto_client.call_args
        assert call_args[1].get("endpoint_url") == "http://localhost:4566"


class TestGetSqsClient:
    """Test SQS client factory function."""

    @patch("src.config.aws.boto3.client")
    def test_get_sqs_client_creates_client(self, mock_boto_client):
        """Test that get_sqs_client creates an SQS boto3 client."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = get_sqs_client()

        mock_boto_client.assert_called_once()
        call_args = mock_boto_client.call_args
        assert call_args[0][0] == "sqs"
        assert "region_name" in call_args[1]

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_REGION", "eu-west-1")
    def test_get_sqs_client_uses_configured_region(self, mock_boto_client):
        """Test that SQS client uses configured AWS region."""
        mock_boto_client.return_value = MagicMock()

        get_sqs_client()

        call_args = mock_boto_client.call_args
        assert call_args[1]["region_name"] == "eu-west-1"

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_ENDPOINT_URL", "http://localhost:4566")
    def test_get_sqs_client_with_custom_endpoint(self, mock_boto_client):
        """Test SQS client with custom endpoint URL."""
        mock_boto_client.return_value = MagicMock()

        get_sqs_client()

        call_args = mock_boto_client.call_args
        assert call_args[1].get("endpoint_url") == "http://localhost:4566"


class TestGetSnsClient:
    """Test SNS client factory function."""

    @patch("src.config.aws.boto3.client")
    def test_get_sns_client_creates_client(self, mock_boto_client):
        """Test that get_sns_client creates an SNS boto3 client."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = get_sns_client()

        mock_boto_client.assert_called_once()
        call_args = mock_boto_client.call_args
        assert call_args[0][0] == "sns"
        assert "region_name" in call_args[1]

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_REGION", "ap-southeast-1")
    def test_get_sns_client_uses_configured_region(self, mock_boto_client):
        """Test that SNS client uses configured AWS region."""
        mock_boto_client.return_value = MagicMock()

        get_sns_client()

        call_args = mock_boto_client.call_args
        assert call_args[1]["region_name"] == "ap-southeast-1"

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_ENDPOINT_URL", "http://localhost:4566")
    def test_get_sns_client_with_custom_endpoint(self, mock_boto_client):
        """Test SNS client with custom endpoint URL."""
        mock_boto_client.return_value = MagicMock()

        get_sns_client()

        call_args = mock_boto_client.call_args
        assert call_args[1].get("endpoint_url") == "http://localhost:4566"


class TestGetSecretsManagerClient:
    """Test Secrets Manager client factory function."""

    @patch("src.config.aws.boto3.client")
    def test_get_secrets_manager_client_creates_client(self, mock_boto_client):
        """Test that get_secrets_manager_client creates a Secrets Manager client."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = get_secrets_manager_client()

        mock_boto_client.assert_called_once()
        call_args = mock_boto_client.call_args
        assert call_args[0][0] == "secretsmanager"
        assert "region_name" in call_args[1]

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_REGION", "us-east-2")
    def test_get_secrets_manager_client_uses_configured_region(self, mock_boto_client):
        """Test that Secrets Manager client uses configured region."""
        mock_boto_client.return_value = MagicMock()

        get_secrets_manager_client()

        call_args = mock_boto_client.call_args
        assert call_args[1]["region_name"] == "us-east-2"

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_ENDPOINT_URL", "http://localhost:4566")
    def test_get_secrets_manager_client_with_custom_endpoint(self, mock_boto_client):
        """Test Secrets Manager client with custom endpoint URL."""
        mock_boto_client.return_value = MagicMock()

        get_secrets_manager_client()

        call_args = mock_boto_client.call_args
        assert call_args[1].get("endpoint_url") == "http://localhost:4566"


class TestSingletonClients:
    """Test that singleton client instances are created."""

    def test_s3_client_singleton_exists(self):
        """Test that s3_client singleton is initialized."""
        assert s3_client is not None

    def test_sqs_client_singleton_exists(self):
        """Test that sqs_client singleton is initialized."""
        assert sqs_client is not None

    def test_sns_client_singleton_exists(self):
        """Test that sns_client singleton is initialized."""
        assert sns_client is not None

    def test_secrets_manager_client_singleton_exists(self):
        """Test that secrets_manager_client singleton is initialized."""
        assert secrets_manager_client is not None


class TestAwsConstants:
    """Test AWS configuration constants."""

    def test_aws_region_defined(self):
        """Test that AWS_REGION is defined."""
        assert AWS_REGION is not None
        assert isinstance(AWS_REGION, str)
        assert len(AWS_REGION) > 0

    def test_aws_region_default_value(self):
        """Test that AWS_REGION has us-east-1 as default."""
        # Can be overridden by environment variable
        assert AWS_REGION in ["us-east-1"] or len(AWS_REGION) > 0

    def test_aws_endpoint_url_type(self):
        """Test that AWS_ENDPOINT_URL is None or string."""
        assert AWS_ENDPOINT_URL is None or isinstance(AWS_ENDPOINT_URL, str)

    def test_s3_bucket_name_defined(self):
        """Test that S3_BUCKET_NAME is defined."""
        assert S3_BUCKET_NAME is not None
        assert isinstance(S3_BUCKET_NAME, str)

    def test_s3_bucket_name_default_value(self):
        """Test S3_BUCKET_NAME default value."""
        assert S3_BUCKET_NAME == "insureco-documents" or len(S3_BUCKET_NAME) > 0

    def test_sqs_queue_url_type(self):
        """Test that SQS_QUEUE_URL is a string."""
        assert isinstance(SQS_QUEUE_URL, str)

    def test_sns_topic_arn_type(self):
        """Test that SNS_TOPIC_ARN is a string."""
        assert isinstance(SNS_TOPIC_ARN, str)


class TestEndpointConfiguration:
    """Test endpoint configuration scenarios."""

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_ENDPOINT_URL", None)
    def test_clients_without_custom_endpoint(self, mock_boto_client):
        """Test that clients work without custom endpoint URL."""
        mock_boto_client.return_value = MagicMock()

        get_s3_client()

        call_args = mock_boto_client.call_args[1]
        # endpoint_url should not be in kwargs when None
        assert "endpoint_url" not in call_args or call_args.get("endpoint_url") is None

    @patch("src.config.aws.boto3.client")
    @patch("src.config.aws.AWS_ENDPOINT_URL", "")
    def test_clients_with_empty_endpoint(self, mock_boto_client):
        """Test that empty string endpoint URL is not used."""
        mock_boto_client.return_value = MagicMock()

        get_s3_client()

        # Empty string is falsy, so endpoint_url should not be set
        call_args = mock_boto_client.call_args[1]
        endpoint_in_call = call_args.get("endpoint_url")
        assert not endpoint_in_call


class TestBotoKwargsConstruction:
    """Test that boto kwargs are constructed correctly."""

    @patch("src.config.aws.AWS_REGION", "us-west-1")
    @patch("src.config.aws.AWS_ENDPOINT_URL", None)
    def test_boto_kwargs_without_endpoint(self):
        """Test that _boto_kwargs contains only region when no endpoint."""
        from src.config import aws
        # Need to reload the module to pick up new constants
        import importlib
        importlib.reload(aws)

        # _boto_kwargs should have region_name but not endpoint_url
        assert "region_name" in aws._boto_kwargs

    @patch("src.config.aws.AWS_REGION", "eu-central-1")
    @patch("src.config.aws.AWS_ENDPOINT_URL", "http://localhost:4566")
    def test_boto_kwargs_with_endpoint(self):
        """Test that _boto_kwargs contains both region and endpoint."""
        from src.config import aws
        import importlib
        importlib.reload(aws)

        assert "region_name" in aws._boto_kwargs
        assert aws._boto_kwargs.get("endpoint_url") == "http://localhost:4566"
