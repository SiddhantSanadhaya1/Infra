"""
InsureCo Insurance Lambda background worker — triggered by SQS messages from the backend.

AWS services used:
  - aws_lambda_function.worker              (this function)
  - aws_lambda_event_source_mapping.sqs_trigger  (SQS -> Lambda trigger)
  - aws_sqs_queue.main                      (event source)
  - aws_sqs_queue.dead_letter               (failed messages land here after retries)
  - aws_dynamodb_table (claims_processing)  (update claim processing status records)
  - aws_sns_topic.alerts                    (publish notifications and error alerts)
  - aws_iam_role.lambda                     (execution role)
  - aws_iam_role_policy_attachment.lambda_vpc (VPC access)

Job types handled:
  - PROCESS_CLAIM:            validate claim, run fraud score, update DynamoDB, notify via SNS
  - WELCOME_EMAIL:            send welcome notification via SNS
  - POLICY_RENEWAL_REMINDER:  send renewal reminder notification via SNS
"""

import json
import logging
import os
import random
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION = os.environ.get("AWS_REGION", "us-east-1")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
DDB_TABLE = os.environ.get("DYNAMODB_TABLE", "insureco-claims-processing")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "insureco")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")

sns = boto3.client("sns", region_name=REGION)
dynamo = boto3.resource("dynamodb", region_name=REGION)


# ── Fraud score calculation ────────────────────────────────────────────────────

def calculate_fraud_score(amount_requested: float, claim_type: str) -> int:
    """
    Demo fraud scoring: returns an integer 0-100.
    Higher score = higher fraud risk.
    In production this would call an ML inference endpoint.
    """
    base_score = random.randint(5, 35)

    # Claims above $50k are flagged with higher base risk
    if amount_requested > 50000:
        base_score += 20
    elif amount_requested > 20000:
        base_score += 10

    # Certain claim types carry higher statistical fraud rates
    high_risk_types = {"THEFT", "COLLISION", "LIABILITY"}
    if claim_type.upper() in high_risk_types:
        base_score += random.randint(0, 15)

    return min(100, base_score)


# ── Job handlers ──────────────────────────────────────────────────────────────

def handle_process_claim(payload: dict) -> None:
    """
    Claims processing job:
      1. Calculate fraud risk score
      2. Write processing record to DynamoDB
      3. Publish SNS notification with result

    DynamoDB record schema:
      PK: claim_id (string)
      claim_number: str
      fraud_score: int
      risk_level: str (LOW / MEDIUM / HIGH)
      processed_at: ISO timestamp
      status: FRAUD_REVIEW | AUTO_APPROVED_FOR_REVIEW
    """
    claim_id = payload.get("claim_id", "UNKNOWN")
    claim_number = payload.get("claim_number", "UNKNOWN")
    policy_id = payload.get("policy_id", "UNKNOWN")
    amount_requested = float(payload.get("amount_requested", 0))
    claim_type = payload.get("claim_type", "GENERAL")

    logger.info(
        "Processing claim claim_id=%s claim_number=%s amount=%.2f",
        claim_id, claim_number, amount_requested
    )

    fraud_score = calculate_fraud_score(amount_requested, claim_type)

    if fraud_score >= 70:
        risk_level = "HIGH"
        processing_status = "FRAUD_REVIEW"
    elif fraud_score >= 40:
        risk_level = "MEDIUM"
        processing_status = "MANUAL_REVIEW"
    else:
        risk_level = "LOW"
        processing_status = "AUTO_APPROVED_FOR_REVIEW"

    processed_at = datetime.now(timezone.utc).isoformat()

    # Write to DynamoDB
    try:
        table = dynamo.Table(DDB_TABLE)
        table.put_item(Item={
            "claim_id": claim_id,
            "claim_number": claim_number,
            "policy_id": policy_id,
            "amount_requested": str(amount_requested),
            "fraud_score": fraud_score,
            "risk_level": risk_level,
            "processing_status": processing_status,
            "processed_at": processed_at,
            "environment": ENVIRONMENT,
        })
        logger.info(
            "DynamoDB updated for claim %s — fraud_score=%d risk=%s status=%s",
            claim_number, fraud_score, risk_level, processing_status
        )
    except Exception as exc:
        logger.error("DynamoDB update failed for claim %s: %s", claim_id, exc)
        raise

    # Publish SNS notification
    if SNS_TOPIC_ARN:
        notification = {
            "event": "CLAIM_PROCESSED",
            "claim_id": claim_id,
            "claim_number": claim_number,
            "fraud_score": fraud_score,
            "risk_level": risk_level,
            "processing_status": processing_status,
            "processed_at": processed_at,
        }
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(notification),
            Subject=f"InsureCo Claim Processed: {claim_number} — Risk: {risk_level}",
            MessageAttributes={
                "event_type": {"DataType": "String", "StringValue": "CLAIM_PROCESSED"},
                "risk_level": {"DataType": "String", "StringValue": risk_level},
            },
        )
        logger.info("SNS notification published for claim %s", claim_number)


