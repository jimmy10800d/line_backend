# LINE 自動化流程引擎 - LINE Webhook 處理
# LINE Workflow Automation Engine - LINE Webhook Handler
"""
LINE Webhook 處理模組
=====================

此模組負責：
1. 接收 LINE 平台發送的 Webhook 事件
2. 驗證請求簽名
3. 解析訊息事件
4. 分派給對應的處理器

安全性：
- 使用 X-Line-Signature 驗證請求來源
- 驗證失敗的請求會被拒絕

資料表：webhooks
"""

import hashlib
import hmac
import base64
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from src.config import logger, settings


# =============================================================================
# 路由器
# =============================================================================

router = APIRouter(tags=["Webhook"])


# =============================================================================
# 資料模型
# =============================================================================


class LineWebhookEvent(BaseModel):
    """LINE Webhook 事件基礎模型"""
    type: str
    timestamp: int
    source: dict
    replyToken: str | None = None
    message: dict | None = None


class LineWebhookRequest(BaseModel):
    """LINE Webhook 請求模型"""
    destination: str | None = None
    events: list[dict]


# =============================================================================
# 簽名驗證
# =============================================================================


def verify_signature(body: bytes, signature: str) -> bool:
    """
    驗證 LINE Webhook 簽名
    
    使用 HMAC-SHA256 演算法驗證請求來源。
    
    Args:
        body: 請求主體（原始 bytes）
        signature: X-Line-Signature 標頭值
    
    Returns:
        bool: 簽名是否有效
    
    安全性：
        - 使用 hmac.compare_digest 避免時序攻擊
        - Channel Secret 必須保密
    """
    if not settings.line_channel_secret:
        logger.warning("LINE_CHANNEL_SECRET 未設定，跳過簽名驗證")
        return True  # 開發環境可能未設定
    
    # 計算預期簽名
    hash_value = hmac.new(
        settings.line_channel_secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash_value).decode("utf-8")
    
    # 安全比較（避免時序攻擊）
    return hmac.compare_digest(signature, expected_signature)


# =============================================================================
# Webhook 端點
# =============================================================================


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    x_line_signature: str = Header(alias="X-Line-Signature", default=""),
) -> dict:
    """
    LINE Webhook 端點
    
    接收 LINE 平台發送的訊息事件並處理。
    
    Args:
        request: HTTP 請求物件
        x_line_signature: LINE 簽名標頭
    
    Returns:
        dict: 處理結果
    
    Raises:
        HTTPException: 簽名驗證失敗時
    
    安全性：
        - 驗證 X-Line-Signature
        - 拒絕無效簽名的請求
    """
    # 取得請求主體
    body = await request.body()
    
    # 驗證簽名
    if not verify_signature(body, x_line_signature):
        logger.warning("LINE Webhook 簽名驗證失敗")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    
    # 解析 JSON
    try:
        data = await request.json()
        webhook_request = LineWebhookRequest(**data)
    except Exception as e:
        logger.error(f"解析 Webhook 請求失敗：{e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body"
        )
    
    # 處理每個事件
    for event in webhook_request.events:
        await process_event(event)
    
    return {"status": "ok"}


# =============================================================================
# 事件處理
# =============================================================================


async def process_event(event: dict) -> None:
    """
    處理單一 LINE 事件
    
    根據事件類型分派給對應的處理器。
    
    Args:
        event: LINE 事件字典
    
    支援的事件類型：
        - message: 訊息事件
        - follow: 加入好友事件
        - unfollow: 封鎖事件
        - postback: Postback 事件
    """
    event_type = event.get("type", "unknown")
    
    logger.info(
        "收到 LINE 事件",
        event_type=event_type,
        source=event.get("source", {}),
    )
    
    try:
        if event_type == "message":
            await handle_message_event(event)
        elif event_type == "follow":
            await handle_follow_event(event)
        elif event_type == "unfollow":
            await handle_unfollow_event(event)
        elif event_type == "postback":
            await handle_postback_event(event)
        else:
            logger.debug(f"忽略未支援的事件類型：{event_type}")
            
    except Exception as e:
        logger.error(f"處理事件失敗：{e}", event_type=event_type)
        # 不拋出例外，避免影響其他事件處理


async def handle_message_event(event: dict) -> None:
    """
    處理訊息事件
    
    解析訊息內容並執行對應的指令。
    
    Args:
        event: 訊息事件字典
    
    訊息類型：
        - text: 文字訊息（主要處理對象）
        - image: 圖片訊息
        - sticker: 貼圖訊息
        - location: 位置訊息
    """
    message = event.get("message", {})
    message_type = message.get("type", "unknown")
    reply_token = event.get("replyToken")
    source = event.get("source", {})
    user_id = source.get("userId", "unknown")
    
    logger.info(
        "收到訊息",
        message_type=message_type,
        user_id=user_id,
    )
    
    if message_type == "text":
        text = message.get("text", "")
        await handle_text_message(user_id, text, reply_token)
    else:
        logger.debug(f"忽略非文字訊息：{message_type}")


