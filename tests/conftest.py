# LINE 自動化流程引擎 - Pytest 配置
# LINE Workflow Automation Engine - Pytest Configuration
"""
Pytest 共用配置和 Fixtures
==========================

此模組提供測試所需的共用配置：
1. 測試資料庫設定
2. FastAPI TestClient
3. Mock 工廠函數
4. 測試資料產生器

使用方式：
    # 在測試中直接使用 fixture
    def test_something(test_client, test_db):
        response = test_client.get("/health")
        assert response.status_code == 200
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_db_session, settings
from src.main import app
from src.models.base import Base


# =============================================================================
# 測試資料庫配置
# =============================================================================

# 使用記憶體資料庫進行測試
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 建立測試用引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# 建立測試用 Session 工廠
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =============================================================================
# Event Loop Fixture
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    建立事件迴圈
    
    使用 session scope 確保整個測試期間使用同一個事件迴圈。
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# 資料庫 Fixtures
# =============================================================================


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    測試資料庫 Session Fixture
    
    每個測試函數都會獲得一個乾淨的資料庫：
    1. 建立所有資料表
    2. 提供 Session
    3. 測試結束後清理資料表
    
    Yields:
        AsyncSession: 測試用資料庫 Session
    """
    # 建立資料表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 提供 Session
    async with test_session_factory() as session:
        yield session
    
    # 清理資料表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    覆寫 get_db_session 依賴
    
    用於 FastAPI 的依賴注入覆寫。
    """
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================================
# FastAPI TestClient Fixtures
# =============================================================================


@pytest.fixture(scope="function")
def test_client(test_db: AsyncSession) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient Fixture
    
    提供同步的測試客戶端，用於測試 API 端點。
    
    Args:
        test_db: 測試資料庫 Session
    
    Yields:
        TestClient: FastAPI 測試客戶端
    """
    # 覆寫資料庫依賴
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    with TestClient(app) as client:
        yield client
    
    # 清理依賴覆寫
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_test_client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    非同步 TestClient Fixture
    
    提供非同步的測試客戶端，用於測試非同步 API。
    
    Args:
        test_db: 測試資料庫 Session
    
    Yields:
        AsyncClient: 非同步 HTTP 客戶端
    """
    # 覆寫資料庫依賴
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # 清理依賴覆寫
    app.dependency_overrides.clear()


# =============================================================================
# 測試資料工廠
# =============================================================================


@pytest.fixture
def user_factory(test_db: AsyncSession):
    """
    用戶資料工廠
    
    提供快速建立測試用戶的方法。
    
    Returns:
        Callable: 用戶建立函數
    """
    from src.models.user import User
    
    async def create_user(
        line_user_id: str = "U1234567890abcdef",
        display_name: str = "測試用戶",
        preferences: dict | None = None,
    ) -> User:
        user = User(
            line_user_id=line_user_id,
            display_name=display_name,
            preferences=preferences or {},
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        return user
    
    return create_user


@pytest.fixture
def workflow_factory(test_db: AsyncSession):
    """
    工作流程資料工廠
    
    提供快速建立測試工作流程的方法。
    
    Returns:
        Callable: 工作流程建立函數
    """
    from src.models.workflow import Workflow
    
    async def create_workflow(
        user_id: str,
        name: str = "測試流程",
        description: str = "這是測試用的工作流程",
        trigger: dict | None = None,
        steps: list | None = None,
        is_active: bool = True,
    ) -> Workflow:
        workflow = Workflow(
            user_id=user_id,
            name=name,
            description=description,
            trigger=trigger or {"type": "command", "value": "/test"},
            steps=steps or [],
            is_active=is_active,
        )
        test_db.add(workflow)
        await test_db.commit()
        await test_db.refresh(workflow)
        return workflow
    
    return create_workflow


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_line_api(mocker):
    """
    LINE API Mock Fixture
    
    模擬 LINE Messaging API 的回應。
    
    Returns:
        MagicMock: LINE API Mock 物件
    """
    mock = mocker.patch("src.services.line_service.LineService._send_request")
    mock.return_value = {}
    return mock


@pytest.fixture
def mock_openai_api(mocker):
    """
    OpenAI API Mock Fixture
    
    模擬 OpenAI API 的回應。
    
    Returns:
        MagicMock: OpenAI API Mock 物件
    """
    mock = mocker.patch("openai.AsyncOpenAI")
    return mock


# =============================================================================
# BDD 測試 Fixtures
# =============================================================================


@pytest.fixture
def test_user() -> dict:
    """
    測試用戶狀態容器
    
    用於在 BDD Step 之間傳遞用戶狀態。
    
    Returns:
        dict: 用戶狀態字典
    """
    return {
        "line_user_id": "U1234567890",
        "display_name": "測試用戶",
        "last_response": None,
        "last_message": None,
    }


@pytest.fixture
def line_webhook_mock():
    """
    LINE Webhook Mock Fixture
    
    提供建立 LINE Webhook 事件的工具。
    
    Returns:
        LineWebhookMock: Webhook Mock 工具
    """
    from tests.mocks.line_mock import LineWebhookMock
    return LineWebhookMock()


@pytest.fixture
def line_reply_mock(mocker):
    """
    LINE 回覆 Mock Fixture
    
    捕獲系統發送的 LINE 回覆訊息。
    
    Returns:
        LineReplyCapture: 回覆捕獲物件
    """
    class LineReplyCapture:
        def __init__(self):
            self.replies = []
        
        def capture(self, message):
            self.replies.append({"type": "text", "text": message})
        
        def get_replies(self):
            return self.replies
        
        def clear(self):
            self.replies = []
    
    capture = LineReplyCapture()
    
    # Mock send_reply 函式
    async def mock_send_reply(reply_token: str, text: str) -> None:
        capture.capture(text)
    
    mocker.patch("src.api.webhook.send_reply", side_effect=mock_send_reply)
    
    return capture


@pytest.fixture
def mock_services():
    """
    外部服務 Mock 集合
    
    提供所有外部服務的 Mock 物件。
    
    Returns:
        dict: Mock 服務字典
    """
    from tests.mocks.external_services import (
        MockOpenAIService,
        MockGoogleCalendarService,
        MockNotionService,
        MockGitHubService,
    )
    
    return {
        "openai": MockOpenAIService(),
        "google_calendar": MockGoogleCalendarService(),
        "notion": MockNotionService(),
        "github": MockGitHubService(),
    }


@pytest.fixture
def test_db_session(test_db):
    """
    BDD 測試用的資料庫 Session 別名
    
    Args:
        test_db: 原始測試資料庫 fixture
    
    Returns:
        AsyncSession: 資料庫 Session
    """
    return test_db


# =============================================================================
# 環境配置
# =============================================================================


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """
    設定測試環境
    
    自動設定測試所需的環境變數。
    """
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "test_secret")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")


# =============================================================================
# 匯出
# =============================================================================

__all__ = [
    "test_db",
    "test_client",
    "async_test_client",
    "user_factory",
    "workflow_factory",
    "mock_line_api",
    "mock_openai_api",
    "test_user",
    "line_webhook_mock",
    "line_reply_mock",
    "mock_services",
    "test_db_session",
]
