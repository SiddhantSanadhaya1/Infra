"""Tests for src/config/aws.py"""
import pytest
from unittest.mock import patch, MagicMock
import os


class TestAWSClientCreation:
    """Test AWS client creation functions."""

    @patch('src.config.aws.boto3.client')
    def test_get_s3_client_with_default_region(self, mock_boto_client):
        """Test S3 client creation with default region."""
        from src.config import aws

        # Reset module-level client
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        client = aws.get_s3_client()

        mock_boto_client.assert_called_with("s3", region_name=aws.AWS_REGION)
        assert client == mock_s3

    @patch('src.config.aws.boto3.client')
    @patch.dict(os.environ, {"AWS_ENDPOINT_URL": "http://localhost:4566"})
    def test_get_s3_client_with_custom_endpoint(self, mock_boto_client):
        """Test S3 client creation with custom endpoint (LocalStack)."""
        # Need to reload module to pick up env var
        import importlib
        from src.config import aws
        importlib.reload(aws)

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        client = aws.get_s3_client()

        # Verify endpoint_url is passed
        call_kwargs = mock_boto_client.call_args[1]
        assert "endpoint_url" in call_kwargs

    @patch('src.config.aws.boto3.client')
    def test_get_sqs_client(self, mock_boto_client):
        """Test SQS client creation."""
        from src.config import aws

        mock_sqs = MagicMock()
        mock_boto_client.return_value = mock_sqs

        client = aws.get_sqs_client()

        mock_boto_client.assert_called_with("sqs", region_name=aws.AWS_REGION)
        assert client == mock_sqs

    @patch('src.config.aws.boto3.client')
    def test_get_sns_client(self, mock_boto_client):
        """Test SNS client creation."""
        from src.config import aws

        mock_sns = MagicMock()
        mock_boto_client.return_value = mock_sns

        client = aws.get_sns_client()

        mock_boto_client.assert_called_with("sns", region_name=aws.AWS_REGION)
        assert client == mock_sns

    @patch('src.config.aws.boto3.client')
    def test_get_secrets_manager_client(self, mock_boto_client):
        """Test Secrets Manager client creation."""
        from src.config import aws

        mock_secrets = MagicMock()
        mock_boto_client.return_value = mock_secrets

        client = aws.get_secrets_manager_client()

        mock_boto_client.assert_called_with("secretsmanager", region_name=aws.AWS_REGION)
        assert client == mock_secrets


class TestAWSConfiguration:
    """Test AWS configuration values."""

    @patch.dict(os.environ, {"AWS_REGION": "us-west-2"})
    def test_custom_aws_region(self):
        """Test that custom AWS region is loaded from environment."""
        import importlib
        from src.config import aws
        importlib.reload(aws)

        assert aws.AWS_REGION == "us-west-2"

    @patch.dict(os.environ, {"S3_BUCKET_NAME": "custom-bucket"})
    def test_custom_s3_bucket_name(self):
        """Test that custom S3 bucket name is loaded from environment."""
        import importlib
        from src.config import aws
        importlib.reload(aws)

        assert aws.S3_BUCKET_NAME == "custom-bucket"

    @patch.dict(os.environ, {"SQS_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789012/test-queue"})
    def test_custom_sqs_queue_url(self):
        """Test that custom SQS queue URL is loaded from environment."""
        import importlib
        from src.config import aws
        importlib.reload(aws)

        assert "test-queue" in aws.SQS_QUEUE_URL

    @patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:test-topic"})
    def test_custom_sns_topic_arn(self):
        """Test that custom SNS topic ARN is loaded from environment."""
        import importlib
        from src.config import aws
        importlib.reload(aws)

        assert "test-topic" in aws.SNS_TOPIC_ARN

    @patch.dict(os.environ, {}, clear=True)
    def test_default_configuration_values(self):
        """Test default configuration when no environment variables are set."""
        import importlib
        from src.config import aws
        importlib.reload(aws)

        assert aws.AWS_REGION == "us-east-1"
        assert aws.S3_BUCKET_NAME == "insureco-documents"
        assert aws.SQS_QUEUE_URL == ""
        assert aws.SNS_TOPIC_ARN == ""
        assert aws.AWS_ENDPOINT_URL is None
