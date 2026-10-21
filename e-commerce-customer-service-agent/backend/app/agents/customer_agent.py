"""客服 Agent 实现，采用 ReAct 推理架构。"""

from typing import Any, Optional

from app.agents.base_agent import BaseAgent
from app.services.intent_service import IntentService
from app.services.sentiment_service import SentimentService, SentimentType
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CustomerServiceAgent(BaseAgent):
    """电商客服 Agent。"""

    def __init__(self, session_id: str, user_id: Optional[int] = None):
        super().__init__(session_id, user_id)
        self.intent_service = IntentService()
        self.sentiment_service = SentimentService()
        self.rag_service = RAGService()
        self.llm_service = LLMService()
        self._init_tools()

    def _init_tools(self) -> None:
        from app.agents.tools.search_knowledge import SearchKnowledgeTool
        from app.agents.tools.query_order import QueryOrderTool
        from app.agents.tools.query_product import QueryProductTool
        from app.agents.tools.refund_tool import RefundTool
        from app.agents.tools.transfer_human import TransferHumanTool
        from app.agents.tools.create_ticket import CreateTicketTool

        tool_map = {
            "search_knowledge": SearchKnowledgeTool(),
            "query_order": QueryOrderTool(),
            "query_product": QueryProductTool(),
            "refund": RefundTool(),
            "transfer_human": TransferHumanTool(),
            "create_ticket": CreateTicketTool(),
        }

        for name, tool in tool_map.items():
            self.register_tool(name, tool)

    async def process(self, input_text: str) -> dict[str, Any]:
        logger.info(f"Agent 处理中: '{input_text[:80]}...'")
        steps: list[dict] = []
        tools_used: list[str] = []

        intent_result = await self.intent_service.recognize(input_text, self.user_id)
        steps.append({
            "thought": f"识别意图为 '{intent_result.intent_code}'，置信度 {intent_result.confidence:.2f}",
            "action": "intent_recognition",
            "observation": f"意图: {intent_result.intent_code}，处理器: {intent_result.handler_type}",
        })

        sentiment, sentiment_score = await self.sentiment_service.analyze(input_text)
        strategy = self.sentiment_service.get_response_strategy(sentiment, sentiment_score)
        steps.append({
            "thought": f"检测到 {sentiment.value} 情感（得分: {sentiment_score:.2f}）",
            "action": "sentiment_analysis",
            "observation": f"策略: {strategy['tone']}，优先级: {strategy['priority']}",
        })

        handler_type = intent_result.handler_type
        if sentiment == SentimentType.NEGATIVE and sentiment_score < -0.5:
            handler_type = "transfer"

        if handler_type == "transfer":
            tool = self.get_tool("transfer_human")
            if tool:
                tools_used.append("transfer_human")
                result = await tool.execute({
                    "session_id": self.session_id,
                    "user_id": self.user_id,
                    "reason": "complaint" if sentiment == SentimentType.NEGATIVE else "user_requested",
                })
                response = result.get("response", "正在为您转接人工客服...")
                steps.append({
                    "thought": "因严重程度触发升级转人工",
                    "action": "transfer_human",
                    "observation": f"已发起转接，队列位置: {result.get('queue_position', '未知')}",
                })
        elif handler_type == "tool":
            tool_name = self._map_intent_to_tool(intent_result.intent_code)
            tool = self.get_tool(tool_name) if tool_name else None
            if tool:
                tools_used.append(tool_name)
                result = await tool.execute({
                    "user_message": input_text,
                    "user_id": self.user_id,
                    "intent": intent_result,
                })
                response = result.get("response", "您的请求已处理完成。")
                steps.append({
                    "thought": f"为意图 '{intent_result.intent_code}' 选择工具 '{tool_name}'",
                    "action": tool_name,
                    "observation": result.get("response", "工具已执行")[:200],
                })
            else:
                response = await self._llm_fallback(input_text)
        elif handler_type == "rag":
            context = await self.rag_service.retrieve(input_text, top_k=3)
            if context:
                tools_used.append("rag_retrieval")
                response = await self.rag_service.generate(input_text, context)
                steps.append({
                    "thought": "从知识库中检索相关文档",
                    "action": "rag_retrieval",
                    "observation": f"检索到 {context.count('[文档')} 篇文档",
                })
            else:
                response = await self._llm_fallback(input_text)
        else:
            response = await self._llm_fallback(input_text)

        response = self._format_response(response, sentiment, strategy)
        self.add_to_history("user", input_text)
        self.add_to_history("assistant", response)

        return {
            "response": response,
            "intent": intent_result.model_dump(),
            "sentiment": sentiment.value,
            "sentiment_score": sentiment_score,
            "steps": steps,
            "tools_used": tools_used,
        }

    def _map_intent_to_tool(self, intent_code: str) -> Optional[str]:
        mapping = {
            "order_query": "query_order", "order_modify": "query_order",
            "cancel_order": "refund", "refund_request": "refund",
            "product_inquiry": "query_product", "shipping_info": "search_knowledge",
            "payment_issue": "create_ticket", "complaint": "transfer_human",
            "human_agent": "transfer_human", "promotion": "search_knowledge",
        }
        return mapping.get(intent_code)

    async def _llm_fallback(self, input_text: str) -> str:
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是小E，电商平台的专业客服助手。"
                        "请保持回答有帮助、简洁、准确。使用通俗易懂的语言。"
                        "如果无法提供帮助，建议用户转接人工客服。"
                    ),
                },
                {"role": "user", "content": input_text},
            ]
            return await self.llm_service.chat(messages)
        except Exception as e:
            logger.error(f"LLM 回退失败: {e}")
            return (
                "非常抱歉，我暂时遇到了技术问题。"
                "请稍后再试，或拨打客服热线获取帮助。"
            )

    def _format_response(self, response: str, sentiment: SentimentType, strategy: dict) -> str:
        if sentiment == SentimentType.NEGATIVE:
            prefix = strategy.get("prefix", "")
            return f"{prefix} {response}"
        return response
