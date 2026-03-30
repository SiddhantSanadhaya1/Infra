import pytest
import json
from datetime import datetime, timezone
from unittest.mock import patch, Mock, MagicMock

import sys
sys.path.insert(0, "/app/workspace/43e204c8-1a4b-47a4-8293-220cb9160890/Infra/app")

from lambda.worker import (
    calculate_fraud_score,
    handle_process_claim,
    handle_welcome_email,
    handle_policy_renewal_reminder,
    lambda_handler,
)


class TestCalculateFraudScore:
    """Test suite for calculate_fraud_score function in Lambda worker."""

    def test_calculate_fraud_score_returns_integer(self):
        """Test that fraud score returns an integer."""
        result = calculate_fraud_score(10000.0, "AUTO")
        assert isinstance(result, int)

    def test_calculate_fraud_score_within_range(self):
        """Test that fraud score is between 0 and 100."""
        result = calculate_fraud_score(10000.0, "HOME")
        assert 0 <= result <= 100

    def test_calculate_fraud_score_high_amount(self):
        """Test fraud score for amount over $50k."""
        scores = [calculate_fraud_score(60000.0, "AUTO") for _ in range(10)]
        avg_score = sum(scores) / len(scores)
        # Should have +20 bonus for >50k
        assert avg_score > 25

    def test_calculate_fraud_score_medium_amount(self):
        """Test fraud score for amount between $20k-$50k."""
        scores = [calculate_fraud_score(30000.0, "HOME") for _ in range(10)]
        avg_score = sum(scores) / len(scores)
        # Should have +10 bonus for >20k
        assert avg_score > 15

    def test_calculate_fraud_score_low_amount(self):
        """Test fraud score for amount under $20k."""
        result = calculate_fraud_score(10000.0, "LIFE")
        # No amount bonus, just base score
        assert 5 <= result <= 50  # base range + maybe type bonus

    def test_calculate_fraud_score_high_risk_types(self):
        """Test fraud score for high-risk claim types."""
        scores_theft = [calculate_fraud_score(25000.0, "THEFT") for _ in range(10)]
        scores_collision = [calculate_fraud_score(25000.0, "COLLISION") for _ in range(10)]

        avg_theft = sum(scores_theft) / len(scores_theft)
        avg_collision = sum(scores_collision) / len(scores_collision)

        # High risk types should have higher average scores
        assert avg_theft > 15
        assert avg_collision > 15

    def test_calculate_fraud_score_low_risk_type(self):
        """Test fraud score for low-risk claim type."""
        result = calculate_fraud_score(10000.0, "medical")
        assert 0 <= result <= 100

    def test_calculate_fraud_score_max_cap(self):
        """Test that fraud score never exceeds 100."""
        result = calculate_fraud_score(999999.0, "THEFT")
        assert result == 100

    def test_calculate_fraud_score_zero_amount(self):
        """Test fraud score with zero amount."""
        result = calculate_fraud_score(0.0, "AUTO")
        assert 0 <= result <= 100

    @pytest.mark.parametrize("claim_type", [
        "THEFT",
        "COLLISION",
        "LIABILITY",
        "theft",  # lowercase
        "Theft",  # mixed case
    ])
    def test_calculate_fraud_score_various_high_risk_types(self, claim_type):
        """Test fraud scores for various high-risk claim types."""
        result = calculate_fraud_score(25000.0, claim_type)
        assert 0 <= result <= 100

    def test_calculate_fraud_score_randomness(self):
        """Test that fraud score has random component."""
        scores = [calculate_fraud_score(25000.0, "AUTO") for _ in range(20)]
        # Should not all be identical
        assert len(set(scores)) > 1