def handle_welcome_email(payload: dict) -> None:
    """
    Send a welcome notification to a new InsureCo policyholder via SNS.
    In production, SNS would fan out to an email delivery Lambda or SES.
    """
    policyholder_id = payload.get("policyholder_id", "UNKNOWN")
    email = payload.get("email", "")
    first_name = payload.get("first_name", "Valued Customer")

    logger.info("Sending welcome notification for policyholder_id=%s email=%s", policyholder_id, email)

    if SNS_TOPIC_ARN:
        message = {
            "event": "WELCOME_EMAIL",
            "policyholder_id": policyholder_id,
            "email": email,
            "first_name": first_name,
            "message": (
                f"Welcome to InsureCo Insurance, {first_name}! "
                "Your account has been created. You can now manage your policies and file claims online."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f"Welcome to InsureCo Insurance, {first_name}!",
            MessageAttributes={
                "event_type": {"DataType": "String", "StringValue": "WELCOME_EMAIL"},
            },
        )
    logger.info("Welcome notification dispatched for policyholder %s", policyholder_id)


def handle_policy_renewal_reminder(payload: dict) -> None:
    """
    Send a policy renewal reminder notification via SNS.
    Triggered before policy expiry (e.g., 30/60 days out).
    """
    policyholder_id = payload.get("policyholder_id", "UNKNOWN")
    policy_id = payload.get("policy_id", "UNKNOWN")
    policy_number = payload.get("policy_number", "UNKNOWN")
    email = payload.get("email", "")
    end_date = payload.get("end_date", "")
    days_until_expiry = payload.get("days_until_expiry", 30)

    logger.info(
        "Sending renewal reminder for policy_number=%s days_until_expiry=%d",
        policy_number, days_until_expiry
    )

    if SNS_TOPIC_ARN:
        message = {
            "event": "POLICY_RENEWAL_REMINDER",
            "policyholder_id": policyholder_id,
            "policy_id": policy_id,
            "policy_number": policy_number,
            "email": email,
            "end_date": end_date,
            "days_until_expiry": days_until_expiry,
            "message": (
                f"Your InsureCo policy {policy_number} expires in {days_until_expiry} days ({end_date}). "
                "Please log in to renew your coverage and avoid a lapse."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f"Action Required: InsureCo Policy {policy_number} Expires in {days_until_expiry} Days",
            MessageAttributes={
                "event_type": {"DataType": "String", "StringValue": "POLICY_RENEWAL_REMINDER"},
            },
        )
    logger.info("Renewal reminder dispatched for policy %s", policy_number)


# ── Job dispatch table ────────────────────────────────────────────────────────

JOB_HANDLERS = {
    "PROCESS_CLAIM": handle_process_claim,
    "WELCOME_EMAIL": handle_welcome_email,
    "POLICY_RENEWAL_REMINDER": handle_policy_renewal_reminder,
}


# ── Lambda entry point ────────────────────────────────────────────────────────

def lambda_handler(event, context):
    """
    SQS event handler — processes each record in the batch.

    Retry logic:
      - On unhandled exceptions, the message is re-raised so the SQS event
        source mapping can retry up to the configured maxReceiveCount.
      - After maxReceiveCount retries, SQS moves the message to the DLQ
        (aws_sqs_queue.dead_letter) for manual inspection.
      - A SNS alert is published on every failure for ops visibility.
    """
    records = event.get("Records", [])
    logger.info("InsureCo Insurance Worker invoked with %d records", len(records))

    failed_message_ids = []

    for record in records:
        message_id = record.get("messageId", "UNKNOWN")
        try:
            body = json.loads(record["body"])
            job_type = body.get("job_type") or body.get("jobType", "")
            payload = body.get("payload", {})

            logger.info("Processing job type=%s messageId=%s", job_type, message_id)

            handler = JOB_HANDLERS.get(job_type)
            if handler is None:
                logger.warning("Unknown job type '%s' — messageId=%s skipping", job_type, message_id)
                continue

            handler(payload)
            logger.info("Job %s completed successfully (messageId=%s)", job_type, message_id)

        except Exception as exc:
            logger.error(
                "Failed to process messageId=%s: %s",
                message_id, exc,
                exc_info=True,
            )
            failed_message_ids.append(message_id)

            # Publish failure alert to SNS
            if SNS_TOPIC_ARN:
                try:
                    sns.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Message=json.dumps({
                            "event": "WORKER_ERROR",
                            "message_id": message_id,
                            "error": str(exc),
                            "environment": ENVIRONMENT,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }),
                        Subject="InsureCo Insurance Worker: Processing Error",
                    )
                except Exception as sns_exc:
                    logger.error("Failed to publish error alert to SNS: %s", sns_exc)

            # Re-raise to trigger SQS retry / DLQ routing
            raise

    if failed_message_ids:
        # Return partial batch failure response for Lambda partial batch processing
        return {
            "batchItemFailures": [
                {"itemIdentifier": mid} for mid in failed_message_ids
            ]
        }

    return {"statusCode": 200, "processedCount": len(records)}
