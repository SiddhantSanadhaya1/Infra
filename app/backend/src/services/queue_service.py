import json
import logging
from typing import Any, Dict, Literal

from src.config.aws import SQS_QUEUE_URL, sqs_client

logger = logging.getLogger(__name__)

JobType = Literal["PROCESS_CLAIM", "WELCOME_EMAIL", "POLICY_RENEWAL_REMINDER"]


def enqueue_job(job_type: JobType, payload: Dict[str, Any]) -> str:
    """
    Send a job message to the SQS queue.
    Returns the SQS MessageId.
    """
    message_body = json.dumps({
        "job_type": job_type,
        "payload": payload,
    })

    if not SQS_QUEUE_URL:
        logger.warning("SQS_QUEUE_URL not configured — skipping job: %s", job_type)
        return "LOCAL_SKIP"

    response = sqs_client.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=message_body,
        MessageAttributes={
            "JobType": {
                "StringValue": job_type,
                "DataType": "String",
            }
        },
    )
    message_id = response.get("MessageId", "UNKNOWN")
    logger.info("Enqueued job %s with MessageId %s", job_type, message_id)
    return message_id
