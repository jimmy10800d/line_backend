# 提醒處理器
# Remind Handler
"""
提醒設定處理器
==============

提供提醒設定功能：
- 解析時間表達式
- 建立定時提醒
- 管理提醒列表
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.commands.parser import CommandType, ParsedCommand
from src.commands.handlers.base import BaseHandler, HandlerResult
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class RemindHandler(BaseHandler):
    """
    提醒設定處理器
    
    解析時間表達式並建立定時提醒。
    """
    
    @property
    def supported_commands(self) -> List[CommandType]:
        """支援的指令類型"""
        return [CommandType.SET_REMINDER]
    
    async def validate(self, command: ParsedCommand) -> Optional[str]:
        """
        驗證指令參數
        
        Args:
            command: 已解析的指令
        
        Returns:
            錯誤訊息，如果驗證通過則返回 None
        """
        content = command.parameters.get("content", "").strip()
        
        if not content:
            return "請提供要提醒的內容。例如：提醒我 開會 在 下午3點"
        
        return None
    
    async def handle(
        self,
        user_id: str,
        command: ParsedCommand,
    ) -> HandlerResult:
        """
        處理提醒設定指令
        
        Args:
            user_id: 用戶 ID
            command: 已解析的指令
        
        Returns:
            HandlerResult: 處理結果
        """
        content = command.parameters.get("content", "").strip()
        time_str = command.parameters.get("time")
        
        logger.info(
            "Setting reminder",
            extra={"user_id": user_id, "content": content, "time": time_str},
        )
        
        try:
            # 解析時間
            remind_time = None
            if time_str:
                remind_time = self._parse_time(time_str)
            
            # 如果沒有指定時間，設為1小時後
            if remind_time is None:
                remind_time = datetime.now() + timedelta(hours=1)
            
            # TODO: 實際儲存提醒到資料庫並設定排程
            # 目前只返回確認訊息
            
            # 格式化回覆
            message = self._format_reminder_message(content, remind_time)
            
            return HandlerResult.success_result(
                message=message,
                data={
                    "content": content,
                    "remind_time": remind_time.isoformat(),
                    "user_id": user_id,
                },
                quick_replies=["我的提醒", "取消提醒"],
            )
            
        except Exception as e:
            logger.error(
                "Reminder creation error",
                extra={"user_id": user_id, "error": str(e)},
            )
            
            return HandlerResult.error_result(
                message="建立提醒時發生錯誤，請稍後再試。",
                error_code="REMINDER_ERROR",
            )
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """
        解析時間表達式
        
        支援格式：
        - 上午/下午 X 點
        - HH:MM（24小時制）
        - X分鐘後
        - X小時後
        - 明天
        
        Args:
            time_str: 時間字串
        
        Returns:
            解析後的 datetime，如果解析失敗則返回 None
        """
        now = datetime.now()
        time_str = time_str.strip()
        
        # 相對時間：X分鐘後
        match = re.search(r"(\d+)\s*分鐘後", time_str)
        if match:
            minutes = int(match.group(1))
            return now + timedelta(minutes=minutes)
        
        # 相對時間：X小時後
        match = re.search(r"(\d+)\s*小時後", time_str)
        if match:
            hours = int(match.group(1))
            return now + timedelta(hours=hours)
        
        # 明天
        if "明天" in time_str:
            tomorrow = now + timedelta(days=1)
            # 如果有時間，解析時間部分
            time_part = time_str.replace("明天", "").strip()
            if time_part:
                time_only = self._parse_time_only(time_part)
                if time_only:
                    return tomorrow.replace(
                        hour=time_only.hour,
                        minute=time_only.minute,
                        second=0,
                        microsecond=0,
                    )
            # 預設明天早上9點
            return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # 24小時制：HH:MM
        match = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            # 如果時間已過，設為明天
            if result <= now:
                result += timedelta(days=1)
            return result
        
        # 上午/下午 X 點
        time_only = self._parse_time_only(time_str)
        if time_only:
            result = now.replace(
                hour=time_only.hour,
                minute=time_only.minute,
                second=0,
                microsecond=0,
            )
            # 如果時間已過，設為明天
            if result <= now:
                result += timedelta(days=1)
            return result
        
        return None
    
    def _parse_time_only(self, time_str: str) -> Optional[datetime]:
        """
        解析時間（只有時分）
        
        Args:
            time_str: 時間字串
        
        Returns:
            包含時間資訊的 datetime（日期無意義）
        """
        now = datetime.now()
        
        # 下午 X 點
        match = re.search(r"下午\s*(\d{1,2})\s*(?:點|:)?(?:(\d{1,2}))?", time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            if hour < 12:
                hour += 12
            return now.replace(hour=hour, minute=minute)
        
        # 上午 X 點
        match = re.search(r"上午\s*(\d{1,2})\s*(?:點|:)?(?:(\d{1,2}))?", time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            if hour == 12:
                hour = 0
            return now.replace(hour=hour, minute=minute)
        
        # 只有數字 X 點
        match = re.search(r"(\d{1,2})\s*點(?:(\d{1,2}))?", time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            return now.replace(hour=hour, minute=minute)
        
        return None
    
    def _format_reminder_message(
        self,
        content: str,
        remind_time: datetime,
    ) -> str:
        """
        格式化提醒確認訊息
        
        Args:
            content: 提醒內容
            remind_time: 提醒時間
        
        Returns:
            格式化的訊息
        """
        time_str = remind_time.strftime("%Y/%m/%d %H:%M")
        
        message = f"""
⏰ 提醒已設定

📝 內容：{content}
🕐 時間：{time_str}

到時間時會發送提醒給您！
        """.strip()
        
        return message


# =============================================================================
# 處理器註冊
# =============================================================================

def get_remind_handler() -> RemindHandler:
    """取得提醒處理器實例"""
    return RemindHandler()

