# LINE 自動化流程引擎 - 工作流程功能
# BDD Feature: User Story 2 - 建立自訂工作流程

@US2 @workflow
Feature: 建立自訂工作流程
  作為一個使用者
  我希望能夠透過 LINE 建立、編輯和管理自訂工作流程
  以便自動化我的日常任務

  Background:
    Given 用戶 "U1234567890" 已加入 LINE 好友
    And 系統已準備接收 Webhook

  # =====================================================
  # Scenario: 建立工作流程
  # =====================================================

  @workflow @create @smoke
  Scenario: 建立新的工作流程
    When 用戶發送訊息 "建立流程 早安提醒"
    Then 系統應該回覆包含 "已建立" 的訊息
    And 工作流程 "早安提醒" 應該被儲存

  @workflow @create
  Scenario: 建立帶有步驟的工作流程
    When 用戶發送訊息 "建立流程 每日報告"
    And 用戶發送訊息 "新增步驟: 查詢天氣"
    And 用戶發送訊息 "新增步驟: 查詢行程"
    And 用戶發送訊息 "完成"
    Then 系統應該回覆確認訊息
    And 工作流程 "每日報告" 應該有 2 個步驟

  @workflow @create
  Scenario: 使用英文指令建立工作流程
    When 用戶發送訊息 "create workflow morning routine"
    Then 系統應該回覆包含 "已建立" 的訊息
    And 工作流程 "morning routine" 應該被儲存

  @workflow @create @error
  Scenario: 建立重複名稱的工作流程
    Given 用戶已有名為 "早安提醒" 的工作流程
    When 用戶發送訊息 "建立流程 早安提醒"
    Then 系統應該回覆包含 "已存在" 的訊息

  # =====================================================
  # Scenario: 列出工作流程
  # =====================================================

  @workflow @list @smoke
  Scenario: 列出所有工作流程
    Given 用戶已有以下工作流程:
      | name     | status   |
      | 早安提醒 | active   |
      | 每日報告 | active   |
      | 週報     | inactive |
    When 用戶發送訊息 "我的流程"
    Then 系統應該回覆包含 "早安提醒" 的訊息
    And 系統應該回覆包含 "每日報告" 的訊息
    And 系統應該回覆包含 "週報" 的訊息

  @workflow @list
  Scenario: 沒有工作流程時列出
    When 用戶發送訊息 "列出流程"
    Then 系統應該回覆包含 "尚未建立" 的訊息

  @workflow @list
  Scenario: 使用英文指令列出工作流程
    Given 用戶已有名為 "test workflow" 的工作流程
    When 用戶發送訊息 "list workflows"
    Then 系統應該回覆包含 "test workflow" 的訊息

  # =====================================================
  # Scenario: 查看工作流程詳情
  # =====================================================

  @workflow @view
  Scenario: 查看工作流程詳情
    Given 用戶已有名為 "每日報告" 的工作流程
    And 工作流程 "每日報告" 包含步驟:
      | order | action   | parameters     |
      | 1     | weather  | city: 台北     |
      | 2     | calendar | range: today   |
    When 用戶發送訊息 "流程詳情 每日報告"
    Then 系統應該回覆包含 "每日報告" 的訊息
    And 系統應該回覆包含 "天氣" 的訊息
    And 系統應該回覆包含 "行程" 的訊息

  @workflow @view @error
  Scenario: 查看不存在的工作流程
    When 用戶發送訊息 "流程詳情 不存在的流程"
    Then 系統應該回覆包含 "找不到" 的訊息

  # =====================================================
  # Scenario: 編輯工作流程
  # =====================================================

  @workflow @edit
  Scenario: 編輯工作流程名稱
    Given 用戶已有名為 "早安提醒" 的工作流程
    When 用戶發送訊息 "編輯流程 早安提醒"
    And 用戶發送訊息 "改名 早安流程"
    Then 系統應該回覆確認訊息
    And 工作流程 "早安流程" 應該被儲存
    And 工作流程 "早安提醒" 應該不存在

  @workflow @edit
  Scenario: 新增步驟到現有工作流程
    Given 用戶已有名為 "每日報告" 的工作流程
    And 工作流程 "每日報告" 有 1 個步驟
    When 用戶發送訊息 "編輯流程 每日報告"
    And 用戶發送訊息 "新增步驟: 提醒開會"
    And 用戶發送訊息 "完成"
    Then 系統應該回覆確認訊息
    And 工作流程 "每日報告" 應該有 2 個步驟

  @workflow @edit
  Scenario: 刪除工作流程中的步驟
    Given 用戶已有名為 "每日報告" 的工作流程
    And 工作流程 "每日報告" 有 3 個步驟
    When 用戶發送訊息 "編輯流程 每日報告"
    And 用戶發送訊息 "刪除步驟 2"
    And 用戶發送訊息 "完成"
    Then 系統應該回覆確認訊息
    And 工作流程 "每日報告" 應該有 2 個步驟

  # =====================================================
  # Scenario: 刪除工作流程
  # =====================================================

  @workflow @delete
  Scenario: 刪除工作流程
    Given 用戶已有名為 "舊流程" 的工作流程
    When 用戶發送訊息 "刪除流程 舊流程"
    Then 系統應該回覆包含 "確認刪除" 的訊息
    When 用戶發送訊息 "確認"
    Then 系統應該回覆包含 "已刪除" 的訊息
    And 工作流程 "舊流程" 應該不存在

  @workflow @delete
  Scenario: 取消刪除工作流程
    Given 用戶已有名為 "重要流程" 的工作流程
    When 用戶發送訊息 "刪除流程 重要流程"
    Then 系統應該回覆包含 "確認刪除" 的訊息
    When 用戶發送訊息 "取消"
    Then 系統應該回覆包含 "已取消" 的訊息
    And 工作流程 "重要流程" 應該被儲存

  @workflow @delete @error
  Scenario: 刪除不存在的工作流程
    When 用戶發送訊息 "刪除流程 不存在"
    Then 系統應該回覆包含 "找不到" 的訊息

  # =====================================================
  # Scenario: 啟用/停用工作流程
  # =====================================================

  @workflow @toggle
  Scenario: 停用工作流程
    Given 用戶已有名為 "早安提醒" 的工作流程
    And 工作流程 "早安提醒" 狀態為 "active"
    When 用戶發送訊息 "停用流程 早安提醒"
    Then 系統應該回覆包含 "已停用" 的訊息
    And 工作流程 "早安提醒" 狀態應該為 "inactive"

  @workflow @toggle
  Scenario: 啟用工作流程
    Given 用戶已有名為 "早安提醒" 的工作流程
    And 工作流程 "早安提醒" 狀態為 "inactive"
    When 用戶發送訊息 "啟用流程 早安提醒"
    Then 系統應該回覆包含 "已啟用" 的訊息
    And 工作流程 "早安提醒" 狀態應該為 "active"

  # =====================================================
  # Scenario: 執行工作流程
  # =====================================================

  @workflow @run @smoke
  Scenario: 執行工作流程
    Given 用戶已有名為 "早安提醒" 的工作流程
    And 工作流程 "早安提醒" 包含步驟:
      | order | action  | parameters   |
      | 1     | weather | city: 台北   |
    When 用戶發送訊息 "執行流程 早安提醒"
    Then 系統應該回覆包含 "執行中" 的訊息
    And 系統應該回覆天氣資訊

  @workflow @run
  Scenario: 執行多步驟工作流程
    Given 用戶已有名為 "每日報告" 的工作流程
    And 工作流程 "每日報告" 包含步驟:
      | order | action  | parameters   |
      | 1     | weather | city: 台北   |
      | 2     | todo    | action: list |
    When 用戶發送訊息 "執行 每日報告"
    Then 系統應該回覆包含 "執行中" 的訊息
    And 所有步驟應該依序執行

  @workflow @run @error
  Scenario: 執行停用的工作流程
    Given 用戶已有名為 "早安提醒" 的工作流程
    And 工作流程 "早安提醒" 狀態為 "inactive"
    When 用戶發送訊息 "執行流程 早安提醒"
    Then 系統應該回覆包含 "已停用" 的訊息

  @workflow @run @error
  Scenario: 執行不存在的工作流程
    When 用戶發送訊息 "執行流程 不存在"
    Then 系統應該回覆包含 "找不到" 的訊息

  # =====================================================
  # Scenario: 工作流程排程
  # =====================================================

  @workflow @schedule
  Scenario: 設定工作流程定時執行
    Given 用戶已有名為 "早安提醒" 的工作流程
    When 用戶發送訊息 "排程 早安提醒 每天 8:00"
    Then 系統應該回覆包含 "已排程" 的訊息
    And 工作流程 "早安提醒" 應該有排程設定

  @workflow @schedule
  Scenario: 取消工作流程排程
    Given 用戶已有名為 "早安提醒" 的工作流程
    And 工作流程 "早安提醒" 已排程在 "每天 8:00"
    When 用戶發送訊息 "取消排程 早安提醒"
    Then 系統應該回覆包含 "已取消" 的訊息
    And 工作流程 "早安提醒" 應該沒有排程設定

  # =====================================================
  # Scenario: 工作流程版本控制
  # =====================================================

  @workflow @version
  Scenario: 查看工作流程歷史版本
    Given 用戶已有名為 "每日報告" 的工作流程
    And 工作流程 "每日報告" 有多個版本
    When 用戶發送訊息 "流程歷史 每日報告"
    Then 系統應該回覆包含 "版本" 的訊息

  @workflow @version
  Scenario: 回復到之前的版本
    Given 用戶已有名為 "每日報告" 的工作流程
    And 工作流程 "每日報告" 有版本 "v1" 和 "v2"
    When 用戶發送訊息 "流程回復 每日報告 v1"
    Then 系統應該回覆包含 "已回復" 的訊息
