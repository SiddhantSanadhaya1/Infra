"""Unit tests for src.services.queue_service module."""
import json
from unittest.mock import patch, MagicMock

import pytest

from src.services.queue_service import enqueue_job


class TestEnqueueJob:
    """Test job enqueueing to SQS."""

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123/test-queue")
    def test_enqueue_job_process_claim(self, mock_sqs_client):
        """Test enqueueing a PROCESS_CLAIM job."""
        mock_sqs_client.send_message.return_value = {"MessageId": "msg-12345"}

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": "5000.00",
        }

        message_id = enqueue_job("PROCESS_CLAIM", payload)

        mock_sqs_client.send_message.assert_called_once()
        call_args = mock_sqs_client.send_message.call_args

        assert call_args[1]["QueueUrl"] == "https://sqs.us-east-1.amazonaws.com/123/test-queue"

        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["job_type"] == "PROCESS_CLAIM"
        assert message_body["payload"] == payload

        assert call_args[1]["MessageAttributes"]["JobType"]["StringValue"] == "PROCESS_CLAIM"
        assert call_args[1]["MessageAttributes"]["JobType"]["DataType"] == "String"

        assert message_id == "msg-12345"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123/queue")
    def test_enqueue_job_welcome_email(self, mock_sqs_client):
        """Test enqueueing a WELCOME_EMAIL job."""
        mock_sqs_client.send_message.return_value = {"MessageId": "msg-67890"}

        payload = {
            "policyholder_id": "ph-789",
            "email": "john@example.com",
            "first_name": "John",
        }

        message_id = enqueue_job("WELCOME_EMAIL", payload)

        mock_sqs_client.send_message.assert_called_once()
        call_args = mock_sqs_client.send_message.call_args

        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["job_type"] == "WELCOME_EMAIL"
        assert message_body["payload"]["email"] == "john@example.com"

        assert message_id == "msg-67890"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.queue.url")
    def test_enqueue_job_policy_renewal_reminder(self, mock_sqs_client):
        """Test enqueueing a POLICY_RENEWAL_REMINDER job."""
        mock_sqs_client.send_message.return_value = {"MessageId": "msg-abc123"}

        payload = {
            "policyholder_id": "ph-123",
            "policy_id": "pol-456",
            "policy_number": "POL-AUTO-20260101-1234",
            "email": "jane@example.com",
            "end_date": "2026-12-31",
            "days_until_expiry": 30,
        }

        message_id = enqueue_job("POLICY_RENEWAL_REMINDER", payload)

        mock_sqs_client.send_message.assert_called_once()
        call_args = mock_sqs_client.send_message.call_args

        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["job_type"] == "POLICY_RENEWAL_REMINDER"
        assert message_body["payload"]["days_until_expiry"] == 30

        assert message_id == "msg-abc123"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "")
    def test_enqueue_job_no_queue_url_configured(self, mock_sqs_client):
        """Test enqueueing job when SQS_QUEUE_URL is not configured."""
        payload = {"test": "data"}

        message_id = enqueue_job("PROCESS_CLAIM", payload)

        # Should not call SQS client
        mock_sqs_client.send_message.assert_not_called()
        assert message_id == "LOCAL_SKIP"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.queue.url")
    def test_enqueue_job_with_empty_payload(self, mock_sqs_client):
        """Test enqueueing job with empty payload."""
        mock_sqs_client.send_message.return_value = {"MessageId": "msg-empty"}

        message_id = enqueue_job("PROCESS_CLAIM", {})

        mock_sqs_client.send_message.assert_called_once()
        call_args = mock_sqs_client.send_message.call_args

        message_body = json.loads(call_args[1]["MessageBody"])
        assert message_body["payload"] == {}
        assert message_id == "msg-empty"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.queue.url")
    def test_enqueue_job_response_without_message_id(self, mock_sqs_client):
        """Test enqueueing job when SQS response missing MessageId."""
        mock_sqs_client.send_message.return_value = {}

        message_id = enqueue_job("WELCOME_EMAIL", {"test": "data"})

        assert message_id == "UNKNOWN"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.queue.url")
    def test_enqueue_job_message_body_is_valid_json(self, mock_sqs_client):
        """Test message body is valid JSON."""
        mock_sqs_client.send_message.return_value = {"MessageId": "msg-123"}

        payload = {"key": "value", "number": 42, "nested": {"data": "test"}}
        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs_client.send_message.call_args
        message_body = call_args[1]["MessageBody"]

        # Should be valid JSON
        parsed = json.loads(message_body)
        assert parsed["job_type"] == "PROCESS_CLAIM"
        assert parsed["payload"] == payload

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.queue.url")
    def test_enqueue_job_sets_message_attributes(self, mock_sqs_client):
        """Test job sets correct SQS message attributes."""
        mock_sqs_client.send_message.return_value = {"MessageId": "msg-123"}

        enqueue_job("PROCESS_CLAIM", {"test": "data"})

        call_args = mock_sqs_client.send_message.call_args
        attributes = call_args[1]["MessageAttributes"]

        assert "JobType" in attributes
        assert attributes["JobType"]["StringValue"] == "PROCESS_CLAIM"
        assert attributes["JobType"]["DataType"] == "String"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.queue.url")
    def test_enqueue_job_with_complex_nested_payload(self, mock_sqs_client):
        """Test enqueueing job with complex nested payload."""
        mock_sqs_client.send_message.return_value = {"MessageId": "msg-complex"}

        payload = {
            "claim_id": "claim-123",
            "metadata": {
                "files": ["file1.pdf", "file2.jpg"],
                "amounts": [100.50, 200.75],
                "nested": {"level2": {"level3": "value"}},
            },
        }

        message_id = enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs_client.send_message.call_args
        message_body = json.loads(call_args[1]["MessageBody"])

        assert message_body["payload"]["metadata"]["files"] == ["file1.pdf", "file2.jpg"]
        assert message_body["payload"]["metadata"]["nested"]["level2"]["level3"] == "value"
        assert message_id == "msg-complex"
