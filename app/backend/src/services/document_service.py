import os
import uuid
from typing import Optional, Tuple

from src.config.aws import S3_BUCKET_NAME, s3_client


def _build_s3_key(
    file_name: str,
    document_type: str,
    claim_id: Optional[str] = None,
    policy_id: Optional[str] = None,
) -> str:
    """Build a structured S3 key for a document."""
    unique_id = str(uuid.uuid4())[:8]
    safe_name = file_name.replace(" ", "_")

    if claim_id:
        return f"claims/{claim_id}/{document_type}/{unique_id}_{safe_name}"
    elif policy_id:
        return f"policies/{policy_id}/{document_type}/{unique_id}_{safe_name}"
    else:
        return f"documents/{document_type}/{unique_id}_{safe_name}"


def generate_presigned_url(
    file_name: str,
    document_type: str,
    content_type: str,
    claim_id: Optional[str] = None,
    policy_id: Optional[str] = None,
    expiry_seconds: int = 3600,
) -> Tuple[str, str]:
    """
    Generate a presigned S3 PUT URL for direct browser upload.
    Returns (presigned_url, file_key).
    """
    file_key = _build_s3_key(file_name, document_type, claim_id, policy_id)

    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": S3_BUCKET_NAME,
            "Key": file_key,
            "ContentType": content_type,
        },
        ExpiresIn=expiry_seconds,
        HttpMethod="PUT",
    )
    return presigned_url, file_key


def generate_download_url(file_key: str, expiry_seconds: int = 900) -> str:
    """Generate a presigned S3 GET URL for document download."""
    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": S3_BUCKET_NAME,
            "Key": file_key,
        },
        ExpiresIn=expiry_seconds,
    )
    return presigned_url
