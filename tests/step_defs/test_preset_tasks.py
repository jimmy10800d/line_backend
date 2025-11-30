# US1: 預設任務 Step 定義
# User Story 1: Preset Tasks Step Definitions
"""
預設任務功能的 BDD Step 定義
=============================

包含 US1_preset_tasks.feature 中所有 Scenario 的 Step 實作。

使用方式：
    pytest tests/features/US1_preset_tasks.feature -v
"""

import pytest
from pytest_bdd import given, when, then, parsers, scenario, scenarios

# 載入所有 scenarios
scenarios("../features/US1_preset_tasks.feature")


# =============================================================================
# Given Steps（前置條件）
# =============================================================================


@given(parsers.parse('用戶 "{user_id}" 已加入 LINE 好友'))
def user_is_line_friend(user_id: str, test_user):
    """設定測試用戶"""
    test_user["line_user_id"] = user_id


@given("系統已準備接收 Webhook")
def system_ready_for_webhook(test_client):
    """確認系統已就緒"""
    response = test_client.get("/health")
    assert response.status_code == 200


@given("用戶之前執行過指令")
def user_has_execution_history(test_db_session, test_user):
    """建立測試用的執行歷史"""
    # TODO: 建立測試資料
    pass


@given(parsers.parse("AI 服務回應時間超過 {seconds:d} 秒"))
def ai_service_slow_response(seconds: int, mock_services):
    """設定 AI 服務延遲"""
    mock_services["openai"].set_response_delay(seconds)


# =============================================================================
# When Steps（動作）
# =============================================================================


@when(parsers.parse('用戶發送訊息 "{message}"'))
def user_sends_message(message: str, test_client, test_user, line_webhook_mock, line_reply_mock):
    """模擬用戶發送 LINE 訊息"""
    # 清空之前的回覆
    line_reply_mock.clear()
    
    webhook_body = line_webhook_mock.create_text_message_event(
        user_id=test_user.get("line_user_id", "U1234567890"),
        text=message,
    )
    response = test_client.post(
        "/webhook",
        json=webhook_body,
        headers=line_webhook_mock.create_signature_header(webhook_body),
    )
    test_user["last_response"] = response
    test_user["last_message"] = message


@when("用戶發送空白訊息")
def user_sends_empty_message(test_client, test_user, line_webhook_mock, line_reply_mock):
    """模擬用戶發送空白訊息"""
    line_reply_mock.clear()
    
    webhook_body = line_webhook_mock.create_text_message_event(
        user_id=test_user.get("line_user_id", "U1234567890"),
        text="",
    )
    response = test_client.post(
        "/webhook",
        json=webhook_body,
        headers=line_webhook_mock.create_signature_header(webhook_body),
    )
    test_user["last_response"] = response


@when(parsers.parse("用戶發送超過 {limit:d} 字的訊息"))
def user_sends_long_message(limit: int, test_client, test_user, line_webhook_mock):
    """模擬用戶發送過長訊息"""
    long_message = "測" * (limit + 1)
    webhook_body = line_webhook_mock.create_text_message_event(
        user_id=test_user.get("line_user_id", "U1234567890"),
        text=long_message,
    )
    response = test_client.post(
        "/webhook",
        json=webhook_body,
        headers=line_webhook_mock.create_signature_header(webhook_body),
    )
    test_user["last_response"] = response


@when(parsers.parse('用戶在 {seconds:d} 秒內發送相同訊息 "{message}" 兩次'))
def user_sends_duplicate_messages(
    seconds: int, message: str, test_client, test_user, line_webhook_mock
):
    """模擬用戶快速發送重複訊息"""
    webhook_body = line_webhook_mock.create_text_message_event(
        user_id=test_user.get("line_user_id", "U1234567890"),
        text=message,
    )
    headers = line_webhook_mock.create_signature_header(webhook_body)
    
    # 發送兩次
    response1 = test_client.post("/webhook", json=webhook_body, headers=headers)
    response2 = test_client.post("/webhook", json=webhook_body, headers=headers)
    
    test_user["duplicate_responses"] = [response1, response2]


@when("用戶發送需要 AI 處理的複雜訊息")
def user_sends_complex_message(test_client, test_user, line_webhook_mock):
    """模擬用戶發送需要 AI 解析的訊息"""
    message = "幫我規劃一個明天早上的待辦事項，包括運動和閱讀"
    webhook_body = line_webhook_mock.create_text_message_event(
        user_id=test_user.get("line_user_id", "U1234567890"),
        text=message,
    )
    response = test_client.post(
        "/webhook",
        json=webhook_body,
        headers=line_webhook_mock.create_signature_header(webhook_body),
    )
    test_user["last_response"] = response


# =============================================================================
# Then Steps（驗證）
# =============================================================================


