"""Unit tests for AWS configuration module"""
import pytest
from unittest.mock import patch, MagicMock
import os


@pytest.fixture(autouse=True)
def reset_aws_module():
    """Reset AWS module state between tests"""
    import sys
    if 'src.config.aws' in sys.modules:
        del sys.modules['src.config.aws']
    yield


class TestAWSClientFactories:
    """Test AWS client factory functions"""

    @patch.dict(os.environ, {"AWS_REGION": "us-west-2"})
    @patch('boto3.client')
    def test_get_s3_client_with_region(self, mock_boto_client):
        """Test S3 client creation with custom region"""
        from src.config.aws import get_s3_client

        client = get_s3_client()

        mock_boto_client.assert_called_once_with("s3", region_name="us-west-2")

    @patch.dict(os.environ, {"AWS_REGION": "us-east-1", "AWS_ENDPOINT_URL": "http://localhost:4566"})
    @patch('boto3.client')
    def test_get_s3_client_with_endpoint_url(self, mock_boto_client):
        """Test S3 client creation with custom endpoint (LocalStack)"""
        from src.config.aws import get_s3_client

        client = get_s3_client()

        mock_boto_client.assert_called_once_with(
            "s3",
            region_name="us-east-1",
            endpoint_url="http://localhost:4566"
        )

    @patch.dict(os.environ, {}, clear=True)
    @patch('boto3.client')
    def test_get_s3_client_default_region(self, mock_boto_client):
        """Test S3 client creation with default region"""
        from src.config.aws import get_s3_client

        client = get_s3_client()

        mock_boto_client.assert_called_once_with("s3", region_name="us-east-1")

    @patch('boto3.client')
    def test_get_sqs_client(self, mock_boto_client):
        """Test SQS client creation"""
        from src.config.aws import get_sqs_client

        client = get_sqs_client()

        mock_boto_client.assert_called_once()
        assert mock_boto_client.call_args[0][0] == "sqs"

    @patch('boto3.client')
    def test_get_sns_client(self, mock_boto_client):
        """Test SNS client creation"""
        from src.config.aws import get_sns_client

        client = get_sns_client()

        mock_boto_client.assert_called_once()
        assert mock_boto_client.call_args[0][0] == "sns"

    @patch('boto3.client')
    def test_get_secrets_manager_client(self, mock_boto_client):
        """Test Secrets Manager client creation"""
        from src.config.aws import get_secrets_manager_client

        client = get_secrets_manager_client()

        mock_boto_client.assert_called_once()
        assert mock_boto_client.call_args[0][0] == "secretsmanager"


class TestAWSConfiguration:
    """Test AWS configuration constants"""

    @patch.dict(os.environ, {"S3_BUCKET_NAME": "my-custom-bucket"})
    def test_s3_bucket_name_custom(self):
        """Test custom S3 bucket name from environment"""
        import sys
        if 'src.config.aws' in sys.modules:
            del sys.modules['src.config.aws']

        from src.config.aws import S3_BUCKET_NAME
        assert S3_BUCKET_NAME == "my-custom-bucket"

    @patch.dict(os.environ, {}, clear=True)
    def test_s3_bucket_name_default(self):
        """Test default S3 bucket name"""
        import sys
        if 'src.config.aws' in sys.modules:
            del sys.modules['src.config.aws']

        from src.config.aws import S3_BUCKET_NAME
        assert S3_BUCKET_NAME == "insureco-documents"

    @patch.dict(os.environ, {"SQS_QUEUE_URL": "https://sqs.us-east-1.amazonaws.com/123/my-queue"})
    def test_sqs_queue_url_custom(self):
        """Test custom SQS queue URL from environment"""
        import sys
        if 'src.config.aws' in sys.modules:
            del sys.modules['src.config.aws']

        from src.config.aws import SQS_QUEUE_URL
        assert SQS_QUEUE_URL == "https://sqs.us-east-1.amazonaws.com/123/my-queue"

    @patch.dict(os.environ, {}, clear=True)
    def test_sqs_queue_url_default(self):
        """Test default SQS queue URL (empty string)"""
        import sys
        if 'src.config.aws' in sys.modules:
            del sys.modules['src.config.aws']

        from src.config.aws import SQS_QUEUE_URL
        assert SQS_QUEUE_URL == ""

    @patch.dict(os.environ, {"SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123:my-topic"})
    def test_sns_topic_arn_custom(self):
        """Test custom SNS topic ARN from environment"""
        import sys
        if 'src.config.aws' in sys.modules:
            del sys.modules['src.config.aws']

        from src.config.aws import SNS_TOPIC_ARN
        assert SNS_TOPIC_ARN == "arn:aws:sns:us-east-1:123:my-topic"


class TestAWSSingletonClients:
    """Test singleton client instances"""

    @patch('boto3.client')
    def test_singleton_s3_client(self, mock_boto_client):
        """Test that s3_client is a singleton"""
        import sys
        if 'src.config.aws' in sys.modules:
            del sys.modules['src.config.aws']

        from src.config.aws import s3_client

        # Singleton should be created on import
        assert s3_client is not None

    @patch('boto3.client')
    def test_singleton_sqs_client(self, mock_boto_client):
        """Test that sqs_client is a singleton"""
        import sys
        if 'src.config.aws' in sys.modules:
            del sys.modules['src.config.aws']

        from src.config.aws import sqs_client

        assert sqs_client is not None
