# Tasks: LINE 自動化流程引擎

**Input**: Design documents from `/specs/001-line-workflow-automation/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/openapi.yaml ✅

**Tests**: 本專案採用測試優先原則，各 User Story 包含測試任務。

**Organization**: 任務按 User Story 分組，確保每個故事可獨立實作和測試。

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 可平行執行（不同檔案、無依賴）
- **[Story]**: 此任務所屬的 User Story（如 US1, US2, US3）
- 描述中包含確切的檔案路徑

---

## Phase 1: Setup (專案初始化)

**Purpose**: 專案基礎結構和配置

- [ ] T001 建立專案目錄結構（依 plan.md 定義）
- [ ] T002 初始化 Python 專案，建立 `pyproject.toml` 和 `requirements.txt`
- [ ] T003 [P] 建立 `.env.example` 環境變數範例檔案
- [ ] T004 [P] 建立 `Dockerfile` 和 `docker-compose.yml`
- [ ] T005 [P] 配置 linting 工具（ruff）和 pre-commit hooks
- [ ] T006 [P] 建立專案 `README.md`（中文說明文件）

---

## Phase 2: Foundational (基礎建設)

**Purpose**: 所有 User Story 共用的核心基礎設施

**⚠️ 重要**: 此階段必須完成後才能開始任何 User Story

### 資料庫與 ORM

- [ ] T007 建立 SQLAlchemy 資料庫連線配置 `src/config.py`
- [ ] T008 [P] 建立 User 模型 `src/models/user.py`
- [ ] T009 [P] 建立 Workflow 模型 `src/models/workflow.py`
- [ ] T010 [P] 建立 ExecutionLog 模型 `src/models/execution_log.py`
- [ ] T011 [P] 建立 Integration 模型 `src/models/integration.py`
- [ ] T012 [P] 建立 Schedule 模型 `src/models/schedule.py`
- [ ] T013 建立資料庫遷移腳本 `scripts/migrate_db.py`

### FastAPI 應用程式框架

- [ ] T014 建立 FastAPI 應用程式入口 `src/main.py`
- [ ] T015 [P] 建立錯誤處理中介軟體 `src/api/__init__.py`
- [ ] T016 [P] 建立日誌配置 `src/config.py`（結構化日誌）

### LINE Bot 基礎

- [ ] T017 建立 LINE Webhook 驗證邏輯 `src/api/webhook.py`
- [ ] T018 建立 LINE 訊息服務基礎類別 `src/services/line_service.py`

### 測試框架

- [ ] T019 建立 pytest 配置 `tests/conftest.py`
- [ ] T020 [P] 建立測試用的 fixtures 和 mock 工具

**Checkpoint**: 基礎設施就緒 - 可開始 User Story 實作

---

## Phase 3: User Story 1 - 透過 LINE 執行預設任務 (Priority: P1) 🎯 MVP

**Goal**: 使用者可透過 LINE 發送指令，系統執行預設任務並回覆結果

**Independent Test**: 發送 `/hello` 或 `/weather 台北` 驗證系統正確回應

### Tests for User Story 1

- [ ] T021 [P] [US1] 單元測試：指令解析器 `tests/unit/test_parser.py`
- [ ] T022 [P] [US1] 整合測試：LINE Webhook 處理 `tests/integration/test_line_webhook.py`
- [ ] T023 [P] [US1] 契約測試：/webhook 端點 `tests/contract/test_api_contracts.py`

### Implementation for User Story 1

- [ ] T024 [US1] 實作指令解析器 `src/commands/parser.py`
- [ ] T025 [US1] 實作指令註冊表 `src/commands/registry.py`
- [ ] T026 [P] [US1] 實作 /help 指令處理器 `src/commands/handlers/help.py`
- [ ] T027 [P] [US1] 實作 /weather 指令處理器 `src/commands/handlers/weather.py`
- [ ] T028 [P] [US1] 實作 /remind 指令處理器 `src/commands/handlers/remind.py`
- [ ] T029 [US1] 整合 OpenAI AI 服務 `src/services/ai_service.py`
- [ ] T030 [US1] 完成 LINE Webhook 處理流程 `src/api/webhook.py`
- [ ] T031 [US1] 實作任務執行器基礎類別 `src/services/task_executor.py`
- [ ] T032 [US1] 實作非同步任務處理（長時間任務回覆「處理中」）

**Checkpoint**: User Story 1 完成 - 可透過 LINE 執行基本指令

---

## Phase 4: User Story 2 - 建立自訂工作流程 (Priority: P2)

**Goal**: 使用者可透過 LINE 對話建立、編輯、刪除自訂工作流程

**Independent Test**: 發送 `/create workflow 早安提醒` 並驗證流程被正確儲存

### Tests for User Story 2

- [ ] T033 [P] [US2] 單元測試：工作流程服務 `tests/unit/test_workflow.py`
- [ ] T034 [P] [US2] 整合測試：工作流程 CRUD `tests/integration/test_workflow_crud.py`
- [ ] T035 [P] [US2] 契約測試：/api/workflows 端點 `tests/contract/test_workflow_api.py`

### Implementation for User Story 2

- [ ] T036 [US2] 實作工作流程服務 `src/services/workflow_service.py`
- [ ] T037 [US2] 實作工作流程 API 路由 `src/api/workflows.py`
- [ ] T038 [P] [US2] 實作 /create workflow 指令 `src/commands/handlers/workflow.py`
- [ ] T039 [P] [US2] 實作 /list workflows 指令 `src/commands/handlers/workflow.py`
- [ ] T040 [P] [US2] 實作 /edit workflow 指令 `src/commands/handlers/workflow.py`
- [ ] T041 [P] [US2] 實作 /delete workflow 指令 `src/commands/handlers/workflow.py`
- [ ] T042 [US2] 實作工作流程版本控制邏輯
- [ ] T043 [US2] 實作工作流程啟用/停用切換

**Checkpoint**: User Story 2 完成 - 可建立和管理自訂工作流程

---

## Phase 5: User Story 3 - 串接外部服務 (Priority: P2)

**Goal**: 使用者可連接 Google Calendar、Notion、GitHub 外部服務

**Independent Test**: 發送 `/connect google` 完成授權後，發送 `/calendar today` 獲取行程

### Tests for User Story 3

- [ ] T044 [P] [US3] 單元測試：OAuth 流程 `tests/unit/test_oauth.py`
- [ ] T045 [P] [US3] 整合測試：Google Calendar 整合 `tests/integration/test_google_calendar.py`
- [ ] T046 [P] [US3] 契約測試：/api/integrations 端點 `tests/contract/test_integration_api.py`

### Implementation for User Story 3

- [ ] T047 [US3] 實作整合服務基礎類別 `src/integrations/base.py`
- [ ] T048 [US3] 實作整合服務 API 路由 `src/api/integrations.py`
- [ ] T049 [P] [US3] 實作 Google Calendar 整合 `src/integrations/google_calendar.py`
- [ ] T050 [P] [US3] 實作 Notion 整合 `src/integrations/notion.py`
- [ ] T051 [P] [US3] 實作 GitHub 整合 `src/integrations/github.py`
- [ ] T052 [P] [US3] 實作天氣 API 整合 `src/integrations/weather.py`
- [ ] T053 [P] [US3] 實作 /connect 指令處理器 `src/commands/handlers/calendar.py`
- [ ] T054 [P] [US3] 實作 /calendar 指令處理器 `src/commands/handlers/calendar.py`
- [ ] T055 [P] [US3] 實作 /notion 指令處理器 `src/commands/handlers/notion.py`
- [ ] T056 [P] [US3] 實作 /github 指令處理器 `src/commands/handlers/github.py`
- [ ] T057 [US3] 實作 OAuth Token 加密儲存
- [ ] T058 [US3] 實作 Token 自動刷新機制

**Checkpoint**: User Story 3 完成 - 可串接外部服務執行任務

---

## Phase 6: User Story 4 - 排程任務執行 (Priority: P3)

**Goal**: 使用者可設定工作流程的定期執行排程

**Independent Test**: 設定 1 分鐘後執行的任務，驗證準時執行並收到 LINE 通知

### Tests for User Story 4

- [ ] T059 [P] [US4] 單元測試：排程服務 `tests/unit/test_scheduler.py`
- [ ] T060 [P] [US4] 整合測試：排程執行 `tests/integration/test_scheduler.py`
- [ ] T061 [P] [US4] 契約測試：/api/schedules 端點 `tests/contract/test_schedule_api.py`

### Implementation for User Story 4

- [ ] T062 [US4] 實作排程服務 `src/services/scheduler_service.py`（使用 APScheduler）
- [ ] T063 [US4] 實作排程 API 路由 `src/api/schedules.py`
- [ ] T064 [P] [US4] 實作 /schedule 指令處理器 `src/commands/handlers/schedule.py`
- [ ] T065 [P] [US4] 實作 /list schedules 指令
- [ ] T066 [P] [US4] 實作 /cancel schedule 指令
- [ ] T067 [US4] 實作 Cron 表達式解析和下次執行時間計算
- [ ] T068 [US4] 實作排程任務自動觸發和結果通知

**Checkpoint**: User Story 4 完成 - 可設定和管理排程任務

---

## Phase 7: User Story 5 - 任務執行歷史與監控 (Priority: P3)

**Goal**: 使用者可查看任務執行歷史、狀態和錯誤日誌

**Independent Test**: 執行數個任務後，發送 `/history` 驗證歷史紀錄完整

### Tests for User Story 5

- [ ] T069 [P] [US5] 單元測試：執行日誌服務 `tests/unit/test_execution_log.py`
- [ ] T070 [P] [US5] 整合測試：歷史查詢 `tests/integration/test_history.py`
- [ ] T071 [P] [US5] 契約測試：/api/history 端點 `tests/contract/test_history_api.py`

### Implementation for User Story 5

- [ ] T072 [US5] 實作執行日誌服務 `src/services/execution_log_service.py`
- [ ] T073 [US5] 實作歷史查詢 API 路由 `src/api/history.py`
- [ ] T074 [P] [US5] 實作 /history 指令處理器 `src/commands/handlers/history.py`
- [ ] T075 [P] [US5] 實作 /history detail 指令
- [ ] T076 [US5] 實作過期日誌清理腳本 `scripts/cleanup_logs.py`（7 天保留期）
- [ ] T077 [US5] 整合執行日誌記錄到所有任務執行流程

**Checkpoint**: User Story 5 完成 - 可查看完整的執行歷史

---

## Phase 8: Web Interface (簡單網頁介面)

**Goal**: 提供簡單的網頁管理介面

- [ ] T078 [P] 建立網頁路由 `src/web/routes.py`
- [ ] T079 [P] 建立基礎模板 `src/web/templates/base.html`
- [ ] T080 [P] 建立首頁 `src/web/templates/index.html`
- [ ] T081 [P] 建立工作流程管理頁面 `src/web/templates/workflows.html`
- [ ] T082 [P] 建立設定頁面 `src/web/templates/settings.html`
- [ ] T083 [P] 建立靜態資源（CSS/JS）`src/web/static/`
- [ ] T084 註冊網頁路由到 FastAPI 應用程式

**Checkpoint**: 網頁介面完成 - 可透過瀏覽器管理流程

---

## Phase 9: Polish & Cross-Cutting Concerns (完善與收尾)

**Purpose**: 跨 User Story 的改進和優化

- [ ] T085 [P] 更新 API 文檔（Swagger/OpenAPI）
- [ ] T086 [P] 補充程式碼中文註解（依 constitution 要求）
- [ ] T087 [P] 建立各模組 README.md
- [ ] T088 程式碼重構和清理
- [ ] T089 效能優化（資料庫查詢、快取）
- [ ] T090 安全性強化（輸入驗證、Token 加密）
- [ ] T091 執行 quickstart.md 驗證流程
- [ ] T092 最終整合測試和驗收

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOCKS ALL USER STORIES
    ↓
    ├── Phase 3 (US1: 預設任務) ← MVP 🎯
    │       ↓
    ├── Phase 4 (US2: 工作流程) ← 可與 US1 平行
    │       ↓
    ├── Phase 5 (US3: 外部服務) ← 可與 US1/US2 平行
    │       ↓
    ├── Phase 6 (US4: 排程) ← 依賴 US2
    │       ↓
    └── Phase 7 (US5: 歷史) ← 可與其他 Story 平行
            ↓
Phase 8 (Web Interface)
    ↓
Phase 9 (Polish)
```

