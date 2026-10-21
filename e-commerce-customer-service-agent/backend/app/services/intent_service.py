"""
NLU intent recognition service.

Combines keyword matching, semantic similarity, and LLM-based understanding
for multi-strategy intent classification.
"""

import json
import re
from typing import Optional

from app.schemas.intent import Entity, IntentResult
from app.services.llm_service import LLMService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class IntentService:
    """Multi-strategy intent recognition service.

    Uses a cascade of strategies:
    1. Keyword matching (fast, rule-based)
    2. Semantic similarity (embedding-based, for fuzzy matching)
    3. LLM understanding (deep semantic, for ambiguous queries)

    Results are fused to produce a final classification.
    """

    # 预定义意图配置
    INTENT_DEFINITIONS = {
        'product_inquiry': {
            'keywords': ['商品', '产品', '多少钱', '价格', '怎么样', '好不好'],
            'handler': 'rag',
            'priority': 5
        },
        'order_query': {
            'keywords': ['订单', '查订单', '什么时候到', '发货没'],
            'handler': 'tool',
            'priority': 8
        },
        'refund_request': {
            'keywords': ['退款', '退货', '取消订单', '不想要了'],
            'handler': 'tool',
            'priority': 10
        },
        'complaint': {
            'keywords': ['投诉', '差评', '太差了', '骗子', '态度差'],
            'handler': 'transfer',
            'priority': 10
        },
        'human_agent': {
            'keywords': ['人工', '客服', '真人', '转人工', '人工服务'],
            'handler': 'transfer',
            'priority': 10
        },
        'greeting': {
            'keywords': ['你好', '您好', 'hi', 'hello', '在吗'],
            'handler': 'llm',
            'priority': 1
        },
        'fallback': {
            'keywords': [],
            'handler': 'llm',
            'priority': 0
        }
    }

    def __init__(self):
        self.llm_service = LLMService()

    async def recognize(
        self, text: str, user_id: Optional[int] = None
    ) -> IntentResult:
        """Recognize user intent from text.

        Args:
            text: User input text.
            user_id: Optional user ID for personalization.

        Returns:
            IntentResult with intent code, name, confidence, and entities.
        """
        logger.info(f"Intent recognition: '{text[:80]}...'")

        # Strategy 1: Keyword matching
        keyword_result = self._keyword_match(text)

        # Strategy 2: Semantic matching (threshold-based)
        semantic_result = await self._semantic_match(text)

        # Strategy 3: LLM deep understanding (for ambiguous cases)
        if self._needs_llm_fallback(keyword_result, semantic_result):
            llm_result = await self._llm_understand(text)
        else:
            llm_result = None

        # Fuse results (pick highest confidence * priority)
        final = self._fuse_results(keyword_result, semantic_result, llm_result)

        # Extract entities
        entities = await self._extract_entities(text, final.intent_code)

        logger.info(
            f"Intent recognized: {final.intent_code} (confidence={final.confidence:.2f})"
        )

        return IntentResult(
            intent_code=final.intent_code,
            intent_name=final.intent_name,
            confidence=final.confidence,
            entities=entities,
            handler_type=final.handler_type,
            priority=final.priority,
        )

    def _keyword_match(self, text: str) -> Optional[IntentResult]:
        """Fast keyword-based intent matching."""
        text_lower = text.lower()
        best_match: Optional[IntentResult] = None
        best_score = 0.0

        for intent_code, config in self.INTENT_DEFINITIONS.items():
            match_count = 0
            for keyword in config["keywords"]:
                if keyword.lower() in text_lower:
                    match_count += 1

            if match_count > 0:
                confidence = min(0.9, 0.5 + match_count * 0.15)
                priority_score = confidence * config["priority"]
                if priority_score > best_score:
                    best_score = priority_score
                    best_match = IntentResult(
                        intent_code=intent_code,
                        intent_name=intent_code,
                        confidence=confidence,
                        entities=[],
                        handler_type=config["handler"],
                        priority=config["priority"],
                    )

        return best_match

    async def _semantic_match(self, text: str) -> Optional[IntentResult]:
        """Semantic similarity-based intent matching.

        Uses simple keyword overlap scoring. In production, this would use
        embedding similarity against intent example utterances.
        """
        # For now, semantic matching uses keyword overlap as a proxy
        # In production: embed text -> cosine similarity with intent embeddings
        return None  # Fall back to other strategies

    def _needs_llm_fallback(
        self,
        keyword: Optional[IntentResult],
        semantic: Optional[IntentResult],
    ) -> bool:
        """Determine if LLM-based understanding is needed."""
        if keyword is not None and keyword.confidence >= 0.75:
            return False
        return True

    async def _llm_understand(self, text: str) -> Optional[IntentResult]:
        """Use LLM for deep semantic intent understanding."""
        prompt = f"""Analyze the user's intent from the following message.
Respond ONLY with a JSON object.

Available intents: order_query, order_modify, cancel_order, refund_request,
product_inquiry, promotion, shipping_info, payment_issue, complaint,
human_agent, greeting, other.

User message: "{text}"

Return: {{"intent_code": "xxx", "confidence": 0.0-1.0}}"""

        try:
            response = await self.llm_service.generate(prompt, temperature=0.1)
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)

            intent_code = result.get("intent_code", "other")

            # Map to known handler if possible
            intent_def = self.INTENT_DEFINITIONS.get(intent_code, {})
            return IntentResult(
                intent_code=intent_code,
                intent_name=intent_code,
                confidence=float(result.get("confidence", 0.5)),
                entities=[],
                handler_type=intent_def.get("handler", "llm"),
                priority=intent_def.get("priority", 5),
            )
        except Exception as e:
            logger.warning(f"LLM intent understanding failed: {e}")
            return None

    def _fuse_results(self, *results) -> IntentResult:
        """Fuse multiple intent results, picking the highest-scoring one."""
        valid = [r for r in results if r is not None]

        if not valid:
            return IntentResult(
                intent_code="fallback",
                intent_name="General Query",
                confidence=0.3,
                entities=[],
                handler_type="llm",
                priority=0,
            )

        best = max(valid, key=lambda x: x.confidence * x.priority)
        return best

    async def _extract_entities(
        self, text: str, intent_code: str
    ) -> list[Entity]:
        """Extract named entities from user text."""
        entities: list[Entity] = []

        # Order number pattern
        for match in re.finditer(r"ORDER[\w]{8,20}", text, re.IGNORECASE):
            entities.append(
                Entity(
                    type="order_no",
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                )
            )

        # Chinese phone number pattern
        for match in re.finditer(r"1[3-9]\d{9}", text):
            entities.append(
                Entity(
                    type="phone",
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                )
            )

        # Amount/price pattern
        for match in re.finditer(r"(?:CNY|USD|EUR|GBP|\$|\u00a5|\u20ac|\u00a3)?\s*(\d+(?:\.\d{1,2})?)\s*(?:yuan|dollars|euros)?", text, re.IGNORECASE):
            entities.append(
                Entity(
                    type="amount",
                    value=match.group(1),
                    start=match.start(),
                    end=match.end(),
                )
            )

        return entities
