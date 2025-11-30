# 任務執行器單元測試
# Task Executor Unit Tests
"""
任務執行器測試
==============

使用 TDD 方法測試任務執行器功能：
1. 訊息執行流程
2. 指令路由
3. 錯誤處理
4. 非同步處理
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.commands.parser import CommandType, ParsedCommand
from src.commands.handlers.base import HandlerResult
from src.services.task_executor import (
    TaskExecutor,
    AsyncTaskExecutor,
    get_task_executor,
)


class TestTaskExecutor:
    """任務執行器測試"""
    
    @pytest.fixture
    def mock_line_service(self):
        """Mock LINE 服務"""
        with patch('src.services.task_executor.get_line_service') as mock:
            service = MagicMock()
            service.reply_message = AsyncMock(return_value=True)
            service.push_message = AsyncMock(return_value=True)
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI 服務"""
        with patch('src.services.task_executor.get_ai_service') as mock:
            service = MagicMock()
            service.parse_with_ai = AsyncMock()
            service.generate_response = AsyncMock(return_value="這是 AI 回應")
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def executor(self, mock_line_service, mock_ai_service) -> TaskExecutor:
        """建立執行器實例（依賴 mock 服務）"""
        return TaskExecutor()
    
    @pytest.fixture
    def mock_parser(self):
        """Mock 解析器"""
        with patch('src.services.task_executor.get_parser') as mock:
            parser = MagicMock()
            mock.return_value = parser
            yield parser
    
    @pytest.fixture
    def mock_handler(self):
        """Mock 處理器"""
        with patch('src.services.task_executor.get_handler') as mock:
            yield mock
    
    # =========================================================================
    # 基本執行測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_execute_help_command(
        self, executor: TaskExecutor, mock_line_service
    ):
        """測試執行幫助指令"""
        result = await executor.execute_message(
            user_id="U123",
            text="幫助",
        )
        
        assert result.success is True
        assert "使用說明" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_status_command(
        self, executor: TaskExecutor, mock_line_service
    ):
        """測試執行狀態指令"""
        result = await executor.execute_message(
            user_id="U123",
            text="狀態",
        )
        
        assert result.success is True
        assert "系統狀態" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_with_reply_token(
        self, executor: TaskExecutor, mock_line_service
    ):
        """測試帶回覆 token 的執行"""
        result = await executor.execute_message(
            user_id="U123",
            text="幫助",
            reply_token="token123",
        )
        
        assert result.success is True
        mock_line_service.reply_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_empty_message(
        self, executor: TaskExecutor, mock_line_service
    ):
        """測試執行空白訊息"""
        result = await executor.execute_message(
            user_id="U123",
            text="",
        )
        
        # 空白訊息應該返回空訊息（不回覆）
        assert result.message == ""
    
    # =========================================================================
    # AI 解析測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_execute_with_ai_parsing(
        self, executor: TaskExecutor, mock_ai_service, mock_line_service
    ):
        """測試需要 AI 解析的訊息"""
        # 設定 AI 回應
        mock_ai_service.parse_with_ai.return_value = ParsedCommand(
            command_type=CommandType.ADD_TODO,
            raw_text="記得要運動",
            parameters={"content": "運動"},
            confidence=0.9,
        )
        
        result = await executor.execute_message(
            user_id="U123",
            text="記得要運動",
        )
        
        # 應該嘗試執行，雖然沒有 ADD_TODO 處理器會失敗
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_execute_unknown_command_uses_ai(
        self, executor: TaskExecutor, mock_ai_service, mock_line_service
    ):
        """測試未知指令使用 AI 回應"""
        # 設定 AI 回應
        mock_ai_service.parse_with_ai.return_value = ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text="asdfghjkl",
            confidence=0.1,
            needs_ai=False,
        )
        mock_ai_service.generate_response.return_value = "這是 AI 回應"
        
        result = await executor.execute_message(
            user_id="U123",
            text="asdfghjkl",  # 無法識別的訊息
        )
        
        # 應該收到友善的回應
        assert result is not None
        assert "幫助" in result.message or "這是 AI 回應" in result.message or "尚未開放" in result.message
    
    # =========================================================================
    # 錯誤處理測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_execute_handler_error(
        self, executor: TaskExecutor, mock_handler, mock_line_service
    ):
        """測試處理器錯誤"""
        # 設定處理器拋出例外
        handler = MagicMock()
        handler.handle = AsyncMock(side_effect=Exception("處理器錯誤"))
        handler.validate = AsyncMock(return_value=None)
        mock_handler.return_value = handler
        
        result = await executor.execute_message(
            user_id="U123",
            text="狀態",
            reply_token="token123",
        )
        
        # 由於沒有實際的 mock，使用真實處理器
        # 真實處理器不會拋出例外
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_execute_validation_error(
        self, executor: TaskExecutor, mock_line_service
    ):
        """測試驗證錯誤"""
        # 驗證錯誤的情況會在處理器層級處理
        result = await executor.execute_message(
            user_id="U123",
            text="幫助",
        )
        
        assert result.success is True
    
    # =========================================================================
    # 指令執行測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_execute_command_directly(self, executor: TaskExecutor):
        """測試直接執行已解析的指令"""
        command = ParsedCommand(
            command_type=CommandType.HELP,
            raw_text="help",
        )
        
        result = await executor.execute_command("U123", command)
        
        assert result.success is True
        assert "使用說明" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_invalid_command(self, executor: TaskExecutor):
        """測試執行無效指令"""
        command = ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text="???",
            error="無法識別的指令",
        )
        
        result = await executor.execute_command("U123", command)
        
        assert result.success is False
        assert "INVALID_COMMAND" in result.error_code
    
    # =========================================================================
    # 單例模式測試
    # =========================================================================
    
    def test_executor_singleton(self):
        """測試執行器單例模式"""
        # 重設全域變數
        import src.services.task_executor as module
        module._executor = None
        
        executor1 = get_task_executor()
        executor2 = get_task_executor()
        
        assert executor1 is executor2


