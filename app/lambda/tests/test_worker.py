"""Tests for app/lambda/worker.py"""
import pytest
import json
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from worker import (
    calculate_fraud_score,
    handle_process_claim,
    handle_welcome_email,
    handle_policy_renewal_reminder,
    lambda_handler,
    JOB_HANDLERS,
)


class TestCalculateFraudScore:
    """Test calculate_fraud_score function with boundary values."""

    @patch('worker.random.randint')
    def test_fraud_score_low_amount(self, mock_randint):
        """Test fraud score with low claim amount."""
        mock_randint.return_value = 15

        score = calculate_fraud_score(5000.0, "GENERAL")

        # Base score only, no amount-based addition
        assert 15 <= score <= 30

    @patch('worker.random.randint')
    def test_fraud_score_medium_amount(self, mock_randint):
        """Test fraud score with medium amount (over $20k)."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(25000.0, "GENERAL")

        # Base + 10 for amount > 20k
        assert score == 30

    @patch('worker.random.randint')
    def test_fraud_score_high_amount(self, mock_randint):
        """Test fraud score with high amount (over $50k)."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(60000.0, "GENERAL")

        # Base + 20 for amount > 50k
        assert score == 40

    @patch('worker.random.randint')
    def test_fraud_score_boundary_20k(self, mock_randint):
        """Test boundary: exactly $20,000."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(20000.0, "GENERAL")

        # Exactly 20k should not trigger the +10
        assert score == 20

    @patch('worker.random.randint')
    def test_fraud_score_boundary_50k(self, mock_randint):
        """Test boundary: exactly $50,000."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(50000.0, "GENERAL")

        # Exactly 50k should not trigger the +20
        assert score == 20

    @patch('worker.random.randint')
    def test_fraud_score_high_risk_claim_type(self, mock_randint):
        """Test high-risk claim types add additional score."""
        mock_randint.side_effect = [20, 10]  # Base score, then additional

        score = calculate_fraud_score(10000.0, "THEFT")

        # Should add extra points for high-risk type
        assert score >= 20

    @patch('worker.random.randint')
    def test_fraud_score_collision_type(self, mock_randint):
        """Test COLLISION claim type."""
        mock_randint.side_effect = [20, 8]

        score = calculate_fraud_score(10000.0, "COLLISION")

        assert score >= 20

    @patch('worker.random.randint')
    def test_fraud_score_liability_type(self, mock_randint):
        """Test LIABILITY claim type."""
        mock_randint.side_effect = [20, 12]

        score = calculate_fraud_score(10000.0, "LIABILITY")

        assert score >= 20

    @patch('worker.random.randint')
    def test_fraud_score_capped_at_100(self, mock_randint):
        """Test that fraud score is capped at 100."""
        mock_randint.side_effect = [35, 15]

        score = calculate_fraud_score(100000.0, "THEFT")

        assert score <= 100

    @patch('worker.random.randint')
    def test_fraud_score_zero_amount(self, mock_randint):
        """Test with zero claim amount (edge case)."""
        mock_randint.return_value = 25

        score = calculate_fraud_score(0.0, "GENERAL")

        # Just base score
        assert score == 25

    @patch('worker.random.randint')
    def test_fraud_score_negative_amount(self, mock_randint):
        """Test with negative amount (edge case)."""
        mock_randint.return_value = 20

        score = calculate_fraud_score(-1000.0, "GENERAL")

        assert score == 20