### User Story Dependencies

| User Story | 依賴 | 可平行 |
|------------|------|--------|
| US1 (P1) | Phase 2 | 無 |
| US2 (P2) | Phase 2 | 可與 US1 平行 |
| US3 (P2) | Phase 2 | 可與 US1/US2 平行 |
| US4 (P3) | US2 | 需 US2 的 Workflow 模型 |
| US5 (P3) | Phase 2 | 可與其他 Story 平行 |

### Parallel Opportunities

**Phase 2 內可平行執行**:
```
T008, T009, T010, T011, T012 (所有模型)
T015, T016 (中介軟體和日誌)
T019, T020 (測試配置)
```

**User Story 1 內可平行執行**:
```
T021, T022, T023 (所有測試)
T026, T027, T028 (所有指令處理器)
```

**User Story 3 內可平行執行**:
```
T049, T050, T051, T052 (所有整合服務)
T053, T054, T055, T056 (所有指令處理器)
```

---

## Implementation Strategy

### MVP First (僅 User Story 1)

1. 完成 Phase 1: Setup
2. 完成 Phase 2: Foundational (**關鍵 - 阻塞所有 Story**)
3. 完成 Phase 3: User Story 1
4. **停止並驗證**: 測試基本指令功能
5. 可部署/展示 MVP