class TestHandleProcessClaim:
    """Test suite for handle_process_claim function."""

    @patch("lambda.worker.sns")
    @patch("lambda.worker.dynamo")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    @patch("lambda.worker.DDB_TABLE", "test-table")
    def test_handle_process_claim_success(self, mock_dynamo, mock_sns):
        """Test successful claim processing."""
        mock_table = Mock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": 5000.0,
            "claim_type": "AUTO"
        }

        handle_process_claim(payload)

        mock_table.put_item.assert_called_once()
        mock_sns.publish.assert_called_once()

    @patch("lambda.worker.sns")
    @patch("lambda.worker.dynamo")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_process_claim_dynamodb_record(self, mock_dynamo, mock_sns):
        """Test that DynamoDB record contains correct fields."""
        mock_table = Mock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": 30000.0,
            "claim_type": "COLLISION"
        }

        handle_process_claim(payload)

        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"]

        assert item["claim_id"] == "claim-123"
        assert item["claim_number"] == "CLM-20260330-1234"
        assert item["policy_id"] == "policy-456"
        assert "fraud_score" in item
        assert "risk_level" in item
        assert "processing_status" in item

    @patch("lambda.worker.sns")
    @patch("lambda.worker.dynamo")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_process_claim_high_fraud_score(self, mock_dynamo, mock_sns):
        """Test claim processing with high fraud score."""
        mock_table = Mock()
        mock_dynamo.Table.return_value = mock_table

        with patch("lambda.worker.calculate_fraud_score", return_value=75):
            payload = {
                "claim_id": "claim-123",
                "claim_number": "CLM-20260330-1234",
                "policy_id": "policy-456",
                "amount_requested": 60000.0,
                "claim_type": "THEFT"
            }

            handle_process_claim(payload)

            call_args = mock_table.put_item.call_args
            item = call_args[1]["Item"]
            assert item["risk_level"] == "HIGH"
            assert item["processing_status"] == "FRAUD_REVIEW"

    @patch("lambda.worker.sns")
    @patch("lambda.worker.dynamo")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_process_claim_medium_fraud_score(self, mock_dynamo, mock_sns):
        """Test claim processing with medium fraud score."""
        mock_table = Mock()
        mock_dynamo.Table.return_value = mock_table

        with patch("lambda.worker.calculate_fraud_score", return_value=50):
            payload = {
                "claim_id": "claim-456",
                "claim_number": "CLM-20260330-5678",
                "policy_id": "policy-789",
                "amount_requested": 25000.0,
                "claim_type": "AUTO"
            }

            handle_process_claim(payload)

            call_args = mock_table.put_item.call_args
            item = call_args[1]["Item"]
            assert item["risk_level"] == "MEDIUM"
            assert item["processing_status"] == "MANUAL_REVIEW"

    @patch("lambda.worker.sns")
    @patch("lambda.worker.dynamo")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_process_claim_low_fraud_score(self, mock_dynamo, mock_sns):
        """Test claim processing with low fraud score."""
        mock_table = Mock()
        mock_dynamo.Table.return_value = mock_table

        with patch("lambda.worker.calculate_fraud_score", return_value=25):
            payload = {
                "claim_id": "claim-789",
                "claim_number": "CLM-20260330-9012",
                "policy_id": "policy-123",
                "amount_requested": 5000.0,
                "claim_type": "HOME"
            }

            handle_process_claim(payload)

            call_args = mock_table.put_item.call_args
            item = call_args[1]["Item"]
            assert item["risk_level"] == "LOW"
            assert item["processing_status"] == "AUTO_APPROVED_FOR_REVIEW"

    @patch("lambda.worker.sns")
    @patch("lambda.worker.dynamo")
    @patch("lambda.worker.SNS_TOPIC_ARN", "")
    def test_handle_process_claim_no_sns_topic(self, mock_dynamo, mock_sns):
        """Test claim processing when SNS topic is not configured."""
        mock_table = Mock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": 5000.0,
            "claim_type": "AUTO"
        }

        handle_process_claim(payload)

        mock_table.put_item.assert_called_once()
        mock_sns.publish.assert_not_called()


