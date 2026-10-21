"""对话编排服务。"""

from typing import Any, Optional
import uuid

from app.services.intent_service import IntentService
from app.services.sentiment_service import SentimentService, SentimentType
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChatService:
    """编排每条用户消息的完整对话处理管线。"""

    def __init__(self):
        self.intent_service = IntentService()
        self.sentiment_service = SentimentService()
        self.rag_service = RAGService()
        self.llm_service = LLMService()

    async def process_message(
        self,
        session_id: str,
        content: str,
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """处理用户消息并生成回复。"""
        logger.info(f"处理会话 {session_id[:8]} 的消息...")

        # 意图识别
        intent_result = await self.intent_service.recognize(content, user_id)

        # 情感分析
        sentiment, sentiment_score = await self.sentiment_service.analyze(content)

        # 决策
        should_escalate = self.sentiment_service.should_escalate(content)
        effective_handler = (
            "transfer" if should_escalate else intent_result.handler_type
        )

        if effective_handler == "transfer":
            response = await self._handle_transfer(intent_result, sentiment)
        elif effective_handler == "tool":
            response = await self._handle_with_tools(intent_result, content, user_id)
        elif effective_handler == "rag":
            response = await self._handle_with_rag(content)
        else:
            response = await self._handle_with_llm(content)

        response = self._format_with_tone(response, sentiment)
        quick_replies = self._generate_quick_replies(intent_result)

        return {
            "response": response,
            "intent": {
                "intent_code": intent_result.intent_code,
                "intent_name": intent_result.intent_name,
                "confidence": intent_result.confidence,
                "entities": [
                    {"type": e.type, "value": e.value} for e in intent_result.entities
                ],
                "handler_type": effective_handler,
                "priority": intent_result.priority,
            },
            "sentiment": sentiment.value,
            "sentiment_score": sentiment_score,
            "quick_replies": quick_replies,
            "need_transfer": effective_handler == "transfer",
        }

    async def create_session(
        self,
        user_id: Optional[int] = None,
        channel: str = "web",
    ) -> dict[str, Any]:
        """创建新的对话会话。"""
        session_id = uuid.uuid4().hex
        logger.info(f"创建会话: {session_id[:8]}...")

        return {
            "session": {
                "session_id": session_id,
                "user_id": user_id,
                "status": "active",
                "channel": channel,
                "message_count": 0,
                "bot_name": "小E",
            },
            "welcome_message": (
                "您好，我是智能客服小E，很高兴为您服务。"
                "我可以帮您查询订单、了解商品信息、处理退款退货等问题。"
                "请问有什么可以帮到您的？"
            ),
            "quick_replies": [
                "查询我的订单",
                "如何退货？",
                "有什么优惠活动？",
                "转人工客服",
            ],
        }

    async def _handle_transfer(
        self, intent_result, sentiment: SentimentType
    ) -> str:
        if sentiment == SentimentType.NEGATIVE:
            return (
                "非常抱歉给您带来了不愉快的体验。"
                "我正在为您转接专业客服专员，他们会优先为您处理。"
                "请稍候片刻，专员将很快接入。"
            )
        return (
            "正在为您转接人工客服，请稍候。"
            "客服专员将很快接入为您服务。"
        )

    async def _handle_with_tools(
        self,
        intent_result,
        content: str,
        user_id: Optional[int],
    ) -> str:
        try:
            from app.agents.customer_agent import CustomerServiceAgent
            agent = CustomerServiceAgent(
                session_id="tool_session",
                user_id=user_id,
            )
            result = await agent.process(content)
            return result.get("response", "您的请求已处理完成。")
        except Exception as e:
            logger.error(f"工具执行失败: {e}")
            return (
                "抱歉，我在处理您的请求时遇到了问题。"
                "让我为您转接人工客服，他们会帮您解决。"
            )

    async def _handle_with_rag(self, content: str) -> str:
        try:
            context = await self.rag_service.retrieve(content, top_k=3)
            if not context:
                return await self._handle_with_llm(content)
            return await self.rag_service.generate(content, context)
        except Exception as e:
            logger.error(f"RAG 处理失败: {e}")
            return await self._handle_with_llm(content)

    async def _handle_with_llm(self, content: str) -> str:
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是小E，电商平台的智能客服助手。"
                        "请保持专业、友好、简洁。"
                        "如果无法回答问题，建议用户转接人工客服。"
                        "使用中文回复。"
                    ),
                },
                {"role": "user", "content": content},
            ]
            return await self.llm_service.chat(messages)
        except Exception as e:
            logger.error(f"LLM 处理失败: {e}")
            return (
                "抱歉，我暂时无法处理您的请求。"
                "请稍后再试，或让我为您转接人工客服。"
            )

    def _format_with_tone(self, response: str, sentiment: SentimentType) -> str:
        strategy = self.sentiment_service.get_response_strategy(sentiment, 0.0)
        if sentiment == SentimentType.NEGATIVE:
            return f"{strategy['prefix']} {response}"
        return response

    def _generate_quick_replies(self, intent_result) -> list[str]:
        quick_reply_map = {
            "order_query": [
                "我的订单到哪了？",
                "修改收货地址",
                "查看物流详情",
            ],
            "product_inquiry": [
                "这个商品有什么规格？",
                "现在有库存吗？",
                "有类似的推荐吗？",
            ],
            "refund_request": [
                "发起退货申请",
                "查询退款进度",
                "退货政策是什么？",
            ],
            "complaint": [
                "我要投诉",
                "提交反馈意见",
                "联系客服主管",
            ],
            "greeting": [
                "查看我的订单",
                "看看有什么优惠",
                "帮我推荐商品",
            ],
        }
        return quick_reply_map.get(intent_result.intent_code, [
            "详细说说",
            "我还有其他问题",
            "帮我转人工客服",
        ])
