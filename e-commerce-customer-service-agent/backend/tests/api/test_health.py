"""Tests for health check and root endpoints."""

import pytest


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Test the root endpoint returns API info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_check(client):
    """Test the health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_api_docs_available(client):
    """Test that API documentation is accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200

    response = await client.get("/redoc")
    assert response.status_code == 200
