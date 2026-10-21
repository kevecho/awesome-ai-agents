"""情感分析服务。"""

from enum import Enum
from typing import Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SentimentType(str, Enum):
    """情感分类标签。"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SentimentService:
    """分析用户消息中的情感倾向。"""

    NEGATIVE_WORDS: dict[str, float] = {
        "非常差": -1.0, "极差": -1.0, "太差了": -1.0,
        "很差": -0.9, "非常糟糕": -1.0, "太糟糕": -1.0,
        "差": -0.7, "失望": -0.7, "不满意": -0.7,
        "生气": -0.9, "愤怒": -1.0, "火大": -0.8,
        "投诉": -0.8, "骗子": -1.0, "假货": -0.9,
        "后悔": -0.6, "坑人": -0.8, "烂": -0.8,
        "垃圾": -0.8, "最差": -0.9, "讨厌": -0.8,
        "烦": -0.6, "无语": -0.6, "恶心": -0.8,
        "terrible": -1.0, "horrible": -1.0, "awful": -1.0,
        "poor": -0.8, "bad": -0.7, "disappointed": -0.7,
        "angry": -0.9, "upset": -0.7, "scam": -1.0,
    }

    POSITIVE_WORDS: dict[str, float] = {
        "非常好": 1.0, "非常棒": 1.0, "太好了": 1.0,
        "很好": 0.9, "很棒": 0.9, "完美": 1.0,
        "满意": 0.7, "喜欢": 0.8, "感谢": 0.6,
        "谢谢": 0.5, "好评": 0.8, "推荐": 0.7,
        "划算": 0.6, "便宜": 0.5, "漂亮": 0.7,
        "给力": 0.7, "赞": 0.6, "不错": 0.5,
        "优秀": 0.8, "超值": 0.7, "好用": 0.6,
        "excellent": 1.0, "perfect": 1.0, "amazing": 1.0,
        "great": 0.8, "good": 0.5, "wonderful": 0.9,
        "love": 0.8, "thank": 0.6, "recommend": 0.7,
    }

    NEGATION_WORDS: set[str] = {"不", "没", "无", "非", "别", "从不", "绝不", "not", "no", "never"}

    ESCALATION_PATTERNS: list[str] = [
        "我要退款", "投诉你们", "举报", "再也不买了",
        "注销账号", "找客服主管", "打投诉电话", "我要投诉",
    ]

    async def analyze(self, text: str) -> tuple[SentimentType, float]:
        """分析文本的情感倾向。"""
        text_lower = text.lower()
        lexicon_score = self._lexicon_score(text_lower)
        rule_score = self._rule_score(text_lower)
        final_score = lexicon_score * 0.7 + rule_score * 0.3
        sentiment = self._score_to_type(final_score)
        logger.debug(f"情感分析: '{text[:50]}...' -> {sentiment.value} ({final_score:.2f})")
        return sentiment, round(final_score, 2)

    def _lexicon_score(self, text: str) -> float:
        total_score = 0.0
        match_count = 0
        for word, score in {**self.NEGATIVE_WORDS, **self.POSITIVE_WORDS}.items():
            if word in text:
                effective_score = score
                if self._is_negated(text, word):
                    effective_score = -score * 0.5
                total_score += effective_score
                match_count += 1
        if match_count == 0:
            return 0.0
        return max(-1.0, min(1.0, total_score / match_count))

    def _is_negated(self, text: str, word: str) -> bool:
        for neg in self.NEGATION_WORDS:
            neg_pos = text.find(neg)
            word_pos = text.find(word)
            if neg_pos != -1 and word_pos != -1 and 0 < word_pos - neg_pos < 6:
                return True
        return False

    def _rule_score(self, text: str) -> float:
        score = 0.0
        import re
        if re.search(r"([!?！？])\1{2,}", text):
            score += 0.1 if "!" in text or "！" in text else -0.05
        question_count = text.count("?") + text.count("？")
        if question_count >= 3:
            score -= 0.1
        return score

    def _score_to_type(self, score: float) -> SentimentType:
        if score <= -0.3:
            return SentimentType.NEGATIVE
        elif score >= 0.3:
            return SentimentType.POSITIVE
        return SentimentType.NEUTRAL

    def should_escalate(self, text: str) -> bool:
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in self.ESCALATION_PATTERNS)

    def get_response_strategy(
        self, sentiment: SentimentType, score: float
    ) -> dict:
        strategies = {
            SentimentType.NEGATIVE: {
                "tone": "empathetic",
                "prefix": "非常抱歉给您带来不便。",
                "action": "consider_escalation",
                "priority": "high",
            },
            SentimentType.NEUTRAL: {
                "tone": "professional",
                "prefix": "感谢您的咨询。",
                "action": "standard_service",
                "priority": "normal",
            },
            SentimentType.POSITIVE: {
                "tone": "friendly",
                "prefix": "很高兴能帮到您。",
                "action": "proactive_recommendation",
                "priority": "normal",
            },
        }
        return strategies.get(sentiment, strategies[SentimentType.NEUTRAL])
