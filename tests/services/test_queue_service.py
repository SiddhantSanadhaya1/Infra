"""Unit tests for queue service module"""
import pytest
from unittest.mock import patch, MagicMock
import json


class TestEnqueueJob:
    """Test job enqueueing to SQS"""

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_process_claim(self, mock_sqs):
        """Test enqueueing PROCESS_CLAIM job"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260401-1234",
            "amount_requested": "5000.00"
        }

        message_id = enqueue_job("PROCESS_CLAIM", payload)

        assert message_id == "msg-123"
        mock_sqs.send_message.assert_called_once()
        call_args = mock_sqs.send_message.call_args[1]
        assert call_args["QueueUrl"] == "https://sqs.us-east-1.amazonaws.com/123/queue"

        # Verify message body
        body = json.loads(call_args["MessageBody"])
        assert body["job_type"] == "PROCESS_CLAIM"
        assert body["payload"] == payload

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_welcome_email(self, mock_sqs):
        """Test enqueueing WELCOME_EMAIL job"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {"MessageId": "msg-456"}

        payload = {
            "policyholder_id": "holder-123",
            "email": "user@example.com",
            "first_name": "John"
        }

        message_id = enqueue_job("WELCOME_EMAIL", payload)

        assert message_id == "msg-456"

        # Verify job type
        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["job_type"] == "WELCOME_EMAIL"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_policy_renewal_reminder(self, mock_sqs):
        """Test enqueueing POLICY_RENEWAL_REMINDER job"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {"MessageId": "msg-789"}

        payload = {
            "policy_id": "policy-123",
            "policy_number": "POL-AUTO-20260401-1234",
            "days_until_expiry": 30
        }

        message_id = enqueue_job("POLICY_RENEWAL_REMINDER", payload)

        assert message_id == "msg-789"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_message_attributes(self, mock_sqs):
        """Test job message includes correct attributes"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        enqueue_job("PROCESS_CLAIM", {"claim_id": "123"})

        call_args = mock_sqs.send_message.call_args[1]
        assert "MessageAttributes" in call_args
        assert "JobType" in call_args["MessageAttributes"]
        assert call_args["MessageAttributes"]["JobType"]["StringValue"] == "PROCESS_CLAIM"
        assert call_args["MessageAttributes"]["JobType"]["DataType"] == "String"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', '')
    def test_enqueue_job_no_queue_url_configured(self, mock_sqs):
        """Test job skipped when SQS_QUEUE_URL is not configured"""
        from src.services.queue_service import enqueue_job

        message_id = enqueue_job("PROCESS_CLAIM", {"claim_id": "123"})

        assert message_id == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', None)
    def test_enqueue_job_queue_url_none(self, mock_sqs):
        """Test job skipped when SQS_QUEUE_URL is None"""
        from src.services.queue_service import enqueue_job

        message_id = enqueue_job("WELCOME_EMAIL", {"email": "test@test.com"})

        assert message_id == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_empty_payload(self, mock_sqs):
        """Test enqueueing job with empty payload"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        message_id = enqueue_job("PROCESS_CLAIM", {})

        assert message_id == "msg-123"

        # Verify empty payload is sent
        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"] == {}

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_complex_payload(self, mock_sqs):
        """Test enqueueing job with complex nested payload"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        payload = {
            "claim_id": "claim-123",
            "metadata": {
                "source": "api",
                "version": "1.0"
            },
            "items": [1, 2, 3]
        }

        message_id = enqueue_job("PROCESS_CLAIM", payload)

        # Verify complex payload serialization
        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"] == payload

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_returns_unknown_on_missing_message_id(self, mock_sqs):
        """Test returns UNKNOWN when MessageId is missing from response"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {}  # No MessageId

        message_id = enqueue_job("PROCESS_CLAIM", {"claim_id": "123"})

        assert message_id == "UNKNOWN"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123/queue')
    def test_enqueue_job_message_body_structure(self, mock_sqs):
        """Test message body has correct structure"""
        from src.services.queue_service import enqueue_job

        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        payload = {"test": "data"}
        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])

        # Verify structure
        assert "job_type" in body
        assert "payload" in body
        assert len(body.keys()) == 2  # Only these two keys
