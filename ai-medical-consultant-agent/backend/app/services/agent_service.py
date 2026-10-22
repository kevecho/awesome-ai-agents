# ============================================================
# AI Medical Consultant - Agent Service (智能体决策编排)
# ============================================================
# 基于文档 3.2 Agent决策编排逻辑 实现
# ============================================================
from typing import Optional, List, Dict, AsyncGenerator
from loguru import logger

from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.config import settings
from app.schemas.structured_output import StructuredOutputError


class MedicalAgent:
    """
    MedicalAgent - 医疗智能体

    核心能力:
    1. 症状分析 (Symptom Analysis) - 提取关键症状，结构化
    2. 意图识别 (Intent Recognition) - 问诊类/查询类/闲聊类
    3. 追问生成 (Follow-up Generation) - 缺失信息追问
    4. 分诊决策 (Triage Decision) - 推荐就诊科室
    5. 鉴别诊断 (Differential Diagnosis) - 可能病因分析
    """

    # 意图类型
    INTENT_CONSULT = "consult"        # 问诊类 - 需要症状分析
    INTENT_QUERY = "query"            # 查询类 - 医学知识查询
    INTENT_CHITCHAT = "chitchat"      # 闲聊类 - 一般对话

    # 紧急关键词 — 双层防御的兜底列表
    EMERGENCY_KEYWORDS = [
        # 心脑血管
        "胸痛", "胸闷", "心慌", "心悸", "心绞痛",
        "呼吸困难", "喘不过气", "窒息", "上不来气",
        # 神经
        "晕倒", "昏倒", "失去意识", "不省人事", "昏迷",
        "抽搐", "痉挛", "癫痫", "口吐白沫",
        "突然看不见", "突然听不见", "半身不遂", "偏瘫", "面瘫",
        "剧烈头痛",
        # 出血/创伤
        "大出血", "吐血", "咳血", "便血",
        "严重外伤", "骨折", "车祸",
        # 中毒/过敏
        "过敏性休克", "喉头水肿",
        "中毒", "误食.*药", "过量.*药", "农药",
        # 其他急症
        "严重烧伤", "大面积烫伤",
        "自杀", "自残", "不想活",
        "高烧.*不退", "持续.*40度",
        "腹痛.*剧烈", "绞痛",
        "严重过敏",
    ]

    def __init__(self):
        self.current_intent = None
        self.collected_symptoms: List[Dict] = []
        self.symptom_collection_round = 0
        self.max_collection_rounds = 3

    # ==================== Agent 主流程 ====================

    async def process(
        self,
        user_message: str,
        consultation_id: int,
        conversation_history: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        Agent主流程 - 处理用户消息并生成回复

        流程:
        1. 意图识别 → 确定消息类型
        2. 症状分析 → 提取/更新结构化症状
        3. 判断追问 → 是否需要更多信息
        4. RAG检索 → 获取相关知识
        5. LLM生成 → 流式生成回复
        """
        # Step 1: 意图识别
        intent = await self._recognize_intent(user_message)
        self.current_intent = intent
        logger.info(f"[Agent] Intent: {intent}, Message: {user_message[:50]}...")

        # Step 2-5: 根据意图执行不同流程
        if intent == self.INTENT_CONSULT:
            async for chunk in self._handle_consult(user_message, conversation_history):
                yield chunk
        elif intent == self.INTENT_QUERY:
            async for chunk in self._handle_query(user_message, conversation_history):
                yield chunk
        else:
            async for chunk in self._handle_chitchat(user_message, conversation_history):
                yield chunk

    # ==================== 紧急检测 ====================

    def _check_emergency_keywords(self, message: str):
        """
        关键词紧急检测 — 不依赖 LLM，零延迟。
        返回匹配到的危险信号关键词，或 None。

        用途：双层防御
          - 第 1 层：LLM 调用前预检（快速拦截，零延迟）
          - 第 2 层：LLM 调用后兜底（LLM 漏判 / JSON 解析失败时补救）
        """
        import re
        message_lower = message.lower()
        for keyword in self.EMERGENCY_KEYWORDS:
            if re.search(keyword, message_lower):
                return keyword
        return None

    # ==================== 意图识别 ====================

    async def _recognize_intent(self, message: str) -> str:
        """识别用户意图"""
        message_lower = message.lower()

        # 问诊类关键词
        consult_keywords = [
            "不舒服", "疼", "痛", "难受", "发烧", "咳嗽", "头晕", "恶心",
            "症状", "怎么办", "怎么回事", "什么原因", "是不是",
            "拉肚子", "失眠", "胸闷", "心慌", "痒", "肿", "出血",
            "不舒服了", "感冒了", "生病了", "发炎", "过敏",
        ]

        # 查询类关键词
        query_keywords = [
            "什么是", "什么意思", "解释", "科普", "介绍", "区别",
            "怎么办", "注意事项", "饮食", "运动", "预防",
        ]

        # 检查问诊类
        for kw in consult_keywords:
            if kw in message_lower:
                return self.INTENT_CONSULT

        # 检查查询类
        for kw in query_keywords:
            if kw in message_lower:
                return self.INTENT_QUERY

        # 默认问诊类（因为医疗场景下大部分是问诊）
        if len(message) > 10:
            return self.INTENT_CONSULT

        return self.INTENT_CHITCHAT

    # ==================== 问诊流程 ====================

    async def _handle_consult(
        self,
        user_message: str,
        history: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """处理问诊类消息"""

        # ===== 第 1 层：LLM 调用前关键词预检 =====
        emergency_hit = self._check_emergency_keywords(user_message)
        if emergency_hit:
            logger.warning(
                f"[Agent] Emergency keyword hit: '{emergency_hit}' "
                f"| message: {user_message[:80]}"
            )
            yield {
                "type": "emergency",
                "content": (
                    "⚠️ 根据您的描述（{}），这可能属于紧急情况！\n\n"
                    "请立即前往医院急诊科就诊或拨打120。"
                ).format(emergency_hit),
                "metadata": {"urgency": "emergency", "source": "keyword_prescan"}
            }
            return

        # Step A: 症状分析 - 从用户消息中提取结构化症状
        yield {"type": "status", "content": "正在分析您的症状...", "metadata": {"step": "symptom_analysis"}}

        try:
            symptom_result = await llm_service.analyze_symptoms(user_message)
        except StructuredOutputError:
            logger.warning(
                f"[Agent] Symptom analysis structured output failed "
                f"→ fail-closed to emergency. message: {user_message[:100]}"
            )
            yield {
                "type": "emergency",
                "content": "⚠️ 根据您的描述，这可能属于紧急情况！请立即前往医院急诊科就诊或拨打120。",
                "metadata": {"urgency": "emergency"}
            }
            return

        # 正常路径：pydantic 属性访问
        if symptom_result.symptoms:
            self.collected_symptoms.extend([
                s.model_dump() for s in symptom_result.symptoms
            ])

        is_emergency = symptom_result.is_emergency

        # ===== 第 2 层：LLM 调用后关键词兜底 =====
        if not is_emergency:
            fallback_hit = self._check_emergency_keywords(user_message)
            if fallback_hit:
                is_emergency = True
                logger.warning(
                    f"[Agent] LLM missed emergency '{fallback_hit}', "
                    f"caught by keyword fallback. "
                    f"LLM response preview: {str(symptom_result)[:200]}"
                )

        # 紧急情况立即建议就医
        if is_emergency:
            yield {
                "type": "emergency",
                "content": "⚠️ 根据您的描述，这可能属于紧急情况！请立即前往医院急诊科就诊或拨打120。",
                "metadata": {"urgency": "emergency"}
            }
            return

        # Step B: 检查是否需要追问
        missing_info = symptom_result.missing_info
        self.symptom_collection_round += 1

        if missing_info and self.symptom_collection_round < self.max_collection_rounds:
            # 需要追问更多信息
            yield {"type": "status", "content": "需要了解更多信息...", "metadata": {"step": "follow_up"}}

            follow_up_prompt = f"""用户说: "{user_message}"

根据已收集的信息，还需要了解:
{chr(10).join(f'- {m}' for m in missing_info)}

请友好地问1-2个最关键的问题来补充信息。回复要自然、亲切。"""
            messages = [{"role": "user", "content": follow_up_prompt}]

            collected = ""
            async for token in llm_service.chat_stream(messages):
                collected += token
                yield {"type": "token", "content": token}

            yield {
                "type": "complete",
                "content": collected,
                "metadata": {
                    "intent": self.INTENT_CONSULT,
                    "step": "follow_up",
                    "symptoms_collected": len(self.collected_symptoms),
                    "missing_info": missing_info,
                }
            }
            return

        # Step C: 信息充足 → RAG检索 + 分诊 + 诊断
        yield {"type": "status", "content": "正在检索医学知识...", "metadata": {"step": "rag_retrieval"}}

        # 构建检索查询
        symptoms_desc = " ".join([
            s.get("name", "") + s.get("description", "")
            for s in self.collected_symptoms
        ])

        # RAG检索
        context = await rag_service.build_context(
            query=f"{user_message} {symptoms_desc}",
            top_k=settings.TOP_K_RETRIEVAL,
            conversation_history=history,
        )

        # 分诊
        yield {"type": "status", "content": "正在分析分诊建议...", "metadata": {"step": "triage"}}

        try:
            triage_result = await llm_service.triage(self.collected_symptoms)
            triage_urgency = triage_result.urgency
            triage_department = triage_result.department
            triage_reasoning = triage_result.reasoning
        except StructuredOutputError:
            logger.warning(
                f"[Agent] Triage structured output failed → fail-closed to emergency. "
                f"symptoms: {symptoms_desc[:100]}"
            )
            triage_urgency = "emergency"
            triage_department = ""
            triage_reasoning = ""

        # 生成回复
        yield {"type": "status", "content": "正在生成诊断建议...", "metadata": {"step": "generating"}}

        # 构建完整上下文
        knowledge_context = context.get("knowledge_context", "")

        messages = llm_service.build_messages(
            user_message=user_message,
            history=history,
            knowledge_context=knowledge_context,
        )

        # 流式输出
        full_response = ""
        async for token in llm_service.chat_stream(
            messages,
            system_prompt=llm_service.SYSTEM_PROMPTS["consultation"],
        ):
            full_response += token
            yield {"type": "token", "content": token}

        yield {
            "type": "triage",
            "content": "",
            "metadata": {
                "urgency": triage_urgency,
                "department": triage_department,
                "reasoning": triage_reasoning,
            }
        }

        # 完成
        yield {
            "type": "complete",
            "content": full_response,
            "metadata": {
                "intent": self.INTENT_CONSULT,
                "step": "complete",
                "symptoms_count": len(self.collected_symptoms),
                "knowledge_sources": len(context.get("retrieved_docs", [])),
            }
        }

        # 重置状态
        self._reset()

    # ==================== 查询流程 ====================

    async def _handle_query(
        self,
        user_message: str,
        history: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """处理医学知识查询 - RAG直接检索回答"""

        yield {"type": "status", "content": "正在检索相关知识...", "metadata": {"step": "rag_retrieval"}}

        # RAG检索
        context = await rag_service.build_context(
            query=user_message,
            top_k=settings.TOP_K_RETRIEVAL,
        )

        knowledge_context = context.get("knowledge_context", "")

        if knowledge_context:
            # 基于检索知识生成回答
            messages = llm_service.build_messages(
                user_message=user_message,
                history=history,
                knowledge_context=knowledge_context,
            )

            full_response = ""
            async for token in llm_service.chat_stream(messages):
                full_response += token
                yield {"type": "token", "content": token}

            yield {
                "type": "complete",
                "content": full_response,
                "metadata": {
                    "intent": self.INTENT_QUERY,
                    "knowledge_sources": len(context.get("retrieved_docs", [])),
                }
            }
        else:
            # 知识库为空时的兜底回复
            msg = "抱歉，当前知识库中没有找到相关信息。请尝试换个方式提问。"
            yield {"type": "token", "content": msg}
            yield {"type": "complete", "content": msg, "metadata": {"intent": self.INTENT_QUERY}}

    # ==================== 闲聊流程 ====================

    async def _handle_chitchat(
        self,
        user_message: str,
        history: Optional[List[Dict]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """处理闲聊 - 普通对话，不需要RAG"""

        messages = list(history or [])
        messages.append({"role": "user", "content": user_message})

        full_response = ""
        async for token in llm_service.chat_stream(messages):
            full_response += token
            yield {"type": "token", "content": token}

        yield {
            "type": "complete",
            "content": full_response,
            "metadata": {"intent": self.INTENT_CHITCHAT}
        }

    # ==================== 分诊决策 ====================

    async def triage(self, symptoms: List[Dict]):
        """执行分诊决策"""
        return await llm_service.triage(symptoms)

    # ==================== 鉴别诊断 ====================

    async def diagnose(self, symptoms: List[Dict]):
        """生成鉴别诊断建议"""
        symptoms_desc = " ".join([s.get("name", "") for s in symptoms])
        context = await rag_service.build_context(query=symptoms_desc)
        return await llm_service.generate_diagnosis(
            symptoms=symptoms,
            knowledge_context=context.get("knowledge_context", ""),
        )

    # ==================== 状态管理 ====================

    def _reset(self):
        """重置Agent状态"""
        self.collected_symptoms = []
        self.symptom_collection_round = 0
        self.current_intent = None

    def get_state(self) -> Dict:
        """获取当前Agent状态"""
        return {
            "intent": self.current_intent,
            "symptoms_collected": len(self.collected_symptoms),
            "collection_round": self.symptom_collection_round,
            "symptoms": self.collected_symptoms,
        }


# Global instance
medical_agent = MedicalAgent()
