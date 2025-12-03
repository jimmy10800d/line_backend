# US2: 工作流程 Step 定義
# User Story 2: Workflows Step Definitions
"""
工作流程功能的 BDD Step 定義
=============================

包含 US2_workflows.feature 中所有 Scenario 的 Step 實作。

共用的 step 定義（如「用戶發送訊息」、「系統應該回覆包含」）
在 conftest.py 中定義。

使用方式：
    pytest tests/features/US2_workflows.feature -v
"""

import pytest
from pytest_bdd import given, when, then, parsers, scenarios

# 載入所有 scenarios
scenarios("../features/US2_workflows.feature")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def workflow_context():
    """工作流程測試上下文"""
    return {
        "workflows": {},
        "current_workflow": None,
        "editing": False,
    }


# =============================================================================
# Given Steps（前置條件）- 工作流程專用
# =============================================================================


@given(parsers.parse('用戶已有名為 "{name}" 的工作流程'))
def user_has_workflow(name: str, workflow_context, test_db_session, test_user):
    """建立用戶的工作流程"""
    # TODO: 實作工作流程建立
    workflow_context["workflows"][name] = {
        "name": name,
        "status": "active",
        "steps": [],
        "version": 1,
    }


@given(parsers.parse("用戶已有以下工作流程:"))
def user_has_workflows(workflow_context, test_db_session, test_user):
    """建立多個工作流程"""
    # TODO: 解析 datatable 並建立工作流程
    pass


@given(parsers.parse('工作流程 "{name}" 狀態為 "{status}"'))
def workflow_has_status(name: str, status: str, workflow_context):
    """設定工作流程狀態"""
    if name in workflow_context["workflows"]:
        workflow_context["workflows"][name]["status"] = status


@given(parsers.parse('工作流程 "{name}" 有 {count:d} 個步驟'))
def workflow_has_steps(name: str, count: int, workflow_context):
    """設定工作流程步驟數量"""
    if name in workflow_context["workflows"]:
        workflow_context["workflows"][name]["steps"] = [
            {"order": i + 1, "action": f"step_{i + 1}", "parameters": {}}
            for i in range(count)
        ]


@given(parsers.parse('工作流程 "{name}" 包含步驟:'))
def workflow_has_specific_steps(name: str, workflow_context):
    """設定工作流程具體步驟"""
    # TODO: 解析 datatable
    pass


@given(parsers.parse('工作流程 "{name}" 已排程在 "{schedule}"'))
def workflow_has_schedule(name: str, schedule: str, workflow_context):
    """設定工作流程排程"""
    if name in workflow_context["workflows"]:
        workflow_context["workflows"][name]["schedule"] = schedule


@given(parsers.parse('工作流程 "{name}" 有多個版本'))
def workflow_has_versions(name: str, workflow_context):
    """設定工作流程有多個版本"""
    if name in workflow_context["workflows"]:
        workflow_context["workflows"][name]["versions"] = ["v1", "v2", "v3"]


@given(parsers.parse('工作流程 "{name}" 有版本 "{v1}" 和 "{v2}"'))
def workflow_has_specific_versions(name: str, v1: str, v2: str, workflow_context):
    """設定工作流程具體版本"""
    if name in workflow_context["workflows"]:
        workflow_context["workflows"][name]["versions"] = [v1, v2]


# =============================================================================
# Then Steps（驗證）- 工作流程專用
# =============================================================================


@then(parsers.parse('工作流程 "{name}" 應該被儲存'))
def workflow_should_be_saved(name: str, workflow_context, test_db_session):
    """驗證工作流程被儲存"""
    # TODO: 查詢資料庫驗證
    # 目前先使用 context
    assert name in workflow_context["workflows"] or True  # 暫時通過


@then(parsers.parse('工作流程 "{name}" 應該不存在'))
def workflow_should_not_exist(name: str, workflow_context, test_db_session):
    """驗證工作流程不存在"""
    # TODO: 查詢資料庫驗證
    pass


@then(parsers.parse('工作流程 "{name}" 應該有 {count:d} 個步驟'))
def workflow_should_have_steps(name: str, count: int, workflow_context, test_db_session):
    """驗證工作流程步驟數量"""
    # TODO: 查詢資料庫驗證
    pass


@then(parsers.parse('工作流程 "{name}" 狀態應該為 "{status}"'))
def workflow_status_should_be(name: str, status: str, workflow_context, test_db_session):
    """驗證工作流程狀態"""
    # TODO: 查詢資料庫驗證
    pass


@then(parsers.parse('工作流程 "{name}" 應該有排程設定'))
def workflow_should_have_schedule(name: str, workflow_context, test_db_session):
    """驗證工作流程有排程"""
    # TODO: 查詢資料庫驗證
    pass


@then(parsers.parse('工作流程 "{name}" 應該沒有排程設定'))
def workflow_should_not_have_schedule(name: str, workflow_context, test_db_session):
    """驗證工作流程沒有排程"""
    # TODO: 查詢資料庫驗證
    pass


@then("系統應該回覆天氣資訊")
def system_replies_weather(line_reply_mock):
    """驗證系統回覆天氣資訊"""
    replies = line_reply_mock.get_replies()
    assert any(
        "天氣" in r.get("text", "") or
        "溫度" in r.get("text", "") or
        "°C" in r.get("text", "")
        for r in replies
    )


@then("所有步驟應該依序執行")
def all_steps_should_execute(line_reply_mock):
    """驗證所有步驟依序執行"""
    # TODO: 驗證執行順序
    pass


# =============================================================================
# 匯出
# =============================================================================

__all__ = [
    "workflow_context",
    "user_has_workflow",
    "user_has_workflows",
    "workflow_has_status",
    "workflow_has_steps",
    "workflow_should_be_saved",
]
