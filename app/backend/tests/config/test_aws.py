"""
Unit tests for src.config.aws
Tests AWS client initialization and configuration.
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestAWSClientInitialization:
    """Test AWS client factory functions"""

    @patch('src.config.aws.boto3.client')
    @patch.dict(os.environ, {'AWS_REGION': 'us-west-2'}, clear=False)
    def test_get_s3_client_default_region(self, mock_boto_client):
        """Test S3 client creation with custom region"""
        from src.config.aws import get_s3_client

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Import after mocking to get fresh instance
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        client = src.config.aws.get_s3_client()

        assert client is not None

    @patch('src.config.aws.boto3.client')
    def test_get_sqs_client(self, mock_boto_client):
        """Test SQS client creation"""
        from src.config.aws import get_sqs_client

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = get_sqs_client()

        assert client is not None
        mock_boto_client.assert_called_with("sqs", region_name="us-east-1")

    @patch('src.config.aws.boto3.client')
    def test_get_sns_client(self, mock_boto_client):
        """Test SNS client creation"""
        from src.config.aws import get_sns_client

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = get_sns_client()

        assert client is not None
        mock_boto_client.assert_called_with("sns", region_name="us-east-1")

    @patch('src.config.aws.boto3.client')
    def test_get_secrets_manager_client(self, mock_boto_client):
        """Test Secrets Manager client creation"""
        from src.config.aws import get_secrets_manager_client

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = get_secrets_manager_client()

        assert client is not None
        mock_boto_client.assert_called_with("secretsmanager", region_name="us-east-1")

    @patch('src.config.aws.boto3.client')
    @patch.dict(os.environ, {'AWS_ENDPOINT_URL': 'http://localhost:4566'}, clear=False)
    def test_client_with_custom_endpoint(self, mock_boto_client):
        """Test client creation with custom endpoint URL (LocalStack)"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client = src.config.aws.get_s3_client()

        # Verify endpoint_url was passed in kwargs
        call_kwargs = mock_boto_client.call_args[1]
        assert 'endpoint_url' in call_kwargs


class TestAWSConfiguration:
    """Test AWS configuration constants"""

    @patch.dict(os.environ, {}, clear=True)
    def test_aws_region_default(self):
        """Test AWS_REGION defaults to us-east-1"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.AWS_REGION == "us-east-1"

    @patch.dict(os.environ, {'AWS_REGION': 'eu-west-1'}, clear=True)
    def test_aws_region_from_env(self):
        """Test AWS_REGION from environment variable"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.AWS_REGION == "eu-west-1"

    @patch.dict(os.environ, {}, clear=True)
    def test_aws_endpoint_url_default_none(self):
        """Test AWS_ENDPOINT_URL defaults to None"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.AWS_ENDPOINT_URL is None

    @patch.dict(os.environ, {'AWS_ENDPOINT_URL': 'http://localstack:4566'}, clear=True)
    def test_aws_endpoint_url_from_env(self):
        """Test AWS_ENDPOINT_URL from environment variable"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.AWS_ENDPOINT_URL == "http://localstack:4566"

    @patch.dict(os.environ, {}, clear=True)
    def test_s3_bucket_name_default(self):
        """Test S3_BUCKET_NAME has default value"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.S3_BUCKET_NAME == "insureco-documents"

    @patch.dict(os.environ, {'S3_BUCKET_NAME': 'custom-bucket'}, clear=True)
    def test_s3_bucket_name_from_env(self):
        """Test S3_BUCKET_NAME from environment variable"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.S3_BUCKET_NAME == "custom-bucket"

    @patch.dict(os.environ, {}, clear=True)
    def test_sqs_queue_url_default_empty(self):
        """Test SQS_QUEUE_URL defaults to empty string"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.SQS_QUEUE_URL == ""

    @patch.dict(os.environ, {'SQS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/123456789012/queue'}, clear=True)
    def test_sqs_queue_url_from_env(self):
        """Test SQS_QUEUE_URL from environment variable"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.SQS_QUEUE_URL == 'https://sqs.us-east-1.amazonaws.com/123456789012/queue'

    @patch.dict(os.environ, {}, clear=True)
    def test_sns_topic_arn_default_empty(self):
        """Test SNS_TOPIC_ARN defaults to empty string"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.SNS_TOPIC_ARN == ""

    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'}, clear=True)
    def test_sns_topic_arn_from_env(self):
        """Test SNS_TOPIC_ARN from environment variable"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        assert src.config.aws.SNS_TOPIC_ARN == 'arn:aws:sns:us-east-1:123456789012:topic'


class TestSingletonClients:
    """Test singleton client instances"""

    @patch('src.config.aws.boto3.client')
    def test_s3_client_is_singleton(self, mock_boto_client):
        """Test s3_client is a singleton instance"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client1 = src.config.aws.s3_client
        client2 = src.config.aws.s3_client

        # Both should reference the same object
        assert client1 is client2

    @patch('src.config.aws.boto3.client')
    def test_sqs_client_is_singleton(self, mock_boto_client):
        """Test sqs_client is a singleton instance"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client1 = src.config.aws.sqs_client
        client2 = src.config.aws.sqs_client

        assert client1 is client2

    @patch('src.config.aws.boto3.client')
    def test_sns_client_is_singleton(self, mock_boto_client):
        """Test sns_client is a singleton instance"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client1 = src.config.aws.sns_client
        client2 = src.config.aws.sns_client

        assert client1 is client2

    @patch('src.config.aws.boto3.client')
    def test_secrets_manager_client_is_singleton(self, mock_boto_client):
        """Test secrets_manager_client is a singleton instance"""
        import importlib
        import src.config.aws
        importlib.reload(src.config.aws)

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        client1 = src.config.aws.secrets_manager_client
        client2 = src.config.aws.secrets_manager_client

        assert client1 is client2
