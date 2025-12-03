# 指令處理器單元測試
# Command Handlers Unit Tests
"""
指令處理器測試
==============

使用 TDD 方法測試指令處理器功能：
1. 幫助處理器
2. 狀態處理器
3. 歷史處理器
4. 處理器結果格式
"""

import pytest
from src.commands.parser import CommandType, ParsedCommand
from src.commands.handlers.base import (
    BaseHandler,
    HandlerResult,
    HelpHandler,
    StatusHandler,
    HistoryHandler,
    get_handler,
    register_handler,
)


class TestHandlerResult:
    """處理器結果測試"""
    
    def test_success_result(self):
        """測試建立成功結果"""
        result = HandlerResult.success_result(
            message="操作成功",
            data={"key": "value"},
            quick_replies=["選項1", "選項2"],
        )
        
        assert result.success is True
        assert result.message == "操作成功"
        assert result.data == {"key": "value"}
        assert result.quick_replies == ["選項1", "選項2"]
        assert result.error_code is None
    
    def test_error_result(self):
        """測試建立錯誤結果"""
        result = HandlerResult.error_result(
            message="操作失敗",
            error_code="ERR_001",
        )
        
        assert result.success is False
        assert result.message == "操作失敗"
        assert result.error_code == "ERR_001"
        assert result.data is None


class TestHelpHandler:
    """幫助處理器測試"""
    
    @pytest.fixture
    def handler(self) -> HelpHandler:
        """建立處理器實例"""
        return HelpHandler()
    
    def test_supported_commands(self, handler: HelpHandler):
        """測試支援的指令類型"""
        assert CommandType.HELP in handler.supported_commands
    
    def test_can_handle_help(self, handler: HelpHandler):
        """測試可以處理幫助指令"""
        assert handler.can_handle(CommandType.HELP) is True
        assert handler.can_handle(CommandType.STATUS) is False
    
    @pytest.mark.asyncio
    async def test_handle_help_command(self, handler: HelpHandler):
        """測試處理幫助指令"""
        command = ParsedCommand(
            command_type=CommandType.HELP,
            raw_text="幫助",
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "使用說明" in result.message
        assert "待辦" in result.message
        assert "筆記" in result.message
        assert "流程" in result.message
        assert result.quick_replies is not None
        assert len(result.quick_replies) > 0


class TestStatusHandler:
    """狀態處理器測試"""
    
    @pytest.fixture
    def handler(self) -> StatusHandler:
        """建立處理器實例"""
        return StatusHandler()
    
    def test_supported_commands(self, handler: StatusHandler):
        """測試支援的指令類型"""
        assert CommandType.STATUS in handler.supported_commands
    
    @pytest.mark.asyncio
    async def test_handle_status_command(self, handler: StatusHandler):
        """測試處理狀態指令"""
        command = ParsedCommand(
            command_type=CommandType.STATUS,
            raw_text="狀態",
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "系統狀態" in result.message
        assert "運作正常" in result.message
        assert result.quick_replies is not None


class TestHistoryHandler:
    """歷史處理器測試"""
    
    @pytest.fixture
    def handler(self) -> HistoryHandler:
        """建立處理器實例"""
        return HistoryHandler()
    
    def test_supported_commands(self, handler: HistoryHandler):
        """測試支援的指令類型"""
        assert CommandType.HISTORY in handler.supported_commands
    
    @pytest.mark.asyncio
    async def test_handle_history_command(self, handler: HistoryHandler):
        """測試處理歷史指令"""
        command = ParsedCommand(
            command_type=CommandType.HISTORY,
            raw_text="歷史",
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "執行歷史" in result.message
        assert result.quick_replies is not None


class TestHandlerRegistry:
    """處理器註冊表測試"""
    
    def test_get_registered_handler(self):
        """測試取得已註冊的處理器"""
        handler = get_handler(CommandType.HELP)
        assert handler is not None
        assert isinstance(handler, HelpHandler)
    
    def test_get_unregistered_handler(self):
        """測試取得未註冊的處理器"""
        # CREATE_WORKFLOW 目前沒有註冊處理器
        handler = get_handler(CommandType.CREATE_WORKFLOW)
        assert handler is None
    
    def test_register_custom_handler(self):
        """測試註冊自訂處理器"""
        class CustomHandler(BaseHandler):
            supported_commands = [CommandType.ADD_TODO]
            
            async def handle(self, user_id, command):
                return HandlerResult.success_result("自訂處理")
        
        custom = CustomHandler()
        register_handler(custom)
        
        handler = get_handler(CommandType.ADD_TODO)
        assert handler is custom


class TestBaseHandler:
    """基礎處理器測試"""
    
    def test_format_success_message(self):
        """測試格式化成功訊息"""
        handler = HelpHandler()
        message = handler.format_success_message(
            "Hello {name}!",
            name="World",
        )
        assert message == "Hello World!"
    
    def test_format_success_message_missing_key(self):
        """測試格式化訊息缺少參數"""
        handler = HelpHandler()
        message = handler.format_success_message(
            "Hello {name}!",
            # 缺少 name 參數
        )
        # 應該返回原始模板而不是拋出例外
        assert message == "Hello {name}!"
    
    @pytest.mark.asyncio
    async def test_validate_default(self):
        """測試預設驗證（不驗證）"""
        handler = HelpHandler()
        command = ParsedCommand(
            command_type=CommandType.HELP,
            raw_text="help",
        )
        
        error = await handler.validate(command)
        assert error is None
