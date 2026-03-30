"""
Comprehensive unit tests for Lambda worker.
Tests job handlers, fraud scoring, and Lambda entry point.
"""
import pytest
import json
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from worker import (
    calculate_fraud_score,
    handle_process_claim,
    handle_welcome_email,
    handle_policy_renewal_reminder,
    lambda_handler,
    JOB_HANDLERS,
)


class TestCalculateFraudScore:
    """Test fraud score calculation logic."""

    @patch("worker.random.randint")
    def test_calculate_fraud_score_low_amount(self, mock_random):
        """Test fraud score for low claim amounts."""
        mock_random.return_value = 20

        score = calculate_fraud_score(5000.0, "AUTO")

        assert score == 20  # Base score only

    @patch("worker.random.randint")
    def test_calculate_fraud_score_medium_amount(self, mock_random):
        """Test fraud score for medium claim amounts (over 20k)."""
        mock_random.return_value = 20

        score = calculate_fraud_score(25000.0, "AUTO")

        assert score == 30  # Base 20 + 10 for > 20k

    @patch("worker.random.randint")
    def test_calculate_fraud_score_high_amount(self, mock_random):
        """Test fraud score for high claim amounts (over 50k)."""
        mock_random.return_value = 20

        score = calculate_fraud_score(75000.0, "AUTO")

        assert score == 40  # Base 20 + 20 for > 50k

    @patch("worker.random.randint")
    def test_calculate_fraud_score_exactly_20k(self, mock_random):
        """Test fraud score at boundary of 20k."""
        mock_random.return_value = 20

        score = calculate_fraud_score(20000.0, "AUTO")

        assert score == 20  # Not over 20k

    @patch("worker.random.randint")
    def test_calculate_fraud_score_exactly_50k(self, mock_random):
        """Test fraud score at boundary of 50k."""
        mock_random.return_value = 20

        score = calculate_fraud_score(50000.0, "AUTO")

        assert score == 30  # Not over 50k, but over 20k

    @patch("worker.random.randint")
    def test_calculate_fraud_score_high_risk_claim_type_theft(self, mock_random):
        """Test fraud score for high-risk claim type: THEFT."""
        mock_random.side_effect = [20, 10]  # Base score, then risk type bonus

        score = calculate_fraud_score(10000.0, "THEFT")

        assert 20 <= score <= 35  # Base + possible risk type bonus

    @patch("worker.random.randint")
    def test_calculate_fraud_score_high_risk_claim_type_collision(self, mock_random):
        """Test fraud score for high-risk claim type: COLLISION."""
        mock_random.side_effect = [20, 10]

        score = calculate_fraud_score(10000.0, "COLLISION")

        assert 20 <= score <= 35

    @patch("worker.random.randint")
    def test_calculate_fraud_score_high_risk_claim_type_liability(self, mock_random):
        """Test fraud score for high-risk claim type: LIABILITY."""
        mock_random.side_effect = [20, 10]

        score = calculate_fraud_score(10000.0, "LIABILITY")

        assert 20 <= score <= 35

    @patch("worker.random.randint")
    def test_calculate_fraud_score_low_risk_claim_type(self, mock_random):
        """Test fraud score for low-risk claim types."""
        mock_random.return_value = 20

        score = calculate_fraud_score(10000.0, "MEDICAL")

        # Low risk types get base score only (no random.randint called for bonus)
        assert score >= 20

    @patch("worker.random.randint")
    def test_calculate_fraud_score_capped_at_100(self, mock_random):
        """Test that fraud score is capped at 100."""
        mock_random.side_effect = [35, 15]  # High base + high risk bonus

        score = calculate_fraud_score(100000.0, "THEFT")

        assert score <= 100

    @patch("worker.random.randint")
    def test_calculate_fraud_score_minimum_score(self, mock_random):
        """Test minimum possible fraud score."""
        mock_random.return_value = 5

        score = calculate_fraud_score(1000.0, "OTHER")

        assert score >= 5

    @patch("worker.random.randint")
    def test_calculate_fraud_score_maximum_score(self, mock_random):
        """Test maximum possible fraud score."""
        mock_random.side_effect = [35, 15]

        score = calculate_fraud_score(100000.0, "THEFT")

        assert score == 100  # Capped at 100

    @patch("worker.random.randint")
    def test_calculate_fraud_score_zero_amount(self, mock_random):
        """Test fraud score with zero claim amount."""
        mock_random.return_value = 20

        score = calculate_fraud_score(0.0, "AUTO")

        assert score == 20

    @patch("worker.random.randint")
    def test_calculate_fraud_score_case_insensitive_claim_type(self, mock_random):
        """Test that claim type matching is case insensitive."""
        mock_random.side_effect = [20, 10]

        score_upper = calculate_fraud_score(10000.0, "THEFT")

        mock_random.side_effect = [20, 10]
        score_lower = calculate_fraud_score(10000.0, "theft")

        # Both should get risk bonus
        assert score_upper >= 20
        assert score_lower >= 20


