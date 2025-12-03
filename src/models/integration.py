# LINE 自動化流程引擎 - 外部服務整合模型
# LINE Workflow Automation Engine - Integration Model
"""
外部服務整合模型模組
====================

此模組定義 Integration 資料模型，儲存外部服務的 OAuth Token。

資料表：integrations
"""

from enum import Enum as PyEnum

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, generate_uuid


class ServiceType(str, PyEnum):
    """
    服務類型列舉
    
    定義系統支援的所有外部服務類型。
    
    Attributes:
        GOOGLE_CALENDAR: Google Calendar
        NOTION: Notion
        GITHUB: GitHub
    """
    GOOGLE_CALENDAR = "google_calendar"
    NOTION = "notion"
    GITHUB = "github"


class Integration(Base, TimestampMixin):
    """
    外部服務整合模型
    
    儲存用戶的外部服務 OAuth Token 和相關設定。
    Token 使用加密儲存，確保安全性。
    
    Attributes:
        id: 主鍵（UUID）
        user_id: 用戶外鍵
        service_type: 服務類型
        access_token: 存取權杖（加密）
        refresh_token: 刷新權杖（加密）
        token_expiry: 權杖過期時間
        metadata: 服務特定資料（JSON）
        created_at: 建立時間
        updated_at: 更新時間
    
    Relationships:
        user: 所屬用戶
    
    安全性：
        - access_token 和 refresh_token 使用 Fernet 加密儲存
        - 解密需要 ENCRYPTION_KEY 環境變數
    
    Metadata JSON Examples:
        Google Calendar: {"email": "user@gmail.com", "calendar_id": "primary"}
        Notion: {"workspace_name": "My Workspace", "workspace_id": "abc123"}
        GitHub: {"username": "jimmy10800d", "default_repo": "line_backend"}
    """
    
    __tablename__ = "integrations"
    __table_args__ = (
        # 每個用戶對每個服務只能有一個整合
        UniqueConstraint("user_id", "service_type", name="uq_user_service"),
        {"comment": "外部服務整合資料表"},
    )
    
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
    
    # ----- 服務資訊 -----
    service_type = Column(
        Enum(ServiceType),
        nullable=False,
        comment="服務類型"
    )
    
    # ----- OAuth Token（加密儲存）-----
    access_token = Column(
        Text,
        nullable=True,
        comment="存取權杖（加密）"
    )
    
    refresh_token = Column(
        Text,
        nullable=True,
        comment="刷新權杖（加密）"
    )
    
    token_expiry = Column(
        DateTime,
        nullable=True,
        comment="權杖過期時間"
    )
    
    # ----- 服務特定資料 -----
    service_metadata = Column(
        "metadata",  # 資料表中仍使用 metadata 欄位名
        JSON,
        nullable=False,
        default=dict,
        comment="服務特定資料（JSON）"
    )
    
    # ----- 關聯 -----
    # 所屬用戶
    user = relationship(
        "User",
        back_populates="integrations"
    )
    
    def __repr__(self) -> str:
        """字串表示"""
        return f"<Integration(id={self.id}, service_type={self.service_type})>"
    
    @property
    def is_token_expired(self) -> bool:
        """
        檢查 Token 是否已過期
        
        Returns:
            bool: Token 是否已過期
        """
        if not self.token_expiry:
            return False
        from datetime import datetime
        return datetime.utcnow() >= self.token_expiry
    
    @property
    def is_connected(self) -> bool:
        """
        檢查是否已連接（有有效 Token）
        
        Returns:
            bool: 是否已連接
        """
        return self.access_token is not None and not self.is_token_expired
    
    def update_tokens(
        self,
        access_token: str,
        refresh_token: str | None = None,
        token_expiry = None
    ) -> None:
        """
        更新 OAuth Token
        
        Args:
            access_token: 新的存取權杖
            refresh_token: 新的刷新權杖（選填）
            token_expiry: 新的過期時間（選填）
        """
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if token_expiry:
            self.token_expiry = token_expiry
    
    def clear_tokens(self) -> None:
        """清除 OAuth Token（斷開連接）"""
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None


# =============================================================================
# 匯出
# =============================================================================

__all__ = ["Integration", "ServiceType"]