### Incremental Delivery

1. Setup + Foundational → 基礎就緒
2. User Story 1 → 測試 → 部署（**MVP!**）
3. User Story 2 → 測試 → 部署
4. User Story 3 → 測試 → 部署
5. User Story 4 + 5 → 測試 → 部署
6. Web Interface + Polish → 最終版本

---

## Summary

| 階段 | 任務數 | 可平行任務 |
|------|--------|-----------|
| Phase 1: Setup | 6 | 4 |
| Phase 2: Foundational | 14 | 10 |
| Phase 3: US1 (MVP) | 12 | 7 |
| Phase 4: US2 | 11 | 6 |
| Phase 5: US3 | 15 | 12 |
| Phase 6: US4 | 10 | 5 |
| Phase 7: US5 | 9 | 5 |
| Phase 8: Web | 7 | 6 |
| Phase 9: Polish | 8 | 3 |
| **Total** | **92** | **58** |

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 = **32 tasks**

**獨立測試標準**:
- US1: `/hello`, `/weather 台北` 正確回應
- US2: `/create workflow 早安提醒` 成功建立
- US3: `/connect google` + `/calendar today` 成功
- US4: 排程任務準時執行
- US5: `/history` 顯示完整紀錄

---

## Notes

- [P] 標記 = 不同檔案、無依賴、可平行
- [Story] 標籤將任務映射到特定 User Story
- 每個 User Story 應可獨立完成和測試
- 驗證測試在實作前失敗
- 每個任務或邏輯群組後提交
- 在任何 Checkpoint 停止以獨立驗證 Story
- 避免：模糊任務、同檔案衝突、破壞獨立性的跨 Story 依賴