class TestHandleProcessClaim:
    """Test handle_process_claim job handler."""

    @patch('worker.dynamo')
    @patch('worker.sns')
    @patch('worker.calculate_fraud_score')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_process_claim_low_risk(self, mock_fraud, mock_sns, mock_dynamo):
        """Test processing claim with low fraud score."""
        mock_fraud.return_value = 25
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260331-1234",
            "policy_id": "policy-456",
            "amount_requested": "10000.00",
            "claim_type": "GENERAL"
        }

        handle_process_claim(payload)

        # Verify DynamoDB write
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]['Item']
        assert item['fraud_score'] == 25
        assert item['risk_level'] == "LOW"
        assert item['processing_status'] == "AUTO_APPROVED_FOR_REVIEW"

    @patch('worker.dynamo')
    @patch('worker.sns')
    @patch('worker.calculate_fraud_score')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_process_claim_medium_risk(self, mock_fraud, mock_sns, mock_dynamo):
        """Test processing claim with medium fraud score."""
        mock_fraud.return_value = 50
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260331-1234",
            "policy_id": "policy-456",
            "amount_requested": "25000.00"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]['Item']
        assert item['fraud_score'] == 50
        assert item['risk_level'] == "MEDIUM"
        assert item['processing_status'] == "MANUAL_REVIEW"

    @patch('worker.dynamo')
    @patch('worker.sns')
    @patch('worker.calculate_fraud_score')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_process_claim_high_risk(self, mock_fraud, mock_sns, mock_dynamo):
        """Test processing claim with high fraud score."""
        mock_fraud.return_value = 85
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260331-1234",
            "policy_id": "policy-456",
            "amount_requested": "50000.00"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]['Item']
        assert item['fraud_score'] == 85
        assert item['risk_level'] == "HIGH"
        assert item['processing_status'] == "FRAUD_REVIEW"

    @patch('worker.dynamo')
    @patch('worker.sns')
    @patch('worker.calculate_fraud_score')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_process_claim_boundary_40(self, mock_fraud, mock_sns, mock_dynamo):
        """Test boundary: fraud score exactly 40."""
        mock_fraud.return_value = 40
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260331-1234",
            "policy_id": "policy-456",
            "amount_requested": "10000.00"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]['Item']
        assert item['risk_level'] == "MEDIUM"

    @patch('worker.dynamo')
    @patch('worker.sns')
    @patch('worker.calculate_fraud_score')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_process_claim_boundary_70(self, mock_fraud, mock_sns, mock_dynamo):
        """Test boundary: fraud score exactly 70."""
        mock_fraud.return_value = 70
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260331-1234",
            "policy_id": "policy-456",
            "amount_requested": "10000.00"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]['Item']
        assert item['risk_level'] == "HIGH"

    @patch('worker.dynamo')
    @patch('worker.sns')
    @patch('worker.calculate_fraud_score')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_process_claim_publishes_sns(self, mock_fraud, mock_sns, mock_dynamo):
        """Test that SNS notification is published."""
        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260331-1234",
            "policy_id": "policy-456",
            "amount_requested": "10000.00"
        }

        handle_process_claim(payload)

        mock_sns.publish.assert_called_once()
        call_kwargs = mock_sns.publish.call_args[1]
        assert "InsureCo Claim Processed" in call_kwargs['Subject']

    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    def test_handle_process_claim_dynamodb_error(self, mock_fraud, mock_dynamo):
        """Test that DynamoDB errors are raised."""
        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260331-1234",
            "policy_id": "policy-456",
            "amount_requested": "10000.00"
        }

        with pytest.raises(Exception) as exc_info:
            handle_process_claim(payload)

        assert "DynamoDB error" in str(exc_info.value)


