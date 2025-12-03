# LINE 自動化流程引擎 - 排程模型
# LINE Workflow Automation Engine - Schedule Model
"""
排程模型模組
============

此模組定義 Schedule 資料模型，儲存工作流程的排程設定。

資料表：schedules
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class Schedule(Base, TimestampMixin):
    """
    排程模型
    
    儲存工作流程的定時執行設定，支援 Cron 表達式。
    
    Attributes:
        id: 主鍵（UUID）
        user_id: 用戶外鍵
        workflow_id: 工作流程外鍵
        name: 排程名稱
        cron_expression: Cron 表達式（如 "0 9 * * *" 表示每天 09:00）
        next_run_at: 下次執行時間
        last_run_at: 上次執行時間
        is_active: 是否啟用
        created_at: 建立時間
        updated_at: 更新時間
    
    Relationships:
        user: 所屬用戶
        workflow: 對應的工作流程
        execution_logs: 執行日誌
    
    Cron 表達式格式：
        分 時 日 月 星期
        例如：
        - "0 9 * * *": 每天 09:00
        - "0 9 * * 1-5": 週一到週五 09:00
        - "*/30 * * * *": 每 30 分鐘
        - "0 9 1 * *": 每月 1 日 09:00
    
    時區：
        所有時間使用台灣時區（UTC+8）
    """
    
    __tablename__ = "schedules"
    __table_args__ = {"comment": "排程資料表"}
    
    # ----- 主鍵 -----
    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="主鍵 UUID"
    )
    
    # ----- 外鍵 -----
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用戶外鍵"
    )
    
    workflow_id = Column(
        String(36),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="工作流程外鍵"
    )
    
    # ----- 排程資訊 -----
    name = Column(
        String(100),
        nullable=False,
        comment="排程名稱"
    )
    
    cron_expression = Column(
        String(50),
        nullable=False,
        comment="Cron 表達式"
    )
    
    # ----- 執行時間 -----
    next_run_at = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="下次執行時間"
    )
    
    last_run_at = Column(
        DateTime,
        nullable=True,
        comment="上次執行時間"
    )
    
    # ----- 狀態 -----
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否啟用"
    )
    
    # ----- 關聯 -----
    # 所屬用戶
    user = relationship(
        "User",
        back_populates="schedules"
    )
    
    # 對應的工作流程
    workflow = relationship(
        "Workflow",
        back_populates="schedules"
    )
    
    # 執行日誌（一對多）
    execution_logs = relationship(
        "ExecutionLog",
        back_populates="schedule",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        """字串表示"""
        return f"<Schedule(id={self.id}, name={self.name}, cron={self.cron_expression})>"
    
    @property
    def is_due(self) -> bool:
        """
        檢查是否已到執行時間
        
        Returns:
            bool: 是否已到執行時間
        """
        if not self.is_active or not self.next_run_at:
            return False
        from datetime import datetime
        return datetime.utcnow() >= self.next_run_at
    
    def calculate_next_run(self) -> None:
        """
        計算下次執行時間
        
        根據 Cron 表達式計算下次執行時間，
        並更新 next_run_at 欄位。
        """
        from datetime import datetime
        from croniter import croniter
        
        # 使用當前時間計算下次執行時間
        cron = croniter(self.cron_expression, datetime.utcnow())
        self.next_run_at = cron.get_next(datetime)
    
    def mark_executed(self) -> None:
        """
        標記為已執行
        
        更新 last_run_at 並計算新的 next_run_at。
        """
        from datetime import datetime
        self.last_run_at = datetime.utcnow()
        self.calculate_next_run()
    
    def activate(self) -> None:
        """啟用排程並計算下次執行時間"""
        self.is_active = True
        self.calculate_next_run()
    
    def deactivate(self) -> None:
        """停用排程"""
        self.is_active = False
        self.next_run_at = None


# =============================================================================
# 匯出
# =============================================================================

__all__ = ["Schedule"]
