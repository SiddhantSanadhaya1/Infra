"""Unit tests for Lambda worker module."""
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

import pytest

# Import worker functions
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import worker


class TestCalculateFraudScore:
    """Test fraud score calculation."""

    @patch("worker.random.randint")
    def test_calculate_fraud_score_low_amount(self, mock_randint):
        """Test fraud score for low claim amount."""
        mock_randint.return_value = 20

        score = worker.calculate_fraud_score(10000.0, "GENERAL")

        # Base score 20, no additional risk
        assert score == 20

    @patch("worker.random.randint")
    def test_calculate_fraud_score_medium_amount(self, mock_randint):
        """Test fraud score for medium claim amount."""
        mock_randint.side_effect = [20, 5]

        score = worker.calculate_fraud_score(25000.0, "GENERAL")

        # Base score 20 + 10 for amount > 20k
        assert score == 30

    @patch("worker.random.randint")
    def test_calculate_fraud_score_high_amount(self, mock_randint):
        """Test fraud score for high claim amount."""
        mock_randint.side_effect = [30, 10]

        score = worker.calculate_fraud_score(60000.0, "GENERAL")

        # Base score 30 + 20 for amount > 50k
        assert score == 50

    @patch("worker.random.randint")
    def test_calculate_fraud_score_high_risk_claim_type(self, mock_randint):
        """Test fraud score for high-risk claim types."""
        mock_randint.side_effect = [25, 12]

        score = worker.calculate_fraud_score(10000.0, "THEFT")

        # Base score 25 + risk type bonus
        assert score >= 25

    @patch("worker.random.randint")
    def test_calculate_fraud_score_collision_type(self, mock_randint):
        """Test fraud score for COLLISION claim type."""
        mock_randint.side_effect = [20, 8]

        score = worker.calculate_fraud_score(15000.0, "COLLISION")

        # COLLISION is high risk type
        assert score >= 20

    @patch("worker.random.randint")
    def test_calculate_fraud_score_liability_type(self, mock_randint):
        """Test fraud score for LIABILITY claim type."""
        mock_randint.side_effect = [15, 10]

        score = worker.calculate_fraud_score(5000.0, "LIABILITY")

        # LIABILITY is high risk type
        assert score >= 15

    @patch("worker.random.randint")
    def test_calculate_fraud_score_capped_at_100(self, mock_randint):
        """Test fraud score is capped at 100."""
        mock_randint.side_effect = [35, 15]

        score = worker.calculate_fraud_score(100000.0, "THEFT")

        # Should never exceed 100
        assert score <= 100

    @patch("worker.random.randint")
    def test_calculate_fraud_score_low_risk_type(self, mock_randint):
        """Test fraud score for low-risk claim type."""
        mock_randint.return_value = 10

        score = worker.calculate_fraud_score(5000.0, "MEDICAL")

        # Base score only
        assert score == 10

    @patch("worker.random.randint")
    def test_calculate_fraud_score_case_insensitive_type(self, mock_randint):
        """Test fraud score handles lowercase claim types."""
        mock_randint.side_effect = [20, 10]

        score = worker.calculate_fraud_score(10000.0, "theft")

        # Should handle case-insensitive matching
        assert score >= 20


class TestHandleProcessClaim:
    """Test PROCESS_CLAIM job handler."""

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test-topic")
    @patch("worker.DDB_TABLE", "test-claims-table")
    def test_handle_process_claim_low_risk(
        self, mock_fraud_score, mock_dynamo, mock_sns
    ):
        """Test processing claim with low fraud risk."""
        mock_fraud_score.return_value = 25
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": "5000.00",
            "claim_type": "MEDICAL",
        }

        worker.handle_process_claim(payload)

        # Verify DynamoDB write
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]

        assert item["claim_id"] == "claim-123"
        assert item["fraud_score"] == 25
        assert item["risk_level"] == "LOW"
        assert item["processing_status"] == "AUTO_APPROVED_FOR_REVIEW"

        # Verify SNS notification
        mock_sns.publish.assert_called_once()

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test-topic")
    @patch("worker.DDB_TABLE", "test-claims-table")
    def test_handle_process_claim_medium_risk(
        self, mock_fraud_score, mock_dynamo, mock_sns
    ):
        """Test processing claim with medium fraud risk."""
        mock_fraud_score.return_value = 55
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-456",
            "claim_number": "CLM-20260330-5678",
            "policy_id": "policy-789",
            "amount_requested": "25000.00",
            "claim_type": "COLLISION",
        }

        worker.handle_process_claim(payload)

        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]

        assert item["fraud_score"] == 55
        assert item["risk_level"] == "MEDIUM"
        assert item["processing_status"] == "MANUAL_REVIEW"

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test-topic")
    @patch("worker.DDB_TABLE", "test-claims-table")
    def test_handle_process_claim_high_risk(
        self, mock_fraud_score, mock_dynamo, mock_sns
    ):
        """Test processing claim with high fraud risk."""
        mock_fraud_score.return_value = 85
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-789",
            "claim_number": "CLM-20260330-9999",
            "policy_id": "policy-111",
            "amount_requested": "75000.00",
            "claim_type": "THEFT",
        }

        worker.handle_process_claim(payload)

        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]

        assert item["fraud_score"] == 85
        assert item["risk_level"] == "HIGH"
        assert item["processing_status"] == "FRAUD_REVIEW"

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "")
    @patch("worker.DDB_TABLE", "test-claims-table")
    def test_handle_process_claim_no_sns_topic(
        self, mock_fraud_score, mock_dynamo, mock_sns
    ):
        """Test processing claim when SNS topic not configured."""
        mock_fraud_score.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": "5000.00",
        }

        worker.handle_process_claim(payload)

        # Should still write to DynamoDB
        mock_table.put_item.assert_called_once()

        # Should not publish to SNS
        mock_sns.publish.assert_not_called()


