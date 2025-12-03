# 基礎指令處理器
# Base Command Handler
"""
基礎指令處理器
==============

定義指令處理器的介面和共用功能：
- 處理結果資料結構
- 抽象處理器基礎類別
- 共用工具方法
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.commands.parser import ParsedCommand, CommandType
from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class CommandContext:
    """指令上下文"""
    
    user_id: str
    """用戶 LINE ID"""
    
    raw_text: str
    """原始訊息文字"""
    
    reply_token: Optional[str] = None
    """LINE 回覆 Token"""
    
    command_type: CommandType = CommandType.UNKNOWN
    """指令類型"""
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    """指令參數"""


@dataclass
class HandlerResult:
    """指令處理結果"""
    
    success: bool
    """是否成功"""
    
    message: str
    """回應訊息（將發送給用戶）"""
    
    data: Optional[Dict[str, Any]] = None
    """附加資料"""
    
    quick_replies: Optional[List[str]] = None
    """快速回覆選項"""
    
    error_code: Optional[str] = None
    """錯誤代碼（如果失敗）"""
    
    @classmethod
    def success_result(
        cls,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        quick_replies: Optional[List[str]] = None
    ) -> "HandlerResult":
        """建立成功結果"""
        return cls(
            success=True,
            message=message,
            data=data,
            quick_replies=quick_replies,
        )
    
    @classmethod
    def error_result(
        cls,
        message: str,
        error_code: Optional[str] = None
    ) -> "HandlerResult":
        """建立錯誤結果"""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
        )


class BaseHandler(ABC):
    """
    指令處理器抽象基礎類別
    
    所有具體指令處理器都應該繼承此類別並實作 handle 方法。
    """
    
    # 此處理器支援的指令類型
    supported_commands: List[CommandType] = []
    
    @abstractmethod
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> HandlerResult:
        """
        處理指令
        
        Args:
            user_id: 用戶 LINE ID
            command: 解析後的指令
        
        Returns:
            HandlerResult: 處理結果
        """
        pass
    
    def can_handle(self, command_type: CommandType) -> bool:
        """
        檢查是否可以處理此指令類型
        
        Args:
            command_type: 指令類型
        
        Returns:
            是否可以處理
        """
        return command_type in self.supported_commands
    
    async def validate(self, command: ParsedCommand) -> Optional[str]:
        """
        驗證指令參數
        
        Args:
            command: 解析後的指令
        
        Returns:
            錯誤訊息（如果驗證失敗）或 None
        """
        return None  # 預設不驗證
    
    def format_success_message(self, template: str, **kwargs) -> str:
        """
        格式化成功訊息
        
        Args:
            template: 訊息模板
            **kwargs: 替換參數
        
        Returns:
            格式化後的訊息
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Message template error: {e}")
            return template


class HelpHandler(BaseHandler):
    """幫助指令處理器"""
    
    supported_commands = [CommandType.HELP]
    
    HELP_MESSAGE = """
📖 **使用說明**

🔹 **預設任務**
• `待辦 [內容]` - 新增待辦事項
• `筆記 [內容]` - 新增筆記
• `花費 [金額] [說明]` - 記錄支出
• `提醒 [內容] 在 [時間]` - 設定提醒

🔹 **工作流程**
• `建立流程 [名稱]` - 建立新流程
• `執行流程 [名稱]` - 執行流程
• `我的流程` - 列出所有流程

🔹 **外部服務**
• `連接 google` - 連接 Google 日曆
• `連接 notion` - 連接 Notion
• `我的服務` - 列出已連接服務

🔹 **其他**
• `狀態` - 查看系統狀態
• `歷史` - 查看執行歷史
• `幫助` - 顯示此說明

💡 也可以使用自然語言，我會嘗試理解您的意思！
    """.strip()
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> HandlerResult:
        """處理幫助指令"""
        return HandlerResult.success_result(
            message=self.HELP_MESSAGE,
            quick_replies=["待辦", "筆記", "我的流程", "狀態"],
        )


class StatusHandler(BaseHandler):
    """狀態指令處理器"""
    
    supported_commands = [CommandType.STATUS]
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> HandlerResult:
        """處理狀態指令"""
        # TODO: 從資料庫取得實際統計資料
        message = """
📊 **系統狀態**

✅ 系統運作正常

📝 您的統計：
• 待辦事項：0 項
• 工作流程：0 個
• 已連接服務：0 個

🕐 最後執行：尚無紀錄
        """.strip()
        
        return HandlerResult.success_result(
            message=message,
            quick_replies=["幫助", "歷史", "我的流程"],
        )


class HistoryHandler(BaseHandler):
    """歷史指令處理器"""
    
    supported_commands = [CommandType.HISTORY]
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> HandlerResult:
        """處理歷史指令"""
        # TODO: 從資料庫取得執行歷史
        message = """
📜 **執行歷史**

尚無執行紀錄。

開始使用指令來建立您的第一筆紀錄！
輸入「幫助」查看可用指令。
        """.strip()
        
        return HandlerResult.success_result(
            message=message,
            quick_replies=["幫助", "待辦 測試", "狀態"],
        )


# 處理器註冊表
_handlers: Dict[CommandType, BaseHandler] = {}


def register_handler(handler: BaseHandler) -> None:
    """註冊指令處理器"""
    for cmd_type in handler.supported_commands:
        _handlers[cmd_type] = handler
        logger.debug(f"Registered handler for {cmd_type.value}")


def get_handler(command_type: CommandType) -> Optional[BaseHandler]:
    """取得指令處理器"""
    return _handlers.get(command_type)


# 註冊內建處理器
register_handler(HelpHandler())
register_handler(StatusHandler())
register_handler(HistoryHandler())
