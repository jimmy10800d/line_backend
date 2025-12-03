# LINE 自動化流程引擎 - 用戶模型
# LINE Workflow Automation Engine - User Model
"""
用戶模型模組
============

此模組定義 User 資料模型，儲存 LINE 用戶資訊。

雖然這是單一用戶系統，但保留 User 模型結構，
方便未來擴展為多用戶系統。

資料表：users
"""

from sqlalchemy import JSON, Column, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """
    用戶模型
    
    儲存 LINE 用戶的基本資訊和偏好設定。
    
    Attributes:
        id: 主鍵（UUID）
        line_user_id: LINE 用戶 ID（唯一）
        display_name: LINE 顯示名稱
        preferences: 用戶偏好設定（JSON）
        created_at: 建立時間
        updated_at: 更新時間
    
    Relationships:
        workflows: 用戶的工作流程（一對多）
        integrations: 用戶的外部服務整合（一對多）
        schedules: 用戶的排程（一對多）
    """
    
    __tablename__ = "users"
    __table_args__ = {"comment": "用戶資料表"}
    
    # ----- 主鍵 -----
    id = Column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        comment="主鍵 UUID"
    )
    
    # ----- LINE 資訊 -----
    line_user_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="LINE 用戶 ID"
    )
    
    display_name = Column(
        String(100),
        nullable=True,
        comment="LINE 顯示名稱"
    )
    
    # ----- 偏好設定 -----
    preferences = Column(
        JSON,
        nullable=False,
        default=dict,
        comment="用戶偏好設定（JSON）"
    )
    
    # ----- 關聯 -----
    # 用戶的工作流程（一對多）
    workflows = relationship(
        "Workflow",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # 用戶的外部服務整合（一對多）
    integrations = relationship(
        "Integration",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # 用戶的排程（一對多）
    schedules = relationship(
        "Schedule",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        """字串表示"""
        return f"<User(id={self.id}, line_user_id={self.line_user_id})>"
    
    @property
    def timezone(self) -> str:
        """
        取得用戶時區
        
        從偏好設定中取得時區，預設為台灣時區。
        
        Returns:
            str: 時區字串（如 'Asia/Taipei'）
        """
        return self.preferences.get("timezone", "Asia/Taipei")
    
    @property
    def language(self) -> str:
        """
        取得用戶語言
        
        從偏好設定中取得語言，預設為繁體中文。
        
        Returns:
            str: 語言代碼（如 'zh-TW'）
        """
        return self.preferences.get("language", "zh-TW")
    
    @property
    def notification_enabled(self) -> bool:
        """
        是否啟用通知
        
        從偏好設定中取得通知開關，預設為啟用。
        
        Returns:
            bool: 是否啟用通知
        """
        return self.preferences.get("notification_enabled", True)


# =============================================================================
# 匯出
# =============================================================================

__all__ = ["User"]
