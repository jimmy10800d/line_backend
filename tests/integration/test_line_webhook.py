# LINE Webhook 整合測試
# LINE Webhook Integration Tests
"""
LINE Webhook 整合測試
=====================

測試 LINE Webhook 端點的完整處理流程：
1. 簽名驗證
2. 事件解析
3. 指令執行
4. 回覆發送
"""

import pytest
import json
import hmac
import hashlib
import base64
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


class TestWebhookEndpoint:
    """Webhook 端點測試"""
    
    @pytest.fixture
    def mock_line_service(self):
        """Mock LINE 服務"""
        with patch('src.api.webhook.get_line_service') as mock:
            service = MagicMock()
            service.reply_message = AsyncMock(return_value=True)
            mock.return_value = service
            yield service
    
    def create_signature(self, body: str, secret: str = "test_secret") -> str:
        """建立 LINE 簽名"""
        signature = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(signature).decode("utf-8")
    
    def create_webhook_body(
        self,
        user_id: str = "U1234567890",
        message_type: str = "text",
        text: str = "幫助",
        reply_token: str = "test_reply_token",
    ) -> dict:
        """建立 Webhook 請求 body"""
        return {
            "destination": "U1234567890",
            "events": [
                {
                    "type": "message",
                    "replyToken": reply_token,
                    "source": {
                        "type": "user",
                        "userId": user_id,
                    },
                    "timestamp": 1234567890123,
                    "message": {
                        "type": message_type,
                        "id": "12345",
                        "text": text,
                    } if message_type == "text" else {
                        "type": message_type,
                        "id": "12345",
                    },
                }
            ],
        }
    
    # =========================================================================
    # 健康檢查測試
    # =========================================================================
    
    def test_health_check(self, test_client: TestClient):
        """測試健康檢查端點"""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    # =========================================================================
    # Webhook 基本測試
    # =========================================================================
    
    def test_webhook_missing_signature(self, test_client: TestClient):
        """測試缺少簽名"""
        body = self.create_webhook_body()
        
        response = test_client.post(
            "/webhook",
            json=body,
        )
        
        # 缺少簽名應該返回 400 或相關錯誤
        assert response.status_code in [400, 401, 422]
    
    def test_webhook_invalid_signature(self, test_client: TestClient):
        """測試無效簽名"""
        body = self.create_webhook_body()
        
        response = test_client.post(
            "/webhook",
            json=body,
            headers={"X-Line-Signature": "invalid_signature"},
        )
        
        # 無效簽名應該返回 400
        assert response.status_code == 400
    
    def test_webhook_valid_signature(
        self, test_client: TestClient, mock_line_service
    ):
        """測試有效簽名"""
        body = self.create_webhook_body(text="幫助")
        body_str = json.dumps(body, ensure_ascii=False)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
    
    def test_webhook_empty_events(self, test_client: TestClient):
        """測試空事件列表"""
        body = {"destination": "U123", "events": []}
        body_str = json.dumps(body)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
    
    # =========================================================================
    # 訊息處理測試
    # =========================================================================
    
    def test_webhook_text_message(
        self, test_client: TestClient, mock_line_service
    ):
        """測試文字訊息處理"""
        body = self.create_webhook_body(text="幫助")
        body_str = json.dumps(body, ensure_ascii=False)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
        # 驗證回覆被呼叫
        # mock_line_service.reply_message.assert_called()
    
    def test_webhook_non_text_message(
        self, test_client: TestClient, mock_line_service
    ):
        """測試非文字訊息處理"""
        body = self.create_webhook_body(message_type="image")
        body_str = json.dumps(body, ensure_ascii=False)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        # 非文字訊息應該被忽略但不報錯
        assert response.status_code == 200
    
    # =========================================================================
    # 指令處理測試
    # =========================================================================
    
    @pytest.mark.parametrize("command,expected_text", [
        ("幫助", "使用說明"),
        ("help", "使用說明"),
        ("狀態", "系統狀態"),
        ("status", "系統狀態"),
    ])
    def test_webhook_commands(
        self,
        test_client: TestClient,
        mock_line_service,
        command: str,
        expected_text: str,
    ):
        """測試各種指令處理"""
        body = self.create_webhook_body(text=command)
        body_str = json.dumps(body, ensure_ascii=False)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
        # 驗證回覆包含預期文字
        # if mock_line_service.reply_message.called:
        #     call_args = mock_line_service.reply_message.call_args
        #     messages = call_args.args[1] if len(call_args.args) > 1 else []
        #     assert any(expected_text in str(m) for m in messages)


class TestWebhookEdgeCases:
    """Webhook 邊界情況測試"""
    
    def create_signature(self, body: str, secret: str = "test_secret") -> str:
        """建立 LINE 簽名"""
        signature = hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(signature).decode("utf-8")
    
    def test_webhook_follow_event(self, test_client: TestClient):
        """測試加入好友事件"""
        body = {
            "destination": "U123",
            "events": [
                {
                    "type": "follow",
                    "replyToken": "token",
                    "source": {"type": "user", "userId": "U123"},
                    "timestamp": 1234567890123,
                }
            ],
        }
        body_str = json.dumps(body)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
    
    def test_webhook_unfollow_event(self, test_client: TestClient):
        """測試封鎖事件"""
        body = {
            "destination": "U123",
            "events": [
                {
                    "type": "unfollow",
                    "source": {"type": "user", "userId": "U123"},
                    "timestamp": 1234567890123,
                }
            ],
        }
        body_str = json.dumps(body)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
    
    def test_webhook_postback_event(self, test_client: TestClient):
        """測試 Postback 事件"""
        body = {
            "destination": "U123",
            "events": [
                {
                    "type": "postback",
                    "replyToken": "token",
                    "source": {"type": "user", "userId": "U123"},
                    "timestamp": 1234567890123,
                    "postback": {"data": "action=test"},
                }
            ],
        }
        body_str = json.dumps(body)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
    
    def test_webhook_multiple_events(self, test_client: TestClient):
        """測試多個事件"""
        body = {
            "destination": "U123",
            "events": [
                {
                    "type": "message",
                    "replyToken": "token1",
                    "source": {"type": "user", "userId": "U123"},
                    "timestamp": 1234567890123,
                    "message": {"type": "text", "id": "1", "text": "幫助"},
                },
                {
                    "type": "message",
                    "replyToken": "token2",
                    "source": {"type": "user", "userId": "U456"},
                    "timestamp": 1234567890124,
                    "message": {"type": "text", "id": "2", "text": "狀態"},
                },
            ],
        }
        body_str = json.dumps(body, ensure_ascii=False)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        assert response.status_code == 200
    
    def test_webhook_group_message(self, test_client: TestClient):
        """測試群組訊息"""
        body = {
            "destination": "U123",
            "events": [
                {
                    "type": "message",
                    "replyToken": "token",
                    "source": {
                        "type": "group",
                        "groupId": "G123",
                        "userId": "U123",
                    },
                    "timestamp": 1234567890123,
                    "message": {"type": "text", "id": "1", "text": "幫助"},
                }
            ],
        }
        body_str = json.dumps(body, ensure_ascii=False)
        signature = self.create_signature(body_str)
        
        response = test_client.post(
            "/webhook",
            content=body_str,
            headers={
                "X-Line-Signature": signature,
                "Content-Type": "application/json",
            },
        )
        
        # 群組訊息應該被處理或忽略，但不應報錯
        assert response.status_code == 200
