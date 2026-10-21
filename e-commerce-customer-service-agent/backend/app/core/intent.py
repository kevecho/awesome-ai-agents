# backend/app/core/intent.py
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class IntentCode(str, Enum):
    PRODUCT_INQUIRY = 'product_inquiry'
    ORDER_QUERY = 'order_query'
    REFUND_REQUEST = 'refund_request'
    COMPLAINT = 'complaint'
    HUMAN_AGENT = 'human_agent'
    GREETING = 'greeting'
    FALLBACK = 'fallback'


class HandlerType(str, Enum):
    LLM = 'llm'
    TOOL = 'tool'
    RAG = 'rag'
    TRANSFER = 'transfer'


class EntityType(str, Enum):
    ORDER_NO = 'order_no'
    PHONE = 'phone'
    PRODUCT_NAME = 'product_name'
    AMOUNT = 'amount'
    DATE = 'date'


INTENT_MAP: Dict[str, str] = {
    IntentCode.PRODUCT_INQUIRY: '商品咨询',
    IntentCode.ORDER_QUERY: '订单查询',
    IntentCode.REFUND_REQUEST: '退款退货',
    IntentCode.COMPLAINT: '投诉建议',
    IntentCode.HUMAN_AGENT: '转人工',
    IntentCode.GREETING: '问候',
    IntentCode.FALLBACK: '其他',
}


def get_intent_name(code: str) -> str:
    return INTENT_MAP.get(code, code)


def get_intent_handler(code: str) -> str:
    handlers: Dict[str, str] = {
        IntentCode.PRODUCT_INQUIRY: HandlerType.RAG,
        IntentCode.ORDER_QUERY: HandlerType.TOOL,
        IntentCode.REFUND_REQUEST: HandlerType.TOOL,
        IntentCode.COMPLAINT: HandlerType.TRANSFER,
        IntentCode.HUMAN_AGENT: HandlerType.TRANSFER,
        IntentCode.GREETING: HandlerType.LLM,
        IntentCode.FALLBACK: HandlerType.LLM,
    }
    return handlers.get(code, HandlerType.LLM)