async def handle_text_message(
    user_id: str,
    text: str,
    reply_token: str | None
) -> None:
    """
    處理文字訊息
    
    解析文字內容，判斷是指令還是自然語言，
    並執行對應的處理邏輯。
    
    Args:
        user_id: LINE 用戶 ID
        text: 訊息文字
        reply_token: 回覆用的 Token
    
    處理流程：
        1. 檢查是否為空白訊息
        2. 解析指令類型
        3. 執行對應的處理器
        4. 如果無法識別，使用 AI 理解意圖
        5. 回覆處理結果
    """
    # 忽略空白訊息
    if not text or not text.strip():
        logger.debug("忽略空白訊息")
        return
    
    # 檢查訊息長度
    if len(text) > 1000:
        if reply_token:
            await send_reply(reply_token, "訊息太長，請簡化您的請求")
        return
    
    logger.info(f"處理文字訊息：{text[:50]}...")
    
    # 解析指令
    from src.commands.parser import CommandParser, CommandType, ParsedCommand
    from src.commands.handlers.base import get_handler
    
    parser = CommandParser()
    parsed = parser.parse(text)
    
    # 取得處理器
    handler = get_handler(parsed.command_type)
    
    if handler:
        # 執行處理器
        try:
            result = await handler.handle(user_id, parsed)
            if reply_token and result and result.message:
                await send_reply(reply_token, result.message)
        except Exception as e:
            logger.error(f"處理器執行失敗：{e}")
            if reply_token:
                await send_reply(reply_token, "處理時發生錯誤，請稍後再試")
    else:
        # 未知指令，嘗試使用 AI 理解
        if parsed.command_type == CommandType.UNKNOWN:
            try:
                from src.services.ai_service import AIService
                ai_service = AIService()
                intent = await ai_service.recognize_intent(text)
                
                if intent and intent.command_type != CommandType.UNKNOWN:
                    # AI 識別到指令，使用識別的參數建立新的 ParsedCommand
                    new_parsed = ParsedCommand(
                        command_type=intent.command_type,
                        raw_text=text,
                        parameters=intent.parameters,
                    )
                    new_handler = get_handler(new_parsed.command_type)
                    if new_handler:
                        result = await new_handler.handle(user_id, new_parsed)
                        if reply_token and result and result.message:
                            await send_reply(reply_token, result.message)
                        return
                
                # AI 無法識別，回覆友善引導
                if reply_token:
                    guidance = (
                        "我不太確定您的意思 🤔\n\n"
                        "試試以下指令：\n"
                        "• 「幫助」- 查看所有指令\n"
                        "• 「待辦 買牛奶」- 新增待辦\n"
                        "• 「天氣 台北」- 查詢天氣\n"
                        "• 「提醒 開會 下午3點」- 設定提醒"
                    )
                    await send_reply(reply_token, guidance)
            except Exception as e:
                logger.error(f"AI 理解失敗：{e}")
                if reply_token:
                    await send_reply(
                        reply_token,
                        "我不太確定您的意思，請試試輸入「幫助」查看可用指令"
                    )


async def handle_follow_event(event: dict) -> None:
    """
    處理加入好友事件
    
    當用戶加入 LINE Bot 好友時：
    1. 建立或更新用戶資料
    2. 發送歡迎訊息
    
    Args:
        event: 加入好友事件字典
    """
    source = event.get("source", {})
    user_id = source.get("userId", "unknown")
    reply_token = event.get("replyToken")
    
    logger.info(f"新用戶加入：{user_id}")
    
    # TODO: 建立用戶資料（T008）
    
    # 發送歡迎訊息
    welcome_message = """
🎉 歡迎使用 LINE 自動化流程引擎！

這是一個個人自動化助手，可以透過 LINE 執行各種自動化任務。

📌 快速開始：
• 輸入 /help 查看所有可用指令
• 輸入 /weather 台北 查詢天氣
• 輸入 /calendar today 查看今日行程

需要幫助嗎？隨時輸入 /help！
    """.strip()
    
    if reply_token:
        await send_reply(reply_token, welcome_message)


async def handle_unfollow_event(event: dict) -> None:
    """
    處理封鎖事件
    
    當用戶封鎖 LINE Bot 時記錄日誌。
    注意：用戶資料不會被刪除，以便用戶重新加入時恢復。
    
    Args:
        event: 封鎖事件字典
    """
    source = event.get("source", {})
    user_id = source.get("userId", "unknown")
    
    logger.info(f"用戶封鎖：{user_id}")


async def handle_postback_event(event: dict) -> None:
    """
    處理 Postback 事件
    
    當用戶點擊按鈕或快速回覆時觸發。
    
    Args:
        event: Postback 事件字典
    """
    postback = event.get("postback", {})
    data = postback.get("data", "")
    source = event.get("source", {})
    user_id = source.get("userId", "unknown")
    reply_token = event.get("replyToken")
    
    logger.info(f"收到 Postback：{data}", user_id=user_id)
    
    # TODO: 處理 Postback 資料


# =============================================================================
# 回覆訊息
# =============================================================================


async def send_reply(reply_token: str, text: str) -> None:
    """
    發送回覆訊息
    
    使用 LINE Messaging API 發送回覆訊息。
    
    Args:
        reply_token: 回覆用的 Token
        text: 回覆文字
    
    注意：
        - Reply Token 只能使用一次
        - Reply Token 在一定時間後過期
    """
    if not settings.line_channel_access_token:
        logger.warning("LINE_CHANNEL_ACCESS_TOKEN 未設定，無法發送回覆")
        return
    
    import httpx
    
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.line_channel_access_token}",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": text,
            }
        ],
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code != 200:
                logger.error(
                    f"發送回覆失敗：{response.status_code}",
                    body=response.text,
                )
            else:
                logger.debug("回覆訊息發送成功")
                
    except Exception as e:
        logger.error(f"發送回覆時發生錯誤：{e}")


# =============================================================================
# 匯出
# =============================================================================

__all__ = [
    "router",
    "verify_signature",
    "handle_webhook",
    "send_reply",
]
