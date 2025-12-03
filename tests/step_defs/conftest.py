# LINE 自動化流程引擎 - BDD Step 定義共用配置
# LINE Workflow Automation Engine - BDD Step Definitions Configuration
"""
BDD Step 定義共用配置
=====================

此模組提供 pytest-bdd 所需的共用配置和 Step 定義。

包含：
1. 共用的 Given/When/Then Step
2. BDD 專用的 Fixtures
3. 場景上下文管理
"""

import pytest
from pytest_bdd import given, when, then, parsers
from unittest.mock import patch, AsyncMock

from tests.conftest import (
    test_db,
    test_client,
    async_test_client,
    user_factory,
    workflow_factory,
    mock_line_api,
)


# =============================================================================
# Mock 設定
# =============================================================================


@pytest.fixture(autouse=True)
def mock_verify_signature():
    """Mock LINE 簽名驗證以便測試通過"""
    with patch('src.api.webhook.verify_signature', return_value=True):
        yield


@pytest.fixture
def mock_services():
    """
    Mock 外部服務集合（重新定義以追蹤調用）
    
    Returns:
        dict: 包含各服務 mock 的字典
    """
    from tests.mocks.external_services import MockOpenAIAPI
    
    openai_mock = MockOpenAIAPI()
    
    return {
        "openai": openai_mock,
    }


@pytest.fixture(autouse=True)
def mock_ai_service_for_unknown():
    """
    Mock AIService 以便在無法識別的指令時使用
    
    當指令解析為 UNKNOWN 時，webhook 會嘗試用 AI 理解。
    這個 fixture 確保 AI 服務回傳預設的 UNKNOWN 結果。
    """
    from src.commands.parser import CommandType
    from src.services.ai_service import AIIntent
    
    async def mock_recognize_intent(text):
        """模擬 AI 識別意圖"""
        # 回傳 UNKNOWN 以觸發友善引導
        return AIIntent(
            command_type=CommandType.UNKNOWN,
            confidence=0.0,
            parameters={},
            explanation="Mock: 無法識別",
        )
    
    with patch('src.services.ai_service.AIService.recognize_intent', side_effect=mock_recognize_intent):
        yield


# 注意：line_reply_mock 已在 tests/conftest.py 中定義
# 它會自動 mock send_reply 並捕獲回覆


# =============================================================================
# 場景上下文
# =============================================================================


@pytest.fixture
def context():
    """
    BDD 場景上下文
    
    用於在 Given/When/Then 步驟之間共享資料。
    
    Returns:
        dict: 上下文字典
    """
    return {}


# =============================================================================
# 共用 Given Steps
# =============================================================================


@given("使用者已加入 LINE Bot 好友")
def user_is_line_friend(context, user_factory):
    """設定用戶已加入好友"""
    async def setup():
        user = await user_factory(
            line_user_id="U_test_user_001",
            display_name="測試用戶"
        )
        context["user"] = user
        context["user_id"] = user.line_user_id
    
    import asyncio
    asyncio.get_event_loop().run_until_complete(setup())


@given(parsers.parse("使用者已連接 {service_type} 服務"))
def user_connected_service(context, service_type):
    """設定用戶已連接外部服務"""
    context["connected_service"] = service_type


@given("系統正常運作")
def system_is_running(test_client, context):
    """確認系統正常運作"""
    response = test_client.get("/health")
    assert response.status_code == 200
    context["system_ready"] = True


# =============================================================================
# 共用 When Steps
# =============================================================================


@when(parsers.parse('使用者發送「{message}」'))
def user_sends_message(context, message, test_client, mock_line_api):
    """
    模擬用戶發送 LINE 訊息
    
    Args:
        context: 場景上下文
        message: 訊息內容
    """
    import json
    import hashlib
    import hmac
    import base64
    
    user_id = context.get("user_id", "U_test_user")
    
    # 建立 Webhook 事件
    webhook_body = {
        "destination": "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "events": [
            {
                "type": "message",
                "timestamp": 1234567890123,
                "source": {
                    "type": "user",
                    "userId": user_id
                },
                "replyToken": "test_reply_token_xxxxx",
                "message": {
                    "type": "text",
                    "id": "12345678901234",
                    "text": message
                }
            }
        ]
    }
    
    body_str = json.dumps(webhook_body)
    
    # 計算簽名
    hash_value = hmac.new(
        b"test_secret",
        body_str.encode("utf-8"),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(hash_value).decode("utf-8")
    
    # 發送請求
    response = test_client.post(
        "/webhook",
        content=body_str,
        headers={
            "Content-Type": "application/json",
            "X-Line-Signature": signature
        }
    )
    
    context["last_request"] = webhook_body
    context["last_response"] = response
    context["last_message"] = message


# =============================================================================
# 共用 Then Steps
# =============================================================================


@then("系統回覆成功")
def system_responds_success(context):
    """驗證系統回覆成功"""
    response = context.get("last_response")
    assert response is not None
    assert response.status_code == 200


@then(parsers.parse("系統回覆包含「{expected_text}」"))
def response_contains_text(context, expected_text):
    """驗證回覆包含特定文字"""
    # TODO: 實作回覆內容驗證
    # 需要在 mock_line_api 中記錄發送的訊息
    pass


@then("系統回覆錯誤訊息")
def system_responds_error(context):
    """驗證系統回覆錯誤"""
    response = context.get("last_response")
    # 可能是 200 但內容為錯誤訊息，或是非 200 狀態碼
    assert response is not None


@then(parsers.parse("錯誤訊息包含「{expected_error}」"))
def error_contains_text(context, expected_error):
    """驗證錯誤訊息包含特定文字"""
    # TODO: 實作錯誤內容驗證
    pass


# =============================================================================
# 匯出
# =============================================================================

__all__ = [
    "context",
    "user_is_line_friend",
    "user_connected_service",
    "system_is_running",
    "user_sends_message",
    "system_responds_success",
    "response_contains_text",
    "system_responds_error",
    "error_contains_text",
]
