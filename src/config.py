# LINE 自動化流程引擎 - 配置管理
# LINE Workflow Automation Engine - Configuration Management
"""
配置管理模組
============

此模組負責：
1. 從環境變數載入配置
2. 提供資料庫連線設定
3. 提供結構化日誌配置
4. 管理各外部服務的 API 金鑰

使用方式：
    from src.config import settings, get_db_session, logger
"""

import os
from functools import lru_cache
from typing import AsyncGenerator

import structlog
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 載入環境變數
load_dotenv()


# =============================================================================
# 應用程式設定
# =============================================================================


class Settings(BaseSettings):
    """
    應用程式設定類別
    
    從環境變數載入所有配置，提供預設值和驗證。
    使用 pydantic-settings 實現類型安全的配置管理。
    """
    
    # ----- 應用程式基本設定 -----
    app_name: str = Field(default="LINE Workflow Automation", description="應用程式名稱")
    app_env: str = Field(default="development", description="執行環境")
    debug: bool = Field(default=False, description="除錯模式")
    host: str = Field(default="0.0.0.0", description="伺服器主機")
    port: int = Field(default=8000, description="伺服器埠號")
    
    # ----- 資料庫設定 -----
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db",
        description="資料庫連線字串"
    )
    
    # ----- LINE Bot 設定 -----
    line_channel_access_token: str = Field(default="", description="LINE Channel Access Token")
    line_channel_secret: str = Field(default="", description="LINE Channel Secret")
    
    # ----- OpenAI 設定 -----
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI 模型")
    
    # ----- Google OAuth 設定 -----
    google_client_id: str = Field(default="", description="Google OAuth Client ID")
    google_client_secret: str = Field(default="", description="Google OAuth Client Secret")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/integrations/google_calendar/callback",
        description="Google OAuth Redirect URI"
    )
    
    # ----- Notion 設定 -----
    notion_integration_token: str = Field(default="", description="Notion Integration Token")
    
    # ----- GitHub 設定 -----
    github_client_id: str = Field(default="", description="GitHub OAuth Client ID")
    github_client_secret: str = Field(default="", description="GitHub OAuth Client Secret")
    github_redirect_uri: str = Field(
        default="http://localhost:8000/api/integrations/github/callback",
        description="GitHub OAuth Redirect URI"
    )
    
    # ----- 天氣 API 設定 -----
    weather_api_key: str = Field(default="", description="OpenWeatherMap API Key")
    
    # ----- 加密設定 -----
    encryption_key: str = Field(default="", description="Token 加密金鑰")
    
    # ----- 日誌設定 -----
    log_level: str = Field(default="INFO", description="日誌等級")
    log_format: str = Field(default="console", description="日誌格式（json/console）")
    
    # ----- 時區設定 -----
    timezone: str = Field(default="Asia/Taipei", description="時區")
    
    class Config:
        """Pydantic 設定"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def is_development(self) -> bool:
        """是否為開發環境"""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """是否為生產環境"""
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """
    取得應用程式設定（單例模式）
    
    使用 lru_cache 確保只建立一次設定物件，
    避免重複讀取環境變數。
    
    Returns:
        Settings: 應用程式設定實例
    """
    return Settings()


# 全域設定實例
settings = get_settings()


# =============================================================================
# 資料庫設定
# =============================================================================


def _create_engine():
    """
    建立 SQLAlchemy 非同步引擎
    
    根據環境設定建立適當的資料庫連線引擎。
    開發環境啟用 SQL 日誌，生產環境則關閉。
    
    Returns:
        AsyncEngine: SQLAlchemy 非同步引擎
    """
    # 確保資料目錄存在
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.split("///")[-1]
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,  # 開發環境顯示 SQL
        future=True,
    )


# 建立全域引擎
engine = _create_engine()

# 建立 Session 工廠
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    取得資料庫 Session（依賴注入用）
    
    這是一個非同步產生器，用於 FastAPI 的依賴注入。
    確保 Session 在使用後正確關閉。
    
    Yields:
        AsyncSession: SQLAlchemy 非同步 Session
    
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# 日誌設定
# =============================================================================


def configure_logging() -> structlog.BoundLogger:
    """
    配置結構化日誌
    
    根據環境設定配置 structlog：
    - 開發環境：彩色控制台輸出
    - 生產環境：JSON 格式輸出
    
    Returns:
        BoundLogger: 配置好的日誌記錄器
    """
    import logging
    import sys
    
    # 設定標準 logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.debug else logging.INFO,
    )
    
    # 根據設定選擇處理器
    if settings.log_format == "json":
        # JSON 格式（適合生產環境和日誌收集）
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        # 控制台格式（適合開發環境）
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


# 配置並取得日誌記錄器
logger = configure_logging()


# =============================================================================
# 匯出
# =============================================================================

__all__ = [
    "settings",
    "get_settings",
    "engine",
    "async_session_factory",
    "get_db_session",
    "logger",
    "configure_logging",
]
