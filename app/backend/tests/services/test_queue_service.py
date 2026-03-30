import pytest
import json
from unittest.mock import patch, Mock

from src.services.queue_service import enqueue_job


class TestEnqueueJob:
    """Test suite for enqueue_job function."""

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_success(self, mock_sqs):
        """Test successful job enqueueing."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {"claim_id": "claim-123", "amount": 5000}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "msg-123"
        mock_sqs.send_message.assert_called_once()

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_correct_message_structure(self, mock_sqs):
        """Test that message body has correct structure."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {"claim_id": "claim-456"}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])

        assert message_body["job_type"] == "PROCESS_CLAIM"
        assert message_body["payload"] == payload

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_process_claim(self, mock_sqs):
        """Test enqueueing PROCESS_CLAIM job type."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": "5000.00"
        }

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args
        assert call_args[1]["MessageAttributes"]["JobType"]["StringValue"] == "PROCESS_CLAIM"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_welcome_email(self, mock_sqs):
        """Test enqueueing WELCOME_EMAIL job type."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-456"}
        payload = {
            "policyholder_id": "holder-123",
            "email": "test@example.com",
            "first_name": "John"
        }

        enqueue_job("WELCOME_EMAIL", payload)

        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["job_type"] == "WELCOME_EMAIL"
        assert message_body["payload"]["email"] == "test@example.com"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_policy_renewal_reminder(self, mock_sqs):
        """Test enqueueing POLICY_RENEWAL_REMINDER job type."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-789"}
        payload = {
            "policy_id": "policy-123",
            "policy_number": "POL-AUTO-20260330-1234",
            "days_until_expiry": 30
        }

        enqueue_job("POLICY_RENEWAL_REMINDER", payload)

        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["job_type"] == "POLICY_RENEWAL_REMINDER"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_message_attributes(self, mock_sqs):
        """Test that message attributes are set correctly."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {"test": "data"}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args
        attributes = call_args[1]["MessageAttributes"]

        assert "JobType" in attributes
        assert attributes["JobType"]["StringValue"] == "PROCESS_CLAIM"
        assert attributes["JobType"]["DataType"] == "String"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_queue_url(self, mock_sqs):
        """Test that correct queue URL is used."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {"test": "data"}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args
        assert call_args[1]["QueueUrl"] == "https://sqs.us-east-1.amazonaws.com/123456/test-queue"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "")
    def test_enqueue_job_no_queue_url_configured(self, mock_sqs):
        """Test behavior when SQS_QUEUE_URL is not configured."""
        payload = {"test": "data"}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", None)
    def test_enqueue_job_none_queue_url(self, mock_sqs):
        """Test behavior when SQS_QUEUE_URL is None."""
        payload = {"test": "data"}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_empty_payload(self, mock_sqs):
        """Test enqueueing job with empty payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {}

        result = enqueue_job("WELCOME_EMAIL", payload)

        assert result == "msg-123"
        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["payload"] == {}

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_complex_payload(self, mock_sqs):
        """Test enqueueing job with complex nested payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {
            "claim": {
                "id": "claim-123",
                "amount": 5000.00,
                "items": ["item1", "item2"],
                "metadata": {"key": "value"}
            }
        }

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["payload"] == payload

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    def test_enqueue_job_no_message_id_in_response(self, mock_sqs):
        """Test handling when MessageId is missing in response."""
        mock_sqs.send_message.return_value = {}
        payload = {"test": "data"}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "UNKNOWN"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456/test-queue")
    @pytest.mark.parametrize("job_type,payload", [
        ("PROCESS_CLAIM", {"claim_id": "123"}),
        ("WELCOME_EMAIL", {"email": "test@example.com"}),
        ("POLICY_RENEWAL_REMINDER", {"policy_id": "456"}),
    ])
    def test_enqueue_job_various_job_types(self, mock_sqs, job_type, payload):
        """Test enqueueing various job types."""
        mock_sqs.send_message.return_value = {"MessageId": f"msg-{job_type}"}

        result = enqueue_job(job_type, payload)

        assert result == f"msg-{job_type}"
        call_args = mock_sqs.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["job_type"] == job_type
