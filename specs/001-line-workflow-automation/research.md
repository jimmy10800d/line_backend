# Research Document: LINE 自動化流程引擎
# 研究文件

**Feature**: 001-line-workflow-automation  
**Date**: 2025-11-30  
**Status**: ✅ 完成

---

## 1. LINE Messaging API 研究

### 1.1 Webhook 機制

**Decision / 決定**: 使用 LINE Messaging API v2 + Webhook

**Rationale / 理由**:
- 官方推薦的整合方式
- 支援所有訊息類型
- 可處理群組和個人訊息
- 有完整的 Python SDK

**Best Practices / 最佳實踐**:
```python
# 驗證 Webhook 簽名
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError

handler = WebhookHandler(channel_secret)

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(400, "Invalid signature")
```

**Alternatives Considered / 考慮的替代方案**:
- Polling：效率低，不推薦
- LINE Login + Messaging：過於複雜

### 1.2 訊息回覆限制

| 限制項目 | 值 |
|----------|-----|
| Reply Token 有效期 | 約 1 分鐘 |
| 單次回覆最大訊息數 | 5 則 |
| Push 訊息免費額度 | 500 則/月 (Free plan) |
| 訊息長度 | 文字 5000 字元 |

**處理長時間任務策略**:
1. 收到訊息後立即回覆「處理中...」
2. 背景執行任務
3. 完成後使用 Push Message 回傳結果

---

## 2. OpenAI API 整合研究

### 2.1 選擇模型

**Decision / 決定**: 使用 GPT-4o-mini 作為預設，可設定切換

**Rationale / 理由**:
- 成本效益高（比 GPT-4 便宜 10 倍以上）
- 回應速度快
- 足夠處理指令理解任務

**Pricing (2024)**: 
- GPT-4o-mini: $0.15 / 1M input tokens, $0.60 / 1M output tokens
- GPT-4o: $2.50 / 1M input tokens, $10 / 1M output tokens

### 2.2 Prompt 設計

**System Prompt 範例**:
```
你是一個 LINE 自動化助手。用戶會用自然語言描述他們想執行的任務。

你的工作是：
1. 理解用戶意圖
2. 將請求轉換為結構化的任務指令
3. 如果意圖不明確，請求澄清

可用的任務類型：
- calendar: Google Calendar 操作 (查詢/新增行程)
- notion: Notion 操作 (搜尋/新增頁面)
- github: GitHub 操作 (查詢 Issue/PR)
- weather: 天氣查詢
- remind: 設定提醒

請以 JSON 格式回覆：
{
  "task_type": "calendar",
  "action": "query",
  "parameters": {"date": "today"}
}
```

### 2.3 錯誤處理

| 錯誤類型 | 處理策略 |
|----------|----------|
| Rate Limit | 實作指數退避重試 |
| Token 超限 | 截斷歷史對話 |
| API 錯誤 | 回退到關鍵字匹配 |

---

## 3. OAuth 2.0 實作研究

### 3.1 流程設計

**Decision / 決定**: 使用 Authorization Code Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  用戶    │     │  系統    │     │ 外部服務  │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     │ /connect google│                │
     │───────────────▶│                │
     │                │                │
     │ 授權連結       │                │
     │◀───────────────│                │
     │                │                │
     │ 用戶點擊授權   │                │
     │───────────────────────────────▶│
     │                │                │
     │                │ Callback + Code│
     │                │◀───────────────│
     │                │                │
     │                │ 交換 Token     │
     │                │───────────────▶│
     │                │                │
     │                │◀───────────────│
     │                │ Access Token   │
     │                │                │
     │ 授權完成       │                │
     │◀───────────────│                │
```

### 3.2 各服務 OAuth 設定

| 服務 | Authorization URL | Token URL | Scopes |
|------|-------------------|-----------|--------|
| Google | accounts.google.com/o/oauth2/v2/auth | oauth2.googleapis.com/token | calendar.readonly, calendar.events |
| Notion | api.notion.com/v1/oauth/authorize | api.notion.com/v1/oauth/token | (使用 Public Integration) |
| GitHub | github.com/login/oauth/authorize | github.com/login/oauth/access_token | repo, read:user |

### 3.3 Token 安全儲存

**Decision / 決定**: 使用 Fernet 對稱加密

```python
from cryptography.fernet import Fernet

# 加密 Token
fernet = Fernet(settings.encryption_key)
encrypted_token = fernet.encrypt(access_token.encode())

# 解密 Token
decrypted_token = fernet.decrypt(encrypted_token).decode()
```

---

## 4. 排程系統研究

### 4.1 選擇排程引擎

**Decision / 決定**: 使用 APScheduler

**Rationale / 理由**:
- Python 原生
- 支援多種觸發器（Cron, Interval, Date）
- 支援持久化（可存入資料庫）
- 輕量級，無需額外服務

**Alternatives Considered / 考慮的替代方案**:
- Celery + Redis: 過於複雜，需要額外服務
- Cron (OS level): 無法動態管理
- Airflow: 過於龐大

### 4.2 APScheduler 配置

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}

executors = {
    'default': AsyncIOExecutor()
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    timezone='Asia/Taipei'  # UTC+8
)
```

### 4.3 Cron 表達式支援

| 用戶輸入 | Cron 表達式 |
|----------|-------------|
| every day 09:00 | 0 9 * * * |
| every monday 10:00 | 0 10 * * 1 |
| every hour | 0 * * * * |
| every 30 minutes | */30 * * * * |

---

## 5. 外部服務 API 研究

### 5.1 Google Calendar API

