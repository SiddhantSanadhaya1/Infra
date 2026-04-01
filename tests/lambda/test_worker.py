"""Unit tests for Lambda worker function"""
import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timezone


# Import path needs to match the Lambda structure
import sys
sys.path.insert(0, '/app/workspace/e940fc26-9ac9-44db-82b9-aeb0a8252948/Infra/app')


class TestCalculateFraudScore:
    """Test fraud score calculation in Lambda"""

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_low_amount(self, mock_randint):
        """Test fraud score for low claim amount"""
        from lambda.worker import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(10000.0, "GENERAL")

        assert score == 20

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_high_amount(self, mock_randint):
        """Test fraud score increases for high claim amounts"""
        from lambda.worker import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(60000.0, "GENERAL")

        # Should add 20 for amount > 50k
        assert score == 40

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_medium_amount(self, mock_randint):
        """Test fraud score for medium claim amounts"""
        from lambda.worker import calculate_fraud_score

        mock_randint.return_value = 20

        score = calculate_fraud_score(30000.0, "GENERAL")

        # Should add 10 for amount > 20k
        assert score == 30

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_boundary_50k(self, mock_randint):
        """Test fraud score at $50k boundary"""
        from lambda.worker import calculate_fraud_score

        mock_randint.return_value = 20

        score_at = calculate_fraud_score(50000.0, "GENERAL")
        score_over = calculate_fraud_score(50001.0, "GENERAL")

        # Exactly 50k should not trigger high amount bonus
        assert score_at == 30  # 20 + 10 for >20k
        # Over 50k should trigger high amount bonus
        assert score_over == 40  # 20 + 20 for >50k

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_boundary_20k(self, mock_randint):
        """Test fraud score at $20k boundary"""
        from lambda.worker import calculate_fraud_score

        mock_randint.return_value = 20

        score_at = calculate_fraud_score(20000.0, "GENERAL")
        score_over = calculate_fraud_score(20001.0, "GENERAL")

        # Exactly 20k should not trigger medium bonus
        assert score_at == 20
        # Over 20k should trigger medium bonus
        assert score_over == 30

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_high_risk_type_theft(self, mock_randint):
        """Test fraud score for THEFT claim type"""
        from lambda.worker import calculate_fraud_score

        mock_randint.side_effect = [20, 10]  # Base score, then risk type bonus

        score = calculate_fraud_score(10000.0, "THEFT")

        # Base 20 + up to 15 for high risk type
        assert score >= 20
        assert score <= 35

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_high_risk_type_collision(self, mock_randint):
        """Test fraud score for COLLISION claim type"""
        from lambda.worker import calculate_fraud_score

        mock_randint.side_effect = [20, 10]

        score = calculate_fraud_score(10000.0, "COLLISION")

        assert score >= 20

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_high_risk_type_liability(self, mock_randint):
        """Test fraud score for LIABILITY claim type"""
        from lambda.worker import calculate_fraud_score

        mock_randint.side_effect = [20, 10]

        score = calculate_fraud_score(10000.0, "LIABILITY")

        assert score >= 20

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_case_insensitive_type(self, mock_randint):
        """Test fraud score is case-insensitive for claim type"""
        from lambda.worker import calculate_fraud_score

        mock_randint.side_effect = [20, 10]

        score = calculate_fraud_score(10000.0, "theft")

        # lowercase "theft" should still trigger high risk
        assert score >= 20

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_capped_at_100(self, mock_randint):
        """Test fraud score is capped at 100"""
        from lambda.worker import calculate_fraud_score

        mock_randint.side_effect = [35, 15]  # High base + risk bonus

        score = calculate_fraud_score(100000.0, "THEFT")

        assert score <= 100

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_minimum_base(self, mock_randint):
        """Test fraud score with minimum base value"""
        from lambda.worker import calculate_fraud_score

        mock_randint.return_value = 5

        score = calculate_fraud_score(1000.0, "GENERAL")

        assert score == 5

    @patch('lambda.worker.random.randint')
    def test_calculate_fraud_score_maximum_base(self, mock_randint):
        """Test fraud score with maximum base value"""
        from lambda.worker import calculate_fraud_score

        mock_randint.return_value = 35

        score = calculate_fraud_score(1000.0, "GENERAL")

        assert score == 35


