"""Tests for chat API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_create_session(client):
    """Test creating a new chat session."""
    response = await client.post("/api/v1/chat/session", json={})
    assert response.status_code == 201
    data = response.json()
    assert "session" in data
    assert "welcome_message" in data
    assert "quick_replies" in data
    assert data["session"]["status"] == "active"


@pytest.mark.asyncio
async def test_send_message(client):
    """Test sending a message."""
    # Create session first
    session_resp = await client.post("/api/v1/chat/session", json={})
    session_id = session_resp.json()["session"]["session_id"]

    # Send a message
    response = await client.post("/api/v1/chat/send", json={
        "session_id": session_id,
        "content": "Hello, I need help with my order",
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "intent" in data
    assert "sentiment" in data
    assert isinstance(data["response"], str)


@pytest.mark.asyncio
async def test_send_empty_message(client):
    """Test that empty messages are rejected."""
    session_resp = await client.post("/api/v1/chat/session", json={})
    session_id = session_resp.json()["session"]["session_id"]

    response = await client.post("/api/v1/chat/send", json={
        "session_id": session_id,
        "content": "",
    })
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_history(client):
    """Test retrieving chat history."""
    response = await client.get(
        "/api/v1/chat/history",
        params={"session_id": "nonexistent", "page": 1, "page_size": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_transfer_to_human(client):
    """Test transferring to human agent."""
    response = await client.post("/api/v1/chat/transfer", json={
        "session_id": "test-session",
        "reason": "user_requested",
    })
    assert response.status_code == 200
    data = response.json()
    assert "transfer_id" in data
    assert "queue_position" in data


@pytest.mark.asyncio
async def test_rate_session(client):
    """Test rating a session."""
    response = await client.post("/api/v1/chat/rate", json={
        "session_id": "test-session",
        "score": 5,
        "comment": "Great service",
    })
    assert response.status_code == 200
