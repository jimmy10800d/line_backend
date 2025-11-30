# Implementation Plan: LINE 自動化流程引擎
# 實作計劃：LINE Workflow Automation Engine

**Branch**: `001-line-workflow-automation` | **Date**: 2025-11-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-line-workflow-automation/spec.md`

## Summary
## 摘要

打造一個以 LINE 為操作介面的個人自動化助手，整合 AI 對話理解（ChatGPT），支援 Google Calendar、Notion、GitHub 外部服務整合，具備工作流程建立、排程執行和執行歷史監控功能。

**核心技術方案**:
- LINE Messaging API 接收用戶訊息
- OpenAI API 進行自然語言理解
- OAuth 2.0 串接外部服務
- 排程引擎支援 Cron 格式
- 簡單網頁介面管理流程

## Technical Context
## 技術背景

**Language/Version**: Python 3.11+（FastAPI 框架，適合 async webhook 處理）
**Primary Dependencies**: 
- FastAPI（Web 框架）
- LINE Bot SDK for Python
- OpenAI Python SDK
- APScheduler（排程引擎）
- SQLAlchemy（ORM）
- Jinja2（網頁模板）

**Storage**: SQLite（單一用戶，輕量級）→ 可升級至 PostgreSQL
**Testing**: pytest + pytest-bdd + pytest-asyncio（BDD/TDD 開發模式）
**Target Platform**: Linux Server（Docker 部署）
**Project Type**: Web Application（Backend API + Simple Frontend）

**Performance Goals**: 
- 回應時間 < 3 秒（簡單任務）
- 支援 100 並發用戶
- 排程準確率 99%

**Constraints**: 
- 單一用戶系統
- 時區固定 UTC+8
- 資料保留 7 天
- 網頁介面為簡單管理（非拖拉式）

**Scale/Scope**: 
- 單一用戶
- 3 外部服務整合
- MVP 預設任務 + 自訂工作流程

## Constitution Check
## 憲章檢查

*GATE: 必須在 Phase 0 研究前通過。Phase 1 設計後重新檢查。*

| 原則 | 狀態 | 說明 |
|------|------|------|
| 文檔與程式碼註解 | ✅ 通過 | 每個模組將包含 README.md，所有程式碼使用詳細中文註解 |
| 測試優先 (BDD/TDD) | ✅ 計劃中 | BDD: pytest-bdd + Gherkin Feature 檔案；TDD: pytest 單元測試 |
| 可觀察性 | ✅ 計劃中 | 結構化日誌 + 執行歷史記錄 |
| 簡單性 | ✅ 通過 | 單一用戶、SQLite、簡單網頁介面 |

**所有憲章檢查通過** ✅

## Project Structure
## 專案結構

### Documentation (this feature)
### 文檔（本功能）

```text
specs/001-line-workflow-automation/
├── spec.md              # 功能規格
├── PRD.md               # 產品需求文件
├── plan.md              # 本實作計劃
├── research.md          # Phase 0 研究輸出
├── data-model.md        # Phase 1 資料模型
├── quickstart.md        # Phase 1 快速開始指南
├── contracts/           # Phase 1 API 契約
│   └── openapi.yaml     # OpenAPI 規格
├── tasks.md             # Phase 2 任務清單
└── checklists/
    └── requirements.md  # 需求檢查清單
