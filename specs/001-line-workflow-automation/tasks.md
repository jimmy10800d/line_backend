# Tasks: LINE 自動化流程引擎

**Input**: Design documents from `/specs/001-line-workflow-automation/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/openapi.yaml ✅

**開發方法**: 本專案採用 **BDD（行為驅動開發）+ TDD（測試驅動開發）** 方法論

**Organization**: 任務按 User Story 分組，確保每個故事可獨立實作和測試。

---

## 開發方法論：BDD + TDD

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

### 工具鏈

| 層級 | 工具 | 用途 |
|------|------|------|
| BDD | `pytest-bdd` | Gherkin 語法 Feature 檔案 |
| TDD | `pytest` | 單元測試、整合測試 |
| API 契約 | `schemathesis` | 從 OpenAPI 自動生成測試 |
| Mock | `pytest-mock` + `respx` | Mock 外部服務 |

### 每個任務的開發流程

```
┌─────────────────────────────────────────────────────────┐
│  1. 寫 BDD Feature（Gherkin 語法）                      │
│     └─ tests/features/USx_xxx.feature                   │
├─────────────────────────────────────────────────────────┤
│  2. 寫 Step 定義骨架（先 pass）                         │
│     └─ tests/step_defs/test_xxx.py                      │
├─────────────────────────────────────────────────────────┤
│  3. TDD 循環：                                          │
│     ① 寫單元測試 (RED)                                  │
│     ② 確認測試失敗                                      │
│     ③ 實作程式碼 (GREEN)                                │
│     ④ 確認測試通過                                      │
│     ⑤ 重構 (REFACTOR)                                   │
├─────────────────────────────────────────────────────────┤
│  4. 完成 Step 定義實作                                  │
├─────────────────────────────────────────────────────────┤
│  5. 執行 BDD 測試確認 Scenario 通過                     │
│     └─ pytest tests/features/ -v                        │
├─────────────────────────────────────────────────────────┤
│  6. 提交程式碼                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: 可平行執行（不同檔案、無依賴）
- **[Story]**: 此任務所屬的 User Story（如 US1, US2, US3）
- 描述中包含確切的檔案路徑

---

## Phase 1: Setup (專案初始化)

**Purpose**: 專案基礎結構和配置

- [X] T001 建立專案目錄結構（依 plan.md 定義，包含 tests/features/ 和 tests/step_defs/）
- [X] T002 初始化 Python 專案，建立 `pyproject.toml` 和 `requirements.txt`（包含 pytest-bdd, pytest-mock, respx, schemathesis）
- [X] T003 [P] 建立 `.env.example` 環境變數範例檔案
- [X] T004 [P] 建立 `Dockerfile` 和 `docker-compose.yml`
- [X] T005 [P] 配置 linting 工具（ruff）和 pre-commit hooks
- [X] T006 [P] 建立專案 `README.md`（中文說明文件，包含 BDD/TDD 開發指南）

---

## Phase 2: Foundational (基礎建設)

**Purpose**: 所有 User Story 共用的核心基礎設施

**⚠️ 重要**: 此階段必須完成後才能開始任何 User Story

### 資料庫與 ORM

- [X] T007 建立 SQLAlchemy 資料庫連線配置 `src/config.py`
- [X] T008 [P] 建立 User 模型 `src/models/user.py`
- [X] T009 [P] 建立 Workflow 模型 `src/models/workflow.py`
- [X] T010 [P] 建立 ExecutionLog 模型 `src/models/execution_log.py`
- [X] T011 [P] 建立 Integration 模型 `src/models/integration.py`
- [X] T012 [P] 建立 Schedule 模型 `src/models/schedule.py`
- [X] T013 建立資料庫遷移腳本 `scripts/migrate_db.py`

### FastAPI 應用程式框架

- [X] T014 建立 FastAPI 應用程式入口 `src/main.py`
- [X] T015 [P] 建立錯誤處理中介軟體 `src/middleware/error_handler.py`
- [X] T016 [P] 建立日誌配置 `src/services/logging_service.py`（結構化日誌）

