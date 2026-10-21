"""Tests for sentiment analysis service."""

import pytest
from app.services.sentiment_service import SentimentService, SentimentType


@pytest.fixture
def service():
    return SentimentService()


@pytest.mark.asyncio
async def test_positive_sentiment(service):
    """Test detection of positive sentiment."""
    sentiment, score = await service.analyze("This product is excellent, I love it!")
    assert sentiment == SentimentType.POSITIVE
    assert score > 0


@pytest.mark.asyncio
async def test_negative_sentiment(service):
    """Test detection of negative sentiment."""
    sentiment, score = await service.analyze("This is terrible, I am very disappointed")
    assert sentiment == SentimentType.NEGATIVE
    assert score < 0


@pytest.mark.asyncio
async def test_neutral_sentiment(service):
    """Test detection of neutral sentiment."""
    sentiment, score = await service.analyze("I want to check my order status")
    assert sentiment == SentimentType.NEUTRAL


@pytest.mark.asyncio
async def test_escalation_detection(service):
    """Test detection of escalation triggers."""
    assert service.should_escalate("I want a refund immediately") is True
    assert service.should_escalate("I will never buy here again") is True
    assert service.should_escalate("Just checking my order") is False


@pytest.mark.asyncio
async def test_response_strategy(service):
    """Test response strategy generation."""
    strategy = service.get_response_strategy(SentimentType.NEGATIVE, -0.8)
    assert strategy["tone"] == "empathetic"
    assert strategy["priority"] == "high"

    strategy = service.get_response_strategy(SentimentType.POSITIVE, 0.8)
    assert strategy["tone"] == "friendly"
