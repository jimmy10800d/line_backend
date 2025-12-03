# Quickstart Guide: LINE 自動化流程引擎
# 快速開始指南

**Feature**: 001-line-workflow-automation  
**Date**: 2025-11-30

---

## 📋 前置需求

### 帳號與 API

- [ ] LINE Developers 帳號 + Messaging API Channel
- [ ] OpenAI API Key
- [ ] Google Cloud Console 專案 + OAuth 2.0 憑證
- [ ] Notion Integration Token
- [ ] GitHub OAuth App

### 開發環境

- Python 3.11+
- Git
- Docker (選用，用於部署)

---

## 🚀 快速開始

### 1. 複製專案

```bash
git clone https://github.com/jimmy10800d/line_backend.git
cd line_backend
git checkout 001-line-workflow-automation
```

### 2. 建立虛擬環境

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env` 檔案：

```env
# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
LINE_CHANNEL_SECRET=your_channel_secret

# OpenAI 設定
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/integrations/google_calendar/callback

# Notion 設定
NOTION_CLIENT_ID=your_client_id
NOTION_CLIENT_SECRET=your_client_secret
NOTION_REDIRECT_URI=http://localhost:8000/api/integrations/notion/callback

# GitHub 設定
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/integrations/github/callback

# 應用設定
SECRET_KEY=your_secret_key_for_encryption
DATABASE_URL=sqlite:///./data/app.db
TIMEZONE=Asia/Taipei
```

### 5. 初始化資料庫

```bash
python -m alembic upgrade head
```

### 6. 啟動開發伺服器

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 設定 LINE Webhook

使用 ngrok 或類似工具暴露本地伺服器：

```bash
ngrok http 8000
```

在 LINE Developers Console 設定 Webhook URL：
```
https://your-ngrok-url.ngrok.io/webhook
```

---

## 🧪 測試（BDD + TDD）

本專案採用 **BDD（行為驅動開發）** 和 **TDD（測試驅動開發）** 方法論。

### 測試結構

```
tests/
├── features/           # BDD Feature 檔案（Gherkin 語法）
│   ├── US1_preset_tasks.feature
│   ├── US2_workflows.feature
│   └── ...
├── step_defs/          # BDD Step 定義
│   ├── test_preset_tasks.py
│   └── ...
├── unit/               # TDD 單元測試
├── integration/        # 整合測試
└── contract/           # API 契約測試
```

### 執行 BDD 測試（Gherkin Feature）

```bash
# 執行所有 BDD 測試
pytest tests/features/ -v

# 執行特定 User Story 的 BDD 測試
pytest tests/step_defs/test_preset_tasks.py -v

# 只執行帶有特定標籤的 Scenario
pytest tests/features/ -v -m "P1"
```

### 執行單元測試（TDD）

```bash
pytest tests/unit -v
```

### 執行整合測試

```bash
pytest tests/integration -v
```

### 執行契約測試（OpenAPI）

```bash
# 使用 schemathesis 自動從 OpenAPI 生成測試
schemathesis run http://localhost:8000/openapi.json
```

### 執行全部測試（含覆蓋率）

```bash
pytest -v --cov=src --cov-report=html
```

### 開發流程（每個功能）

```bash
# 1. 寫 BDD Feature（先定義行為）
# 2. 執行測試確認失敗
pytest tests/step_defs/test_xxx.py -v

# 3. 寫 TDD 單元測試
pytest tests/unit/test_xxx.py -v

# 4. 實作程式碼直到測試通過
# 5. 重構
# 6. 確認 BDD 測試通過
pytest tests/features/USx_xxx.feature -v
```

---

## 📱 使用說明

### 基本指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `/help` | 顯示幫助 | `/help` |
| `/weather` | 查詢天氣 | `/weather 台北` |
| `/remind` | 設定提醒 | `/remind 30分鐘後 開會` |

### Google Calendar 指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `/connect google` | 連接 Google 帳號 | `/connect google` |
| `/calendar today` | 查詢今日行程 | `/calendar today` |
| `/calendar add` | 新增行程 | `/calendar add 明天 14:00 開會` |

### Notion 指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `/connect notion` | 連接 Notion | `/connect notion` |
| `/notion search` | 搜尋頁面 | `/notion search 專案計畫` |
| `/notion add` | 新增頁面 | `/notion add 會議記錄` |

### GitHub 指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `/connect github` | 連接 GitHub | `/connect github` |
| `/github issues` | 查詢 Issue | `/github issues open` |
| `/github create` | 建立 Issue | `/github create bug 登入失敗` |

### 工作流程指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `/create workflow` | 建立流程 | `/create workflow 早安提醒` |
| `/list workflows` | 列出流程 | `/list workflows` |
| `/run workflow` | 執行流程 | `/run workflow 早安提醒` |

### 排程指令

| 指令 | 說明 | 範例 |
|------|------|------|
| `/schedule` | 設定排程 | `/schedule 早安提醒 every day 09:00` |
| `/list schedules` | 列出排程 | `/list schedules` |
| `/cancel schedule` | 取消排程 | `/cancel schedule 早安提醒` |

### 歷史查詢

| 指令 | 說明 | 範例 |
|------|------|------|
| `/history` | 查看歷史 | `/history` |
| `/history detail` | 歷史詳情 | `/history detail abc123` |

---

## 🌐 網頁介面

啟動伺服器後訪問：

- **首頁**: http://localhost:8000/
- **工作流程管理**: http://localhost:8000/web/workflows
- **整合設定**: http://localhost:8000/web/settings
- **API 文檔**: http://localhost:8000/docs (Swagger UI)

---

## 🐳 Docker 部署

### 建置映像

```bash
docker build -t line-workflow-engine .
```

### 使用 Docker Compose

```bash
docker-compose up -d
```

### docker-compose.yml 範例

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

## 🔧 常見問題

### Q: LINE Webhook 驗證失敗？

1. 確認 `LINE_CHANNEL_SECRET` 正確
2. 確認 Webhook URL 可被 LINE 平台訪問
3. 檢查伺服器日誌中的簽名驗證錯誤

### Q: OAuth 授權後無法取得 Token？

1. 確認 Redirect URI 與設定一致
2. 確認 Client ID 和 Secret 正確
3. 檢查 OAuth scope 是否足夠

### Q: 排程未執行？

1. 確認排程狀態為 `is_active: true`
2. 確認伺服器時區設定為 `Asia/Taipei`
3. 檢查 `next_run_at` 時間是否正確

---

## 📚 相關文件

| 文件 | 說明 |
|------|------|
| [spec.md](./spec.md) | 功能規格 |
| [PRD.md](./PRD.md) | 產品需求文件 |
| [data-model.md](./data-model.md) | 資料模型 |
| [contracts/openapi.yaml](./contracts/openapi.yaml) | API 契約 |
| [research.md](./research.md) | 技術研究 |