class TestHandleWelcomeEmail:
    """Test WELCOME_EMAIL job handler."""

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test-topic")
    def test_handle_welcome_email(self, mock_sns):
        """Test sending welcome email notification."""
        payload = {
            "policyholder_id": "ph-123",
            "email": "john@example.com",
            "first_name": "John",
        }

        worker.handle_welcome_email(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args

        assert call_args[1]["TopicArn"] == "arn:aws:sns:us-east-1:123:test-topic"
        assert "Welcome to InsureCo Insurance, John!" in call_args[1]["Subject"]

        message = json.loads(call_args[1]["Message"])
        assert message["event"] == "WELCOME_EMAIL"
        assert message["email"] == "john@example.com"

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "")
    def test_handle_welcome_email_no_sns_topic(self, mock_sns):
        """Test welcome email when SNS topic not configured."""
        payload = {
            "policyholder_id": "ph-456",
            "email": "jane@example.com",
            "first_name": "Jane",
        }

        worker.handle_welcome_email(payload)

        # Should not publish when SNS not configured
        mock_sns.publish.assert_not_called()


class TestHandlePolicyRenewalReminder:
    """Test POLICY_RENEWAL_REMINDER job handler."""

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test-topic")
    def test_handle_policy_renewal_reminder(self, mock_sns):
        """Test sending policy renewal reminder."""
        payload = {
            "policyholder_id": "ph-789",
            "policy_id": "pol-123",
            "policy_number": "POL-AUTO-20260101-1234",
            "email": "customer@example.com",
            "end_date": "2026-12-31",
            "days_until_expiry": 30,
        }

        worker.handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args

        assert "Action Required" in call_args[1]["Subject"]
        assert "POL-AUTO-20260101-1234" in call_args[1]["Subject"]
        assert "30 Days" in call_args[1]["Subject"]

        message = json.loads(call_args[1]["Message"])
        assert message["event"] == "POLICY_RENEWAL_REMINDER"
        assert message["days_until_expiry"] == 30

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "")
    def test_handle_policy_renewal_reminder_no_sns_topic(self, mock_sns):
        """Test renewal reminder when SNS topic not configured."""
        payload = {
            "policy_id": "pol-456",
            "policy_number": "POL-HOME-20260101-5678",
            "days_until_expiry": 60,
        }

        worker.handle_policy_renewal_reminder(payload)

        # Should not publish when SNS not configured
        mock_sns.publish.assert_not_called()


class TestLambdaHandler:
    """Test Lambda entry point."""

    @patch("worker.handle_process_claim")
    def test_lambda_handler_single_record(self, mock_handler):
        """Test Lambda handler with single SQS record."""
        event = {
            "Records": [
                {
                    "messageId": "msg-123",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-123"},
                    }),
                }
            ]
        }

        result = worker.lambda_handler(event, None)

        mock_handler.assert_called_once_with({"claim_id": "claim-123"})
        assert result["statusCode"] == 200
        assert result["processedCount"] == 1

    @patch("worker.handle_welcome_email")
    def test_lambda_handler_welcome_email_job(self, mock_handler):
        """Test Lambda handler with WELCOME_EMAIL job."""
        event = {
            "Records": [
                {
                    "messageId": "msg-456",
                    "body": json.dumps({
                        "job_type": "WELCOME_EMAIL",
                        "payload": {"policyholder_id": "ph-123"},
                    }),
                }
            ]
        }

        result = worker.lambda_handler(event, None)

        mock_handler.assert_called_once_with({"policyholder_id": "ph-123"})
        assert result["processedCount"] == 1

    def test_lambda_handler_unknown_job_type(self):
        """Test Lambda handler skips unknown job types."""
        event = {
            "Records": [
                {
                    "messageId": "msg-789",
                    "body": json.dumps({
                        "job_type": "UNKNOWN_JOB",
                        "payload": {},
                    }),
                }
            ]
        }

        result = worker.lambda_handler(event, None)

        # Should complete successfully but skip unknown job
        assert result["statusCode"] == 200

    @patch("worker.handle_process_claim")
    def test_lambda_handler_multiple_records(self, mock_handler):
        """Test Lambda handler with multiple SQS records."""
        event = {
            "Records": [
                {
                    "messageId": "msg-1",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-1"},
                    }),
                },
                {
                    "messageId": "msg-2",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-2"},
                    }),
                },
            ]
        }

        result = worker.lambda_handler(event, None)

        assert mock_handler.call_count == 2
        assert result["processedCount"] == 2

    @patch("worker.handle_process_claim")
    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:test-topic")
    def test_lambda_handler_with_exception(self, mock_sns, mock_handler):
        """Test Lambda handler handles exceptions."""
        mock_handler.side_effect = Exception("Processing error")

        event = {
            "Records": [
                {
                    "messageId": "msg-error",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-999"},
                    }),
                }
            ]
        }

        with pytest.raises(Exception):
            worker.lambda_handler(event, None)

        # Should publish error alert to SNS
        mock_sns.publish.assert_called()
