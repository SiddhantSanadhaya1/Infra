"""
Pytest configuration and shared fixtures for InsureCo Insurance backend tests.
"""
import pytest
from unittest.mock import Mock
from datetime import date, datetime


@pytest.fixture
def mock_async_session():
    """Create a mock AsyncSession for database testing."""
    session = Mock()
    session.execute = Mock()
    session.flush = Mock()
    session.refresh = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.add = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def sample_policy_data():
    """Provide sample policy data for testing."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "policyholder_id": "650e8400-e29b-41d4-a716-446655440000",
        "policy_type": "AUTO",
        "policy_number": "POL-AUTO-20260330-1234",
        "premium_amount": "1200.00",
        "coverage_amount": "50000.00",
        "start_date": date.today(),
        "end_date": date.today().replace(year=date.today().year + 1),
        "status": "ACTIVE",
    }


@pytest.fixture
def sample_claim_data():
    """Provide sample claim data for testing."""
    return {
        "id": "750e8400-e29b-41d4-a716-446655440000",
        "policy_id": "550e8400-e29b-41d4-a716-446655440000",
        "claim_number": "CLM-20260330-5678",
        "claim_type": "COLLISION",
        "description": "Vehicle damage from accident",
        "amount_requested": "5000.00",
        "amount_approved": None,
        "status": "SUBMITTED",
        "incident_date": date.today(),
        "filed_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_policyholder_data():
    """Provide sample policyholder data for testing."""
    return {
        "id": "650e8400-e29b-41d4-a716-446655440000",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "date_of_birth": date(1985, 5, 15),
        "address": "123 Main St, Anytown, USA 12345",
    }


@pytest.fixture
def sample_document_data():
    """Provide sample document data for testing."""
    return {
        "id": "850e8400-e29b-41d4-a716-446655440000",
        "claim_id": "750e8400-e29b-41d4-a716-446655440000",
        "policy_id": None,
        "document_type": "invoice",
        "file_key": "claims/claim-123/invoice/12345678_invoice.pdf",
        "file_name": "invoice.pdf",
        "uploaded_at": datetime.utcnow(),
    }


@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client."""
    client = Mock()
    client.generate_presigned_url = Mock(return_value="https://s3.aws.com/presigned-url")
    return client


@pytest.fixture
def mock_sqs_client():
    """Create a mock SQS client."""
    client = Mock()
    client.send_message = Mock(return_value={"MessageId": "test-message-id"})
    return client


@pytest.fixture
def mock_sns_client():
    """Create a mock SNS client."""
    client = Mock()
    client.publish = Mock(return_value={"MessageId": "test-sns-message-id"})
    return client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = Mock()
    client.get = Mock(return_value=None)
    client.set = Mock(return_value=True)
    client.setex = Mock(return_value=True)
    client.delete = Mock(return_value=1)
    return client


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    table = Mock()
    table.put_item = Mock(return_value={})
    table.get_item = Mock(return_value={"Item": {}})
    table.update_item = Mock(return_value={})
    table.delete_item = Mock(return_value={})
    return table