class TestHandleWelcomeEmail:
    """Test suite for handle_welcome_email function."""

    @patch("lambda.worker.sns")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_welcome_email_success(self, mock_sns):
        """Test successful welcome email sending."""
        payload = {
            "policyholder_id": "holder-123",
            "email": "test@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_called_once()

    @patch("lambda.worker.sns")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_welcome_email_message_content(self, mock_sns):
        """Test that welcome email message contains correct content."""
        payload = {
            "policyholder_id": "holder-456",
            "email": "jane@example.com",
            "first_name": "Jane"
        }

        handle_welcome_email(payload)

        call_args = mock_sns.publish.call_args
        message = json.loads(call_args[1]["Message"])

        assert message["event"] == "WELCOME_EMAIL"
        assert message["policyholder_id"] == "holder-456"
        assert message["email"] == "jane@example.com"
        assert message["first_name"] == "Jane"
        assert "Welcome to InsureCo Insurance, Jane!" in message["message"]

    @patch("lambda.worker.sns")
    @patch("lambda.worker.SNS_TOPIC_ARN", "")
    def test_handle_welcome_email_no_sns_topic(self, mock_sns):
        """Test welcome email when SNS topic is not configured."""
        payload = {
            "policyholder_id": "holder-123",
            "email": "test@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_not_called()


class TestHandlePolicyRenewalReminder:
    """Test suite for handle_policy_renewal_reminder function."""

    @patch("lambda.worker.sns")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_policy_renewal_reminder_success(self, mock_sns):
        """Test successful renewal reminder sending."""
        payload = {
            "policyholder_id": "holder-123",
            "policy_id": "policy-456",
            "policy_number": "POL-AUTO-20260330-1234",
            "email": "test@example.com",
            "end_date": "2026-06-30",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_called_once()

    @patch("lambda.worker.sns")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_handle_policy_renewal_reminder_message_content(self, mock_sns):
        """Test that renewal reminder message contains correct content."""
        payload = {
            "policyholder_id": "holder-789",
            "policy_id": "policy-123",
            "policy_number": "POL-HOME-20260330-5678",
            "email": "user@example.com",
            "end_date": "2026-05-15",
            "days_until_expiry": 60
        }

        handle_policy_renewal_reminder(payload)

        call_args = mock_sns.publish.call_args
        message = json.loads(call_args[1]["Message"])

        assert message["event"] == "POLICY_RENEWAL_REMINDER"
        assert message["policy_number"] == "POL-HOME-20260330-5678"
        assert message["days_until_expiry"] == 60
        assert "expires in 60 days" in message["message"]

    @patch("lambda.worker.sns")
    @patch("lambda.worker.SNS_TOPIC_ARN", "")
    def test_handle_policy_renewal_reminder_no_sns_topic(self, mock_sns):
        """Test renewal reminder when SNS topic is not configured."""
        payload = {
            "policyholder_id": "holder-123",
            "policy_id": "policy-456",
            "policy_number": "POL-AUTO-20260330-1234",
            "email": "test@example.com",
            "end_date": "2026-06-30",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_not_called()


class TestLambdaHandler:
    """Test suite for lambda_handler function."""

    @patch("lambda.worker.handle_process_claim")
    def test_lambda_handler_process_claim(self, mock_handler):
        """Test Lambda handler routing to PROCESS_CLAIM handler."""
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

    @patch("lambda.worker.handle_welcome_email")
    def test_lambda_handler_welcome_email(self, mock_handler):
        """Test Lambda handler routing to WELCOME_EMAIL handler."""
        event = {
            "Records": [
                {
                    "messageId": "msg-456",
                    "body": json.dumps({
                        "job_type": "WELCOME_EMAIL",
                        "payload": {"email": "test@example.com"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        mock_handler.assert_called_once_with({"email": "test@example.com"})
        assert result["statusCode"] == 200

    @patch("lambda.worker.handle_policy_renewal_reminder")
    def test_lambda_handler_renewal_reminder(self, mock_handler):
        """Test Lambda handler routing to POLICY_RENEWAL_REMINDER handler."""
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

        mock_handler.assert_called_once_with({"policy_id": "policy-123"})
        assert result["statusCode"] == 200

    def test_lambda_handler_unknown_job_type(self):
        """Test Lambda handler with unknown job type (should skip)."""
        event = {
            "Records": [
                {
                    "messageId": "msg-999",
                    "body": json.dumps({
                        "job_type": "UNKNOWN_TYPE",
                        "payload": {}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        # Should complete without error
        assert result["statusCode"] == 200

    def test_lambda_handler_empty_records(self):
        """Test Lambda handler with empty records."""
        event = {"Records": []}

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert result["processedCount"] == 0

    @patch("lambda.worker.handle_process_claim")
    def test_lambda_handler_multiple_records(self, mock_handler):
        """Test Lambda handler with multiple records."""
        event = {
            "Records": [
                {
                    "messageId": "msg-1",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-1"}
                    })
                },
                {
                    "messageId": "msg-2",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-2"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        assert mock_handler.call_count == 2
        assert result["processedCount"] == 2

    @patch("lambda.worker.handle_process_claim")
    @patch("lambda.worker.sns")
    @patch("lambda.worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:test-topic")
    def test_lambda_handler_error_handling(self, mock_sns, mock_handler):
        """Test Lambda handler error handling and SNS alert."""
        mock_handler.side_effect = Exception("Test error")

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
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args
        message = json.loads(call_args[1]["Message"])
        assert message["event"] == "WORKER_ERROR"
