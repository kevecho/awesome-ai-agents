"""Tests for intent recognition API."""

import pytest


@pytest.mark.asyncio
async def test_classify_intent(client):
    """Test single intent classification."""
    response = await client.post("/api/v1/intent/classify", json={
        "text": "I want to check my order status",
    })
    assert response.status_code == 200
    data = response.json()
    assert "intent" in data
    assert "intent_code" in data["intent"]
    assert "confidence" in data["intent"]
    assert "processing_time_ms" in data


@pytest.mark.asyncio
async def test_classify_batch(client):
    """Test batch intent classification."""
    response = await client.post("/api/v1/intent/classify-batch", json={
        "texts": [
            "Where is my order?",
            "What is your return policy?",
            "I want to speak to a human",
        ],
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 3