### LINE Bot 基礎

- [X] T017 建立 LINE Webhook 驗證邏輯 `src/api/webhook.py`
- [X] T018 建立 LINE 訊息服務基礎類別 `src/services/line_service.py`
- [X] T018a [P] 建立指令佇列服務 `src/commands/queue.py`（處理多指令同時發送的佇列機制）

### 測試框架（BDD/TDD 基礎設施）

- [X] T019 建立 pytest 配置 `tests/conftest.py`（共用 fixtures、mock 工廠）
- [X] T020 [P] 建立 pytest-bdd 配置和共用 Step 定義 `tests/step_defs/conftest.py`
- [X] T020a [P] 建立 LINE Webhook Mock 工具 `tests/mocks/line_mock.py`
- [X] T020b [P] 建立外部服務 Mock 工具 `tests/mocks/external_services.py`

**Checkpoint**: 基礎設施就緒 - 可開始 User Story 的 BDD/TDD 開發 ✅

---

## Phase 3: User Story 1 - 透過 LINE 執行預設任務 (Priority: P1) 🎯 MVP

**Goal**: 使用者可透過 LINE 發送指令，系統執行預設任務並回覆結果

**Independent Test**: 發送 `/hello` 或 `/weather 台北` 驗證系統正確回應

### Step 1: BDD Feature 定義 (先寫行為規格)

- [X] T021 [US1] 撰寫 BDD Feature 檔案 `tests/features/US1_preset_tasks.feature`
  - Scenario: 發送 /help 取得指令列表
  - Scenario: 發送 /weather 查詢天氣
  - Scenario: 處理無效指令
  - Scenario: 長時間任務回覆處理中

### Step 2: Step 定義骨架 (確保測試失敗)

- [X] T022 [US1] 建立 Step 定義骨架 `tests/step_defs/test_preset_tasks.py`（先 pass/skip）

### Step 3: TDD 單元測試 → 實作 (RED → GREEN → REFACTOR)

- [X] T023 [P] [US1] TDD: 指令解析器測試 `tests/unit/test_parser.py` → 實作 `src/commands/parser.py`
- [X] T024 [P] [US1] TDD: 指令註冊表測試 → 實作 `src/commands/handlers/base.py`
- [X] T025 [P] [US1] TDD: /help 處理器測試 → 實作 `src/commands/handlers/base.py`
- [X] T026 [P] [US1] TDD: /weather 處理器測試 → 實作 `src/commands/handlers/weather.py`
- [X] T027 [P] [US1] TDD: /remind 處理器測試 → 實作 `src/commands/handlers/remind.py`
- [X] T028 [US1] TDD: AI 服務測試 → 實作 `src/services/ai_service.py`
- [X] T028a [US1] TDD: AI 意圖識別測試（自然語言 → 指令轉換，如「幫我查今天的行程」→ `/calendar today`）
- [X] T029 [US1] TDD: 任務執行器測試 → 實作 `src/services/task_executor.py`

### Step 4: 整合測試

- [X] T030 [US1] 整合測試：LINE Webhook 處理 `tests/integration/test_line_webhook.py`
- [X] T031 [US1] 契約測試：/webhook 端點 `tests/contract/test_api_contracts.py`

### Step 5: 完成 Step 定義並通過 BDD 測試

- [X] T032 [US1] 完成 Step 定義實作 `tests/step_defs/test_preset_tasks.py`
- [X] T033 [US1] 完成 LINE Webhook 處理流程 `src/api/webhook.py`
- [ ] T034 [US1] 實作非同步任務處理（長時間任務回覆「處理中」）⏳ 進階功能，MVP 階段暫跳
- [X] T035 [US1] 執行 BDD 測試確認所有 Scenario 通過 ✅ 24/24 passed

**Checkpoint**: User Story 1 完成 - 可透過 LINE 執行基本指令（BDD 測試全綠）✅

---

## Phase 4: User Story 2 - 建立自訂工作流程 (Priority: P2)

**Goal**: 使用者可透過 LINE 對話建立、編輯、刪除自訂工作流程