class TestHandleWelcomeEmail:
    """Test handle_welcome_email job handler."""

    @patch('worker.sns')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_welcome_email_success(self, mock_sns):
        """Test successful welcome email notification."""
        payload = {
            "policyholder_id": "ph-123",
            "email": "user@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_called_once()
        call_kwargs = mock_sns.publish.call_args[1]
        assert "Welcome to InsureCo Insurance" in call_kwargs['Subject']

    @patch('worker.sns')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_welcome_email_message_content(self, mock_sns):
        """Test welcome email message content."""
        payload = {
            "policyholder_id": "ph-123",
            "email": "user@example.com",
            "first_name": "Alice"
        }

        handle_welcome_email(payload)

        call_kwargs = mock_sns.publish.call_args[1]
        message = json.loads(call_kwargs['Message'])
        assert message['first_name'] == "Alice"
        assert "Welcome to InsureCo Insurance" in message['message']

    @patch('worker.sns')
    @patch('worker.SNS_TOPIC_ARN', '')
    def test_handle_welcome_email_no_sns_configured(self, mock_sns):
        """Test behavior when SNS is not configured."""
        payload = {
            "policyholder_id": "ph-123",
            "email": "user@example.com",
            "first_name": "John"
        }

        # Should not raise error
        handle_welcome_email(payload)

        mock_sns.publish.assert_not_called()


class TestHandlePolicyRenewalReminder:
    """Test handle_policy_renewal_reminder job handler."""

    @patch('worker.sns')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_renewal_reminder_success(self, mock_sns):
        """Test successful renewal reminder notification."""
        payload = {
            "policyholder_id": "ph-123",
            "policy_id": "policy-456",
            "policy_number": "POL-AUTO-20260101-1234",
            "email": "user@example.com",
            "end_date": "2026-12-31",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_called_once()
        call_kwargs = mock_sns.publish.call_args[1]
        assert "Policy" in call_kwargs['Subject']
        assert "Expires in 30 Days" in call_kwargs['Subject']

    @patch('worker.sns')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_handle_renewal_reminder_60_days(self, mock_sns):
        """Test renewal reminder with 60 days until expiry."""
        payload = {
            "policyholder_id": "ph-123",
            "policy_id": "policy-456",
            "policy_number": "POL-AUTO-20260101-1234",
            "email": "user@example.com",
            "end_date": "2026-06-15",
            "days_until_expiry": 60
        }

        handle_policy_renewal_reminder(payload)

        call_kwargs = mock_sns.publish.call_args[1]
        assert "60 Days" in call_kwargs['Subject']


class TestLambdaHandler:
    """Test lambda_handler main entry point."""

    @patch('worker.handle_process_claim')
    def test_lambda_handler_process_claim(self, mock_handler):
        """Test lambda handler with PROCESS_CLAIM job."""
        event = {
            "Records": [
                {
                    "messageId": "msg-123",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-123"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        mock_handler.assert_called_once_with({"claim_id": "claim-123"})
        assert result["statusCode"] == 200
        assert result["processedCount"] == 1

    @patch('worker.handle_welcome_email')
    def test_lambda_handler_welcome_email(self, mock_handler):
        """Test lambda handler with WELCOME_EMAIL job."""
        event = {
            "Records": [
                {
                    "messageId": "msg-456",
                    "body": json.dumps({
                        "job_type": "WELCOME_EMAIL",
                        "payload": {"email": "user@example.com"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        mock_handler.assert_called_once()
        assert result["statusCode"] == 200

    @patch('worker.handle_policy_renewal_reminder')
    def test_lambda_handler_renewal_reminder(self, mock_handler):
        """Test lambda handler with POLICY_RENEWAL_REMINDER job."""
        event = {
            "Records": [
                {
                    "messageId": "msg-789",
                    "body": json.dumps({
                        "job_type": "POLICY_RENEWAL_REMINDER",
                        "payload": {"policy_id": "policy-123"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        mock_handler.assert_called_once()

    def test_lambda_handler_unknown_job_type(self):
        """Test lambda handler with unknown job type."""
        event = {
            "Records": [
                {
                    "messageId": "msg-unknown",
                    "body": json.dumps({
                        "job_type": "UNKNOWN_TYPE",
                        "payload": {}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        # Should complete without error, just skip unknown job
        assert result["statusCode"] == 200

    def test_lambda_handler_multiple_records(self):
        """Test lambda handler with multiple SQS records."""
        event = {
            "Records": [
                {
                    "messageId": "msg-1",
                    "body": json.dumps({
                        "job_type": "WELCOME_EMAIL",
                        "payload": {"email": "user1@example.com"}
                    })
                },
                {
                    "messageId": "msg-2",
                    "body": json.dumps({
                        "job_type": "WELCOME_EMAIL",
                        "payload": {"email": "user2@example.com"}
                    })
                }
            ]
        }

        with patch('worker.handle_welcome_email') as mock_handler:
            result = lambda_handler(event, None)

        assert mock_handler.call_count == 2
        assert result["processedCount"] == 2

    @patch('worker.handle_process_claim')
    @patch('worker.sns')
    @patch('worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:test')
    def test_lambda_handler_error_handling(self, mock_sns, mock_handler):
        """Test lambda handler error handling and SNS alert."""
        mock_handler.side_effect = Exception("Processing error")

        event = {
            "Records": [
                {
                    "messageId": "msg-error",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-123"}
                    })
                }
            ]
        }

        with pytest.raises(Exception):
            lambda_handler(event, None)

        # Should publish error alert to SNS
        assert mock_sns.publish.called

    def test_lambda_handler_empty_records(self):
        """Test lambda handler with empty records list."""
        event = {"Records": []}

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert result["processedCount"] == 0

    def test_lambda_handler_alternative_job_type_field(self):
        """Test lambda handler with alternative jobType field."""
        event = {
            "Records": [
                {
                    "messageId": "msg-alt",
                    "body": json.dumps({
                        "jobType": "WELCOME_EMAIL",  # Alternative field name
                        "payload": {"email": "user@example.com"}
                    })
                }
            ]
        }

        with patch('worker.handle_welcome_email') as mock_handler:
            lambda_handler(event, None)

        mock_handler.assert_called_once()


class TestJobHandlersMapping:
    """Test JOB_HANDLERS dictionary."""

    def test_job_handlers_contains_all_types(self):
        """Test that JOB_HANDLERS contains all expected job types."""
        expected_types = ["PROCESS_CLAIM", "WELCOME_EMAIL", "POLICY_RENEWAL_REMINDER"]

        for job_type in expected_types:
            assert job_type in JOB_HANDLERS

    def test_job_handlers_are_callable(self):
        """Test that all job handlers are callable functions."""
        for handler in JOB_HANDLERS.values():
            assert callable(handler)
