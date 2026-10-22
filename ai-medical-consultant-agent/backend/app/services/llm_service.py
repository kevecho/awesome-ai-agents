# ============================================================
# AI Medical Consultant - LLM Service (大语言模型服务)
# ============================================================
# 基于文档 3.3 LLM调用逻辑 实现
# ============================================================
from typing import Optional, List, Dict, AsyncGenerator
from openai import AsyncOpenAI
from loguru import logger
from pydantic import BaseModel

from app.config import settings
from app.schemas.structured_output import StructuredOutputError


class LLMService:
    """
    LLM服务 - 大语言模型调用

    配置:
    - 模型: deepseek-chat (兼容OpenAI接口)
    - 温度: 0.7
    - 流式输出: True
    - 最大Tokens: 4096
    """

    SYSTEM_PROMPTS = {
        "consultation": """你是一位专业的AI医疗助手，名为"小医"。你的职责是：

1. **症状收集**: 通过友好的多轮对话收集患者症状，包括：
   - 主要症状（什么不舒服？）
   - 持续时间（多久了？）
   - 严重程度（轻微/中等/严重）
   - 伴随症状（还有其他不适吗？）
   - 既往病史（有相关病史吗？）

2. **健康建议**: 基于收集到的信息，给出初步的健康建议和注意事项。

3. **分诊指导**: 根据症状推荐合适的就诊科室。

4. **医学知识**: 当被问及医学术语或疾病时，用通俗易懂的语言解释。

**重要原则**：
- 你不是真正的医生，不能替代专业医疗诊断
- 如果症状描述涉及紧急情况（胸痛、呼吸困难、严重出血等），立即建议就医
- 回答要专业但易懂，避免过于复杂的医学术语
- 保护用户隐私，不存储或分享敏感健康信息
- 每次回答末尾附上免责声明："⚠️ 本内容由AI生成，仅供参考，不构成医疗建议。如有不适请及时就医。" """,

        "symptom_analysis": """你是一位症状分析专家。请分析以下患者描述的症状，提取关键信息并结构化输出。

请以JSON格式返回：
{
  "symptoms": [
    {"name": "症状名", "location": "部位", "duration": "持续时间", "severity": "严重程度"}
  ],
  "missing_info": ["还需要了解的信息"],
  "is_emergency": false,
  "suggested_department": "推荐科室"
}""",

        "triage": """你是一位分诊专家。根据患者的症状，判断紧急程度并推荐就诊科室。

请以JSON格式返回：
{
  "urgency": "normal/urgent/emergency",
  "department": "推荐科室",
  "reasoning": "分诊理由",
  "confidence": 0.0-1.0
}""",

        "diagnosis": """你是一位临床诊断专家。基于以下患者信息和检索到的医学知识，给出可能的鉴别诊断建议。

注意：你提供的是"可能的情况"而非"确诊"，需要列出多种可能性并注明每种可能性的依据。

请以JSON格式返回：
{
  "possible_conditions": [
    {"name": "可能的疾病", "probability": "high/medium/low", "basis": "判断依据", "description": "简要描述"}
  ],
  "suggested_exams": ["建议的检查项目"],
  "care_advice": ["护理建议"],
  "when_to_seek_emergency": "什么情况需要立即就医"
}""",
    }

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    # ==================== 非流式调用 ====================

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        非流式LLM调用

        Args:
            messages: 对话历史 [{"role": "user/assistant/system", "content": "..."}]
            system_prompt: 系统提示词（覆盖默认）
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            LLM回复文本
        """
        full_messages = []

        # 添加系统提示词
        prompt = system_prompt or self.SYSTEM_PROMPTS["consultation"]
        full_messages.append({"role": "system", "content": prompt})

        # 添加对话历史
        full_messages.extend(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=False,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return f"抱歉，AI服务暂时不可用，请稍后重试。错误: {str(e)}"

    # ==================== 流式调用 ====================

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式LLM调用 - 逐token返回

        用于WebSocket实时推送
        """
        full_messages = []

        prompt = system_prompt or self.SYSTEM_PROMPTS["consultation"]
        full_messages.append({"role": "system", "content": prompt})
        full_messages.extend(messages)

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content

        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            yield f"\n\n[AI服务异常: {str(e)}]"

    # ==================== 结构化调用 ====================

    async def chat_structured(
        self,
        system_prompt: str,
        user_content: str,
        schema_model: type[BaseModel],
        use_tool: Optional[Dict] = None,
        temperature: float = 0.3,
    ) -> BaseModel:
        """
        结构化 LLM 调用 — 用 JSON mode 或 function calling 保证输出合法，
        再通过 pydantic 校验字段名和类型。

        Args:
            system_prompt: 系统提示词（含 JSON 字段描述）
            user_content: 用户输入
            schema_model: pydantic 模型类，用于校验返回数据
            use_tool: 传 None 走 JSON mode；传 tool dict 走 function calling
            temperature: 温度参数（结构化输出推荐低温度）

        Returns:
            校验通过的 pydantic 模型实例

        Raises:
            StructuredOutputError: JSON 解析或 pydantic 校验失败
        """
        import json

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        kwargs: Dict = dict(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=self.max_tokens,
            stream=False,
        )

        if use_tool is not None:
            kwargs["tools"] = [use_tool]
            kwargs["tool_choice"] = {
                "type": "function",
                "function": {"name": use_tool["function"]["name"]},
            }
        else:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = await self.client.chat.completions.create(**kwargs)
            msg = resp.choices[0].message

            if msg.tool_calls:
                raw = msg.tool_calls[0].function.arguments
            else:
                raw = msg.content

            data = json.loads(raw)
            return schema_model.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error(f"[chat_structured] JSON decode failed: {e} | raw: {raw[:200]}")
            raise StructuredOutputError(f"JSON解析失败: {e}") from e
        except Exception as e:
            logger.error(f"[chat_structured] Structured output failed: {e}")
            raise StructuredOutputError(str(e)) from e

    # ==================== 结构化调用（业务方法） ====================

    async def analyze_symptoms(self, user_message: str) -> "SymptomAnalysis":
        """症状分析 - 提取结构化症状信息"""
        from app.schemas.structured_output import SymptomAnalysis
        return await self.chat_structured(
            system_prompt=self.SYSTEM_PROMPTS["symptom_analysis"],
            user_content=user_message,
            schema_model=SymptomAnalysis,
        )

    async def triage(self, symptoms: List[Dict]) -> "TriageResult":
        """智能分诊 - 判断紧急程度和推荐科室"""
        from app.schemas.structured_output import TriageResult
        symptoms_text = "\n".join([
            f"- {s.get('name', '')}: {s.get('description', '')}"
            for s in symptoms
        ])
        return await self.chat_structured(
            system_prompt=self.SYSTEM_PROMPTS["triage"],
            user_content=f"患者症状：\n{symptoms_text}",
            schema_model=TriageResult,
        )

    async def generate_diagnosis(
        self,
        symptoms: List[Dict],
        knowledge_context: str,
    ) -> "DiagnosisResult":
        """诊断建议 - 基于RAG知识生成鉴别诊断"""
        from app.schemas.structured_output import DiagnosisResult
        symptoms_text = "\n".join([
            f"- {s.get('name', '')}: {s.get('description', '')}"
            for s in symptoms
        ])
        user_content = f"""患者症状：
{symptoms_text}

参考医学知识：
{knowledge_context}

请基于以上信息给出鉴别诊断建议。"""
        return await self.chat_structured(
            system_prompt=self.SYSTEM_PROMPTS["diagnosis"],
            user_content=user_content,
            schema_model=DiagnosisResult,
            temperature=0.5,
        )

    # ==================== 辅助方法 ====================

    def build_messages(
        self,
        user_message: str,
        history: Optional[List[Dict]] = None,
        knowledge_context: Optional[str] = None,
    ) -> List[Dict]:
        """构建包含RAG上下文的完整消息"""
        messages = []

        if knowledge_context:
            messages.append({
                "role": "system",
                "content": f"以下是与当前问诊相关的医学知识，请基于这些知识回答问题：\n\n{knowledge_context}"
            })

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})
        return messages


# Global instance
llm_service = LLMService()