**Independent Test**: 發送 `/create workflow 早安提醒` 並驗證流程被正確儲存

### Step 1: BDD Feature 定義

- [ ] T036 [US2] 撰寫 BDD Feature 檔案 `tests/features/US2_workflows.feature`
  - Scenario: 建立新工作流程
  - Scenario: 列出所有工作流程
  - Scenario: 編輯工作流程
  - Scenario: 刪除工作流程
  - Scenario: 啟用/停用工作流程

### Step 2: Step 定義骨架

- [ ] T037 [US2] 建立 Step 定義骨架 `tests/step_defs/test_workflows.py`

### Step 3: TDD 單元測試 → 實作

- [ ] T038 [P] [US2] TDD: 工作流程服務測試 → 實作 `src/services/workflow_service.py`
- [ ] T039 [P] [US2] TDD: 工作流程 API 測試 → 實作 `src/api/workflows.py`
- [ ] T040 [P] [US2] TDD: /create workflow 測試 → 實作 `src/commands/handlers/workflow.py`
- [ ] T041 [P] [US2] TDD: /list workflows 測試
- [ ] T042 [P] [US2] TDD: /edit workflow 測試
- [ ] T043 [P] [US2] TDD: /delete workflow 測試

### Step 4: 整合測試與契約測試

- [ ] T044 [US2] 整合測試：工作流程 CRUD `tests/integration/test_workflow_crud.py`
- [ ] T045 [US2] 契約測試：/api/workflows 端點 `tests/contract/test_workflow_api.py`

### Step 5: 完成 Step 定義並通過 BDD 測試

- [ ] T046 [US2] 完成 Step 定義實作
- [ ] T047 [US2] 實作工作流程版本控制邏輯
- [ ] T047a [US2] 實作工作流程版本歷史查詢
- [ ] T047b [US2] 實作工作流程斷點續傳（步驟執行狀態記錄與恢復）
- [ ] T048 [US2] 實作工作流程啟用/停用切換
- [ ] T049 [US2] 執行 BDD 測試確認所有 Scenario 通過

**Checkpoint**: User Story 2 完成 - 可建立和管理自訂工作流程（BDD 測試全綠）

---

## Phase 5: User Story 3 - 串接外部服務 (Priority: P2)

**Goal**: 使用者可連接 Google Calendar、Notion、GitHub 外部服務

**Independent Test**: 發送 `/connect google` 完成授權後，發送 `/calendar today` 獲取行程

### Step 1: BDD Feature 定義

- [ ] T050 [US3] 撰寫 BDD Feature 檔案 `tests/features/US3_integrations.feature`
  - Scenario: 連接 Google Calendar
  - Scenario: 查詢今日行程
  - Scenario: 連接 Notion
  - Scenario: 連接 GitHub
  - Scenario: 外部服務暫時無法連線

### Step 2: Step 定義骨架

- [ ] T051 [US3] 建立 Step 定義骨架 `tests/step_defs/test_integrations.py`

### Step 3: TDD 單元測試 → 實作

- [ ] T052 [US3] TDD: OAuth 流程測試 → 實作 `src/integrations/base.py`
- [ ] T053 [US3] TDD: 整合 API 測試 → 實作 `src/api/integrations.py`
- [ ] T054 [P] [US3] TDD: Google Calendar 測試 → 實作 `src/integrations/google_calendar.py`
- [ ] T055 [P] [US3] TDD: Notion 測試 → 實作 `src/integrations/notion.py`
- [ ] T056 [P] [US3] TDD: GitHub 測試 → 實作 `src/integrations/github.py`
- [ ] T057 [P] [US3] TDD: 天氣 API 測試 → 實作 `src/integrations/weather.py`
- [ ] T058 [P] [US3] TDD: /connect 指令測試 → 實作 `src/commands/handlers/calendar.py`
- [ ] T059 [P] [US3] TDD: /calendar 指令測試
- [ ] T060 [P] [US3] TDD: /notion 指令測試 → 實作 `src/commands/handlers/notion.py`
- [ ] T061 [P] [US3] TDD: /github 指令測試 → 實作 `src/commands/handlers/github.py`

