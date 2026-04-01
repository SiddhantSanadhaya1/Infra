"""Pytest configuration and shared fixtures"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from decimal import Decimal
from datetime import date, datetime, timezone
import uuid


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.delete.return_value = 1
    return mock_client


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing"""
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/presigned-url"
    return mock_client


@pytest.fixture
def mock_sqs_client():
    """Mock SQS client for testing"""
    mock_client = MagicMock()
    mock_client.send_message.return_value = {"MessageId": "test-message-id"}
    return mock_client


@pytest.fixture
def mock_sns_client():
    """Mock SNS client for testing"""
    mock_client = MagicMock()
    mock_client.publish.return_value = {"MessageId": "test-sns-id"}
    return mock_client


@pytest.fixture
def mock_dynamodb_table():
    """Mock DynamoDB table for testing"""
    mock_table = MagicMock()
    mock_table.put_item.return_value = {}
    return mock_table


@pytest.fixture
def sample_policy():
    """Sample policy object for testing"""
    from src.config.database import PolicyStatus, PolicyType

    policy = MagicMock()
    policy.id = uuid.uuid4()
    policy.policyholder_id = uuid.uuid4()
    policy.policy_type = PolicyType.AUTO
    policy.policy_number = "POL-AUTO-20260401-1234"
    policy.premium_amount = Decimal("1500.00")
    policy.coverage_amount = Decimal("100000.00")
    policy.start_date = date(2026, 1, 1)
    policy.end_date = date(2027, 1, 1)
    policy.status = PolicyStatus.ACTIVE
    return policy


@pytest.fixture
def sample_claim():
    """Sample claim object for testing"""
    from src.config.database import ClaimStatus

    claim = MagicMock()
    claim.id = uuid.uuid4()
    claim.policy_id = uuid.uuid4()
    claim.claim_number = "CLM-20260401-5678"
    claim.claim_type = "COLLISION"
    claim.description = "Vehicle collision on highway"
    claim.amount_requested = Decimal("5000.00")
    claim.amount_approved = None
    claim.status = ClaimStatus.SUBMITTED
    claim.incident_date = date(2026, 3, 15)
    return claim


@pytest.fixture
def mock_db_session():
    """Mock async database session"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session