| 操作 | API Endpoint | 方法 |
|------|--------------|------|
| 查詢行程 | /calendars/{id}/events | GET |
| 新增行程 | /calendars/{id}/events | POST |
| 刪除行程 | /calendars/{id}/events/{eventId} | DELETE |

**Rate Limit**: 1,000,000 requests/day

### 5.2 Notion API

| 操作 | API Endpoint | 方法 |
|------|--------------|------|
| 搜尋 | /search | POST |
| 查詢資料庫 | /databases/{id}/query | POST |
| 新增頁面 | /pages | POST |

**Rate Limit**: 3 requests/second

### 5.3 GitHub API

| 操作 | API Endpoint | 方法 |
|------|--------------|------|
| 查詢 Issues | /repos/{owner}/{repo}/issues | GET |
| 建立 Issue | /repos/{owner}/{repo}/issues | POST |
| 查詢 PRs | /repos/{owner}/{repo}/pulls | GET |

**Rate Limit**: 5,000 requests/hour (authenticated)

### 5.4 天氣 API

**Decision / 決定**: 使用中央氣象署開放資料 API

**Rationale / 理由**:
- 免費
- 台灣本地資料
- 中文回應

**API**: https://opendata.cwa.gov.tw/api/

---

## 6. 資料庫設計考量

### 6.1 選擇資料庫

**Decision / 決定**: SQLite + SQLAlchemy ORM

**Rationale / 理由**:
- 單一用戶，不需要併發處理
- 零配置，無需額外服務
- 足夠處理預期的資料量
- 易於備份（單一檔案）

**Migration Path / 遷移路徑**:
如未來需要多用戶，可遷移至 PostgreSQL（SQLAlchemy 支援）

### 6.2 資料清理策略

```python
# 每日清理超過 7 天的日誌
from datetime import datetime, timedelta

async def cleanup_old_logs():
    cutoff = datetime.now() - timedelta(days=7)
    await ExecutionLog.filter(created_at__lt=cutoff).delete()
```

---

## 7. BDD/TDD 開發工具研究

### 7.1 pytest-bdd

**Decision / 決定**: 使用 pytest-bdd 進行 BDD 測試

**Rationale / 理由**:
- 與 pytest 生態系統完美整合
- 支援 Gherkin 語法
- 可複用 pytest fixtures
- 活躍的社群支援

**Feature 檔案範例**:
```gherkin
# tests/features/US1_preset_tasks.feature
Feature: 透過 LINE 執行預設任務
  作為一個 LINE 用戶
  我想要發送指令給 Bot
  以便快速執行自動化任務

  @P1 @MVP
  Scenario: 發送 /help 取得指令列表
    Given 用戶已加入 LINE Bot 好友
    When 用戶發送訊息 "/help"
    Then 系統應回覆可用指令列表
```

**Step 定義範例**:
```python
# tests/step_defs/test_preset_tasks.py
from pytest_bdd import scenarios, given, when, then, parsers

scenarios('../features/US1_preset_tasks.feature')

@given('用戶已加入 LINE Bot 好友')
def user_is_friend(mock_line_user):
    return mock_line_user

@when(parsers.parse('用戶發送訊息 "{message}"'))
def user_sends_message(test_client, message):
    # 實作...
    pass
```

### 7.2 Mock 工具

**選擇**: pytest-mock + respx

| 工具 | 用途 |
|------|------|
| pytest-mock | 一般 Python 函數 mock |
| respx | httpx 請求 mock（LINE、OpenAI API） |

**respx 範例**:
```python
import respx

@respx.mock
async def test_line_reply():
    respx.post("https://api.line.me/v2/bot/message/reply").respond(200)
    # 測試程式碼...
```

### 7.3 API 契約測試

**選擇**: schemathesis

**Rationale / 理由**:
- 從 OpenAPI 規格自動生成測試
- 發現邊緣案例
- 驗證 API 符合契約

```bash
# 執行契約測試
schemathesis run http://localhost:8000/openapi.json
```

### 7.4 測試金字塔

```
        ▲
       /E2E\        ← 少量：LINE 實際對話
      /─────\
     / BDD  \       ← Feature + Step 定義
    /─────────\
   / 整合測試 \     ← API 端點 + 資料庫
  /─────────────\
 /   TDD 單元    \  ← 服務邏輯、解析器
/─────────────────\
```

---

## 8. 總結與建議

### 8.1 技術堆疊確認

| 層級 | 技術選擇 |
|------|----------|
| Web Framework | FastAPI |
| LINE SDK | line-bot-sdk |
| AI | OpenAI API (GPT-4o-mini) |
| Database | SQLite + SQLAlchemy |
| Scheduler | APScheduler |
| Template | Jinja2 |
| **BDD Testing** | **pytest-bdd** |
| **TDD Testing** | **pytest + pytest-asyncio** |
| **Mock** | **pytest-mock + respx** |
| **API Contract** | **schemathesis** |

### 8.2 潛在風險與緩解

| 風險 | 緩解策略 |
|------|----------|
| OpenAI API 成本 | 使用便宜模型 + 設定用量上限 |
| Notion Rate Limit (3/s) | 實作請求佇列和快取 |
| OAuth Token 過期 | 自動刷新機制 |
| LINE Push 限額 | 監控用量 + 升級方案 |

### 8.3 下一步

1. ✅ 完成研究文件
2. ✅ 設計資料模型 (data-model.md)
3. ✅ 定義 API 契約 (contracts/openapi.yaml)
4. ✅ 撰寫快速開始指南 (quickstart.md)
5. ✅ 任務分解 (tasks.md)
