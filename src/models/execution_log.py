# LINE 自動化流程引擎 - 執行日誌模型
# LINE Workflow Automation Engine - Execution Log Model
"""
執行日誌模型模組
================

此模組定義 ExecutionLog 資料模型，記錄所有任務執行歷史。

資料保留政策：7 天後自動清除

資料表：execution_logs
"""

from enum import Enum as PyEnum

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class ExecutionStatus(str, PyEnum):
    """
    執行狀態列舉
    
    定義任務執行的所有可能狀態。
    
    Attributes:
        PENDING: 等待執行
        RUNNING: 執行中
        SUCCESS: 執行成功
        FAILED: 執行失敗
        CANCELLED: 已取消
    """
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionLog(Base, TimestampMixin):
    """
    執行日誌模型
    
    記錄所有任務執行的歷史紀錄，包含輸入、輸出和錯誤資訊。
    
    Attributes:
        id: 主鍵（UUID）
        workflow_id: 工作流程外鍵（可為空，預設任務無對應流程）
        schedule_id: 排程外鍵（可為空，手動觸發無對應排程）
        task_type: 任務類型
        status: 執行狀態
        input: 輸入參數（JSON）
        output: 輸出結果（JSON）
        error: 錯誤訊息
        started_at: 開始時間
        finished_at: 結束時間
        created_at: 建立時間
        updated_at: 更新時間
    
    Relationships:
        workflow: 對應的工作流程
        schedule: 對應的排程
    
    資料保留：
        日誌保留 7 天，超過自動清除。
        清理腳本：scripts/cleanup_logs.py
    """
    
    __tablename__ = "execution_logs"
    __table_args__ = {"comment": "執行日誌資料表"}
    
    # ----- 主鍵 -----
    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="主鍵 UUID"
    )
    
    # ----- 外鍵 -----
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="工作流程外鍵（可為空）"
    )
    
    schedule_id = Column(
        String(36),
        ForeignKey("schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="排程外鍵（可為空）"
    )
    
    # ----- 任務資訊 -----
    task_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="任務類型（如 weather、calendar、remind 等）"
    )
    
    status = Column(
        Enum(ExecutionStatus),
        nullable=False,
        default=ExecutionStatus.PENDING,
        index=True,
        comment="執行狀態"
    )
    
    # ----- 輸入輸出 -----
    input = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="輸入參數（JSON）"
    )
    
    output = Column(
        JSON,
        nullable=True,
        default=dict,
        comment="輸出結果（JSON）"
    )
    
    error = Column(
        Text,
        nullable=True,
        comment="錯誤訊息"
    )
    
    # ----- 執行時間 -----
    started_at = Column(
        DateTime,
        nullable=True,
        comment="開始時間"
    )
    
    finished_at = Column(
        DateTime,
        nullable=True,
        comment="結束時間"
    )
    
    # ----- 關聯 -----
    # 對應的工作流程
    workflow = relationship(
        "Workflow",
        back_populates="execution_logs"
    )
    
    # 對應的排程
    schedule = relationship(
        "Schedule",
        back_populates="execution_logs"
    )
    
    def __repr__(self) -> str:
        """字串表示"""
        return f"<ExecutionLog(id={self.id}, task_type={self.task_type}, status={self.status})>"
    
    @property
    def is_completed(self) -> bool:
        """
        是否已完成（成功或失敗）
        
        Returns:
            bool: 是否已完成
        """
        return self.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED)
    
    @property
    def is_success(self) -> bool:
        """
        是否執行成功
        
        Returns:
            bool: 是否成功
        """
        return self.status == ExecutionStatus.SUCCESS
    
    @property
    def duration_seconds(self) -> float | None:
        """
        計算執行時間（秒）
        
        Returns:
            float | None: 執行時間，若未完成則返回 None
        """
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None
    
    def mark_running(self) -> None:
        """標記為執行中"""
        from datetime import datetime
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def mark_success(self, output: dict | None = None) -> None:
        """
        標記為成功
        
        Args:
            output: 輸出結果
        """
        from datetime import datetime
        self.status = ExecutionStatus.SUCCESS
        self.finished_at = datetime.utcnow()
        if output:
            self.output = output
    
    def mark_failed(self, error: str) -> None:
        """
        標記為失敗
        
        Args:
            error: 錯誤訊息
        """
        from datetime import datetime
        self.status = ExecutionStatus.FAILED
        self.finished_at = datetime.utcnow()
        self.error = error
    
    def mark_cancelled(self) -> None:
        """標記為已取消"""
        from datetime import datetime
        self.status = ExecutionStatus.CANCELLED
        self.finished_at = datetime.utcnow()


# =============================================================================
# 匯出
# =============================================================================

__all__ = ["ExecutionLog", "ExecutionStatus"]
