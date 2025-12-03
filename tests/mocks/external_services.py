# LINE 自動化流程引擎 - 外部服務 Mock 工具
# LINE Workflow Automation Engine - External Services Mock Utilities
"""
外部服務 Mock 工具
==================

此模組提供外部服務測試所需的 Mock 工具。

包含：
1. Google Calendar API Mock
2. Notion API Mock
3. GitHub API Mock
4. OpenWeatherMap API Mock
5. OpenAI API Mock
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


# =============================================================================
# Google Calendar Mock
# =============================================================================


@dataclass
class MockCalendarEvent:
    """Mock 日曆事件"""
    id: str = "event_001"
    summary: str = "測試會議"
    description: str = ""
    start: datetime = field(default_factory=datetime.now)
    end: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    location: str = ""
    
    def to_dict(self) -> dict:
        """轉換為 Google Calendar API 格式"""
        return {
            "id": self.id,
            "summary": self.summary,
            "description": self.description,
            "start": {
                "dateTime": self.start.isoformat(),
                "timeZone": "Asia/Taipei"
            },
            "end": {
                "dateTime": self.end.isoformat(),
                "timeZone": "Asia/Taipei"
            },
            "location": self.location,
        }


class MockGoogleCalendarAPI:
    """
    Mock Google Calendar API
    
    模擬 Google Calendar API 的回應。
    """
    
    def __init__(self):
        """初始化 Mock"""
        self.events: list[MockCalendarEvent] = []
    
    def add_event(self, event: MockCalendarEvent) -> None:
        """新增事件"""
        self.events.append(event)
    
    def list_events(
        self,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 10,
    ) -> dict:
        """
        列出事件
        
        Returns:
            dict: Google Calendar API 格式的回應
        """
        filtered = self.events
        
        if time_min:
            filtered = [e for e in filtered if e.start >= time_min]
        if time_max:
            filtered = [e for e in filtered if e.start <= time_max]
        
        return {
            "items": [e.to_dict() for e in filtered[:max_results]],
            "nextPageToken": None,
        }
    
    def get_today_events(self) -> dict:
        """取得今日事件"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return self.list_events(time_min=today, time_max=tomorrow)


# =============================================================================
# Notion Mock
# =============================================================================


@dataclass
class MockNotionPage:
    """Mock Notion 頁面"""
    id: str = "page_001"
    title: str = "測試頁面"
    content: str = ""
    created_time: datetime = field(default_factory=datetime.now)
    last_edited_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """轉換為 Notion API 格式"""
        return {
            "id": self.id,
            "properties": {
                "title": {
                    "title": [{"text": {"content": self.title}}]
                }
            },
            "created_time": self.created_time.isoformat(),
            "last_edited_time": self.last_edited_time.isoformat(),
        }


class MockNotionAPI:
    """
    Mock Notion API
    
    模擬 Notion API 的回應。
    """
    
    def __init__(self):
        """初始化 Mock"""
        self.pages: list[MockNotionPage] = []
        self.databases: dict[str, list[dict]] = {}
    
    def add_page(self, page: MockNotionPage) -> None:
        """新增頁面"""
        self.pages.append(page)
    
    def search(self, query: str) -> dict:
        """
        搜尋
        
        Returns:
            dict: Notion API 格式的回應
        """
        results = [
            p.to_dict() for p in self.pages
            if query.lower() in p.title.lower()
        ]
        return {
            "results": results,
            "has_more": False,
        }


# =============================================================================
# GitHub Mock
# =============================================================================


@dataclass
class MockGitHubIssue:
    """Mock GitHub Issue"""
    number: int = 1
    title: str = "測試 Issue"
    body: str = ""
    state: str = "open"
    labels: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """轉換為 GitHub API 格式"""
        return {
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "state": self.state,
            "labels": [{"name": label} for label in self.labels],
            "created_at": self.created_at.isoformat(),
        }


