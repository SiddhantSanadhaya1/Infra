import os

import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", None)  # For LocalStack / dev overrides

_boto_kwargs = {
    "region_name": AWS_REGION,
}
if AWS_ENDPOINT_URL:
    _boto_kwargs["endpoint_url"] = AWS_ENDPOINT_URL


def get_s3_client():
    return boto3.client("s3", **_boto_kwargs)


def get_sqs_client():
    return boto3.client("sqs", **_boto_kwargs)


def get_sns_client():
    return boto3.client("sns", **_boto_kwargs)


def get_secrets_manager_client():
    return boto3.client("secretsmanager", **_boto_kwargs)


# Singleton clients for reuse within a process
s3_client = get_s3_client()
sqs_client = get_sqs_client()
sns_client = get_sns_client()
secrets_manager_client = get_secrets_manager_client()

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "insureco-documents")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