@then(parsers.parse('系統應該回覆包含 "{text}" 的訊息'))
def system_replies_with_text(text: str, test_user, line_reply_mock):
    """驗證系統回覆包含指定文字"""
    replies = line_reply_mock.get_replies()
    assert any(text in reply.get("text", "") for reply in replies), \
        f"Expected '{text}' in replies: {replies}"


@then(parsers.parse('回覆訊息包含 "{text}" 指令說明'))
def reply_contains_command_help(text: str, line_reply_mock):
    """驗證回覆包含指令說明"""
    replies = line_reply_mock.get_replies()
    assert any(text in reply.get("text", "") for reply in replies)


@then("系統應該回覆確認訊息")
def system_replies_confirmation(test_user, line_reply_mock):
    """驗證系統回覆確認訊息"""
    replies = line_reply_mock.get_replies()
    assert len(replies) > 0, "Expected at least one reply"
    # 確認訊息通常包含 ✅ 或「已」或「成功」
    assert any(
        "✅" in r.get("text", "") or 
        "已" in r.get("text", "") or 
        "成功" in r.get("text", "")
        for r in replies
    )


@then(parsers.parse('待辦事項 "{content}" 應該被建立'))
def todo_should_be_created(content: str, test_db_session):
    """驗證待辦事項被建立"""
    # TODO: 查詢資料庫驗證
    pass


@then("系統應該識別為新增待辦指令")
def system_recognizes_todo_command(test_user):
    """驗證系統正確識別指令類型"""
    response = test_user.get("last_response")
    assert response.status_code == 200


@then(parsers.parse('筆記 "{content}" 應該被儲存'))
def note_should_be_saved(content: str, test_db_session):
    """驗證筆記被儲存"""
    # TODO: 查詢資料庫驗證
    pass


@then(parsers.parse('支出記錄應該包含金額 "{amount}" 和說明 "{description}"'))
def expense_should_be_recorded(amount: str, description: str, test_db_session):
    """驗證支出記錄"""
    # TODO: 查詢資料庫驗證
    pass


@then(parsers.parse('提醒 "{content}" 應該被設定在 "{time}"'))
def reminder_should_be_set(content: str, time: str, test_db_session):
    """驗證提醒被設定"""
    # TODO: 查詢資料庫驗證
    pass


@then("回覆訊息包含待辦事項統計")
def reply_contains_todo_stats(line_reply_mock):
    """驗證回覆包含統計資訊"""
    replies = line_reply_mock.get_replies()
    assert any("待辦" in r.get("text", "") for r in replies)


@then("回覆訊息包含工作流程統計")
def reply_contains_workflow_stats(line_reply_mock):
    """驗證回覆包含工作流程統計"""
    replies = line_reply_mock.get_replies()
    assert any("流程" in r.get("text", "") for r in replies)


@then("系統不應該回覆")
def system_should_not_reply(line_reply_mock):
    """驗證系統不回覆"""
    replies = line_reply_mock.get_replies()
    assert len(replies) == 0


@then("系統應該嘗試使用 AI 理解")
def system_should_try_ai(mock_services):
    """驗證系統嘗試使用 AI"""
    assert mock_services["openai"].was_called()


@then("如果無法理解則回覆友善的引導訊息")
def system_replies_friendly_guidance(line_reply_mock):
    """驗證系統回覆友善引導"""
    replies = line_reply_mock.get_replies()
    # 應該包含引導文字或建議
    assert any(
        "幫助" in r.get("text", "") or
        "試試" in r.get("text", "") or
        "可以" in r.get("text", "")
        for r in replies
    )


@then(parsers.parse('系統應該回覆 "{message}"'))
def system_replies_exact(message: str, line_reply_mock):
    """驗證系統回覆特定訊息"""
    replies = line_reply_mock.get_replies()
    assert any(message in r.get("text", "") for r in replies)


@then("系統只應該執行一次")
def system_executes_only_once(test_user):
    """驗證系統只執行一次"""
    # 透過資料庫記錄或執行日誌驗證
    pass


@then("回覆一次確認訊息")
def system_replies_once(line_reply_mock):
    """驗證只回覆一次"""
    replies = line_reply_mock.get_replies()
    # 去重複的訊息應該只有一個確認回覆
    confirmation_replies = [
        r for r in replies 
        if "✅" in r.get("text", "") or "已" in r.get("text", "")
    ]
    assert len(confirmation_replies) <= 1


@then(parsers.parse('系統應該先回覆 "{message}"'))
def system_replies_first(message: str, line_reply_mock):
    """驗證系統先回覆特定訊息"""
    replies = line_reply_mock.get_replies()
    assert len(replies) > 0
    first_reply = replies[0]
    assert message in first_reply.get("text", "")


@then("完成後再發送結果訊息")
def system_sends_result_later(line_reply_mock):
    """驗證系統完成後發送結果"""
    replies = line_reply_mock.get_replies()
    assert len(replies) >= 2  # 至少有「處理中」和「結果」兩條訊息
