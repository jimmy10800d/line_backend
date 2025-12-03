# 指令佇列服務
# Command Queue Service
"""
指令佇列服務
============

處理指令執行的佇列管理：
- 防止重複執行（Deduplication）
- 執行順序保證（FIFO）
- 失敗重試機制
- Edge Case 處理（空白、無效指令）
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from collections import OrderedDict

from src.commands.parser import ParsedCommand, CommandType
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class QueueStatus(Enum):
    """佇列項目狀態"""
    PENDING = "pending"       # 等待執行
    PROCESSING = "processing" # 執行中
    COMPLETED = "completed"   # 執行完成
    FAILED = "failed"         # 執行失敗
    SKIPPED = "skipped"       # 跳過（重複）


@dataclass
class QueueItem:
    """佇列項目"""
    
    id: str
    """唯一識別碼"""
    
    user_id: str
    """用戶 LINE ID"""
    
    command: ParsedCommand
    """解析後的指令"""
    
    status: QueueStatus = QueueStatus.PENDING
    """狀態"""
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    """建立時間"""
    
    processed_at: Optional[datetime] = None
    """處理時間"""
    
    retry_count: int = 0
    """重試次數"""
    
    max_retries: int = 3
    """最大重試次數"""
    
    result: Optional[Any] = None
    """執行結果"""
    
    error: Optional[str] = None
    """錯誤訊息"""
    
    def can_retry(self) -> bool:
        """檢查是否可以重試"""
        return self.retry_count < self.max_retries


class CommandQueue:
    """
    指令佇列
    
    使用記憶體佇列管理指令執行，支援：
    - 去重複（同一用戶在短時間內的重複指令）
    - 優先順序（FIFO）
    - 並發限制
    """
    
    # 去重複時間窗口（秒）
    DEDUP_WINDOW_SECONDS = 5
    
    # 最大佇列長度
    MAX_QUEUE_SIZE = 1000
    
    # 每用戶最大並發數
    MAX_CONCURRENT_PER_USER = 3
    
    def __init__(self):
        """初始化佇列"""
        self._queue: OrderedDict[str, QueueItem] = OrderedDict()
        self._recent_hashes: Dict[str, datetime] = {}  # 用於去重複
        self._user_processing: Dict[str, int] = {}  # 用戶並發計數
        self._lock = asyncio.Lock()
        self._handlers: Dict[CommandType, Callable] = {}
    
    def register_handler(
        self,
        command_type: CommandType,
        handler: Callable
    ) -> None:
        """
        註冊指令處理器
        
        Args:
            command_type: 指令類型
            handler: 處理函數（async）
        """
        self._handlers[command_type] = handler
        logger.debug(f"Registered handler for {command_type.value}")
    
    def _generate_dedup_hash(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> str:
        """
        生成去重複用的雜湊值
        
        Args:
            user_id: 用戶 ID
            command: 解析後的指令
        
        Returns:
            雜湊字串
        """
        content = f"{user_id}:{command.command_type.value}:{command.raw_text}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, hash_key: str) -> bool:
        """
        檢查是否為重複指令
        
        Args:
            hash_key: 雜湊鍵
        
        Returns:
            是否重複
        """
        now = datetime.utcnow()
        
        # 清理過期的雜湊
        expired_keys = [
            k for k, v in self._recent_hashes.items()
            if now - v > timedelta(seconds=self.DEDUP_WINDOW_SECONDS)
        ]
        for k in expired_keys:
            del self._recent_hashes[k]
        
        # 檢查是否存在
        if hash_key in self._recent_hashes:
            return True
        
        # 記錄新雜湊
        self._recent_hashes[hash_key] = now
        return False
    
    async def enqueue(
        self,
        user_id: str,
        command: ParsedCommand
    ) -> Optional[QueueItem]:
        """
        將指令加入佇列
        
        Args:
            user_id: 用戶 LINE ID
            command: 解析後的指令
        
        Returns:
            佇列項目（如果成功加入）或 None（如果被過濾）
        """
        async with self._lock:
            # 檢查佇列大小
            if len(self._queue) >= self.MAX_QUEUE_SIZE:
                logger.warning("Queue is full, rejecting command")
                return None
            
            # 檢查指令有效性
            if not command.is_valid():
                logger.debug(f"Invalid command rejected: {command.error}")
                return None
            
            # 去重複檢查
            dedup_hash = self._generate_dedup_hash(user_id, command)
            if self._is_duplicate(dedup_hash):
                logger.info(f"Duplicate command skipped: {command.raw_text[:50]}")
                return None
            
            # 建立佇列項目
            item = QueueItem(
                id=dedup_hash,
                user_id=user_id,
                command=command,
            )
            
            self._queue[item.id] = item
            logger.info(
                f"Command enqueued",
                extra={
                    "queue_id": item.id,
                    "user_id": user_id,
                    "command_type": command.command_type.value,
                },
            )
            
            return item
    
    async def dequeue(self, user_id: Optional[str] = None) -> Optional[QueueItem]:
        """
        取出下一個待處理的指令
        
        Args:
            user_id: 可選，指定用戶的指令
        
        Returns:
            佇列項目或 None
        """
        async with self._lock:
            for item_id, item in self._queue.items():
                # 只處理等待中的項目
                if item.status != QueueStatus.PENDING:
                    continue
                
                # 如果指定用戶，只取該用戶的指令
                if user_id and item.user_id != user_id:
                    continue
                
                # 檢查用戶並發限制
                current_count = self._user_processing.get(item.user_id, 0)
                if current_count >= self.MAX_CONCURRENT_PER_USER:
                    continue
                
                # 更新狀態
                item.status = QueueStatus.PROCESSING
                self._user_processing[item.user_id] = current_count + 1
                
                return item
        
        return None
    
    async def complete(
        self,
        item: QueueItem,
        result: Any = None,
        error: Optional[str] = None
    ) -> None:
        """
        標記指令完成
        
        Args:
            item: 佇列項目
            result: 執行結果
            error: 錯誤訊息（如果失敗）
        """
        async with self._lock:
            item.processed_at = datetime.utcnow()
            item.result = result
            item.error = error
            
            if error:
                if item.can_retry():
                    item.retry_count += 1
                    item.status = QueueStatus.PENDING
                    logger.warning(
                        f"Command failed, will retry",
                        extra={
                            "queue_id": item.id,
                            "retry_count": item.retry_count,
                            "error": error,
                        },
                    )
                else:
                    item.status = QueueStatus.FAILED
                    logger.error(
                        f"Command failed permanently",
                        extra={
                            "queue_id": item.id,
                            "error": error,
                        },
                    )
            else:
                item.status = QueueStatus.COMPLETED
                logger.info(
                    f"Command completed",
                    extra={"queue_id": item.id},
                )
                # 從佇列移除已完成的項目
                del self._queue[item.id]
            
            # 更新並發計數
            current_count = self._user_processing.get(item.user_id, 1)
            self._user_processing[item.user_id] = max(0, current_count - 1)
    
    async def process_next(self, user_id: Optional[str] = None) -> Optional[Any]:
        """
        處理下一個指令
        
        Args:
            user_id: 可選，指定用戶
        
        Returns:
            處理結果或 None
        """
        item = await self.dequeue(user_id)
        if not item:
            return None
        
        command_type = item.command.command_type
        handler = self._handlers.get(command_type)
        
        if not handler:
            await self.complete(
                item,
                error=f"No handler for command type: {command_type.value}"
            )
            return None
        
        try:
            result = await handler(item.user_id, item.command)
            await self.complete(item, result=result)
            return result
        except Exception as e:
            await self.complete(item, error=str(e))
            return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        取得佇列統計資訊
        
        Returns:
            統計資訊字典
        """
        status_counts = {status.value: 0 for status in QueueStatus}
        for item in self._queue.values():
            status_counts[item.status.value] += 1
        
        return {
            "total": len(self._queue),
            "by_status": status_counts,
            "recent_hashes": len(self._recent_hashes),
        }


# 單例模式
_queue: Optional[CommandQueue] = None


def get_queue() -> CommandQueue:
    """取得指令佇列單例"""
    global _queue
    if _queue is None:
        _queue = CommandQueue()
    return _queue
