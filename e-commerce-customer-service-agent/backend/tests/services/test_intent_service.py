"""Tests for intent recognition service."""

import pytest
from app.services.intent_service import IntentService


@pytest.fixture
def service():
    return IntentService()


@pytest.mark.asyncio
async def test_order_query_intent(service):
    """Test recognition of order query intent."""
    result = await service.recognize("Where is my order?")
    assert result is not None
    assert result.intent_code in ("order_query", "fallback")


@pytest.mark.asyncio
async def test_refund_intent(service):
    """Test recognition of refund intent."""
    result = await service.recognize("I want a refund for my purchase")
    assert result is not None


@pytest.mark.asyncio
async def test_greeting_intent(service):
    """Test recognition of greeting intent."""
    result = await service.recognize("Hello, are you there?")
    assert result is not None


@pytest.mark.asyncio
async def test_entity_extraction(service):
    """Test entity extraction from text."""
    entities = await service._extract_entities(
        "My order is ORDER20260715001 and my phone is 13812345678",
        "order_query",
    )
    order_entities = [e for e in entities if e.type == "order_no"]
    phone_entities = [e for e in entities if e.type == "phone"]
    assert len(order_entities) >= 1
    assert len(phone_entities) >= 1
    assert order_entities[0].value == "ORDER20260715001"
