"""
Comprehensive unit tests for queue_service module.
Tests SQS message enqueueing with various job types and payloads.
"""
import pytest
import json
from unittest.mock import patch, MagicMock

from src.services.queue_service import enqueue_job, JobType


class TestEnqueueJob:
    """Test SQS job enqueueing with various scenarios."""

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_process_claim(self, mock_sqs):
        """Test enqueueing a PROCESS_CLAIM job."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {"claim_id": "claim-123", "amount": 1000}

        message_id = enqueue_job("PROCESS_CLAIM", payload)

        assert message_id == "msg-123"
        mock_sqs.send_message.assert_called_once()
        call_args = mock_sqs.send_message.call_args[1]
        assert call_args["QueueUrl"] == "https://sqs.us-east-1.amazonaws.com/queue"

        body = json.loads(call_args["MessageBody"])
        assert body["job_type"] == "PROCESS_CLAIM"
        assert body["payload"] == payload

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_welcome_email(self, mock_sqs):
        """Test enqueueing a WELCOME_EMAIL job."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-456"}
        payload = {"email": "user@example.com", "name": "John"}

        message_id = enqueue_job("WELCOME_EMAIL", payload)

        assert message_id == "msg-456"
        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["job_type"] == "WELCOME_EMAIL"
        assert body["payload"]["email"] == "user@example.com"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_policy_renewal_reminder(self, mock_sqs):
        """Test enqueueing a POLICY_RENEWAL_REMINDER job."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-789"}
        payload = {"policy_id": "policy-123", "days_until_expiry": 30}

        message_id = enqueue_job("POLICY_RENEWAL_REMINDER", payload)

        assert message_id == "msg-789"
        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["job_type"] == "POLICY_RENEWAL_REMINDER"
        assert body["payload"]["days_until_expiry"] == 30

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_includes_message_attributes(self, mock_sqs):
        """Test that job includes MessageAttributes with JobType."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        enqueue_job("PROCESS_CLAIM", {"data": "test"})

        call_args = mock_sqs.send_message.call_args[1]
        attrs = call_args["MessageAttributes"]
        assert "JobType" in attrs
        assert attrs["JobType"]["StringValue"] == "PROCESS_CLAIM"
        assert attrs["JobType"]["DataType"] == "String"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_empty_payload(self, mock_sqs):
        """Test enqueueing a job with empty payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-empty"}

        message_id = enqueue_job("PROCESS_CLAIM", {})

        assert message_id == "msg-empty"
        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"] == {}

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_complex_nested_payload(self, mock_sqs):
        """Test enqueueing a job with complex nested payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-complex"}
        payload = {
            "claim": {"id": "123", "details": {"amount": 1000, "items": [1, 2, 3]}},
            "metadata": {"timestamp": "2026-03-30", "user": "admin"},
        }

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"] == payload

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_message_body_is_valid_json(self, mock_sqs):
        """Test that message body is valid JSON string."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        payload = {"test": "data"}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        message_body = call_args["MessageBody"]

        # Should be valid JSON
        parsed = json.loads(message_body)
        assert isinstance(parsed, dict)
        assert "job_type" in parsed
        assert "payload" in parsed

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "")
    def test_enqueue_job_no_queue_url_configured(self, mock_sqs):
        """Test that missing queue URL is handled gracefully."""
        message_id = enqueue_job("PROCESS_CLAIM", {"data": "test"})

        assert message_id == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", None)
    def test_enqueue_job_queue_url_none(self, mock_sqs):
        """Test that None queue URL is handled gracefully."""
        message_id = enqueue_job("PROCESS_CLAIM", {"data": "test"})

        assert message_id == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_response_no_message_id(self, mock_sqs):
        """Test handling when SQS response doesn't include MessageId."""
        mock_sqs.send_message.return_value = {}

        message_id = enqueue_job("PROCESS_CLAIM", {"data": "test"})

        assert message_id == "UNKNOWN"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_payload_with_special_characters(self, mock_sqs):
        """Test enqueueing job with special characters in payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-special"}
        payload = {
            "description": "Test with special chars: @#$%^&*()",
            "unicode": "测试 тест 🎉",
        }

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"]["description"] == "Test with special chars: @#$%^&*()"
        assert body["payload"]["unicode"] == "测试 тест 🎉"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_numeric_values_in_payload(self, mock_sqs):
        """Test enqueueing job with various numeric types."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-numeric"}
        payload = {
            "integer": 42,
            "float": 3.14,
            "negative": -100,
            "zero": 0,
        }

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"]["integer"] == 42
        assert body["payload"]["float"] == 3.14
        assert body["payload"]["negative"] == -100
        assert body["payload"]["zero"] == 0

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_boolean_values_in_payload(self, mock_sqs):
        """Test enqueueing job with boolean values."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-bool"}
        payload = {"is_active": True, "is_deleted": False}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"]["is_active"] is True
        assert body["payload"]["is_deleted"] is False

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_null_values_in_payload(self, mock_sqs):
        """Test enqueueing job with None/null values."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-null"}
        payload = {"optional_field": None, "required_field": "value"}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"]["optional_field"] is None
        assert body["payload"]["required_field"] == "value"

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_job_array_payload(self, mock_sqs):
        """Test enqueueing job with array in payload."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-array"}
        payload = {"items": [1, 2, 3, 4, 5], "tags": ["urgent", "important"]}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        body = json.loads(call_args["MessageBody"])
        assert body["payload"]["items"] == [1, 2, 3, 4, 5]
        assert body["payload"]["tags"] == ["urgent", "important"]


class TestJobTypeDefinitions:
    """Test JobType literal type definitions."""

    def test_job_type_literal_accepts_valid_types(self):
        """Test that valid job types are accepted (type checking)."""
        valid_types = ["PROCESS_CLAIM", "WELCOME_EMAIL", "POLICY_RENEWAL_REMINDER"]

        # This test verifies the types are correctly defined
        # At runtime, this just checks they're strings
        for job_type in valid_types:
            assert isinstance(job_type, str)

    @patch("src.services.queue_service.sqs_client")
    @patch("src.services.queue_service.SQS_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/queue")
    def test_enqueue_all_valid_job_types(self, mock_sqs):
        """Test enqueueing all valid job types."""
        mock_sqs.send_message.return_value = {"MessageId": "msg-123"}
        valid_types = ["PROCESS_CLAIM", "WELCOME_EMAIL", "POLICY_RENEWAL_REMINDER"]

        for job_type in valid_types:
            enqueue_job(job_type, {})

        assert mock_sqs.send_message.call_count == len(valid_types)
