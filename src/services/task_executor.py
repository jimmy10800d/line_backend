# 任務執行器
# Task Executor
"""
任務執行器
==========

統一的任務執行管理：
- 指令路由到處理器
- 執行日誌記錄
- 非同步任務處理
- 錯誤恢復
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.commands.parser import CommandType, ParsedCommand, get_parser
from src.commands.queue import get_queue
from src.commands.handlers.base import get_handler, HandlerResult
from src.services.ai_service import get_ai_service
from src.services.line_service import get_line_service
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class TaskExecutor:
    """
    任務執行器
    
    協調指令解析、處理器調用和結果回覆的核心組件。
    """
    
    # 長時間任務閾值（秒）
    LONG_TASK_THRESHOLD = 5.0
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        初始化任務執行器
        
        Args:
            db_session: 可選的資料庫 Session
        """
        self._db_session = db_session
        self._parser = get_parser()
        self._queue = get_queue()
        self._ai_service = get_ai_service()
        self._line_service = get_line_service()
    
    async def execute_message(
        self,
        user_id: str,
        text: str,
        reply_token: Optional[str] = None,
    ) -> HandlerResult:
        """
        執行用戶訊息
        
        完整的訊息處理流程：
        1. 解析指令
        2. 如果需要，使用 AI 解析
        3. 路由到處理器
        4. 記錄執行日誌
        5. 發送回覆
        
        Args:
            user_id: 用戶 LINE ID
            text: 訊息文字
            reply_token: LINE 回覆 token
        
        Returns:
            HandlerResult: 執行結果
        """
        start_time = datetime.utcnow()
        
        logger.info(
            "Executing message",
            extra={"user_id": user_id, "text": text[:100]},
        )
        
        try:
            # Step 1: 解析指令
            command = self._parser.parse(text)
            
            # Step 2: 如果需要 AI 解析
            if command.needs_ai:
                logger.debug("Using AI to parse command")
                command = await self._ai_service.parse_with_ai(text)
            
            # Step 3: 路由到處理器
            result = await self._route_and_execute(user_id, command)
            
            # Step 4: 記錄執行日誌
            await self._log_execution(
                user_id=user_id,
                command=command,
                result=result,
                start_time=start_time,
            )
            
            # Step 5: 發送回覆
            if reply_token and result.message:
                await self._send_reply(reply_token, result)
            
            return result
            
        except Exception as e:
            logger.error(
                "Task execution error",
                extra={"user_id": user_id, "error": str(e)},
            )
            
            error_result = HandlerResult.error_result(
                message="抱歉，處理您的請求時發生錯誤。請稍後再試。",
                error_code="EXECUTION_ERROR",
            )
            
            if reply_token:
                await self._send_reply(reply_token, error_result)
            
            return error_result
    
    async def execute_command(
        self,
        user_id: str,
        command: ParsedCommand,
    ) -> HandlerResult:
        """
        執行已解析的指令
        
        Args:
            user_id: 用戶 LINE ID
            command: 已解析的指令
        
        Returns:
            HandlerResult: 執行結果
        """
        return await self._route_and_execute(user_id, command)
    
    async def _route_and_execute(
        self,
        user_id: str,
        command: ParsedCommand,
    ) -> HandlerResult:
        """
        路由並執行指令
        
        Args:
            user_id: 用戶 LINE ID
            command: 已解析的指令
        
        Returns:
            HandlerResult: 執行結果
        """
        # 檢查指令有效性
        if not command.is_valid():
            logger.debug(f"Invalid command: {command.error}")
            return HandlerResult.error_result(
                message=self._get_error_message(command),
                error_code="INVALID_COMMAND",
            )
        
        # 取得處理器
        handler = get_handler(command.command_type)
        
        if not handler:
            logger.warning(f"No handler for command type: {command.command_type}")
            return await self._handle_unknown_command(user_id, command)
        
        # 驗證指令參數
        validation_error = await handler.validate(command)
        if validation_error:
            return HandlerResult.error_result(
                message=validation_error,
                error_code="VALIDATION_ERROR",
            )
        
        # 執行處理器
        return await handler.handle(user_id, command)
    
    async def _handle_unknown_command(
        self,
        user_id: str,
        command: ParsedCommand,
    ) -> HandlerResult:
        """
        處理未知指令
        
        Args:
            user_id: 用戶 LINE ID
            command: 已解析的指令
        
        Returns:
            HandlerResult: 處理結果
        """
        # 嘗試使用 AI 生成回應
        if command.confidence < 0.3:
            response = await self._ai_service.generate_response(
                command.raw_text,
                system_context="""你是一個友善的助手。
                用戶發送了一條無法識別的訊息。
                請友善地引導用戶使用正確的指令格式，
                並建議他們輸入「幫助」來查看可用指令。
                回覆要簡短、親切。"""
            )
            
            return HandlerResult.success_result(
                message=response,
                quick_replies=["幫助", "狀態", "我的流程"],
            )
        
        # 如果有一定信心度但沒有處理器
        return HandlerResult.error_result(
            message="抱歉，這個功能尚未開放。請輸入「幫助」查看可用指令。",
            error_code="NOT_IMPLEMENTED",
        )
    
    def _get_error_message(self, command: ParsedCommand) -> str:
        """
        取得錯誤訊息
        
        Args:
            command: 失敗的指令
        
        Returns:
            str: 錯誤訊息
        """
        if command.error == "空白訊息":
            return ""  # 不回覆空白訊息
        
        return f"無法理解您的訊息。{command.error or '請嘗試重新描述或輸入「幫助」查看可用指令。'}"
    
    async def _send_reply(
        self,
        reply_token: str,
        result: HandlerResult,
    ) -> None:
        """
        發送 LINE 回覆
        
        Args:
            reply_token: LINE 回覆 token
            result: 處理結果
        """
        if not result.message:
            return
        
        try:
            messages = [{"type": "text", "text": result.message}]
            
            # 如果有快速回覆選項，添加到訊息中
            if result.quick_replies:
                messages[0]["quickReply"] = {
                    "items": [
                        {
                            "type": "action",
                            "action": {
                                "type": "message",
                                "label": reply[:20],  # 標籤最多 20 字元
                                "text": reply,
                            }
                        }
                        for reply in result.quick_replies[:13]  # 最多 13 個
                    ]
                }
            
            await self._line_service.reply_message(reply_token, messages)
            
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
    
    async def _log_execution(
        self,
        user_id: str,
        command: ParsedCommand,
        result: HandlerResult,
        start_time: datetime,
    ) -> None:
        """
        記錄執行日誌
        
        Args:
            user_id: 用戶 ID
            command: 執行的指令
            result: 執行結果
            start_time: 開始時間
        """
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(
            "Task execution completed",
            extra={
                "user_id": user_id,
                "command_type": command.command_type.value,
                "success": result.success,
                "duration_seconds": duration,
            },
        )
        
        # TODO: 寫入資料庫執行日誌（T032）
        # if self._db_session:
        #     from src.models.execution_log import ExecutionLog
        #     log = ExecutionLog(...)
        #     self._db_session.add(log)
        #     await self._db_session.commit()


class AsyncTaskExecutor(TaskExecutor):
    """
    非同步任務執行器
    
    支援長時間任務的處理，會先回覆「處理中」訊息。
    """
    
    async def execute_message_async(
        self,
        user_id: str,
        text: str,
        reply_token: str,
    ) -> None:
        """
        非同步執行訊息
        
        如果任務預計耗時較長，會先回覆「處理中」訊息，
        然後在背景完成任務後再推送結果。
        
        Args:
            user_id: 用戶 LINE ID
            text: 訊息文字
            reply_token: LINE 回覆 token
        """
        # 先發送處理中訊息
        await self._line_service.reply_message(
            reply_token,
            [{"type": "text", "text": "⏳ 處理中，請稍候..."}],
        )
        
        # 執行實際任務
        result = await self.execute_message(user_id, text)
        
        # 推送結果
        if result.message:
            messages = [{"type": "text", "text": result.message}]
            await self._line_service.push_message(user_id, messages)


# 單例模式
_executor: Optional[TaskExecutor] = None


def get_task_executor(db_session: Optional[AsyncSession] = None) -> TaskExecutor:
    """取得任務執行器單例"""
    global _executor
    if _executor is None or db_session is not None:
        _executor = TaskExecutor(db_session)
    return _executor
