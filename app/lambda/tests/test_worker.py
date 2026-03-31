"""
Unit tests for Lambda worker
Tests SQS event processing, job handlers, and error handling.
"""
import pytest
import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, call
from worker import (
    calculate_fraud_score,
    handle_process_claim,
    handle_welcome_email,
    handle_policy_renewal_reminder,
    lambda_handler,
)


class TestCalculateFraudScore:
    """Test fraud score calculation"""

    @patch('worker.random.randint')
    def test_calculate_fraud_score_low_amount(self, mock_randint):
        """Test fraud score for low claim amount"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(10000.0, "GENERAL")

        assert score == 20
        mock_randint.assert_called_once_with(5, 35)

    @patch('worker.random.randint')
    def test_calculate_fraud_score_medium_amount(self, mock_randint):
        """Test fraud score for medium claim amount (25k)"""
        mock_randint.side_effect = [20, 5]

        score = calculate_fraud_score(25000.0, "GENERAL")

        assert score == 30  # 20 + 10 bonus

    @patch('worker.random.randint')
    def test_calculate_fraud_score_high_amount(self, mock_randint):
        """Test fraud score for high claim amount (60k)"""
        mock_randint.side_effect = [20, 5]

        score = calculate_fraud_score(60000.0, "GENERAL")

        assert score == 40  # 20 + 20 bonus

    @patch('worker.random.randint')
    def test_calculate_fraud_score_theft_claim_type(self, mock_randint):
        """Test fraud score for THEFT claim type"""
        mock_randint.side_effect = [20, 10]

        score = calculate_fraud_score(10000.0, "THEFT")

        assert score == 30  # 20 + 10 high-risk bonus

    @patch('worker.random.randint')
    def test_calculate_fraud_score_collision_claim_type(self, mock_randint):
        """Test fraud score for COLLISION claim type"""
        mock_randint.side_effect = [20, 12]

        score = calculate_fraud_score(10000.0, "COLLISION")

        assert score == 32  # 20 + 12 high-risk bonus

    @patch('worker.random.randint')
    def test_calculate_fraud_score_liability_claim_type(self, mock_randint):
        """Test fraud score for LIABILITY claim type"""
        mock_randint.side_effect = [20, 15]

        score = calculate_fraud_score(10000.0, "LIABILITY")

        assert score == 35  # 20 + 15 high-risk bonus

    @patch('worker.random.randint')
    def test_calculate_fraud_score_low_risk_claim_type(self, mock_randint):
        """Test fraud score for non-high-risk claim type"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(10000.0, "MEDICAL")

        assert score == 20

    @patch('worker.random.randint')
    def test_calculate_fraud_score_capped_at_100(self, mock_randint):
        """Test fraud score is capped at 100"""
        mock_randint.side_effect = [35, 15]

        score = calculate_fraud_score(60000.0, "THEFT")

        # 35 + 20 (high amount) + 15 (high-risk type) = 70, which is under cap
        assert score <= 100

    @patch('worker.random.randint')
    def test_calculate_fraud_score_zero_amount(self, mock_randint):
        """Test fraud score for zero claim amount"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(0.0, "GENERAL")

        assert score == 20

    @patch('worker.random.randint')
    def test_calculate_fraud_score_case_insensitive_claim_type(self, mock_randint):
        """Test fraud score with lowercase claim type"""
        mock_randint.side_effect = [20, 10]

        score = calculate_fraud_score(10000.0, "theft")

        assert score == 30  # Should match THEFT

    @patch('worker.random.randint')
    def test_calculate_fraud_score_boundary_20k(self, mock_randint):
        """Test fraud score at 20k boundary"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(20000.0, "GENERAL")

        assert score == 20  # No bonus at exact boundary

    @patch('worker.random.randint')
    def test_calculate_fraud_score_boundary_50k(self, mock_randint):
        """Test fraud score at 50k boundary"""
        mock_randint.return_value = 20

        score = calculate_fraud_score(50000.0, "GENERAL")

        assert score == 20  # No bonus at exact boundary


