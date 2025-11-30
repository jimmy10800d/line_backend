---
# 代理描述：創建或更新專案憲章，並確保所有相依模板保持同步
description: Create or update the project constitution from interactive or provided principle inputs, ensuring all dependent templates stay in sync.
# 交接配置：定義如何將任務交給其他代理
handoffs: 
  - label: Build Specification  # 標籤：建立規格
    agent: speckit.specify      # 目標代理：規格制定代理
    prompt: Implement the feature specification based on the updated constitution. I want to build...  # 交接提示詞
---

## User Input
## 用戶輸入

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).
# 重要：在繼續之前，您**必須**考慮用戶輸入（如果不為空）。

## Outline
## 大綱

You are updating the project constitution at `.specify/memory/constitution.md`. This file is a TEMPLATE containing placeholder tokens in square brackets (e.g. `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`). Your job is to (a) collect/derive concrete values, (b) fill the template precisely, and (c) propagate any amendments across dependent artifacts.
# 您正在更新位於 `.specify/memory/constitution.md` 的專案憲章。
# 此文件是一個模板，包含方括號中的佔位符（例如 `[PROJECT_NAME]`、`[PRINCIPLE_1_NAME]`）。
# 您的工作是：(a) 收集/推導具體值，(b) 精確填充模板，(c) 將任何修改傳播到相依的產物中。

Follow this execution flow:
# 遵循此執行流程：

1. Load the existing constitution template at `.specify/memory/constitution.md`.
   # 1. 載入位於 `.specify/memory/constitution.md` 的現有憲章模板。
   - Identify every placeholder token of the form `[ALL_CAPS_IDENTIFIER]`.
     # - 識別所有形式為 `[全大寫標識符]` 的佔位符標記。
   **IMPORTANT**: The user might require less or more principles than the ones used in the template. If a number is specified, respect that - follow the general template. You will update the doc accordingly.
   # **重要**：用戶可能需要比模板中使用的原則更少或更多的原則。如果指定了數量，請遵守 - 遵循通用模板。您將相應更新文檔。

2. Collect/derive values for placeholders:
   # 2. 收集/推導佔位符的值：
   - If user input (conversation) supplies a value, use it.
     # - 如果用戶輸入（對話）提供了值，則使用它。
   - Otherwise infer from existing repo context (README, docs, prior constitution versions if embedded).
     # - 否則從現有倉庫上下文推斷（README、文檔、之前的憲章版本（如果嵌入））。
   - For governance dates: `RATIFICATION_DATE` is the original adoption date (if unknown ask or mark TODO), `LAST_AMENDED_DATE` is today if changes are made, otherwise keep previous.
     # - 對於治理日期：`RATIFICATION_DATE` 是原始採納日期（如果未知則詢問或標記為 TODO），
     #   `LAST_AMENDED_DATE` 是今天（如果進行了更改），否則保留之前的日期。
   - `CONSTITUTION_VERSION` must increment according to semantic versioning rules:
     # - `CONSTITUTION_VERSION` 必須根據語義化版本規則遞增：
     - MAJOR: Backward incompatible governance/principle removals or redefinitions.
       # - MAJOR（主版本）：不向後兼容的治理/原則刪除或重新定義。
     - MINOR: New principle/section added or materially expanded guidance.
       # - MINOR（次版本）：新增原則/章節或實質性擴展指導。
     - PATCH: Clarifications, wording, typo fixes, non-semantic refinements.
       # - PATCH（修訂版本）：澄清、措辭、錯字修復、非語義改進。
   - If version bump type ambiguous, propose reasoning before finalizing.
     # - 如果版本升級類型不明確，請在最終確定之前提出推理。

3. Draft the updated constitution content:
   # 3. 起草更新後的憲章內容：
   - Replace every placeholder with concrete text (no bracketed tokens left except intentionally retained template slots that the project has chosen not to define yet—explicitly justify any left).
     # - 用具體文本替換每個佔位符（不留下任何括號標記，除非專案有意保留尚未定義的模板槽位——明確說明任何保留的理由）。
   - Preserve heading hierarchy and comments can be removed once replaced unless they still add clarifying guidance.
     # - 保留標題層次結構，一旦替換後可以刪除註釋，除非它們仍然添加澄清性指導。
   - Ensure each Principle section: succinct name line, paragraph (or bullet list) capturing non‑negotiable rules, explicit rationale if not obvious.
     # - 確保每個原則部分：簡潔的名稱行、段落（或項目符號列表）捕捉不可協商的規則、如果不明顯則明確理由。
   - Ensure Governance section lists amendment procedure, versioning policy, and compliance review expectations.
     # - 確保治理部分列出修改程序、版本控制政策和合規審查期望。

