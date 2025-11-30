# AI 對話服務
# AI Conversation Service
"""
AI 對話服務
===========

使用 OpenAI GPT-4o-mini 進行自然語言理解：
- 意圖識別（Intent Recognition）
- 自然語言轉指令
- 對話上下文管理
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.config import settings
from src.commands.parser import CommandType, ParsedCommand
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class AIIntent:
    """AI 識別的意圖"""
    
    command_type: CommandType
    """識別的指令類型"""
    
    confidence: float
    """信心度（0.0-1.0）"""
    
    parameters: Dict[str, Any]
    """提取的參數"""
    
    explanation: Optional[str] = None
    """解釋說明"""


class AIService:
    """
    AI 對話服務
    
    使用 OpenAI GPT-4o-mini 模型進行自然語言處理。
    """
    
    # 系統提示詞
    SYSTEM_PROMPT = """你是一個 LINE 自動化助手的意圖識別器。
    
你的任務是分析用戶的訊息，識別他們的意圖，並轉換為系統指令。

可識別的指令類型：
- add_todo: 新增待辦事項（例如：「記得要買牛奶」、「待辦 開會」）
- add_note: 新增筆記（例如：「筆記 今天很開心」、「記下這個想法」）
- add_expense: 記錄支出（例如：「花了 100 元吃午餐」、「支出 50 飲料」）
- set_reminder: 設定提醒（例如：「提醒我明天開會」、「下午3點提醒我打電話」）
- create_workflow: 建立工作流程（例如：「建立一個早安提醒流程」）
- run_workflow: 執行工作流程（例如：「執行早安流程」）
- list_workflows: 列出工作流程（例如：「我的流程」）
- connect_service: 連接外部服務（例如：「連接 Google 日曆」）
- list_services: 列出已連接服務（例如：「我的服務」）
- help: 顯示說明（例如：「幫助」、「怎麼用」）
- status: 顯示狀態（例如：「狀態」）
- history: 查看歷史（例如：「歷史」）
- unknown: 無法識別

請以 JSON 格式回應：
{
    "command_type": "指令類型",
    "confidence": 0.0-1.0,
    "parameters": {
        "content": "提取的內容",
        "amount": 金額（如果是支出）,
        "time": "時間（如果是提醒）",
        "service": "服務名稱（如果是連接服務）"
    },
    "explanation": "解釋為什麼這樣識別"
}
"""
    
    def __init__(self):
        """初始化 AI 服務"""
        self._client = None
        self._model = settings.openai_model
    
    @property
    def client(self):
        """延遲載入 OpenAI 客戶端"""
        if self._client is None:
            try:
                import openai
                self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.warning("OpenAI package not installed")
                self._client = None
        return self._client
    
    async def recognize_intent(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AIIntent:
        """
        識別用戶意圖
        
        Args:
            text: 用戶輸入的文字
            context: 可選的對話上下文
        
        Returns:
            AIIntent: 識別結果
        """
        if not self.client:
            logger.error("OpenAI client not available")
            return AIIntent(
                command_type=CommandType.UNKNOWN,
                confidence=0.0,
                parameters={},
                explanation="AI 服務不可用",
            )
        
        try:
            # 建立對話訊息
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ]
            
            # 如果有上下文，添加到訊息中
            if context and context.get("previous_messages"):
                for msg in context["previous_messages"][-5:]:  # 最多保留 5 條
                    messages.insert(-1, msg)
            
            # 呼叫 OpenAI API
            response = await self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.3,  # 低溫度以獲得更一致的結果
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            
            # 解析回應
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            # 轉換為 AIIntent
            command_type = self._parse_command_type(result.get("command_type", "unknown"))
            
            return AIIntent(
                command_type=command_type,
                confidence=float(result.get("confidence", 0.5)),
                parameters=result.get("parameters", {}),
                explanation=result.get("explanation"),
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return AIIntent(
                command_type=CommandType.UNKNOWN,
                confidence=0.0,
                parameters={},
                explanation=f"解析 AI 回應失敗: {e}",
            )
        except Exception as e:
            logger.error(f"AI service error: {e}")
            return AIIntent(
                command_type=CommandType.UNKNOWN,
                confidence=0.0,
                parameters={},
                explanation=f"AI 服務錯誤: {e}",
            )
    
    def _parse_command_type(self, type_str: str) -> CommandType:
        """
        解析指令類型字串
        
        Args:
            type_str: 指令類型字串
        
        Returns:
            CommandType: 指令類型列舉
        """
        type_map = {
            "add_todo": CommandType.ADD_TODO,
            "add_note": CommandType.ADD_NOTE,
            "add_expense": CommandType.ADD_EXPENSE,
            "set_reminder": CommandType.SET_REMINDER,
            "create_workflow": CommandType.CREATE_WORKFLOW,
            "run_workflow": CommandType.RUN_WORKFLOW,
            "list_workflows": CommandType.LIST_WORKFLOWS,
            "delete_workflow": CommandType.DELETE_WORKFLOW,
            "connect_service": CommandType.CONNECT_SERVICE,
            "disconnect_service": CommandType.DISCONNECT_SERVICE,
            "list_services": CommandType.LIST_SERVICES,
            "help": CommandType.HELP,
            "status": CommandType.STATUS,
            "history": CommandType.HISTORY,
        }
        return type_map.get(type_str.lower(), CommandType.UNKNOWN)
    
    async def parse_with_ai(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ParsedCommand:
        """
        使用 AI 解析指令
        
        Args:
            text: 原始訊息文字
            context: 可選的對話上下文
        
        Returns:
            ParsedCommand: 解析結果
        """
        intent = await self.recognize_intent(text, context)
        
        return ParsedCommand(
            command_type=intent.command_type,
            raw_text=text,
            parameters=intent.parameters,
            confidence=intent.confidence,
            needs_ai=False,  # 已經經過 AI 解析
            error=None if intent.confidence > 0.3 else intent.explanation,
        )
    
    async def generate_response(
        self,
        user_message: str,
        system_context: Optional[str] = None
    ) -> str:
        """
        生成對話回應
        
        Args:
            user_message: 用戶訊息
            system_context: 系統上下文
        
        Returns:
            str: 生成的回應
        """
        if not self.client:
            return "抱歉，AI 服務暫時不可用。請稍後再試。"
        
        try:
            messages = []
            
            if system_context:
                messages.append({"role": "system", "content": system_context})
            
            messages.append({"role": "user", "content": user_message})
            
            response = await self.client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI response generation error: {e}")
            return "抱歉，我無法理解您的訊息。請試著用不同的方式描述。"


# 單例模式
_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """取得 AI 服務單例"""
    global _service
    if _service is None:
        _service = AIService()
    return _service