### Step 4: 整合測試與契約測試

- [ ] T062 [US3] 整合測試：Google Calendar 整合 `tests/integration/test_google_calendar.py`
- [ ] T063 [US3] 契約測試：/api/integrations 端點 `tests/contract/test_integration_api.py`

### Step 5: 完成 Step 定義並通過 BDD 測試

- [ ] T064 [US3] 完成 Step 定義實作
- [ ] T065 [US3] 實作 OAuth Token 加密儲存
- [ ] T066 [US3] 實作 Token 自動刷新機制
- [ ] T066a [US3] 實作外部服務重試機制（最多 3 次，指數退避）
- [ ] T067 [US3] 執行 BDD 測試確認所有 Scenario 通過

**Checkpoint**: User Story 3 完成 - 可串接外部服務執行任務（BDD 測試全綠）

---

## Phase 6: User Story 4 - 排程任務執行 (Priority: P3)

**Goal**: 使用者可設定工作流程的定期執行排程

**Independent Test**: 設定 1 分鐘後執行的任務，驗證準時執行並收到 LINE 通知

### Step 1: BDD Feature 定義

- [ ] T068 [US4] 撰寫 BDD Feature 檔案 `tests/features/US4_schedules.feature`
  - Scenario: 設定排程任務
  - Scenario: 列出所有排程
  - Scenario: 取消排程
  - Scenario: 排程準時執行

### Step 2: Step 定義骨架

- [ ] T069 [US4] 建立 Step 定義骨架 `tests/step_defs/test_schedules.py`

### Step 3: TDD 單元測試 → 實作

- [ ] T070 [US4] TDD: 排程服務測試 → 實作 `src/services/scheduler_service.py`
- [ ] T071 [US4] TDD: 排程 API 測試 → 實作 `src/api/schedules.py`
- [ ] T072 [P] [US4] TDD: /schedule 指令測試 → 實作 `src/commands/handlers/schedule.py`
- [ ] T073 [P] [US4] TDD: /list schedules 測試
- [ ] T074 [P] [US4] TDD: /cancel schedule 測試
- [ ] T075 [US4] TDD: Cron 解析器測試

### Step 4: 整合測試與契約測試

- [ ] T076 [US4] 整合測試：排程執行 `tests/integration/test_scheduler.py`
- [ ] T077 [US4] 契約測試：/api/schedules 端點 `tests/contract/test_schedule_api.py`

### Step 5: 完成 Step 定義並通過 BDD 測試

- [ ] T078 [US4] 完成 Step 定義實作
- [ ] T079 [US4] 實作排程任務自動觸發和結果通知
- [ ] T080 [US4] 執行 BDD 測試確認所有 Scenario 通過

**Checkpoint**: User Story 4 完成 - 可設定和管理排程任務（BDD 測試全綠）

---

## Phase 7: User Story 5 - 任務執行歷史與監控 (Priority: P3)

**Goal**: 使用者可查看任務執行歷史、狀態和錯誤日誌

**Independent Test**: 執行數個任務後，發送 `/history` 驗證歷史紀錄完整

### Step 1: BDD Feature 定義

- [ ] T081 [US5] 撰寫 BDD Feature 檔案 `tests/features/US5_history.feature`
  - Scenario: 查看執行歷史
  - Scenario: 查看歷史詳情
  - Scenario: 過期日誌自動清理

### Step 2: Step 定義骨架

- [ ] T082 [US5] 建立 Step 定義骨架 `tests/step_defs/test_history.py`

### Step 3: TDD 單元測試 → 實作

- [ ] T083 [US5] TDD: 執行日誌服務測試 → 實作 `src/services/execution_log_service.py`
- [ ] T084 [US5] TDD: 歷史 API 測試 → 實作 `src/api/history.py`
- [ ] T085 [P] [US5] TDD: /history 指令測試 → 實作 `src/commands/handlers/history.py`
- [ ] T086 [P] [US5] TDD: /history detail 測試

