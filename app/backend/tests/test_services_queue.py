"""Tests for src/services/queue_service.py"""
import pytest
import json
from unittest.mock import MagicMock, patch

from src.services.queue_service import enqueue_job


class TestEnqueueJob:
    """Test enqueue_job function."""

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_process_claim(self, mock_sqs):
        """Test enqueueing a PROCESS_CLAIM job."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-12345"}

        payload = {
            "claim_id": "claim-123",
            "amount": "10000.00"
        }
        message_id = enqueue_job("PROCESS_CLAIM", payload)

        assert message_id == "msg-12345"
        mock_sqs.send_message.assert_called_once()
        call_kwargs = mock_sqs.send_message.call_args[1]
        assert call_kwargs['QueueUrl'] == 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_welcome_email(self, mock_sqs):
        """Test enqueueing a WELCOME_EMAIL job."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-67890"}

        payload = {
            "email": "user@example.com",
            "name": "John Doe"
        }
        message_id = enqueue_job("WELCOME_EMAIL", payload)

        assert message_id == "msg-67890"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_policy_renewal_reminder(self, mock_sqs):
        """Test enqueueing a POLICY_RENEWAL_REMINDER job."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-reminder"}

        payload = {
            "policy_id": "policy-456",
            "days_until_expiry": 30
        }
        message_id = enqueue_job("POLICY_RENEWAL_REMINDER", payload)

        assert message_id == "msg-reminder"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_message_body_format(self, mock_sqs):
        """Test that message body is correctly formatted as JSON."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-test"}

        payload = {"key": "value", "number": 42}
        enqueue_job("PROCESS_CLAIM", payload)

        call_kwargs = mock_sqs.send_message.call_args[1]
        message_body = call_kwargs['MessageBody']
        parsed = json.loads(message_body)

        assert parsed['job_type'] == "PROCESS_CLAIM"
        assert parsed['payload'] == payload

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_message_attributes(self, mock_sqs):
        """Test that message attributes include job type."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-test"}

        enqueue_job("PROCESS_CLAIM", {"data": "test"})

        call_kwargs = mock_sqs.send_message.call_args[1]
        attributes = call_kwargs['MessageAttributes']

        assert 'JobType' in attributes
        assert attributes['JobType']['StringValue'] == "PROCESS_CLAIM"
        assert attributes['JobType']['DataType'] == "String"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', '')
    def test_enqueue_job_no_queue_url(self, mock_sqs):
        """Test behavior when SQS_QUEUE_URL is not configured."""
        payload = {"test": "data"}
        message_id = enqueue_job("PROCESS_CLAIM", payload)

        # Should return LOCAL_SKIP and not call SQS
        assert message_id == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_empty_payload(self, mock_sqs):
        """Test enqueueing job with empty payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-empty"}

        message_id = enqueue_job("PROCESS_CLAIM", {})

        assert message_id == "msg-empty"
        call_kwargs = mock_sqs.send_message.call_args[1]
        message_body = call_kwargs['MessageBody']
        parsed = json.loads(message_body)
        assert parsed['payload'] == {}

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_complex_payload(self, mock_sqs):
        """Test enqueueing job with complex nested payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-complex"}

        payload = {
            "nested": {"key": {"deep": "value"}},
            "list": [1, 2, 3],
            "null": None,
            "bool": True
        }
        message_id = enqueue_job("PROCESS_CLAIM", payload)

        assert message_id == "msg-complex"
        call_kwargs = mock_sqs.send_message.call_args[1]
        message_body = call_kwargs['MessageBody']
        parsed = json.loads(message_body)
        assert parsed['payload'] == payload

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_no_message_id_in_response(self, mock_sqs):
        """Test handling when response doesn't contain MessageId."""
        mock_sqs.send_message.return_value = {}

        message_id = enqueue_job("PROCESS_CLAIM", {"test": "data"})

        assert message_id == "UNKNOWN"

    @patch('src.services.queue_service.sqs_client')
    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue')
    def test_enqueue_job_sqs_exception(self, mock_sqs):
        """Test that SQS exceptions are propagated."""
        mock_sqs.send_message.side_effect = Exception("SQS error")

        with pytest.raises(Exception) as exc_info:
            enqueue_job("PROCESS_CLAIM", {"test": "data"})

        assert "SQS error" in str(exc_info.value)
