# LINE 自動化流程引擎 - LINE Webhook Mock 工具
# LINE Workflow Automation Engine - LINE Webhook Mock Utilities
"""
LINE Webhook Mock 工具
======================

此模組提供 LINE Webhook 測試所需的 Mock 工具。

包含：
1. Webhook 事件建立器
2. 簽名產生器
3. 回覆驗證器
"""

import base64
import hashlib
import hmac
import json
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MockLineEvent:
    """
    Mock LINE 事件
    
    用於建立測試用的 LINE Webhook 事件。
    """
    event_type: str = "message"
    user_id: str = "U_test_user_001"
    reply_token: str = "test_reply_token"
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    message_type: str = "text"
    message_text: str = ""
    message_id: str = "12345678901234"
    postback_data: str = ""
    
    def to_dict(self) -> dict:
        """
        轉換為字典格式
        
        Returns:
            dict: LINE 事件字典
        """
        event = {
            "type": self.event_type,
            "timestamp": self.timestamp,
            "source": {
                "type": "user",
                "userId": self.user_id
            },
            "replyToken": self.reply_token,
        }
        
        if self.event_type == "message":
            event["message"] = {
                "type": self.message_type,
                "id": self.message_id,
            }
            if self.message_type == "text":
                event["message"]["text"] = self.message_text
                
        elif self.event_type == "postback":
            event["postback"] = {
                "data": self.postback_data
            }
        
        return event


class MockLineWebhook:
    """
    Mock LINE Webhook 建立器
    
    用於建立完整的 Webhook 請求，包含簽名。
    
    使用範例：
        webhook = MockLineWebhook(secret="your_secret")
        body, signature = webhook.create_text_message("Hello!")
    """
    
    def __init__(self, secret: str = "test_secret"):
        """
        初始化 Mock Webhook
        
        Args:
            secret: LINE Channel Secret
        """
        self.secret = secret
        self.destination = "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    
    def _calculate_signature(self, body: str) -> str:
        """
        計算 Webhook 簽名
        
        Args:
            body: 請求主體 JSON 字串
        
        Returns:
            str: Base64 編碼的簽名
        """
        hash_value = hmac.new(
            self.secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256
        ).digest()
        return base64.b64encode(hash_value).decode("utf-8")
    
    def create_request(self, events: list[MockLineEvent]) -> tuple[str, str]:
        """
        建立 Webhook 請求
        
        Args:
            events: 事件列表
        
        Returns:
            tuple[str, str]: (請求主體 JSON, 簽名)
        """
        body_dict = {
            "destination": self.destination,
            "events": [event.to_dict() for event in events]
        }
        body = json.dumps(body_dict)
        signature = self._calculate_signature(body)
        return body, signature
    
    def create_text_message(
        self,
        text: str,
        user_id: str = "U_test_user_001",
    ) -> tuple[str, str]:
        """
        建立文字訊息 Webhook 請求
        
        Args:
            text: 訊息文字
            user_id: 用戶 ID
        
        Returns:
            tuple[str, str]: (請求主體 JSON, 簽名)
        """
        event = MockLineEvent(
            event_type="message",
            user_id=user_id,
            message_type="text",
            message_text=text,
        )
        return self.create_request([event])
    
    def create_follow_event(
        self,
        user_id: str = "U_test_user_001",
    ) -> tuple[str, str]:
        """
        建立加入好友 Webhook 請求
        
        Args:
            user_id: 用戶 ID
        
        Returns:
            tuple[str, str]: (請求主體 JSON, 簽名)
        """
        event = MockLineEvent(
            event_type="follow",
            user_id=user_id,
        )
        return self.create_request([event])
    
    def create_postback_event(
        self,
        data: str,
        user_id: str = "U_test_user_001",
    ) -> tuple[str, str]:
        """
        建立 Postback Webhook 請求
        
        Args:
            data: Postback 資料
            user_id: 用戶 ID
        
        Returns:
            tuple[str, str]: (請求主體 JSON, 簽名)
        """
        event = MockLineEvent(
            event_type="postback",
            user_id=user_id,
            postback_data=data,
        )
        return self.create_request([event])