### Step 4: 整合測試與契約測試

- [ ] T087 [US5] 整合測試：歷史查詢 `tests/integration/test_history.py`
- [ ] T088 [US5] 契約測試：/api/history 端點 `tests/contract/test_history_api.py`

### Step 5: 完成 Step 定義並通過 BDD 測試

- [ ] T089 [US5] 完成 Step 定義實作
- [ ] T090 [US5] 實作過期日誌清理腳本 `scripts/cleanup_logs.py`（7 天保留期）
- [ ] T091 [US5] 整合執行日誌記錄到所有任務執行流程
- [ ] T092 [US5] 執行 BDD 測試確認所有 Scenario 通過

**Checkpoint**: User Story 5 完成 - 可查看完整的執行歷史（BDD 測試全綠）

---

## Phase 8: Web Interface (簡單網頁介面)

**Goal**: 提供簡單的網頁管理介面

- [ ] T093 [P] 建立網頁路由 `src/web/routes.py`
- [ ] T094 [P] 建立基礎模板 `src/web/templates/base.html`
- [ ] T095 [P] 建立首頁 `src/web/templates/index.html`
- [ ] T096 [P] 建立工作流程管理頁面 `src/web/templates/workflows.html`
- [ ] T097 [P] 建立設定頁面 `src/web/templates/settings.html`
- [ ] T098 [P] 建立靜態資源（CSS/JS）`src/web/static/`
- [ ] T099 註冊網頁路由到 FastAPI 應用程式

**Checkpoint**: 網頁介面完成 - 可透過瀏覽器管理流程

---

## Phase 9: Polish & Cross-Cutting Concerns (完善與收尾)

**Purpose**: 跨 User Story 的改進和優化

- [ ] T100 [P] 更新 API 文檔（Swagger/OpenAPI）
- [ ] T101 [P] 補充程式碼中文註解（依 constitution 要求）
- [ ] T102 [P] 建立各模組 README.md
- [ ] T103 程式碼重構和清理
- [ ] T104 效能優化（資料庫查詢、快取）
- [ ] T105 安全性強化（輸入驗證、Token 加密）
- [ ] T106 執行 quickstart.md 驗證流程
- [ ] T107 執行所有 BDD Feature 測試（最終驗收）
- [ ] T108 測試覆蓋率報告生成（目標 > 80%）

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

| 階段 | 任務數 | BDD Feature | TDD 測試 |
|------|--------|-------------|----------|
| Phase 1: Setup | 6 | - | - |
| Phase 2: Foundational | 17 | - | 基礎設施 |
| Phase 3: US1 (MVP) | 16 | US1_preset_tasks.feature | ✅ |
| Phase 4: US2 | 16 | US2_workflows.feature | ✅ |
| Phase 5: US3 | 19 | US3_integrations.feature | ✅ |
| Phase 6: US4 | 13 | US4_schedules.feature | ✅ |
| Phase 7: US5 | 12 | US5_history.feature | ✅ |
| Phase 8: Web | 7 | - | - |
| Phase 9: Polish | 9 | 全部 Feature | 覆蓋率報告 |
| **Total** | **115** | **5 Features** | **全流程** |

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 = **39 tasks**

**BDD/TDD 驗收標準**:
- 每個 User Story 的 BDD Feature 測試全部通過
- 單元測試覆蓋率 > 80%
- 整合測試覆蓋所有 API 端點
- 契約測試驗證 OpenAPI 規格

---

## Notes

- [P] 標記 = 不同檔案、無依賴、可平行
- [Story] 標籤將任務映射到特定 User Story
- **BDD 流程**: Feature → Step 骨架 → TDD 實作 → Step 完成 → BDD 通過
- **TDD 循環**: 紅（測試失敗）→ 綠（測試通過）→ 重構
- 每個 User Story 應可獨立完成和測試
- 在任何 Checkpoint 停止以獨立驗證 Story
- 提交前確保相關測試通過
- 避免：模糊任務、同檔案衝突、破壞獨立性的跨 Story 依賴