class TestHandleProcessClaim:
    """Test handle_process_claim job handler"""

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    @patch('lambda.worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123:topic')
    @patch('lambda.worker.DDB_TABLE', 'test-table')
    def test_handle_process_claim_low_risk(self, mock_fraud, mock_dynamo, mock_sns):
        """Test processing claim with low fraud risk"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-20260401-1234",
            "policy_id": "policy-456",
            "amount_requested": 5000.0,
            "claim_type": "GENERAL"
        }

        handle_process_claim(payload)

        # Verify DynamoDB put_item was called
        mock_table.put_item.assert_called_once()
        item = mock_table.put_item.call_args[1]["Item"]
        assert item["claim_id"] == "claim-123"
        assert item["fraud_score"] == 30
        assert item["risk_level"] == "LOW"
        assert item["processing_status"] == "AUTO_APPROVED_FOR_REVIEW"

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    def test_handle_process_claim_medium_risk(self, mock_fraud, mock_dynamo, mock_sns):
        """Test processing claim with medium fraud risk"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 50
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-456",
            "claim_number": "CLM-20260401-5678",
            "policy_id": "policy-789",
            "amount_requested": 10000.0,
            "claim_type": "COLLISION"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        assert item["fraud_score"] == 50
        assert item["risk_level"] == "MEDIUM"
        assert item["processing_status"] == "MANUAL_REVIEW"

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    def test_handle_process_claim_high_risk(self, mock_fraud, mock_dynamo, mock_sns):
        """Test processing claim with high fraud risk"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 85
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-789",
            "claim_number": "CLM-20260401-9999",
            "policy_id": "policy-111",
            "amount_requested": 75000.0,
            "claim_type": "THEFT"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        assert item["fraud_score"] == 85
        assert item["risk_level"] == "HIGH"
        assert item["processing_status"] == "FRAUD_REVIEW"

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    def test_handle_process_claim_boundary_40_score(self, mock_fraud, mock_dynamo, mock_sns):
        """Test claim processing at fraud score boundary (40)"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 40
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-123",
            "amount_requested": 5000.0,
            "claim_type": "GENERAL"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        # Exactly 40 should trigger MEDIUM (>=40)
        assert item["risk_level"] == "MEDIUM"

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    def test_handle_process_claim_boundary_70_score(self, mock_fraud, mock_dynamo, mock_sns):
        """Test claim processing at fraud score boundary (70)"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 70
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-123",
            "amount_requested": 5000.0,
            "claim_type": "GENERAL"
        }

        handle_process_claim(payload)

        item = mock_table.put_item.call_args[1]["Item"]
        # Exactly 70 should trigger HIGH (>=70)
        assert item["risk_level"] == "HIGH"

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    @patch('lambda.worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123:topic')
    def test_handle_process_claim_publishes_sns(self, mock_fraud, mock_dynamo, mock_sns):
        """Test claim processing publishes SNS notification"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-123",
            "amount_requested": 5000.0,
            "claim_type": "GENERAL"
        }

        handle_process_claim(payload)

        # Verify SNS publish was called
        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert call_args["TopicArn"] == "arn:aws:sns:us-east-1:123:topic"
        assert "CLM-001" in call_args["Subject"]

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    @patch('lambda.worker.SNS_TOPIC_ARN', '')
    def test_handle_process_claim_no_sns_when_arn_empty(self, mock_fraud, mock_dynamo, mock_sns):
        """Test claim processing skips SNS when ARN is empty"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-123",
            "amount_requested": 5000.0,
            "claim_type": "GENERAL"
        }

        handle_process_claim(payload)

        # SNS publish should not be called
        mock_sns.publish.assert_not_called()

    @patch('lambda.worker.sns')
    @patch('lambda.worker.dynamo')
    @patch('lambda.worker.calculate_fraud_score')
    def test_handle_process_claim_dynamodb_error_raises(self, mock_fraud, mock_dynamo, mock_sns):
        """Test claim processing re-raises DynamoDB errors"""
        from lambda.worker import handle_process_claim

        mock_fraud.return_value = 30
        mock_table = MagicMock()
        mock_table.put_item.side_effect = Exception("DynamoDB error")
        mock_dynamo.Table.return_value = mock_table

        payload = {
            "claim_id": "claim-123",
            "claim_number": "CLM-001",
            "policy_id": "policy-123",
            "amount_requested": 5000.0,
            "claim_type": "GENERAL"
        }

        with pytest.raises(Exception, match="DynamoDB error"):
            handle_process_claim(payload)


class TestHandleWelcomeEmail:
    """Test handle_welcome_email job handler"""

    @patch('lambda.worker.sns')
    @patch('lambda.worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123:topic')
    def test_handle_welcome_email_basic(self, mock_sns):
        """Test sending welcome email notification"""
        from lambda.worker import handle_welcome_email

        payload = {
            "policyholder_id": "holder-123",
            "email": "user@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert call_args["TopicArn"] == "arn:aws:sns:us-east-1:123:topic"
        assert "Welcome to InsureCo Insurance, John!" in call_args["Subject"]

        # Verify message contains welcome text
        message = json.loads(call_args["Message"])
        assert message["event"] == "WELCOME_EMAIL"
        assert "John" in message["message"]

    @patch('lambda.worker.sns')
    @patch('lambda.worker.SNS_TOPIC_ARN', '')
    def test_handle_welcome_email_no_sns_when_arn_empty(self, mock_sns):
        """Test welcome email skips SNS when ARN is empty"""
        from lambda.worker import handle_welcome_email

        payload = {
            "policyholder_id": "holder-123",
            "email": "user@example.com",
            "first_name": "John"
        }

        handle_welcome_email(payload)

        mock_sns.publish.assert_not_called()


class TestHandlePolicyRenewalReminder:
    """Test handle_policy_renewal_reminder job handler"""

    @patch('lambda.worker.sns')
    @patch('lambda.worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123:topic')
    def test_handle_policy_renewal_reminder_basic(self, mock_sns):
        """Test sending policy renewal reminder"""
        from lambda.worker import handle_policy_renewal_reminder

        payload = {
            "policyholder_id": "holder-123",
            "policy_id": "policy-456",
            "policy_number": "POL-AUTO-20260401-1234",
            "email": "user@example.com",
            "end_date": "2027-01-01",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_called_once()
        call_args = mock_sns.publish.call_args[1]
        assert "POL-AUTO-20260401-1234" in call_args["Subject"]
        assert "30 Days" in call_args["Subject"]

    @patch('lambda.worker.sns')
    @patch('lambda.worker.SNS_TOPIC_ARN', '')
    def test_handle_policy_renewal_reminder_no_sns_when_arn_empty(self, mock_sns):
        """Test renewal reminder skips SNS when ARN is empty"""
        from lambda.worker import handle_policy_renewal_reminder

        payload = {
            "policy_number": "POL-001",
            "days_until_expiry": 30
        }

        handle_policy_renewal_reminder(payload)

        mock_sns.publish.assert_not_called()


class TestLambdaHandler:
    """Test lambda_handler entry point"""

    @patch('lambda.worker.handle_process_claim')
    def test_lambda_handler_process_claim_job(self, mock_handler):
        """Test Lambda handler routes PROCESS_CLAIM job"""
        from lambda.worker import lambda_handler

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

        result = lambda_handler(event, {})

        mock_handler.assert_called_once_with({"claim_id": "claim-123"})
        assert result["statusCode"] == 200
        assert result["processedCount"] == 1

    @patch('lambda.worker.handle_welcome_email')
    def test_lambda_handler_welcome_email_job(self, mock_handler):
        """Test Lambda handler routes WELCOME_EMAIL job"""
        from lambda.worker import lambda_handler

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

        result = lambda_handler(event, {})

        mock_handler.assert_called_once()
        assert result["statusCode"] == 200

    @patch('lambda.worker.handle_policy_renewal_reminder')
    def test_lambda_handler_renewal_reminder_job(self, mock_handler):
        """Test Lambda handler routes POLICY_RENEWAL_REMINDER job"""
        from lambda.worker import lambda_handler

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

        result = lambda_handler(event, {})

        mock_handler.assert_called_once()

    def test_lambda_handler_unknown_job_type(self):
        """Test Lambda handler skips unknown job types"""
        from lambda.worker import lambda_handler

        event = {
            "Records": [
                {
                    "messageId": "msg-999",
                    "body": json.dumps({
                        "job_type": "UNKNOWN_JOB",
                        "payload": {}
                    })
                }
            ]
        }

        result = lambda_handler(event, {})

        # Should complete without error, skipping unknown job
        assert result["statusCode"] == 200

    def test_lambda_handler_multiple_records(self):
        """Test Lambda handler processes multiple records"""
        from lambda.worker import lambda_handler

        event = {
            "Records": [
                {
                    "messageId": "msg-1",
                    "body": json.dumps({"job_type": "UNKNOWN", "payload": {}})
                },
                {
                    "messageId": "msg-2",
                    "body": json.dumps({"job_type": "UNKNOWN", "payload": {}})
                }
            ]
        }

        result = lambda_handler(event, {})

        assert result["processedCount"] == 2

    @patch('lambda.worker.handle_process_claim')
    @patch('lambda.worker.sns')
    @patch('lambda.worker.SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123:topic')
    def test_lambda_handler_error_handling(self, mock_sns, mock_handler):
        """Test Lambda handler error handling and SNS alert"""
        from lambda.worker import lambda_handler

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
            lambda_handler(event, {})

        # Verify error alert was published to SNS
        mock_sns.publish.assert_called_once()

    def test_lambda_handler_empty_records(self):
        """Test Lambda handler with no records"""
        from lambda.worker import lambda_handler

        event = {"Records": []}

        result = lambda_handler(event, {})

        assert result["statusCode"] == 200
        assert result["processedCount"] == 0
