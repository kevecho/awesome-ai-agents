"""Agent management and execution API endpoints."""

from fastapi import APIRouter

from app.schemas.agent import (
    AgentExecuteRequest,
    AgentExecuteResponse,
    AgentStep,
    ToolInfo,
)
from app.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger(__name__)


@router.post("/execute", response_model=AgentExecuteResponse)
async def execute_agent(request: AgentExecuteRequest) -> AgentExecuteResponse:
    """Execute an agent for a given task."""
    import time
    import uuid

    start = time.monotonic()
    agent_id = uuid.uuid4().hex[:12]

    try:
        from app.agents.customer_agent import CustomerServiceAgent
        agent = CustomerServiceAgent(
            session_id=request.session_id,
            user_id=request.user_id,
        )
        result = await agent.process(request.task)

        steps = []
        for i, step_data in enumerate(result.get("steps", []), 1):
            steps.append(AgentStep(
                step_number=i,
                thought=step_data.get("thought", ""),
                action=step_data.get("action"),
                action_input=step_data.get("action_input"),
                observation=step_data.get("observation"),
            ))

        elapsed = (time.monotonic() - start) * 1000

        return AgentExecuteResponse(
            agent_id=agent_id,
            session_id=request.session_id,
            final_answer=result.get("response", ""),
            steps=steps,
            tools_used=result.get("tools_used", []),
            execution_time_ms=round(elapsed, 2),
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        elapsed = (time.monotonic() - start) * 1000
        return AgentExecuteResponse(
            agent_id=agent_id,
            session_id=request.session_id,
            final_answer="Sorry, I encountered an error. Let me connect you with a human agent.",
            steps=[],
            tools_used=[],
            execution_time_ms=round(elapsed, 2),
        )


@router.get("/tools", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    """List all available agent tools."""
    from app.agents.tools.search_knowledge import SearchKnowledgeTool
    from app.agents.tools.query_order import QueryOrderTool
    from app.agents.tools.query_product import QueryProductTool
    from app.agents.tools.refund_tool import RefundTool
    from app.agents.tools.transfer_human import TransferHumanTool
    from app.agents.tools.create_ticket import CreateTicketTool

    tool_classes = [
        SearchKnowledgeTool, QueryOrderTool, QueryProductTool,
        RefundTool, TransferHumanTool, CreateTicketTool,
    ]

    tools = []
    for cls in tool_classes:
        instance = cls()
        tools.append(ToolInfo(
            name=instance.name,
            description=instance.description,
            requires_auth=getattr(instance, "requires_auth", False),
            schema=instance.get_schema() if hasattr(instance, "get_schema") else {},
        ))
    return tools