class TestHandleProcessClaim:
    """Test PROCESS_CLAIM job handler."""

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_handle_process_claim_low_risk(self, mock_fraud, mock_dynamo, mock_sns):
        """Test processing claim with low fraud risk."""
        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000",
            "claim_type": "AUTO"
        }

        handle_process_claim(payload)

        # Verify DynamoDB write
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]
        assert item["fraud_score"] == 30
        assert item["risk_level"] == "LOW"
        assert item["processing_status"] == "AUTO_APPROVED_FOR_REVIEW"

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_handle_process_claim_medium_risk(self, mock_fraud, mock_dynamo, mock_sns):
        """Test processing claim with medium fraud risk."""
        mock_fraud.return_value = 55
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000",
            "claim_type": "AUTO"
        }

        handle_process_claim(payload)

        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]
        assert item["fraud_score"] == 55
        assert item["risk_level"] == "MEDIUM"
        assert item["processing_status"] == "MANUAL_REVIEW"

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_handle_process_claim_high_risk(self, mock_fraud, mock_dynamo, mock_sns):
        """Test processing claim with high fraud risk."""
        mock_fraud.return_value = 85
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000",
            "claim_type": "AUTO"
        }

        handle_process_claim(payload)

        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]
        assert item["fraud_score"] == 85
        assert item["risk_level"] == "HIGH"
        assert item["processing_status"] == "FRAUD_REVIEW"

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    def test_handle_process_claim_risk_boundary_40(self, mock_fraud, mock_dynamo, mock_sns):
        """Test risk level at exactly 40 (boundary between LOW and MEDIUM)."""
        mock_fraud.return_value = 40
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000"
        }

        handle_process_claim(payload)

        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]
        assert item["risk_level"] == "MEDIUM"  # >= 40 is MEDIUM

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    def test_handle_process_claim_risk_boundary_70(self, mock_fraud, mock_dynamo, mock_sns):
        """Test risk level at exactly 70 (boundary between MEDIUM and HIGH)."""
        mock_fraud.return_value = 70
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000"
        }

        handle_process_claim(payload)

        call_args = mock_table.put_item.call_args[1]
        item = call_args["Item"]
        assert item["risk_level"] == "HIGH"  # >= 70 is HIGH

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_handle_process_claim_publishes_sns(self, mock_fraud, mock_dynamo, mock_sns):
        """Test that SNS notification is published."""
        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000"
        }

        handle_process_claim(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert call_args["TopicArn"] == "arn:aws:sns:us-east-1:123456789012:topic"
        assert "CLM-001" in call_args["Subject"]

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    @patch("worker.SNS_TOPIC_ARN", "")
    def test_handle_process_claim_no_sns_topic(self, mock_fraud, mock_dynamo, mock_sns):
        """Test that SNS publish is skipped when no topic ARN configured."""
        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000"
        }

        handle_process_claim(payload)

        mock_sns.publish.assert_not_called()

    @patch("worker.sns")
    @patch("worker.dynamo")
    @patch("worker.calculate_fraud_score")
    def test_handle_process_claim_dynamodb_failure_raises(self, mock_fraud, mock_dynamo, mock_sns):
        """Test that DynamoDB errors are raised."""
        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-456",
            "amount_requested": "10000"
        }

        with pytest.raises(Exception, match="DynamoDB error"):
            handle_process_claim(payload)


