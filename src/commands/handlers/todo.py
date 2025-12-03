# LINE 自動化流程引擎 - 待辦/筆記/支出處理器
# LINE Workflow Automation Engine - Todo/Note/Expense Handlers
"""
待辦/筆記/支出處理器
====================

處理用戶的快速記錄指令：
- add_todo: 新增待辦事項
- add_note: 新增筆記
- add_expense: 記錄支出
"""

from typing import Optional

from src.commands.parser import ParsedCommand, CommandType
from src.commands.handlers.base import BaseHandler, HandlerResult, register_handler
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class TodoHandler(BaseHandler):
    """待辦事項處理器"""
    
    supported_commands = [CommandType.ADD_TODO]
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> HandlerResult:
        """處理新增待辦指令"""
        content = command.parameters.get("content", "")
        
        if not content:
            return HandlerResult.error_result(
                message="請提供待辦事項內容\n例如：待辦 買牛奶",
                error_code="MISSING_CONTENT"
            )
        
        # TODO: 儲存到資料庫
        logger.info(f"新增待辦事項: {content}", extra={"user_id": user_id})
        
        return HandlerResult.success_result(
            message=f"✅ 已新增待辦事項\n\n📝 {content}",
            data={"content": content, "type": "todo"},
            quick_replies=["待辦", "我的待辦", "幫助"],
        )
    
    async def validate(self, command: ParsedCommand) -> Optional[str]:
        """驗證指令參數"""
        content = command.parameters.get("content", "")
        if len(content) > 500:
            return "待辦事項內容過長（最多 500 字）"
        return None


class NoteHandler(BaseHandler):
    """筆記處理器"""
    
    supported_commands = [CommandType.ADD_NOTE]
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> HandlerResult:
        """處理新增筆記指令"""
        content = command.parameters.get("content", "")
        
        if not content:
            return HandlerResult.error_result(
                message="請提供筆記內容\n例如：筆記 今天天氣很好",
                error_code="MISSING_CONTENT"
            )
        
        # TODO: 儲存到資料庫
        logger.info(f"新增筆記: {content}", extra={"user_id": user_id})
        
        return HandlerResult.success_result(
            message=f"📝 已記錄筆記\n\n{content}",
            data={"content": content, "type": "note"},
            quick_replies=["筆記", "我的筆記", "幫助"],
        )
    
    async def validate(self, command: ParsedCommand) -> Optional[str]:
        """驗證指令參數"""
        content = command.parameters.get("content", "")
        if len(content) > 2000:
            return "筆記內容過長（最多 2000 字）"
        return None


class ExpenseHandler(BaseHandler):
    """支出處理器"""
    
    supported_commands = [CommandType.ADD_EXPENSE]
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> HandlerResult:
        """處理記錄支出指令"""
        amount = command.parameters.get("amount", 0)
        description = command.parameters.get("description", "")
        
        if not amount or amount <= 0:
            return HandlerResult.error_result(
                message="請提供有效的金額\n例如：花費 150 午餐",
                error_code="INVALID_AMOUNT"
            )
        
        # TODO: 儲存到資料庫
        logger.info(f"記錄支出: ${amount} {description}", extra={"user_id": user_id})
        
        desc_text = f" - {description}" if description else ""
        return HandlerResult.success_result(
            message=f"💰 已記錄支出\n\n$ {amount}{desc_text}",
            data={"amount": amount, "description": description, "type": "expense"},
            quick_replies=["花費", "本月支出", "幫助"],
        )
    
    async def validate(self, command: ParsedCommand) -> Optional[str]:
        """驗證指令參數"""
        amount = command.parameters.get("amount", 0)
        if amount > 10000000:
            return "金額過大（最多 1000 萬）"
        return None


# 註冊處理器
register_handler(TodoHandler())
register_handler(NoteHandler())
register_handler(ExpenseHandler())