```

### Source Code (repository root)
### 原始碼（倉庫根目錄）

```text
line_backend/
├── README.md                    # 專案說明（中文）
├── pyproject.toml               # Python 專案配置
├── requirements.txt             # 依賴清單
├── .env.example                 # 環境變數範例
├── Dockerfile                   # Docker 部署
├── docker-compose.yml           # Docker Compose 配置
│
├── src/                         # 主要原始碼
│   ├── __init__.py
│   ├── main.py                  # FastAPI 應用程式入口
│   ├── config.py                # 設定管理
│   │
│   ├── api/                     # API 路由
│   │   ├── __init__.py
│   │   ├── webhook.py           # LINE Webhook 處理
│   │   ├── workflows.py         # 工作流程 API
│   │   └── integrations.py      # 外部服務整合 API
│   │
│   ├── models/                  # 資料模型
│   │   ├── __init__.py
│   │   ├── user.py              # 用戶模型
│   │   ├── workflow.py          # 工作流程模型
│   │   ├── task.py              # 任務模型
│   │   ├── schedule.py          # 排程模型
│   │   ├── integration.py       # 整合服務模型
│   │   └── execution_log.py     # 執行日誌模型
│   │
│   ├── services/                # 業務邏輯
│   │   ├── __init__.py
│   │   ├── line_service.py      # LINE 訊息處理
│   │   ├── ai_service.py        # AI 對話服務 (OpenAI)
│   │   ├── workflow_service.py  # 工作流程引擎
│   │   ├── scheduler_service.py # 排程服務
│   │   └── task_executor.py     # 任務執行器
│   │
│   ├── integrations/            # 外部服務整合
│   │   ├── __init__.py
│   │   ├── base.py              # 整合基礎類別
│   │   ├── google_calendar.py   # Google Calendar 整合
│   │   ├── notion.py            # Notion 整合
│   │   ├── github.py            # GitHub 整合
│   │   └── weather.py           # 天氣 API 整合
│   │
│   ├── commands/                # 指令處理
│   │   ├── __init__.py
│   │   ├── parser.py            # 指令解析器
│   │   ├── registry.py          # 指令註冊表
│   │   └── handlers/            # 各指令處理器
│   │       ├── __init__.py
│   │       ├── help.py
│   │       ├── calendar.py
│   │       ├── notion.py
│   │       ├── github.py
│   │       ├── weather.py
│   │       ├── remind.py
│   │       └── workflow.py
│   │
│   └── web/                     # 簡單網頁介面
│       ├── __init__.py
│       ├── routes.py            # 網頁路由
│       ├── templates/           # Jinja2 模板
│       │   ├── base.html
│       │   ├── index.html
│       │   ├── workflows.html
│       │   └── settings.html
│       └── static/              # 靜態資源
│           ├── css/
│           └── js/
│
├── tests/                       # 測試（BDD/TDD）
│   ├── __init__.py
│   ├── conftest.py              # pytest 配置 + 共用 fixtures
│   ├── features/                # BDD Feature 檔案（Gherkin）
│   │   ├── US1_preset_tasks.feature
│   │   ├── US2_workflows.feature
│   │   ├── US3_integrations.feature
│   │   ├── US4_schedules.feature
│   │   └── US5_history.feature
│   ├── step_defs/               # BDD Step 定義
│   │   ├── conftest.py
│   │   ├── test_preset_tasks.py
│   │   ├── test_workflows.py
│   │   ├── test_integrations.py
│   │   ├── test_schedules.py
│   │   └── test_history.py
│   ├── unit/                    # TDD 單元測試
│   │   ├── test_parser.py
│   │   ├── test_ai_service.py
│   │   └── test_workflow.py
│   ├── integration/             # 整合測試
│   │   ├── test_line_webhook.py
│   │   ├── test_google_calendar.py
│   │   └── test_scheduler.py
│   └── contract/                # API 契約測試
│       └── test_api_contracts.py
│
└── scripts/                     # 維護腳本
    ├── cleanup_logs.py          # 清理過期日誌
    └── migrate_db.py            # 資料庫遷移
```

**Structure Decision / 結構決定**: 採用 Web Application 結構，包含 Backend API（FastAPI）和簡單 Frontend（Jinja2 模板）。單一倉庫管理，適合個人專案。

## Complexity Tracking
## 複雜度追蹤

> 無憲章違規，此區塊僅供記錄設計決策

| 決策 | 理由 | 拒絕的替代方案 |
|------|------|----------------|
| 使用 SQLite | 單一用戶、輕量級、無需額外服務 | PostgreSQL：過於複雜，個人使用不需要 |
| 使用 Jinja2 模板 | 簡單、無需前端框架 | React/Vue：過於複雜，只需簡單管理介面 |
| APScheduler | Python 原生、易整合 | Celery：需要 Redis/RabbitMQ，過於複雜 |

---

## Phase 0: Research (研究階段) ✅ 完成
## 研究階段已完成

已產出 `research.md`，包含：
- [x] LINE Messaging API 最佳實踐
- [x] OpenAI API 整合模式
- [x] OAuth 2.0 實作細節
- [x] APScheduler 使用模式
- [x] 各外部服務 API 限制

## Phase 1: Design (設計階段) ✅ 完成
## 設計階段已完成

已產出：
- [x] `data-model.md` - 資料模型詳細設計
- [x] `contracts/openapi.yaml` - API 契約
- [x] `quickstart.md` - 快速開始指南

## Phase 2: Tasks (任務階段) ✅ 完成
## 任務階段已完成

已產出 `tasks.md`，包含：
- [x] 92 個任務，依 User Story 組織
- [x] MVP 範圍：32 個任務（Phase 1-3）
- [x] 58 個可平行執行任務
- [x] 獨立測試標準定義

---

## Next Steps
## 下一步

1. ✅ 完成實作計劃 (plan.md)
2. ✅ 執行 Phase 0 研究，產出 research.md
3. ✅ 執行 Phase 1 設計，產出資料模型和 API 契約
4. ✅ 執行 Phase 2 任務規劃，產出 tasks.md
5. ⏳ 開始實作（從 Phase 1: Setup 開始）
