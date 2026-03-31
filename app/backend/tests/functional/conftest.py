"""
Shared fixtures for functional tests.
Tests require a running InsureCo API instance.
"""
import os
from typing import Generator
import httpx
import pytest


# Configure base URL from environment variable
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL for API requests."""
    return BASE_URL


@pytest.fixture(scope="function")
def client(base_url: str) -> Generator[httpx.Client, None, None]:
    """Create an HTTP client for making API requests."""
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="function")
def async_client(base_url: str) -> Generator[httpx.AsyncClient, None, None]:
    """Create an async HTTP client for making API requests."""
    async def _client():
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            yield client
    return _client()