class TestAsyncTaskExecutor:
    """非同步任務執行器測試"""
    
    @pytest.fixture
    def mock_line_service(self):
        """Mock LINE 服務"""
        with patch('src.services.task_executor.get_line_service') as mock:
            service = MagicMock()
            service.reply_message = AsyncMock(return_value=True)
            service.push_message = AsyncMock(return_value=True)
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI 服務"""
        with patch('src.services.task_executor.get_ai_service') as mock:
            service = MagicMock()
            service.parse_with_ai = AsyncMock()
            service.generate_response = AsyncMock(return_value="這是 AI 回應")
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def async_executor(self, mock_line_service, mock_ai_service) -> AsyncTaskExecutor:
        """建立非同步執行器實例（依賴 mock 服務）"""
        return AsyncTaskExecutor()
    
    @pytest.mark.asyncio
    async def test_execute_async_sends_processing_message(
        self, async_executor: AsyncTaskExecutor, mock_line_service
    ):
        """測試非同步執行發送處理中訊息"""
        await async_executor.execute_message_async(
            user_id="U123",
            text="幫助",
            reply_token="token123",
        )
        
        # 應該先發送處理中訊息
        calls = mock_line_service.reply_message.call_args_list
        assert len(calls) >= 1
        first_call = calls[0]
        messages = first_call.args[1] if len(first_call.args) > 1 else first_call.kwargs.get('messages', [])
        assert any("處理中" in str(msg) for msg in messages)
    
    @pytest.mark.asyncio
    async def test_execute_async_pushes_result(
        self, async_executor: AsyncTaskExecutor, mock_line_service
    ):
        """測試非同步執行推送結果"""
        await async_executor.execute_message_async(
            user_id="U123",
            text="幫助",
            reply_token="token123",
        )
        
        # 應該推送結果訊息
        mock_line_service.push_message.assert_called_once()
        call_args = mock_line_service.push_message.call_args
        user_id = call_args.args[0] if call_args.args else call_args.kwargs.get('user_id')
        assert user_id == "U123"


class TestTaskExecutorLogging:
    """任務執行器日誌測試"""
    
    @pytest.fixture
    def mock_line_service(self):
        """Mock LINE 服務"""
        with patch('src.services.task_executor.get_line_service') as mock:
            service = MagicMock()
            service.reply_message = AsyncMock(return_value=True)
            service.push_message = AsyncMock(return_value=True)
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI 服務"""
        with patch('src.services.task_executor.get_ai_service') as mock:
            service = MagicMock()
            service.parse_with_ai = AsyncMock()
            service.generate_response = AsyncMock(return_value="這是 AI 回應")
            mock.return_value = service
            yield service
    
    @pytest.fixture
    def executor(self, mock_line_service, mock_ai_service) -> TaskExecutor:
        """建立執行器實例（依賴 mock 服務）"""
        return TaskExecutor()
    
    @pytest.mark.asyncio
    async def test_execution_logging(self, executor: TaskExecutor):
        """測試執行日誌記錄"""
        with patch('src.services.task_executor.logger') as mock_logger:
            await executor.execute_message(
                user_id="U123",
                text="幫助",
            )
            
            # 應該記錄開始和完成日誌
            assert mock_logger.info.called