class MockGitHubAPI:
    """
    Mock GitHub API
    
    模擬 GitHub API 的回應。
    """
    
    def __init__(self):
        """初始化 Mock"""
        self.issues: list[MockGitHubIssue] = []
        self.pull_requests: list[dict] = []
    
    def add_issue(self, issue: MockGitHubIssue) -> None:
        """新增 Issue"""
        self.issues.append(issue)
    
    def list_issues(self, state: str = "open") -> list[dict]:
        """
        列出 Issues
        
        Returns:
            list[dict]: GitHub API 格式的回應
        """
        filtered = [
            i.to_dict() for i in self.issues
            if state == "all" or i.state == state
        ]
        return filtered


# =============================================================================
# Weather API Mock
# =============================================================================


@dataclass
class MockWeatherData:
    """Mock 天氣資料"""
    city: str = "Taipei"
    temperature: float = 25.0
    humidity: int = 70
    description: str = "晴天"
    icon: str = "01d"
    
    def to_dict(self) -> dict:
        """轉換為 OpenWeatherMap API 格式"""
        return {
            "name": self.city,
            "main": {
                "temp": self.temperature,
                "humidity": self.humidity,
            },
            "weather": [
                {
                    "description": self.description,
                    "icon": self.icon,
                }
            ],
        }


class MockWeatherAPI:
    """
    Mock Weather API
    
    模擬 OpenWeatherMap API 的回應。
    """
    
    def __init__(self):
        """初始化 Mock"""
        self.weather_data: dict[str, MockWeatherData] = {
            "Taipei": MockWeatherData(city="Taipei", temperature=25.0, description="晴天"),
            "Tokyo": MockWeatherData(city="Tokyo", temperature=20.0, description="多雲"),
        }
    
    def get_weather(self, city: str) -> dict | None:
        """
        取得天氣資料
        
        Args:
            city: 城市名稱
        
        Returns:
            dict | None: 天氣資料，找不到時返回 None
        """
        data = self.weather_data.get(city)
        return data.to_dict() if data else None


# =============================================================================
# OpenAI Mock
# =============================================================================


class MockOpenAIAPI:
    """
    Mock OpenAI API
    
    模擬 OpenAI API 的回應。
    """
    
    def __init__(self):
        """初始化 Mock"""
        self.responses: dict[str, str] = {}
        self.default_response = "這是 AI 的回覆。"
        self._called = False
        self._response_delay = 0
    
    def set_response(self, prompt_contains: str, response: str) -> None:
        """
        設定特定 prompt 的回應
        
        Args:
            prompt_contains: prompt 包含的文字
            response: 回應內容
        """
        self.responses[prompt_contains] = response
    
    def set_response_delay(self, seconds: int) -> None:
        """設定回應延遲秒數"""
        self._response_delay = seconds
    
    def was_called(self) -> bool:
        """檢查是否被呼叫過"""
        return self._called
    
    async def chat_completion(self, messages: list[dict]) -> dict:
        """
        模擬 Chat Completion API
        
        Args:
            messages: 訊息列表
        
        Returns:
            dict: OpenAI API 格式的回應
        """
        self._called = True
        
        # 模擬延遲
        if self._response_delay > 0:
            import asyncio
            await asyncio.sleep(self._response_delay)
        
        # 取得最後一則用戶訊息
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # 查找對應的回應
        response_text = self.default_response
        for key, value in self.responses.items():
            if key in user_message:
                response_text = value
                break
        
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }


# =============================================================================
# 匯出
# =============================================================================

# 別名（用於向後兼容）
MockGoogleCalendarService = MockGoogleCalendarAPI
MockNotionService = MockNotionAPI
MockGitHubService = MockGitHubAPI
MockOpenAIService = MockOpenAIAPI

__all__ = [
    "MockCalendarEvent",
    "MockGoogleCalendarAPI",
    "MockGoogleCalendarService",
    "MockNotionPage",
    "MockNotionAPI",
    "MockNotionService",
    "MockGitHubIssue",
    "MockGitHubAPI",
    "MockGitHubService",
    "MockWeatherData",
    "MockWeatherAPI",
    "MockOpenAIAPI",
    "MockOpenAIService",
]