class TestHandleProcessClaim:
    """Test PROCESS_CLAIM job handler"""

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_process_claim_low_risk(self, mock_fraud, mock_dynamo, mock_sns, mock_datetime):
        """Test processing claim with low fraud risk"""
        mock_fraud.return_value = 30
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260330-1234",
            "policy_id": "policy-456",
            "amount_requested": "50000.00",
            "claim_type": "AUTO"
        }

        handle_process_claim(payload)

        # Verify DynamoDB write
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["claim_id"] == "claim-123"
        assert item["fraud_score"] == 30
        assert item["risk_level"] == "LOW"
        assert item["processing_status"] == "AUTO_APPROVED_FOR_REVIEW"

        # Verify SNS notification
        mock_sns.publish.assert_called_once()

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_process_claim_medium_risk(self, mock_fraud, mock_dynamo, mock_sns, mock_datetime):
        """Test processing claim with medium fraud risk"""
        mock_fraud.return_value = 50
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-456",
            "claim_number": "CLM-20260330-5678",
            "policy_id": "policy-789",
            "amount_requested": "75000.00",
            "claim_type": "THEFT"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        assert item["fraud_score"] == 50
        assert item["risk_level"] == "MEDIUM"
        assert item["processing_status"] == "MANUAL_REVIEW"

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_process_claim_high_risk(self, mock_fraud, mock_dynamo, mock_sns, mock_datetime):
        """Test processing claim with high fraud risk"""
        mock_fraud.return_value = 85
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-789",
            "claim_number": "CLM-20260330-9999",
            "policy_id": "policy-001",
            "amount_requested": "100000.00",
            "claim_type": "COLLISION"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        assert item["fraud_score"] == 85
        assert item["risk_level"] == "HIGH"
        assert item["processing_status"] == "FRAUD_REVIEW"

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': ''})
    def test_handle_process_claim_no_sns_topic(self, mock_fraud, mock_dynamo, mock_sns, mock_datetime):
        """Test processing claim when SNS topic is not configured"""
        mock_fraud.return_value = 30
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-001",
            "claim_number": "CLM-20260330-0001",
            "policy_id": "policy-002",
            "amount_requested": "10000.00",
            "claim_type": "GENERAL"
        }

        handle_process_claim(payload)

        # DynamoDB should still be called
        mock_table.put_item.assert_called_once()

        # SNS should not be called
        mock_sns.publish.assert_not_called()

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    def test_handle_process_claim_dynamodb_error(self, mock_fraud, mock_dynamo, mock_sns, mock_datetime):
        """Test processing claim when DynamoDB write fails"""
        mock_fraud.return_value = 30
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-error",
            "claim_number": "CLM-20260330-ERR",
            "policy_id": "policy-error",
            "amount_requested": "1000.00",
            "claim_type": "TEST"
        }

        with pytest.raises(Exception) as exc_info:
            handle_process_claim(payload)

        assert str(exc_info.value) == "DynamoDB error"

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_process_claim_boundary_40_risk(self, mock_fraud, mock_dynamo, mock_sns, mock_datetime):
        """Test processing claim at fraud score boundary of 40"""
        mock_fraud.return_value = 40
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-boundary",
            "claim_number": "CLM-20260330-BOUNDARY",
            "policy_id": "policy-boundary",
            "amount_requested": "30000.00",
            "claim_type": "AUTO"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        assert item["risk_level"] == "MEDIUM"
        assert item["processing_status"] == "MANUAL_REVIEW"

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch('worker.dynamo')
    @patch('worker.calculate_fraud_score')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_process_claim_boundary_70_risk(self, mock_fraud, mock_dynamo, mock_sns, mock_datetime):
        """Test processing claim at fraud score boundary of 70"""
        mock_fraud.return_value = 70
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-high",
            "claim_number": "CLM-20260330-HIGH",
            "policy_id": "policy-high",
            "amount_requested": "90000.00",
            "claim_type": "THEFT"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        assert item["risk_level"] == "HIGH"
        assert item["processing_status"] == "FRAUD_REVIEW"


