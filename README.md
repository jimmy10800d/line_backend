# LINE 自動化流程引擎

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![BDD/TDD](https://img.shields.io/badge/Testing-BDD%2FTDD-purple.svg)](docs/testing.md)

**以 LINE 為操作介面的個人自動化助手**

整合 AI 對話理解，支援 Google Calendar、Notion、GitHub 外部服務整合

</div>

---

## 📋 目錄

- [功能特色](#-功能特色)
- [系統架構](#-系統架構)
- [快速開始](#-快速開始)
- [開發指南](#-開發指南)
- [BDD/TDD 開發流程](#-bddtdd-開發流程)
- [API 文檔](#-api-文檔)
- [部署指南](#-部署指南)
- [專案結構](#-專案結構)

---

## ✨ 功能特色

### 🤖 核心功能

| 功能 | 說明 | 狀態 |
|------|------|------|
| LINE 指令執行 | 透過 LINE 發送指令執行自動化任務 | 🚧 開發中 |
| AI 對話理解 | 整合 ChatGPT 理解自然語言指令 | 🚧 開發中 |
| 自訂工作流程 | 建立、編輯、管理自訂自動化流程 | ⏳ 計劃中 |
| 外部服務整合 | Google Calendar、Notion、GitHub | ⏳ 計劃中 |
| 排程任務 | 定時執行工作流程 | ⏳ 計劃中 |
| 執行歷史 | 查看任務執行紀錄與錯誤日誌 | ⏳ 計劃中 |

### 📱 預設指令

```
/help          - 查看所有可用指令
/weather 台北  - 查詢天氣
/remind 30分鐘 喝水 - 設定提醒
/calendar today - 查詢今日行程
/notion search 關鍵字 - 搜尋 Notion
/github issues - 查詢 GitHub Issues
```

---

## 🏗 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                    LINE Bot 介面                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  指令解析   │  │  AI 對話    │  │  結果回覆   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    工作流程引擎                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  流程管理   │  │  任務執行   │  │  排程系統   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    外部服務整合層                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Google  │  │  Notion  │  │  GitHub  │  │ Weather │ │
│  │ Calendar │  │          │  │          │  │   API   │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速開始

### 環境需求

- Python 3.11+
- Docker & Docker Compose（選用）

### 安裝步驟

#### 1. 複製專案

```bash
git clone https://github.com/jimmy10800d/line_backend.git
cd line_backend
```

#### 2. 建立虛擬環境

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

#### 3. 安裝依賴

```bash
# 安裝主要依賴
pip install -r requirements.txt

# 安裝開發依賴（開發時需要）
pip install -r requirements-dev.txt
```

#### 4. 設定環境變數

```bash
# 複製環境變數範例檔案
cp .env.example .env

# 編輯 .env 填入實際值
# 必填：LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, OPENAI_API_KEY
```

#### 5. 初始化資料庫

```bash
python scripts/migrate_db.py
```

#### 6. 啟動服務

```bash
# 開發模式（熱重載）
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Docker
docker-compose up -d
```

#### 7. 驗證安裝

開啟瀏覽器訪問：http://localhost:8000/docs

---

## 💻 開發指南

### 安裝 Pre-commit Hooks

```bash
pre-commit install
```

### 程式碼風格檢查

```bash
# Linting
ruff check src/

# Formatting
ruff format src/
```

### 類型檢查

```bash
mypy src/
```

---

## 🧪 BDD/TDD 開發流程

本專案採用 **BDD（行為驅動開發）+ TDD（測試驅動開發）** 方法論。

### 測試金字塔

```
        ▲
       /E2E\        ← 少量：LINE 實際對話測試
      /─────\
     / BDD  \       ← Feature 檔案 + Step 定義
    /─────────\
   / 整合測試 \     ← API 端點 + 資料庫
  /─────────────\
 /   TDD 單元    \  ← 服務邏輯、解析器
/─────────────────\
```

### 開發流程

```
1. 寫 BDD Feature（Gherkin 語法）
   └─ tests/features/USx_xxx.feature

2. 寫 Step 定義骨架（先 pass）
   └─ tests/step_defs/test_xxx.py

3. TDD 循環：
   ① 寫單元測試 (RED)
   ② 確認測試失敗
   ③ 實作程式碼 (GREEN)
   ④ 確認測試通過
   ⑤ 重構 (REFACTOR)

4. 完成 Step 定義實作

5. 執行 BDD 測試確認 Scenario 通過
   └─ pytest tests/features/ -v

6. 提交程式碼
```

### 執行測試

```bash
# 執行所有測試
pytest

# 執行單元測試
pytest tests/unit/ -v

# 執行 BDD 測試
pytest tests/features/ -v

# 執行整合測試
pytest tests/integration/ -v

# 執行契約測試
pytest tests/contract/ -v

# 產生覆蓋率報告
pytest --cov=src --cov-report=html

# 執行特定標記的測試
pytest -m "unit" -v
pytest -m "bdd" -v
```

### 測試目錄結構

```
tests/
├── conftest.py              # 共用 fixtures
├── features/                # BDD Feature 檔案（Gherkin）
│   ├── US1_preset_tasks.feature
│   ├── US2_workflows.feature
│   └── ...
├── step_defs/               # BDD Step 定義
│   ├── conftest.py
│   ├── test_preset_tasks.py
│   └── ...
├── unit/                    # TDD 單元測試
├── integration/             # 整合測試
├── contract/                # API 契約測試
└── mocks/                   # Mock 工具
```

---

## 📚 API 文檔

啟動服務後，訪問以下 URL：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 主要 API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/webhook` | LINE Webhook 端點 |
| GET | `/api/workflows` | 取得所有工作流程 |
| POST | `/api/workflows` | 建立工作流程 |
| GET | `/api/integrations` | 取得整合服務列表 |
| GET | `/api/schedules` | 取得排程列表 |
| GET | `/api/history` | 取得執行歷史 |
| GET | `/health` | 健康檢查 |

---

## 🐳 部署指南

### Docker 部署

```bash
# 建置映像
docker build -t line-workflow .

# 執行容器
docker run -d \
  --name line-workflow \
  -p 8000:8000 \
  --env-file .env \
  line-workflow
```

### Docker Compose 部署

```bash
# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

---

## 📁 專案結構

```
line_backend/
├── README.md                    # 專案說明（本文件）
├── pyproject.toml               # Python 專案配置
├── requirements.txt             # 主要依賴
├── requirements-dev.txt         # 開發依賴
├── .env.example                 # 環境變數範例
├── Dockerfile                   # Docker 配置
├── docker-compose.yml           # Docker Compose 配置
│
├── src/                         # 主要原始碼
│   ├── __init__.py
│   ├── main.py                  # FastAPI 應用程式入口
│   ├── config.py                # 設定管理
│   ├── api/                     # API 路由
│   ├── models/                  # 資料模型
│   ├── services/                # 業務邏輯
│   ├── integrations/            # 外部服務整合
│   ├── commands/                # 指令處理
│   └── web/                     # 網頁介面
│
├── tests/                       # 測試（BDD/TDD）
│   ├── features/                # BDD Feature 檔案
│   ├── step_defs/               # BDD Step 定義
│   ├── unit/                    # 單元測試
│   ├── integration/             # 整合測試
│   └── contract/                # 契約測試
│
├── scripts/                     # 維護腳本
│   ├── migrate_db.py            # 資料庫遷移
│   └── cleanup_logs.py          # 清理過期日誌
│
├── specs/                       # 規格文件
│   └── 001-line-workflow-automation/
│
└── data/                        # 資料庫檔案（.gitignore）
```

---

## 📄 授權

本專案採用 [MIT License](LICENSE) 授權。

---

## 👤 維護者

- **Jimmy** - [@jimmy10800d](https://github.com/jimmy10800d)

---

<div align="center">

**Made with ❤️ for automation**

</div>
