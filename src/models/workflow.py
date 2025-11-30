# LINE 自動化流程引擎 - 工作流程模型
# LINE Workflow Automation Engine - Workflow Model
"""
工作流程模型模組
================

此模組定義 Workflow 資料模型，儲存自訂工作流程定義。

資料表：workflows
"""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class Workflow(Base, TimestampMixin):
    """
    工作流程模型
    
    儲存用戶自訂的工作流程定義，包含觸發條件和執行步驟。
    
    Attributes:
        id: 主鍵（UUID）
        user_id: 用戶外鍵
        name: 流程名稱
        description: 流程描述
        trigger: 觸發條件（JSON）
        steps: 執行步驟（JSON 陣列）
        is_active: 是否啟用
        version: 版本號
        created_at: 建立時間
        updated_at: 更新時間
    
    Relationships:
        user: 所屬用戶
        schedules: 關聯的排程
        execution_logs: 執行日誌
    
    Trigger JSON Schema:
        {
            "type": "command" | "schedule" | "webhook",
            "value": "/morning"  # 指令、Cron 表達式或 Webhook URL
        }
    
    Steps JSON Schema:
        [
            {
                "order": 1,
                "type": "google_calendar",
                "action": "query",
                "params": {"date": "today"},
                "output_var": "today_events"
            },
            ...
        ]
    """
    
    __tablename__ = "workflows"
    __table_args__ = {"comment": "工作流程資料表"}
    
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
    
    # ----- 基本資訊 -----
    name = Column(
        String(100),
        nullable=False,
        comment="流程名稱"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="流程描述"
    )
    
    # ----- 流程定義 -----
    trigger = Column(
        JSON,
        nullable=False,
        comment="觸發條件（JSON）"
    )
    
    steps = Column(
        JSON,
        nullable=False,
        default=list,
        comment="執行步驟（JSON 陣列）"
    )
    
    # ----- 狀態 -----
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="是否啟用"
    )
    
    # ----- 版本控制 -----
    version = Column(
        Integer,
        nullable=False,
        default=1,
        comment="版本號"
    )
    
    # ----- 關聯 -----
    # 所屬用戶
    user = relationship(
        "User",
        back_populates="workflows"
    )
    
    # 關聯的排程（一對多）
    schedules = relationship(
        "Schedule",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # 執行日誌（一對多）
    execution_logs = relationship(
        "ExecutionLog",
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        """字串表示"""
        return f"<Workflow(id={self.id}, name={self.name}, version={self.version})>"
    
    @property
    def trigger_type(self) -> str:
        """
        取得觸發類型
        
        Returns:
            str: 觸發類型（command、schedule、webhook）
        """
        return self.trigger.get("type", "command")
    
    @property
    def trigger_value(self) -> str:
        """
        取得觸發值
        
        Returns:
            str: 觸發值（指令、Cron 表達式或 Webhook URL）
        """
        return self.trigger.get("value", "")
    
    @property
    def step_count(self) -> int:
        """
        取得步驟數量
        
        Returns:
            int: 步驟數量
        """
        return len(self.steps) if self.steps else 0
    
    def increment_version(self) -> None:
        """
        增加版本號
        
        每次更新流程定義時應呼叫此方法。
        """
        self.version += 1


# =============================================================================
# 匯出
# =============================================================================

__all__ = ["Workflow"]
