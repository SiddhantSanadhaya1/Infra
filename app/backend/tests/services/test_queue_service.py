"""
Unit tests for src.services.queue_service
Tests SQS job enqueueing functionality.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.services.queue_service import enqueue_job


class TestEnqueueJob:
    """Test job enqueueing to SQS"""

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_process_claim(self, mock_sqs):
        """Test enqueueing a PROCESS_CLAIM job"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-12345"}

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": "50000.00"
        }

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "msg-12345"
        mock_sqs.send_message.assert_called_once()
        call_args = mock_sqs.send_message.call_args[1]
        assert call_args["QueueUrl"] == 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue'

        message_body = json.loads(call_args["MessageBody"])
        assert message_body["job_type"] == "PROCESS_CLAIM"
        assert message_body["payload"] == payload

        assert call_args["MessageAttributes"]["JobType"]["StringValue"] == "PROCESS_CLAIM"
        assert call_args["MessageAttributes"]["JobType"]["DataType"] == "String"

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_welcome_email(self, mock_sqs):
        """Test enqueueing a WELCOME_EMAIL job"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-67890"}

        payload = {
            "policyholder_id": "holder-789",
            "email": "user@example.com",
            "first_name": "John"
        }

        result = enqueue_job("WELCOME_EMAIL", payload)

        assert result == "msg-67890"
        call_args = mock_sqs.send_message.call_args[1]
        message_body = json.loads(call_args["MessageBody"])
        assert message_body["job_type"] == "WELCOME_EMAIL"
        assert message_body["payload"]["email"] == "user@example.com"

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_policy_renewal_reminder(self, mock_sqs):
        """Test enqueueing a POLICY_RENEWAL_REMINDER job"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-reminder-001"}

        payload = {
            "policyholder_id": "holder-001",
            "policy_id": "policy-001",
            "policy_number": "POL-AUTO-20260101-0001",
            "email": "customer@example.com",
            "end_date": "2026-12-31",
            "days_until_expiry": 30
        }

        result = enqueue_job("POLICY_RENEWAL_REMINDER", payload)

        assert result == "msg-reminder-001"
        call_args = mock_sqs.send_message.call_args[1]
        message_body = json.loads(call_args["MessageBody"])
        assert message_body["job_type"] == "POLICY_RENEWAL_REMINDER"
        assert message_body["payload"]["days_until_expiry"] == 30

    @patch('src.services.queue_service.SQS_QUEUE_URL', None)
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_no_queue_url(self, mock_sqs):
        """Test enqueueing job when SQS_QUEUE_URL is not configured"""
        payload = {"claim_id": "claim-123"}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch('src.services.queue_service.SQS_QUEUE_URL', '')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_empty_queue_url(self, mock_sqs):
        """Test enqueueing job when SQS_QUEUE_URL is empty string"""
        payload = {"claim_id": "claim-456"}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "LOCAL_SKIP"
        mock_sqs.send_message.assert_not_called()

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_no_message_id_in_response(self, mock_sqs):
        """Test enqueueing job when response has no MessageId"""
        mock_sqs.send_message.return_value = {}

        payload = {"claim_id": "claim-789"}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "UNKNOWN"

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_empty_payload(self, mock_sqs):
        """Test enqueueing job with empty payload"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-empty"}

        result = enqueue_job("PROCESS_CLAIM", {})

        assert result == "msg-empty"
        call_args = mock_sqs.send_message.call_args[1]
        message_body = json.loads(call_args["MessageBody"])
        assert message_body["payload"] == {}

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_complex_payload(self, mock_sqs):
        """Test enqueueing job with complex nested payload"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-complex"}

        payload = {
            "claim_id": "claim-001",
            "metadata": {
                "user": "admin",
                "timestamp": "2026-03-30T12:00:00Z",
                "tags": ["urgent", "high-value"]
            },
            "amounts": [1000, 2000, 3000]
        }

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "msg-complex"
        call_args = mock_sqs.send_message.call_args[1]
        message_body = json.loads(call_args["MessageBody"])
        assert message_body["payload"]["metadata"]["tags"] == ["urgent", "high-value"]
        assert message_body["payload"]["amounts"] == [1000, 2000, 3000]

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_message_attributes_format(self, mock_sqs):
        """Test enqueueing job verifies MessageAttributes format"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-attr-test"}

        payload = {"test": "data"}

        enqueue_job("WELCOME_EMAIL", payload)

        call_args = mock_sqs.send_message.call_args[1]
        msg_attrs = call_args["MessageAttributes"]

        assert "JobType" in msg_attrs
        assert msg_attrs["JobType"]["StringValue"] == "WELCOME_EMAIL"
        assert msg_attrs["JobType"]["DataType"] == "String"

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_message_body_is_json_string(self, mock_sqs):
        """Test enqueueing job verifies MessageBody is JSON string"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-json"}

        payload = {"key": "value"}

        enqueue_job("PROCESS_CLAIM", payload)

        call_args = mock_sqs.send_message.call_args[1]
        message_body = call_args["MessageBody"]

        # Verify it's a string
        assert isinstance(message_body, str)

        # Verify it's valid JSON
        parsed = json.loads(message_body)
        assert parsed["job_type"] == "PROCESS_CLAIM"
        assert parsed["payload"] == payload

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_with_special_characters_in_payload(self, mock_sqs):
        """Test enqueueing job with special characters in payload"""
        mock_sqs.send_message.return_value = {"MessageId": "msg-special"}

        payload = {
            "description": "Claim with special chars: @#$%^&*()_+{}[]|\\:\";<>?,./",
            "unicode": "测试 тест"
        }

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "msg-special"
        call_args = mock_sqs.send_message.call_args[1]
        message_body = json.loads(call_args["MessageBody"])
        assert message_body["payload"]["description"] == "Claim with special chars: @#$%^&*()_+{}[]|\\:\";<>?,./"\
        assert message_body["payload"]["unicode"] == "测试 тест"

    @patch('src.services.queue_service.SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/insureco-queue')
    @patch('src.services.queue_service.sqs_client')
    def test_enqueue_job_returns_message_id_from_response(self, mock_sqs):
        """Test enqueueing job returns MessageId from SQS response"""
        mock_sqs.send_message.return_value = {
            "MessageId": "custom-message-id-12345",
            "MD5OfMessageBody": "abc123",
            "OtherField": "ignored"
        }

        payload = {"test": "data"}

        result = enqueue_job("PROCESS_CLAIM", payload)

        assert result == "custom-message-id-12345"