class TestHandleWelcomeEmail:
    """Test WELCOME_EMAIL job handler."""

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_handle_welcome_email_success(self, mock_sns):
        """Test sending welcome email notification."""
        payload = {
            "policyholder_id": "ph-123",
            "email": "user@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert call_args["TopicArn"] == "arn:aws:sns:us-east-1:123456789012:topic"
        assert "John" in call_args["Subject"]

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "")
    def test_handle_welcome_email_no_sns_topic(self, mock_sns):
        """Test welcome email when no SNS topic configured."""
        payload = {
            "policyholder_id": "ph-123",
            "email": "user@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_not_called()

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_handle_welcome_email_missing_first_name(self, mock_sns):
        """Test welcome email with missing first_name (uses default)."""
        payload = {
            "policyholder_id": "ph-123",
            "email": "user@example.com"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert "Valued Customer" in call_args["Subject"]


class TestHandlePolicyRenewalReminder:
    """Test POLICY_RENEWAL_REMINDER job handler."""

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_handle_policy_renewal_reminder_success(self, mock_sns):
        """Test sending policy renewal reminder."""
        payload = {
            "policyholder_id": "ph-123",
            "policy_id": "policy-456",
            "policy_number": "POL-001",
            "email": "user@example.com",
            "end_date": "2026-12-31",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert call_args["TopicArn"] == "arn:aws:sns:us-east-1:123456789012:topic"
        assert "POL-001" in call_args["Subject"]
        assert "30 Days" in call_args["Subject"]

    @patch("worker.sns")
    @patch("worker.SNS_TOPIC_ARN", "")
    def test_handle_policy_renewal_reminder_no_sns_topic(self, mock_sns):
        """Test renewal reminder when no SNS topic configured."""
        payload = {
            "policyholder_id": "ph-123",
            "policy_id": "policy-456",
            "policy_number": "POL-001",
            "email": "user@example.com",
            "end_date": "2026-12-31",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_not_called()


class TestJobHandlers:
    """Test JOB_HANDLERS dispatch table."""

    def test_job_handlers_contains_all_types(self):
        """Test that all job types are in the dispatch table."""
        expected_types = ["PROCESS_CLAIM", "WELCOME_EMAIL", "POLICY_RENEWAL_REMINDER"]

        for job_type in expected_types:
            assert job_type in JOB_HANDLERS

    def test_job_handlers_functions_callable(self):
        """Test that all handler functions are callable."""
        for handler in JOB_HANDLERS.values():
            assert callable(handler)


class TestLambdaHandler:
    """Test Lambda entry point function."""

    @patch("worker.JOB_HANDLERS")
    def test_lambda_handler_processes_single_record(self, mock_handlers):
        """Test lambda_handler with single SQS record."""
        mock_handler = MagicMock()
        mock_handlers.get.return_value = mock_handler

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

    @patch("worker.JOB_HANDLERS")
    def test_lambda_handler_processes_multiple_records(self, mock_handlers):
        """Test lambda_handler with multiple SQS records."""
        mock_handler = MagicMock()
        mock_handlers.get.return_value = mock_handler

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
                        "job_type": "WELCOME_EMAIL",
                        "payload": {"email": "user@example.com"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        assert mock_handler.call_count == 2
        assert result["processedCount"] == 2

    @patch("worker.JOB_HANDLERS")
    def test_lambda_handler_unknown_job_type(self, mock_handlers):
        """Test lambda_handler with unknown job type (should skip)."""
        mock_handlers.get.return_value = None

        event = {
            "Records": [
                {
                    "messageId": "msg-123",
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

    @patch("worker.sns")
    @patch("worker.JOB_HANDLERS")
    @patch("worker.SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:topic")
    def test_lambda_handler_error_publishes_sns_alert(self, mock_handlers, mock_sns):
        """Test that errors trigger SNS alert."""
        mock_handler = MagicMock()
        mock_handler.side_effect = Exception("Processing error")
        mock_handlers.get.return_value = mock_handler

        event = {
            "Records": [
                {
                    "messageId": "msg-123",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {}
                    })
                }
            ]
        }

        with pytest.raises(Exception):
            lambda_handler(event, None)

        # SNS alert should be published
        mock_sns.publish.assert_called()
        call_args = mock_sns.publish.call_args[1]
        assert "WORKER_ERROR" in call_args["Message"]

    @patch("worker.JOB_HANDLERS")
    def test_lambda_handler_partial_batch_failure(self, mock_handlers):
        """Test lambda_handler returns batch failure info."""
        mock_handler = MagicMock()
        mock_handler.side_effect = [None, Exception("Error"), None]
        mock_handlers.get.return_value = mock_handler

        event = {
            "Records": [
                {"messageId": "msg-1", "body": json.dumps({"job_type": "TEST", "payload": {}})},
                {"messageId": "msg-2", "body": json.dumps({"job_type": "TEST", "payload": {}})},
                {"messageId": "msg-3", "body": json.dumps({"job_type": "TEST", "payload": {}})},
            ]
        }

        # First and third should succeed, second should fail
        try:
            lambda_handler(event, None)
        except Exception:
            pass

    @patch("worker.JOB_HANDLERS")
    def test_lambda_handler_empty_records(self, mock_handlers):
        """Test lambda_handler with no records."""
        event = {"Records": []}

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert result["processedCount"] == 0

    @patch("worker.JOB_HANDLERS")
    def test_lambda_handler_alternative_job_type_field(self, mock_handlers):
        """Test lambda_handler with jobType field (alternative naming)."""
        mock_handler = MagicMock()
        mock_handlers.get.return_value = mock_handler

        event = {
            "Records": [
                {
                    "messageId": "msg-123",
                    "body": json.dumps({
                        "jobType": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-123"}
                    })
                }
            ]
        }

        lambda_handler(event, None)

        # Handler should still be called
        mock_handler.assert_called_once()
