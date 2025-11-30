# LINE 自動化流程引擎 - 資料模型基礎類別
# LINE Workflow Automation Engine - Base Model Classes
"""
資料模型基礎模組
================

此模組定義所有 SQLAlchemy 模型的基礎類別和共用 Mixin。

包含：
- Base: SQLAlchemy 宣告式基礎類別
- TimestampMixin: 時間戳記 Mixin（created_at, updated_at）
- generate_uuid: UUID 產生函數

使用方式：
    from src.models.base import Base, TimestampMixin, generate_uuid
    
    class MyModel(Base, TimestampMixin):
        __tablename__ = "my_table"
        id = Column(String(36), primary_key=True, default=generate_uuid)
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy 宣告式基礎類別
    
    所有資料模型都應繼承此類別。
    使用 SQLAlchemy 2.0 風格的 DeclarativeBase。
    """
    pass


class TimestampMixin:
    """
    時間戳記 Mixin
    
    提供 created_at 和 updated_at 欄位，
    自動記錄建立時間和更新時間。
    
    Attributes:
        created_at: 建立時間（自動設定）
        updated_at: 更新時間（自動更新）
    """
    
    # 建立時間：使用資料庫伺服器時間
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="建立時間"
    )
    
    # 更新時間：建立時設定，每次更新時自動更新
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新時間"
    )


def generate_uuid() -> str:
    """
    產生 UUID 字串
    
    使用 UUID4 產生隨機唯一識別碼。
    
    Returns:
        str: 36 字元的 UUID 字串（含連字號）
    
    Example:
        >>> generate_uuid()
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    """
    return str(uuid.uuid4())


# =============================================================================
# 匯出
# =============================================================================

__all__ = [
    "Base",
    "TimestampMixin",
    "generate_uuid",
]
