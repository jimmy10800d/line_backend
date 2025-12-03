# 指令佇列服務單元測試
# Command Queue Service Unit Tests
"""
指令佇列服務測試
================

使用 TDD 方法測試指令佇列功能：
1. 入隊和出隊操作
2. 去重複機制
3. 並發限制
4. 失敗重試
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.commands.parser import CommandType, ParsedCommand
from src.commands.queue import (
    CommandQueue,
    QueueItem,
    QueueStatus,
    get_queue,
)


class TestCommandQueue:
    """指令佇列測試"""
    
    @pytest.fixture
    def queue(self) -> CommandQueue:
        """建立新的佇列實例"""
        return CommandQueue()
    
    @pytest.fixture
    def sample_command(self) -> ParsedCommand:
        """建立範例指令"""
        return ParsedCommand(
            command_type=CommandType.ADD_TODO,
            raw_text="待辦 買牛奶",
            parameters={"content": "買牛奶"},
        )
    
    # =========================================================================
    # 基本功能測試
    # =========================================================================
    
    def test_queue_singleton(self):
        """測試佇列單例模式"""
        queue1 = get_queue()
        queue2 = get_queue()
        assert queue1 is queue2
    
    @pytest.mark.asyncio
    async def test_enqueue_valid_command(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試加入有效指令"""
        item = await queue.enqueue("U123", sample_command)
        
        assert item is not None
        assert item.user_id == "U123"
        assert item.command == sample_command
        assert item.status == QueueStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_enqueue_invalid_command(self, queue: CommandQueue):
        """測試加入無效指令"""
        invalid_cmd = ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text="???",
            error="無法識別",
        )
        
        item = await queue.enqueue("U123", invalid_cmd)
        assert item is None  # 無效指令不應該入隊
    
    @pytest.mark.asyncio
    async def test_dequeue_command(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試取出指令"""
        await queue.enqueue("U123", sample_command)
        
        item = await queue.dequeue()
        
        assert item is not None
        assert item.status == QueueStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_dequeue_empty_queue(self, queue: CommandQueue):
        """測試從空佇列取出"""
        item = await queue.dequeue()
        assert item is None
    
    @pytest.mark.asyncio
    async def test_dequeue_specific_user(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試取出特定用戶的指令"""
        await queue.enqueue("U123", sample_command)
        await queue.enqueue("U456", sample_command)
        
        item = await queue.dequeue(user_id="U456")
        
        assert item is not None
        assert item.user_id == "U456"
    
    # =========================================================================
    # 去重複測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_deduplication(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試去重複機制"""
        # 第一次入隊應該成功
        item1 = await queue.enqueue("U123", sample_command)
        assert item1 is not None
        
        # 短時間內相同指令應該被過濾
        item2 = await queue.enqueue("U123", sample_command)
        assert item2 is None
    
    @pytest.mark.asyncio
    async def test_deduplication_different_users(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試不同用戶的相同指令不去重"""
        item1 = await queue.enqueue("U123", sample_command)
        item2 = await queue.enqueue("U456", sample_command)
        
        assert item1 is not None
        assert item2 is not None
    
    @pytest.mark.asyncio
    async def test_deduplication_different_commands(self, queue: CommandQueue):
        """測試不同指令不去重"""
        cmd1 = ParsedCommand(
            command_type=CommandType.ADD_TODO,
            raw_text="待辦 A",
            parameters={"content": "A"},
        )
        cmd2 = ParsedCommand(
            command_type=CommandType.ADD_TODO,
            raw_text="待辦 B",
            parameters={"content": "B"},
        )
        
        item1 = await queue.enqueue("U123", cmd1)
        item2 = await queue.enqueue("U123", cmd2)
        
        assert item1 is not None
        assert item2 is not None
    
    # =========================================================================
    # 完成和失敗處理測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_complete_success(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試成功完成指令"""
        await queue.enqueue("U123", sample_command)
        item = await queue.dequeue()
        
        await queue.complete(item, result={"success": True})
        
        assert item.status == QueueStatus.COMPLETED
        assert item.result == {"success": True}
        assert item.processed_at is not None
    
    @pytest.mark.asyncio
    async def test_complete_with_error_retry(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試失敗後重試"""
        await queue.enqueue("U123", sample_command)
        item = await queue.dequeue()
        
        # 第一次失敗
        await queue.complete(item, error="暫時錯誤")
        
        assert item.status == QueueStatus.PENDING  # 應該回到等待狀態
        assert item.retry_count == 1
        assert item.can_retry() is True
    
    @pytest.mark.asyncio
    async def test_complete_max_retries_exceeded(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試超過最大重試次數"""
        await queue.enqueue("U123", sample_command)
        item = await queue.dequeue()
        item.retry_count = item.max_retries  # 模擬已重試多次
        
        await queue.complete(item, error="永久錯誤")
        
        assert item.status == QueueStatus.FAILED
        assert item.can_retry() is False
    
    # =========================================================================
    # 並發限制測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_concurrent_limit_per_user(self, queue: CommandQueue):
        """測試用戶並發限制"""
        # 加入多個指令
        for i in range(5):
            cmd = ParsedCommand(
                command_type=CommandType.ADD_TODO,
                raw_text=f"待辦 {i}",
                parameters={"content": str(i)},
            )
            await queue.enqueue("U123", cmd)
        
        # 取出到達並發限制
        processing = []
        for _ in range(queue.MAX_CONCURRENT_PER_USER):
            item = await queue.dequeue(user_id="U123")
            if item:
                processing.append(item)
        
        # 再次取出應該返回 None（達到限制）
        extra = await queue.dequeue(user_id="U123")
        assert extra is None
        
        # 完成一個後應該可以取出新的
        await queue.complete(processing[0])
        next_item = await queue.dequeue(user_id="U123")
        assert next_item is not None
    
    # =========================================================================
    # 佇列容量測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_queue_max_size(self, queue: CommandQueue):
        """測試佇列最大容量"""
        original_max = queue.MAX_QUEUE_SIZE
        queue.MAX_QUEUE_SIZE = 3  # 暫時設定較小的限制
        
        try:
            for i in range(5):
                cmd = ParsedCommand(
                    command_type=CommandType.ADD_TODO,
                    raw_text=f"待辦 {i}",
                    parameters={"content": str(i)},
                )
                await queue.enqueue(f"U{i}", cmd)  # 不同用戶避免去重
            
            stats = queue.get_queue_stats()
            assert stats["total"] <= 3
        finally:
            queue.MAX_QUEUE_SIZE = original_max
    
    # =========================================================================
    # 處理器註冊和執行測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_register_and_process_handler(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試註冊和處理指令"""
        results = []
        
        async def todo_handler(user_id: str, command: ParsedCommand):
            results.append((user_id, command.parameters.get("content")))
            return {"handled": True}
        
        queue.register_handler(CommandType.ADD_TODO, todo_handler)
        await queue.enqueue("U123", sample_command)
        
        result = await queue.process_next()
        
        assert result == {"handled": True}
        assert len(results) == 1
        assert results[0] == ("U123", "買牛奶")
    
    @pytest.mark.asyncio
    async def test_process_without_handler(self, queue: CommandQueue):
        """測試沒有處理器的指令"""
        cmd = ParsedCommand(
            command_type=CommandType.STATUS,
            raw_text="狀態",
        )
        await queue.enqueue("U123", cmd)
        
        result = await queue.process_next()
        
        assert result is None  # 沒有處理器應該返回 None
    
    # =========================================================================
    # 統計資訊測試
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_queue_stats(
        self, queue: CommandQueue, sample_command: ParsedCommand
    ):
        """測試佇列統計"""
        await queue.enqueue("U123", sample_command)
        
        stats = queue.get_queue_stats()
        
        assert stats["total"] == 1
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["processing"] == 0


class TestQueueItem:
    """佇列項目測試"""
    
    def test_queue_item_creation(self):
        """測試建立佇列項目"""
        cmd = ParsedCommand(
            command_type=CommandType.HELP,
            raw_text="help",
        )
        item = QueueItem(
            id="test123",
            user_id="U123",
            command=cmd,
        )
        
        assert item.id == "test123"
        assert item.user_id == "U123"
        assert item.status == QueueStatus.PENDING
        assert item.retry_count == 0
        assert item.can_retry() is True
    
    def test_queue_item_can_retry(self):
        """測試重試檢查"""
        cmd = ParsedCommand(command_type=CommandType.HELP, raw_text="help")
        item = QueueItem(id="test", user_id="U123", command=cmd)
        
        assert item.can_retry() is True
        
        item.retry_count = item.max_retries
        assert item.can_retry() is False
