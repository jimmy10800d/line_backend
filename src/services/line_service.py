# LINE 自動化流程引擎 - LINE 訊息服務
# LINE Workflow Automation Engine - LINE Message Service
"""
LINE 訊息服務模組
=================

此模組提供 LINE Messaging API 的封裝，負責：
1. 發送各類型訊息（文字、圖片、按鈕等）
2. 管理訊息佇列
3. 處理 Rate Limit

使用方式：
    from src.services.line_service import LineService
    
    service = LineService()
    await service.send_text_message(user_id, "Hello!")
"""

from typing import Any

import httpx

from src.config import logger, settings


class LineService:
    """
    LINE 訊息服務
    
    封裝 LINE Messaging API 的各種操作。
    
    Attributes:
        access_token: LINE Channel Access Token
        api_base_url: LINE API 基礎 URL
    
    使用範例：
        service = LineService()
        
        # 發送文字訊息
        await service.send_text_message(user_id, "Hello!")
        
        # 發送帶按鈕的訊息
        await service.send_buttons_message(
            user_id,
            title="選擇操作",
            text="請選擇要執行的操作",
            actions=[
                {"type": "message", "label": "查看天氣", "text": "/weather"},
                {"type": "message", "label": "查看行程", "text": "/calendar today"},
            ]
        )
    """
    
    def __init__(self, access_token: str | None = None):
        """
        初始化 LINE 訊息服務
        
        Args:
            access_token: LINE Channel Access Token，如未提供則從環境變數讀取
        """
        self.access_token = access_token or settings.line_channel_access_token
        self.api_base_url = "https://api.line.me/v2/bot"
    
    @property
    def _headers(self) -> dict[str, str]:
        """取得 HTTP 請求標頭"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }
    
    async def _send_request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
    ) -> dict | None:
        """
        發送 HTTP 請求到 LINE API
        
        Args:
            method: HTTP 方法（GET、POST 等）
            endpoint: API 端點（相對路徑）
            data: 請求資料
        
        Returns:
            dict | None: 回應資料，錯誤時返回 None
        """
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=self._headers,
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    return response.json() if response.text else {}
                else:
                    logger.error(
                        f"LINE API 請求失敗",
                        status_code=response.status_code,
                        endpoint=endpoint,
                        response=response.text,
                    )
                    return None
                    
        except Exception as e:
            logger.error(f"LINE API 請求錯誤：{e}", endpoint=endpoint)
            return None
    
    # =========================================================================
    # 發送訊息
    # =========================================================================
    
    async def push_message(self, user_id: str, messages: list[dict]) -> bool:
        """
        主動推送訊息給用戶
        
        Args:
            user_id: LINE 用戶 ID
            messages: 訊息列表（最多 5 則）
        
        Returns:
            bool: 是否發送成功
        
        注意：
            - Push Message 有發送數量限制
            - 免費方案每月 500 則
        """
        data = {
            "to": user_id,
            "messages": messages[:5],  # 最多 5 則
        }
        
        result = await self._send_request("POST", "/message/push", data)
        return result is not None
    
    async def reply_message(self, reply_token: str, messages: list[dict]) -> bool:
        """
        回覆訊息
        
        Args:
            reply_token: 回覆用的 Token
            messages: 訊息列表（最多 5 則）
        
        Returns:
            bool: 是否發送成功
        
        注意：
            - Reply Token 只能使用一次
            - Reply Token 在一定時間後過期
        """
        data = {
            "replyToken": reply_token,
            "messages": messages[:5],
        }
        
        result = await self._send_request("POST", "/message/reply", data)
        return result is not None
    
    async def send_text_message(
        self,
        user_id: str,
        text: str,
        reply_token: str | None = None,
    ) -> bool:
        """
        發送文字訊息
        
        Args:
            user_id: LINE 用戶 ID
            text: 訊息文字
            reply_token: 回覆 Token（如有提供則使用回覆，否則使用推送）
        
        Returns:
            bool: 是否發送成功
        """
        message = {
            "type": "text",
            "text": text,
        }
        
        if reply_token:
            return await self.reply_message(reply_token, [message])
        else:
            return await self.push_message(user_id, [message])
    
    async def send_buttons_message(
        self,
        user_id: str,
        title: str,
        text: str,
        actions: list[dict],
        thumbnail_url: str | None = None,
        reply_token: str | None = None,
    ) -> bool:
        """
        發送按鈕模板訊息
        
        Args:
            user_id: LINE 用戶 ID
            title: 標題
            text: 說明文字
            actions: 按鈕動作列表（最多 4 個）
            thumbnail_url: 縮圖 URL
            reply_token: 回覆 Token
        
        Returns:
            bool: 是否發送成功
        
        Actions 格式：
            [
                {"type": "message", "label": "按鈕文字", "text": "發送的訊息"},
                {"type": "uri", "label": "開啟連結", "uri": "https://example.com"},
                {"type": "postback", "label": "Postback", "data": "action=xxx"},
            ]
        """
        template = {
            "type": "buttons",
            "title": title[:40],  # 標題限制 40 字
            "text": text[:160],  # 文字限制 160 字
            "actions": actions[:4],  # 最多 4 個按鈕
        }
        
        if thumbnail_url:
            template["thumbnailImageUrl"] = thumbnail_url
        
        message = {
            "type": "template",
            "altText": title,
            "template": template,
        }
        
        if reply_token:
            return await self.reply_message(reply_token, [message])
        else:
            return await self.push_message(user_id, [message])
    
    async def send_confirm_message(
        self,
        user_id: str,
        text: str,
        yes_action: dict,
        no_action: dict,
        reply_token: str | None = None,
    ) -> bool:
        """
        發送確認模板訊息
        
        Args:
            user_id: LINE 用戶 ID
            text: 確認文字
            yes_action: 確認按鈕動作
            no_action: 取消按鈕動作
            reply_token: 回覆 Token
        
        Returns:
            bool: 是否發送成功
        """
        message = {
            "type": "template",
            "altText": text,
            "template": {
                "type": "confirm",
                "text": text[:240],  # 限制 240 字
                "actions": [yes_action, no_action],
            },
        }
        
        if reply_token:
            return await self.reply_message(reply_token, [message])
        else:
            return await self.push_message(user_id, [message])
    
    async def send_quick_reply(
        self,
        user_id: str,
        text: str,
        items: list[dict],
        reply_token: str | None = None,
    ) -> bool:
        """
        發送快速回覆訊息
        
        Args:
            user_id: LINE 用戶 ID
            text: 訊息文字
            items: 快速回覆項目列表（最多 13 個）
            reply_token: 回覆 Token
        
        Returns:
            bool: 是否發送成功
        
        Items 格式：
            [
                {
                    "type": "action",
                    "action": {
                        "type": "message",
                        "label": "選項文字",
                        "text": "發送的訊息"
                    }
                },
            ]
        """
        message = {
            "type": "text",
            "text": text,
            "quickReply": {
                "items": items[:13],  # 最多 13 個
            },
        }
        
        if reply_token:
            return await self.reply_message(reply_token, [message])
        else:
            return await self.push_message(user_id, [message])
    
    # =========================================================================
    # 用戶資訊
    # =========================================================================
    
    async def get_user_profile(self, user_id: str) -> dict | None:
        """
        取得用戶個人資料
        
        Args:
            user_id: LINE 用戶 ID
        
        Returns:
            dict | None: 用戶資料，包含 displayName、pictureUrl 等
        """
        return await self._send_request("GET", f"/profile/{user_id}")


# =============================================================================
# 依賴注入函式
# =============================================================================

_line_service_instance: LineService | None = None


def get_line_service() -> LineService:
    """
    取得 LINE 服務實例（單例模式）
    
    Returns:
        LineService: LINE 服務實例
    """
    global _line_service_instance
    if _line_service_instance is None:
        _line_service_instance = LineService()
    return _line_service_instance


# =============================================================================
# 建立全域實例（向後相容）
# =============================================================================

line_service = LineService()


# =============================================================================
# 匯出
# =============================================================================

__all__ = ["LineService", "line_service", "get_line_service"]