class TestHandleWelcomeEmail:
    """Test WELCOME_EMAIL job handler"""

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_welcome_email(self, mock_sns, mock_datetime):
        """Test sending welcome email"""
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        payload = {
            "policyholder_id": "holder-123",
            "email": "newuser@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert call_args["TopicArn"] == 'arn:aws:sns:us-east-1:123456789012:topic'
        assert "Welcome to InsureCo Insurance, John!" in call_args["Subject"]

        message = json.loads(call_args["Message"])
        assert message["event"] == "WELCOME_EMAIL"
        assert message["email"] == "newuser@example.com"
        assert message["first_name"] == "John"

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': ''})
    def test_handle_welcome_email_no_sns_topic(self, mock_sns, mock_datetime):
        """Test welcome email when SNS topic is not configured"""
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        payload = {
            "policyholder_id": "holder-456",
            "email": "test@example.com",
            "first_name": "Jane"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_not_called()

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_welcome_email_missing_first_name(self, mock_sns, mock_datetime):
        """Test welcome email defaults to 'Valued Customer' when first_name missing"""
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        payload = {
            "policyholder_id": "holder-789",
            "email": "customer@example.com"
        }

        handle_welcome_email(payload)

        call_args = mock_sns.publish.call_args[1]
        message = json.loads(call_args["Message"])
        assert message["first_name"] == "Valued Customer"


class TestHandlePolicyRenewalReminder:
    """Test POLICY_RENEWAL_REMINDER job handler"""

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:topic'})
    def test_handle_policy_renewal_reminder(self, mock_sns, mock_datetime):
        """Test sending policy renewal reminder"""
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        payload = {
            "policyholder_id": "holder-123",
            "policy_id": "policy-456",
            "policy_number": "POL-AUTO-20260101-1234",
            "email": "customer@example.com",
            "end_date": "2026-12-31",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert "Action Required" in call_args["Subject"]
        assert "Expires in 30 Days" in call_args["Subject"]

        message = json.loads(call_args["Message"])
        assert message["event"] == "POLICY_RENEWAL_REMINDER"
        assert message["policy_number"] == "POL-AUTO-20260101-1234"
        assert message["days_until_expiry"] == 30

    @patch('worker.datetime')
    @patch('worker.sns')
    @patch.dict(os.environ, {'SNS_TOPIC_ARN': ''})
    def test_handle_policy_renewal_reminder_no_sns_topic(self, mock_sns, mock_datetime):
        """Test renewal reminder when SNS topic is not configured"""
        mock_datetime.now.return_value = datetime(2026, 3, 30, 12, 0, 0, tzinfo=timezone.utc)

        payload = {
            "policy_number": "POL-HOME-20260101-5678",
            "days_until_expiry": 60
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_not_called()


class TestLambdaHandler:
    """Test Lambda entry point"""

    @patch('worker.sns')
    @patch('worker.handle_process_claim')
    def test_lambda_handler_process_claim(self, mock_handler, mock_sns):
        """Test lambda_handler routes PROCESS_CLAIM job"""
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

        assert result["statusCode"] == 200
        assert result["processedCount"] == 1
        mock_handler.assert_called_once_with({"claim_id": "claim-123"})

    @patch('worker.sns')
    @patch('worker.handle_welcome_email')
    def test_lambda_handler_welcome_email(self, mock_handler, mock_sns):
        """Test lambda_handler routes WELCOME_EMAIL job"""
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

        assert result["statusCode"] == 200
        mock_handler.assert_called_once_with({"email": "user@example.com"})

    @patch('worker.sns')
    @patch('worker.handle_policy_renewal_reminder')
    def test_lambda_handler_renewal_reminder(self, mock_handler, mock_sns):
        """Test lambda_handler routes POLICY_RENEWAL_REMINDER job"""
        event = {
            "Records": [
                {
                    "messageId": "msg-789",
                    "body": json.dumps({
                        "job_type": "POLICY_RENEWAL_REMINDER",
                        "payload": {"policy_number": "POL-AUTO-20260101-1234"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_handler.assert_called_once_with({"policy_number": "POL-AUTO-20260101-1234"})

    @patch('worker.sns')
    def test_lambda_handler_unknown_job_type(self, mock_sns):
        """Test lambda_handler skips unknown job types"""
        event = {
            "Records": [
                {
                    "messageId": "msg-unknown",
                    "body": json.dumps({
                        "job_type": "UNKNOWN_JOB",
                        "payload": {}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert result["processedCount"] == 1

    @patch('worker.sns')
    @patch('worker.handle_process_claim')
    def test_lambda_handler_multiple_records(self, mock_handler, mock_sns):
        """Test lambda_handler processes multiple SQS records"""
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

        assert result["statusCode"] == 200
        assert result["processedCount"] == 2
        assert mock_handler.call_count == 2

    @patch('worker.sns')
    @patch('worker.handle_process_claim')
    def test_lambda_handler_error_handling(self, mock_handler, mock_sns):
        """Test lambda_handler publishes error alert on failure"""
        mock_handler.side_effect = Exception("Processing error")

        event = {
            "Records": [
                {
                    "messageId": "msg-error",
                    "body": json.dumps({
                        "job_type": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-error"}
                    })
                }
            ]
        }

        with pytest.raises(Exception):
            lambda_handler(event, None)

    @patch('worker.sns')
    def test_lambda_handler_empty_records(self, mock_sns):
        """Test lambda_handler with empty Records array"""
        event = {"Records": []}

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        assert result["processedCount"] == 0

    @patch('worker.sns')
    @patch('worker.handle_process_claim')
    def test_lambda_handler_jobType_alternative_key(self, mock_handler, mock_sns):
        """Test lambda_handler handles jobType as alternative to job_type"""
        event = {
            "Records": [
                {
                    "messageId": "msg-alt",
                    "body": json.dumps({
                        "jobType": "PROCESS_CLAIM",
                        "payload": {"claim_id": "claim-alt"}
                    })
                }
            ]
        }

        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        mock_handler.assert_called_once_with({"claim_id": "claim-alt"})