4. Consistency propagation checklist (convert prior checklist into active validations):
   # 4. 一致性傳播檢查清單（將之前的檢查清單轉換為主動驗證）：
   - Read `.specify/templates/plan-template.md` and ensure any "Constitution Check" or rules align with updated principles.
     # - 讀取 `.specify/templates/plan-template.md` 並確保任何「憲章檢查」或規則與更新的原則保持一致。
   - Read `.specify/templates/spec-template.md` for scope/requirements alignment—update if constitution adds/removes mandatory sections or constraints.
     # - 讀取 `.specify/templates/spec-template.md` 以進行範圍/需求對齊——如果憲章添加/刪除強制性部分或約束，則更新。
   - Read `.specify/templates/tasks-template.md` and ensure task categorization reflects new or removed principle-driven task types (e.g., observability, versioning, testing discipline).
     # - 讀取 `.specify/templates/tasks-template.md` 並確保任務分類反映新的或刪除的原則驅動型任務類型（例如，可觀察性、版本控制、測試規範）。
   - Read each command file in `.specify/templates/commands/*.md` (including this one) to verify no outdated references (agent-specific names like CLAUDE only) remain when generic guidance is required.
     # - 讀取 `.specify/templates/commands/*.md` 中的每個命令文件（包括此文件），以驗證在需要通用指導時沒有過時的引用（僅限代理特定名稱如 CLAUDE）。
   - Read any runtime guidance docs (e.g., `README.md`, `docs/quickstart.md`, or agent-specific guidance files if present). Update references to principles changed.
     # - 讀取任何運行時指導文檔（例如，`README.md`、`docs/quickstart.md` 或代理特定的指導文件（如果存在））。更新對已更改原則的引用。

5. Produce a Sync Impact Report (prepend as an HTML comment at top of the constitution file after update):
   # 5. 生成同步影響報告（在更新後作為 HTML 註釋附加到憲章文件頂部）：
   - Version change: old → new
     # - 版本更改：舊版本 → 新版本
   - List of modified principles (old title → new title if renamed)
     # - 修改的原則列表（如果重命名，舊標題 → 新標題）
   - Added sections
     # - 添加的部分
   - Removed sections
     # - 刪除的部分
   - Templates requiring updates (✅ updated / ⚠ pending) with file paths
     # - 需要更新的模板（✅ 已更新 / ⚠ 待處理）及文件路徑
   - Follow-up TODOs if any placeholders intentionally deferred.
     # - 如果有任何佔位符被有意推遲，則後續的 TODO 項目。

6. Validation before final output:
   # 6. 最終輸出前的驗證：
   - No remaining unexplained bracket tokens.
     # - 沒有剩餘未解釋的括號標記。
   - Version line matches report.
     # - 版本行與報告匹配。
   - Dates ISO format YYYY-MM-DD.
     # - 日期使用 ISO 格式 YYYY-MM-DD。
   - Principles are declarative, testable, and free of vague language ("should" → replace with MUST/SHOULD rationale where appropriate).
     # - 原則是聲明性的、可測試的，並且沒有模糊語言（"應該" → 在適當的地方用 MUST/SHOULD 理由替換）。

7. Write the completed constitution back to `.specify/memory/constitution.md` (overwrite).
   # 7. 將完成的憲章寫回 `.specify/memory/constitution.md`（覆蓋）。

8. Output a final summary to the user with:
   # 8. 向用戶輸出最終摘要，包括：
   - New version and bump rationale.
     # - 新版本和升級理由。
   - Any files flagged for manual follow-up.
     # - 任何標記為需要手動跟進的文件。
   - Suggested commit message (e.g., `docs: amend constitution to vX.Y.Z (principle additions + governance update)`).
     # - 建議的提交消息（例如，`docs: amend constitution to vX.Y.Z (principle additions + governance update)`）。

Formatting & Style Requirements:
# 格式與風格要求：

- Use Markdown headings exactly as in the template (do not demote/promote levels).
  # - 完全按照模板使用 Markdown 標題（不要降級/升級級別）。
- Wrap long rationale lines to keep readability (<100 chars ideally) but do not hard enforce with awkward breaks.
  # - 換行長理由以保持可讀性（理想情況下 <100 個字符），但不要強制使用尷尬的斷行。
- Keep a single blank line between sections.
  # - 在各部分之間保留一個空行。
- Avoid trailing whitespace.
  # - 避免尾隨空格。

If the user supplies partial updates (e.g., only one principle revision), still perform validation and version decision steps.
# 如果用戶提供部分更新（例如，僅一個原則修訂），仍然執行驗證和版本決策步驟。

If critical info missing (e.g., ratification date truly unknown), insert `TODO(<FIELD_NAME>): explanation` and include in the Sync Impact Report under deferred items.
# 如果缺少關鍵信息（例如，批准日期確實未知），插入 `TODO(<FIELD_NAME>): explanation` 並在同步影響報告的延期項目下包含。

Do not create a new template; always operate on the existing `.specify/memory/constitution.md` file.
# 不要創建新模板；始終在現有的 `.specify/memory/constitution.md` 文件上操作。
