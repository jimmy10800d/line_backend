# Remind 處理器單元測試
# Remind Handler Unit Tests
"""
提醒處理器測試
==============

使用 TDD 方法測試提醒設定功能：
1. 提醒建立
2. 時間解析
3. 提醒列表
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.commands.parser import CommandType, ParsedCommand
from src.commands.handlers.remind import RemindHandler


class TestRemindHandler:
    """提醒處理器測試"""
    
    @pytest.fixture
    def handler(self) -> RemindHandler:
        """建立處理器實例"""
        return RemindHandler()
    
    # =========================================================================
    # 基本功能測試
    # =========================================================================
    
    def test_supported_commands(self, handler: RemindHandler):
        """測試支援的指令類型"""
        assert CommandType.SET_REMINDER in handler.supported_commands
    
    def test_can_handle_reminder(self, handler: RemindHandler):
        """測試能否處理提醒指令"""
        assert handler.can_handle(CommandType.SET_REMINDER)
    
    def test_cannot_handle_other_commands(self, handler: RemindHandler):
        """測試不處理其他指令"""
        assert not handler.can_handle(CommandType.HELP)
    
    # =========================================================================
    # 提醒建立測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_create_reminder_simple(self, handler: RemindHandler):
        """測試建立簡單提醒"""
        command = ParsedCommand(
            command_type=CommandType.SET_REMINDER,
            raw_text="提醒我 開會",
            parameters={"content": "開會"},
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "開會" in result.message
        assert "提醒" in result.message
    
    @pytest.mark.asyncio
    async def test_create_reminder_with_time(self, handler: RemindHandler):
        """測試建立帶時間的提醒"""
        command = ParsedCommand(
            command_type=CommandType.SET_REMINDER,
            raw_text="提醒我 開會 在 下午3點",
            parameters={"content": "開會", "time": "下午3點"},
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "開會" in result.message
        assert "3" in result.message or "15" in result.message
    
    @pytest.mark.asyncio
    async def test_create_reminder_with_relative_time(self, handler: RemindHandler):
        """測試建立帶相對時間的提醒"""
        command = ParsedCommand(
            command_type=CommandType.SET_REMINDER,
            raw_text="提醒我 吃藥 在 30分鐘後",
            parameters={"content": "吃藥", "time": "30分鐘後"},
        )
        
        result = await handler.handle("U123", command)
        
        assert result.success is True
        assert "吃藥" in result.message
    
    # =========================================================================
    # 驗證測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_validate_missing_content(self, handler: RemindHandler):
        """測試缺少提醒內容"""
        command = ParsedCommand(
            command_type=CommandType.SET_REMINDER,
            raw_text="提醒",
            parameters={},
        )
        
        error = await handler.validate(command)
        assert error is not None
        assert "內容" in error or "content" in error.lower()
    
    # =========================================================================
    # 時間解析測試
    # =========================================================================
    
    def test_parse_time_afternoon(self, handler: RemindHandler):
        """測試解析下午時間"""
        result = handler._parse_time("下午3點")
        assert result is not None
        assert result.hour == 15
    
    def test_parse_time_morning(self, handler: RemindHandler):
        """測試解析上午時間"""
        result = handler._parse_time("上午10點")
        assert result is not None
        assert result.hour == 10
    
    def test_parse_time_24hour(self, handler: RemindHandler):
        """測試解析24小時制"""
        result = handler._parse_time("14:30")
        assert result is not None
        assert result.hour == 14
        assert result.minute == 30
    
    def test_parse_time_relative_minutes(self, handler: RemindHandler):
        """測試解析相對分鐘"""
        now = datetime.now()
        result = handler._parse_time("30分鐘後")
        assert result is not None
        # 應該大約是現在時間加30分鐘
        expected = now + timedelta(minutes=30)
        assert abs((result - expected).total_seconds()) < 60
    
    def test_parse_time_relative_hours(self, handler: RemindHandler):
        """測試解析相對小時"""
        now = datetime.now()
        result = handler._parse_time("2小時後")
        assert result is not None
        # 應該大約是現在時間加2小時
        expected = now + timedelta(hours=2)
        assert abs((result - expected).total_seconds()) < 60
    
    def test_parse_time_tomorrow(self, handler: RemindHandler):
        """測試解析明天"""
        result = handler._parse_time("明天")
        assert result is not None
        tomorrow = datetime.now() + timedelta(days=1)
        assert result.date() == tomorrow.date()
    
    def test_parse_time_invalid(self, handler: RemindHandler):
        """測試解析無效時間"""
        result = handler._parse_time("不是時間")
        # 無效時間應該返回 None
        assert result is None
    
    # =========================================================================
    # 格式化測試
    # =========================================================================
    
    def test_format_reminder_message(self, handler: RemindHandler):
        """測試格式化提醒訊息"""
        remind_time = datetime(2024, 1, 15, 14, 30)
        message = handler._format_reminder_message("開會", remind_time)
        
        assert "開會" in message
        assert "14:30" in message or "2:30" in message

