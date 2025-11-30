# [PROJECT_NAME] Constitution
# [專案名稱] 憲章
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->
<!-- 範例：規格憲章、任務流程憲章等 -->

## Core Principles
## 核心原則

### [PRINCIPLE_1_NAME]
### [原則1名稱]
<!-- Example: I. Library-First -->
<!-- 範例：I. 函式庫優先 -->
[PRINCIPLE_1_DESCRIPTION]
[原則1描述]
<!-- Example: Every feature starts as a standalone library; Libraries must be self-contained, independently testable, documented; Clear purpose required - no organizational-only libraries -->
<!-- 範例：每個功能都從獨立的函式庫開始；函式庫必須自包含、可獨立測試、有文檔；需要明確目的 - 不允許僅為組織而存在的函式庫 -->

### [PRINCIPLE_2_NAME]
### [原則2名稱]
<!-- Example: II. CLI Interface -->
<!-- 範例：II. 命令列介面 -->
[PRINCIPLE_2_DESCRIPTION]
[原則2描述]
<!-- Example: Every library exposes functionality via CLI; Text in/out protocol: stdin/args → stdout, errors → stderr; Support JSON + human-readable formats -->
<!-- 範例：每個函式庫透過 CLI 暴露功能；文字輸入/輸出協定：stdin/args → stdout，錯誤 → stderr；支援 JSON 和人類可讀格式 -->

### [PRINCIPLE_3_NAME]
### [原則3名稱]
<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
<!-- 範例：III. 測試優先（不可協商） -->
[PRINCIPLE_3_DESCRIPTION]
[原則3描述]
<!-- Example: TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced -->
<!-- 範例：TDD 強制執行：撰寫測試 → 用戶批准 → 測試失敗 → 然後實作；嚴格執行紅-綠-重構循環 -->

### [PRINCIPLE_4_NAME]
### [原則4名稱]
<!-- Example: IV. Integration Testing -->
<!-- 範例：IV. 整合測試 -->
[PRINCIPLE_4_DESCRIPTION]
[原則4描述]
<!-- Example: Focus areas requiring integration tests: New library contract tests, Contract changes, Inter-service communication, Shared schemas -->
<!-- 範例：需要整合測試的重點領域：新函式庫契約測試、契約變更、服務間通訊、共享架構 -->

### [PRINCIPLE_5_NAME]
### [原則5名稱]
<!-- Example: V. Observability, VI. Versioning & Breaking Changes, VII. Simplicity -->
<!-- 範例：V. 可觀察性、VI. 版本控制與重大變更、VII. 簡單性 -->
[PRINCIPLE_5_DESCRIPTION]
[原則5描述]
<!-- Example: Text I/O ensures debuggability; Structured logging required; Or: MAJOR.MINOR.BUILD format; Or: Start simple, YAGNI principles -->
<!-- 範例：文字輸入/輸出確保可除錯性；需要結構化日誌；或：MAJOR.MINOR.BUILD 格式；或：從簡單開始，YAGNI 原則 -->

### PRINCIPLE_6: Documentation & Code Comments
### 原則6：文檔與程式碼註解

**所有程式碼必須包含詳細的中文註解**

1. **程式碼註解要求**：
   - 每個函數/方法必須有說明其用途、參數和返回值的中文註解
   - 複雜邏輯必須有逐行或區塊中文註解解釋
   - 類別和模組開頭必須有概述其職責的中文註解
   - 重要的業務邏輯決策必須用註解說明原因

2. **README.md 要求**：
   - 每個模組/組件必須包含 README.md
   - 內容包括：目的、設置說明、使用範例、依賴項、API 文檔

3. **文檔更新**：
   - 文檔更新是功能完成的必要條件
   - 程式碼變更必須同步更新相關註解

## [SECTION_2_NAME]
## [章節2名稱]
<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->
<!-- 範例：額外限制、安全需求、效能標準等 -->

[SECTION_2_CONTENT]
[章節2內容]
<!-- Example: Technology stack requirements, compliance standards, deployment policies, etc. -->
<!-- 範例：技術堆疊需求、合規標準、部署政策等 -->

## [SECTION_3_NAME]
## [章節3名稱]
<!-- Example: Development Workflow, Review Process, Quality Gates, etc. -->
<!-- 範例：開發流程、審查流程、品質關卡等 -->

[SECTION_3_CONTENT]
[章節3內容]
<!-- Example: Code review requirements, testing gates, deployment approval process, etc. -->
<!-- 範例：代碼審查需求、測試關卡、部署批准流程等 -->

## Governance
## 治理

<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->
<!-- 範例：憲章優先於所有其他實踐；修訂需要文檔、批准、遷移計劃 -->

[GOVERNANCE_RULES]
[治理規則]
<!-- Example: All PRs/reviews must verify compliance; Complexity must be justified; Use [GUIDANCE_FILE] for runtime development guidance -->
<!-- 範例：所有 PR/審查必須驗證合規性；複雜性必須有理由；使用 [GUIDANCE_FILE] 作為運行時開發指導 -->

**Maintainer**: Jimmy (jimmy10800d) | **Version**: 1.0.0 | **Ratified**: 2025-11-30 | **Last Amended**: 2025-11-30
**維護人員**: Jimmy (jimmy10800d) | **版本**: 1.0.0 | **批准日期**: 2025-11-30 | **最後修訂日期**: 2025-11-30
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
<!-- 範例：版本：2.1.1 | 批准日期：2025-06-13 | 最後修訂日期：2025-07-16 -->
