"""Pytest configuration and shared fixtures for backend tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.config.database import Base


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing cache operations."""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.delete.return_value = 1
    return mock_client


@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing document operations."""
    mock_client = MagicMock()
    mock_client.generate_presigned_url.return_value = "https://s3.example.com/presigned-url"
    return mock_client


@pytest.fixture
def mock_sqs_client():
    """Mock SQS client for testing queue operations."""
    mock_client = MagicMock()
    mock_client.send_message.return_value = {"MessageId": "test-message-id"}
    return mock_client


@pytest.fixture
def mock_sns_client():
    """Mock SNS client for testing notification operations."""
    mock_client = MagicMock()
    mock_client.publish.return_value = {"MessageId": "test-sns-message-id"}
    return mock_client


@pytest.fixture
async def async_db_engine():
    """Create an in-memory async SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_db_session(async_db_engine):
    """Create an async database session for testing."""
    async_session_maker = async_sessionmaker(
        async_db_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def test_client():
    """Create a TestClient for FastAPI testing."""
    return TestClient(app)


@pytest.fixture
def mock_jwt_payload():
    """Default JWT payload for authenticated requests."""
    return {
        "sub": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "role": "policyholder"
    }
