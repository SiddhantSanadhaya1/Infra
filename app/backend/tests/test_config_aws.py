"""Unit tests for src.config.aws module."""
import os
from unittest.mock import MagicMock, patch

import pytest

from src.config.aws import (
    get_s3_client,
    get_sqs_client,
    get_sns_client,
    get_secrets_manager_client,
)


class TestAWSConfig:
    """Test AWS configuration and client creation."""

    @patch.dict(os.environ, {"AWS_REGION": "us-west-2", "AWS_ENDPOINT_URL": ""})
    @patch("src.config.aws.boto3")
    def test_get_s3_client_with_custom_region(self, mock_boto3):
        """Test S3 client creation with custom region."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        client = get_s3_client()

        mock_boto3.client.assert_called_once_with("s3", region_name="us-west-2")
        assert client == mock_client

    @patch.dict(os.environ, {"AWS_REGION": "us-east-1", "AWS_ENDPOINT_URL": ""})
    @patch("src.config.aws.boto3")
    def test_get_s3_client_with_default_region(self, mock_boto3):
        """Test S3 client creation with default region."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        client = get_s3_client()

        mock_boto3.client.assert_called_once_with("s3", region_name="us-east-1")
        assert client == mock_client

    @patch.dict(
        os.environ,
        {"AWS_REGION": "us-east-1", "AWS_ENDPOINT_URL": "http://localhost:4566"},
    )
    @patch("src.config.aws.boto3")
    def test_get_s3_client_with_endpoint_url(self, mock_boto3):
        """Test S3 client creation with custom endpoint (LocalStack)."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        client = get_s3_client()

        mock_boto3.client.assert_called_once_with(
            "s3", region_name="us-east-1", endpoint_url="http://localhost:4566"
        )
        assert client == mock_client

    @patch.dict(os.environ, {"AWS_REGION": "eu-west-1", "AWS_ENDPOINT_URL": ""})
    @patch("src.config.aws.boto3")
    def test_get_sqs_client(self, mock_boto3):
        """Test SQS client creation."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        client = get_sqs_client()

        mock_boto3.client.assert_called_once_with("sqs", region_name="eu-west-1")
        assert client == mock_client

    @patch.dict(os.environ, {"AWS_REGION": "ap-south-1", "AWS_ENDPOINT_URL": ""})
    @patch("src.config.aws.boto3")
    def test_get_sns_client(self, mock_boto3):
        """Test SNS client creation."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        client = get_sns_client()

        mock_boto3.client.assert_called_once_with("sns", region_name="ap-south-1")
        assert client == mock_client

    @patch.dict(os.environ, {"AWS_REGION": "us-east-2", "AWS_ENDPOINT_URL": ""})
    @patch("src.config.aws.boto3")
    def test_get_secrets_manager_client(self, mock_boto3):
        """Test Secrets Manager client creation."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        client = get_secrets_manager_client()

        mock_boto3.client.assert_called_once_with(
            "secretsmanager", region_name="us-east-2"
        )
        assert client == mock_client

    @patch.dict(
        os.environ,
        {
            "AWS_REGION": "us-east-1",
            "AWS_ENDPOINT_URL": "http://localstack:4566",
        },
    )
    @patch("src.config.aws.boto3")
    def test_all_clients_use_same_endpoint(self, mock_boto3):
        """Test all AWS clients use the same endpoint configuration."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        get_s3_client()
        get_sqs_client()
        get_sns_client()
        get_secrets_manager_client()

        # Check all clients were created with the same endpoint
        calls = mock_boto3.client.call_args_list
        assert len(calls) == 4
        for call in calls:
            assert call[1]["endpoint_url"] == "http://localstack:4566"
            assert call[1]["region_name"] == "us-east-1"

    @patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"})
    def test_s3_bucket_name_from_env(self):
        """Test S3 bucket name is read from environment."""
        from src.config import aws

        # Re-import to get updated env var
        import importlib

        importlib.reload(aws)
        assert aws.S3_BUCKET_NAME == "test-bucket"

    @patch.dict(os.environ, {"SQS_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"})
    def test_sqs_queue_url_from_env(self):
        """Test SQS queue URL is read from environment."""
        from src.config import aws
        import importlib

        importlib.reload(aws)
        assert aws.SQS_QUEUE_URL == "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"

    @patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789:test-topic"})
    def test_sns_topic_arn_from_env(self):
        """Test SNS topic ARN is read from environment."""
        from src.config import aws
        import importlib

        importlib.reload(aws)
        assert aws.SNS_TOPIC_ARN == "arn:aws:sns:us-east-1:123456789:test-topic"
