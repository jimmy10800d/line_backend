# AI 服務單元測試
# AI Service Unit Tests
"""
AI 服務測試
===========

使用 TDD 方法測試 AI 服務功能：
1. 意圖識別
2. 指令轉換
3. 回應生成
4. 錯誤處理
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from src.commands.parser import CommandType
from src.services.ai_service import (
    AIService,
    AIIntent,
    get_ai_service,
)


class TestAIIntent:
    """AI 意圖資料結構測試"""
    
    def test_create_intent(self):
        """測試建立意圖物件"""
        intent = AIIntent(
            command_type=CommandType.ADD_TODO,
            confidence=0.95,
            parameters={"content": "買牛奶"},
            explanation="識別為新增待辦事項",
        )
        
        assert intent.command_type == CommandType.ADD_TODO
        assert intent.confidence == 0.95
        assert intent.parameters["content"] == "買牛奶"
        assert intent.explanation == "識別為新增待辦事項"


class TestAIService:
    """AI 服務測試"""
    
    @pytest.fixture
    def service(self) -> AIService:
        """建立服務實例"""
        return AIService()
    
    @pytest.fixture
    def mock_openai_response(self):
        """建立 Mock OpenAI 回應"""
        def create_response(content: dict):
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(
                    message=MagicMock(content=json.dumps(content))
                )
            ]
            return mock_response
        return create_response
    
    def test_service_singleton(self):
        """測試服務單例模式"""
        service1 = get_ai_service()
        service2 = get_ai_service()
        assert service1 is service2
    
    def test_parse_command_type(self, service: AIService):
        """測試指令類型解析"""
        assert service._parse_command_type("add_todo") == CommandType.ADD_TODO
        assert service._parse_command_type("add_note") == CommandType.ADD_NOTE
        assert service._parse_command_type("ADD_EXPENSE") == CommandType.ADD_EXPENSE
        assert service._parse_command_type("unknown_type") == CommandType.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_recognize_intent_without_client(self, service: AIService):
        """測試沒有 OpenAI 客戶端時的意圖識別"""
        service._client = None
        # 模擬 openai 套件未安裝
        with patch.object(type(service), 'client', property(lambda self: None)):
            intent = await service.recognize_intent("測試訊息")
        
        assert intent.command_type == CommandType.UNKNOWN
        assert intent.confidence == 0.0
        assert "不可用" in intent.explanation
    
    @pytest.mark.asyncio
    async def test_recognize_intent_todo(
        self, service: AIService, mock_openai_response
    ):
        """測試識別待辦事項意圖"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response({
                "command_type": "add_todo",
                "confidence": 0.95,
                "parameters": {"content": "買牛奶"},
                "explanation": "用戶想要記住要買牛奶",
            })
        )
        
        service._client = mock_client
        intent = await service.recognize_intent("記住要買牛奶")
        
        assert intent.command_type == CommandType.ADD_TODO
        assert intent.confidence == 0.95
        assert intent.parameters["content"] == "買牛奶"
    
    @pytest.mark.asyncio
    async def test_recognize_intent_expense(
        self, service: AIService, mock_openai_response
    ):
        """測試識別支出記錄意圖"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response({
                "command_type": "add_expense",
                "confidence": 0.90,
                "parameters": {"amount": 150, "content": "午餐"},
                "explanation": "用戶記錄了午餐支出",
            })
        )
        
        service._client = mock_client
        intent = await service.recognize_intent("午餐花了 150 元")
        
        assert intent.command_type == CommandType.ADD_EXPENSE
        assert intent.parameters["amount"] == 150
    
    @pytest.mark.asyncio
    async def test_recognize_intent_reminder(
        self, service: AIService, mock_openai_response
    ):
        """測試識別提醒意圖"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response({
                "command_type": "set_reminder",
                "confidence": 0.88,
                "parameters": {"content": "開會", "time": "下午3點"},
                "explanation": "用戶想設定開會提醒",
            })
        )
        
        service._client = mock_client
        intent = await service.recognize_intent("下午3點提醒我開會")
        
        assert intent.command_type == CommandType.SET_REMINDER
        assert intent.parameters["time"] == "下午3點"
    
    @pytest.mark.asyncio
    async def test_recognize_intent_json_error(self, service: AIService):
        """測試 JSON 解析錯誤處理"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="invalid json"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        service._client = mock_client
        intent = await service.recognize_intent("測試")
        
        assert intent.command_type == CommandType.UNKNOWN
        assert intent.confidence == 0.0
        assert "解析" in intent.explanation
    
    @pytest.mark.asyncio
    async def test_recognize_intent_api_error(self, service: AIService):
        """測試 API 錯誤處理"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        service._client = mock_client
        intent = await service.recognize_intent("測試")
        
        assert intent.command_type == CommandType.UNKNOWN
        assert "錯誤" in intent.explanation
    
    @pytest.mark.asyncio
    async def test_parse_with_ai(
        self, service: AIService, mock_openai_response
    ):
        """測試使用 AI 解析指令"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response({
                "command_type": "add_todo",
                "confidence": 0.92,
                "parameters": {"content": "運動"},
                "explanation": "識別為待辦事項",
            })
        )
        
        service._client = mock_client
        parsed = await service.parse_with_ai("記得要運動")
        
        assert parsed.command_type == CommandType.ADD_TODO
        assert parsed.parameters["content"] == "運動"
        assert parsed.confidence == 0.92
        assert parsed.needs_ai is False
    
    @pytest.mark.asyncio
    async def test_generate_response_without_client(self, service: AIService):
        """測試沒有客戶端時的回應生成"""
        with patch.object(type(service), 'client', property(lambda self: None)):
            response = await service.generate_response("你好")
        
        assert "不可用" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, service: AIService):
        """測試成功生成回應"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="您好！有什麼我可以幫您的嗎？"))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        service._client = mock_client
        response = await service.generate_response("你好")
        
        assert "您好" in response
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self, service: AIService):
        """測試回應生成錯誤處理"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )
        
        service._client = mock_client
        response = await service.generate_response("你好")
        
        assert "抱歉" in response


class TestAIServiceWithContext:
    """AI 服務上下文測試"""
    
    @pytest.fixture
    def service(self) -> AIService:
        """建立服務實例"""
        return AIService()
    
    @pytest.mark.asyncio
    async def test_recognize_with_context(self, service: AIService):
        """測試帶上下文的意圖識別"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "command_type": "add_todo",
                "confidence": 0.85,
                "parameters": {"content": "買牛奶"},
            })))
        ]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        context = {
            "previous_messages": [
                {"role": "user", "content": "我要新增待辦"},
                {"role": "assistant", "content": "好的，請告訴我內容"},
            ]
        }
        
        service._client = mock_client
        intent = await service.recognize_intent("買牛奶", context)
        
        # 驗證 API 被正確呼叫
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs.get('messages', call_args.args[0] if call_args.args else [])
        
        # 應該包含上下文訊息
        assert len(messages) >= 3  # system + context + user
