"""
Lambda background worker — triggered by SQS messages from the backend.

AWS services used:
  - aws_lambda_function.worker              (this function)
  - aws_lambda_event_source_mapping.sqs_trigger  (SQS → Lambda trigger)
  - aws_sqs_queue.main                      (event source)
  - aws_sqs_queue.dead_letter               (failed messages land here)
  - aws_dynamodb_table.sessions             (update job-status records)
  - aws_sns_topic.alerts                    (publish notifications/errors)
  - aws_s3_bucket.app                       (read uploaded files for processing)
  - aws_iam_role.lambda                     (execution role)
  - aws_iam_role_policy_attachment.lambda_vpc (VPC access for Redis/RDS if needed)
"""

import json
import logging
import os
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

REGION         = os.environ.get("AWS_REGION", "us-east-1")
SNS_TOPIC_ARN  = os.environ.get("SNS_TOPIC_ARN", "")
DDB_TABLE      = os.environ.get("DYNAMODB_SESSIONS_TABLE", "infra-app-dev-sessions")
S3_BUCKET      = os.environ.get("S3_BUCKET_NAME", "")

sns    = boto3.client("sns",      region_name=REGION)
dynamo = boto3.resource("dynamodb", region_name=REGION)
s3     = boto3.client("s3",       region_name=REGION)


def handle_send_welcome_email(payload: dict):
    """Send a welcome email notification via SNS."""
    message = {
        "type":   "WELCOME_EMAIL",
        "userId": payload["userId"],
        "email":  payload["email"],
    }
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=json.dumps(message),
        Subject="New user registration",
    )
    logger.info(f"Published welcome email notification for user {payload['userId']}")


def handle_process_upload(payload: dict):
    """
    Post-upload processing: read the uploaded file from S3,
    perform lightweight processing, update DynamoDB record.

    AWS services:
      - aws_s3_bucket.app             (GetObject)
      - aws_dynamodb_table.sessions   (UpdateItem for job tracking)
      - aws_sns_topic.alerts          (publish on error)
    """
    key     = payload["key"]
    file_id = payload["fileId"]

    # Fetch file metadata from S3
    head = s3.head_object(Bucket=S3_BUCKET, Key=key)
    size = head["ContentLength"]
    logger.info(f"Processing upload key={key} size={size} fileId={file_id}")

    # Record processing completion in DynamoDB
    table = dynamo.Table(DDB_TABLE)
    table.put_item(Item={
        "session_id": f"job:{file_id}",
        "status":     "processed",
        "s3_key":     key,
        "size_bytes": size,
    })

    logger.info(f"File processing complete for fileId={file_id}")


JOB_HANDLERS = {
    "SEND_WELCOME_EMAIL": handle_send_welcome_email,
    "PROCESS_UPLOAD":     handle_process_upload,
}


def lambda_handler(event, context):
    """
    SQS event handler — processes each record in the batch.
    Partial batch failures are handled by raising on any error
    so the SQS event source mapping retries the failed messages.
    """
    for record in event.get("Records", []):
        try:
            body     = json.loads(record["body"])
            job_type = body["jobType"]
            payload  = body["payload"]

            logger.info(f"Processing job type={job_type} messageId={record['messageId']}")

            handler = JOB_HANDLERS.get(job_type)
            if not handler:
                logger.warning(f"Unknown job type: {job_type} — skipping")
                continue

            handler(payload)

        except Exception as exc:
            logger.error(f"Failed to process message {record.get('messageId')}: {exc}", exc_info=True)

            # Notify ops via SNS
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=f"Lambda worker error: {exc}",
                    Subject="Worker failure alert",
                )
            except Exception:
                pass

            raise  # Re-raise so SQS retries / routes to DLQ

    return {"statusCode": 200, "body": "OK"}
