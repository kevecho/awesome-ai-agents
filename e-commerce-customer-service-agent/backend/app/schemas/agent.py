"""
Pydantic schemas for agent management and execution.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent for a given task."""

    session_id: str = Field(..., description="Session UUID")
    user_id: Optional[int] = Field(None, description="User ID")
    task: str = Field(..., min_length=1, max_length=2000, description="Task description")
    context: Optional[dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class AgentStep(BaseModel):
    """A single step in an agent's reasoning chain."""

    step_number: int = Field(..., description="Step index")
    thought: str = Field(..., description="Agent's reasoning")
    action: Optional[str] = Field(None, description="Tool called")
    action_input: Optional[dict[str, Any]] = Field(None, description="Tool parameters")
    observation: Optional[str] = Field(None, description="Tool result")


class AgentExecuteResponse(BaseModel):
    """Response from an agent execution."""

    agent_id: str = Field(..., description="Agent instance ID")
    session_id: str = Field(..., description="Session UUID")
    final_answer: str = Field(..., description="Agent's final response")
    steps: list[AgentStep] = Field(default_factory=list, description="Reasoning steps")
    tools_used: list[str] = Field(default_factory=list, description="Tools called")
    execution_time_ms: float = Field(..., description="Total execution time")


class ToolInfo(BaseModel):
    """Information about a registered agent tool."""

    name: str = Field(..., description="Tool identifier")
    description: str = Field(..., description="Tool description")
    requires_auth: bool = Field(False, description="Whether auth is required")
    schema: dict[str, Any] = Field(..., description="Tool JSON schema")
