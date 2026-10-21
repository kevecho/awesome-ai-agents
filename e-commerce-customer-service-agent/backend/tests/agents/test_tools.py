"""Tests for agent tools."""

import pytest
from app.agents.tools.transfer_human import TransferHumanTool
from app.agents.tools.create_ticket import CreateTicketTool


@pytest.mark.asyncio
async def test_transfer_human_tool():
    """Test human transfer tool."""
    tool = TransferHumanTool()
    result = await tool.execute({
        "session_id": "test-session",
        "user_id": 1,
        "reason": "user_requested",
    })
    assert result["success"] is True
    assert "response" in result
    assert "transfer_id" in result
    assert "queue_position" in result


@pytest.mark.asyncio
async def test_create_ticket_tool():
    """Test ticket creation tool."""
    tool = CreateTicketTool()
    result = await tool.execute({
        "session_id": "test-session",
        "user_id": 1,
        "type": "consult",
        "title": "Test ticket",
        "content": "This is a test ticket for unit testing",
    })
    assert result["success"] is True
    assert "ticket_no" in result
    assert "response" in result