class LineWebhookMock:
    """
    LINE Webhook Mock（相容於 BDD Step 定義）
    
    提供簡化的 API 用於 BDD 測試。
    
    使用範例：
        mock = LineWebhookMock()
        body = mock.create_text_message_event("U123", "Hello")
        headers = mock.create_signature_header(body)
    """
    
    def __init__(self, secret: str = "test_secret"):
        """初始化"""
        self.secret = secret
        self.destination = "Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    
    def _calculate_signature(self, body_str: str) -> str:
        """計算簽名"""
        hash_value = hmac.new(
            self.secret.encode("utf-8"),
            body_str.encode("utf-8") if isinstance(body_str, str) else body_str,
            hashlib.sha256
        ).digest()
        return base64.b64encode(hash_value).decode("utf-8")
    
    def create_text_message_event(
        self,
        user_id: str = "U_test_user_001",
        text: str = "",
        reply_token: str = "test_reply_token",
    ) -> dict:
        """
        建立文字訊息事件（返回 dict）
        
        Args:
            user_id: 用戶 ID
            text: 訊息文字
            reply_token: 回覆 Token
        
        Returns:
            dict: Webhook 請求主體
        """
        return {
            "destination": self.destination,
            "events": [
                {
                    "type": "message",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "source": {
                        "type": "user",
                        "userId": user_id
                    },
                    "replyToken": reply_token,
                    "message": {
                        "type": "text",
                        "id": "12345678901234",
                        "text": text
                    }
                }
            ]
        }
    
    def create_signature_header(self, body: dict | str) -> dict:
        """
        建立包含簽名的 HTTP headers
        
        Args:
            body: 請求主體（dict 或 JSON string）
        
        Returns:
            dict: HTTP headers
        """
        if isinstance(body, dict):
            body_str = json.dumps(body)
        else:
            body_str = body
        
        signature = self._calculate_signature(body_str)
        return {
            "Content-Type": "application/json",
            "X-Line-Signature": signature
        }


class MockLineReplyRecorder:
    """
    Mock LINE 回覆記錄器
    
    用於記錄和驗證發送的 LINE 回覆訊息。
    
    使用範例：
        recorder = MockLineReplyRecorder()
        # ... 執行測試 ...
        assert recorder.has_reply_with_text("Hello!")
    """
    
    def __init__(self):
        """初始化記錄器"""
        self.replies: list[dict] = []
        self.push_messages: list[dict] = []
    
    def record_reply(self, reply_token: str, messages: list[dict]) -> None:
        """
        記錄回覆訊息
        
        Args:
            reply_token: 回覆 Token
            messages: 訊息列表
        """
        self.replies.append({
            "reply_token": reply_token,
            "messages": messages,
        })
    
    def record_push(self, user_id: str, messages: list[dict]) -> None:
        """
        記錄推送訊息
        
        Args:
            user_id: 用戶 ID
            messages: 訊息列表
        """
        self.push_messages.append({
            "user_id": user_id,
            "messages": messages,
        })
    
    def get_last_reply(self) -> dict | None:
        """取得最後一則回覆"""
        return self.replies[-1] if self.replies else None
    
    def get_last_reply_text(self) -> str | None:
        """取得最後一則回覆的文字"""
        last = self.get_last_reply()
        if last and last["messages"]:
            first_msg = last["messages"][0]
            if first_msg.get("type") == "text":
                return first_msg.get("text")
        return None
    
    def has_reply_with_text(self, text: str) -> bool:
        """
        檢查是否有包含特定文字的回覆
        
        Args:
            text: 要檢查的文字
        
        Returns:
            bool: 是否有符合的回覆
        """
        for reply in self.replies:
            for msg in reply["messages"]:
                if msg.get("type") == "text" and text in msg.get("text", ""):
                    return True
        return False
    
    def clear(self) -> None:
        """清除所有記錄"""
        self.replies.clear()
        self.push_messages.clear()


# =============================================================================
# 匯出
# =============================================================================

__all__ = [
    "MockLineEvent",
    "MockLineWebhook",
    "LineWebhookMock",
    "MockLineReplyRecorder",
]
