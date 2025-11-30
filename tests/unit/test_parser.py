# 指令解析器單元測試
# Command Parser Unit Tests
"""
指令解析器測試
==============

使用 TDD 方法測試指令解析器功能：
1. 規則匹配解析
2. 參數提取
3. 自然語言識別
4. 邊界情況處理
"""

import pytest
from src.commands.parser import (
    CommandParser,
    CommandType,
    ParsedCommand,
    get_parser,
)


class TestCommandParser:
    """指令解析器測試"""
    
    @pytest.fixture
    def parser(self) -> CommandParser:
        """建立解析器實例"""
        return CommandParser()
    
    # =========================================================================
    # 基本解析功能測試
    # =========================================================================
    
    def test_parser_singleton(self):
        """測試解析器單例模式"""
        parser1 = get_parser()
        parser2 = get_parser()
        assert parser1 is parser2
    
    def test_parse_empty_text(self, parser: CommandParser):
        """測試解析空白文字"""
        result = parser.parse("")
        assert result.command_type == CommandType.UNKNOWN
        assert result.error == "空白訊息"
    
    def test_parse_whitespace_only(self, parser: CommandParser):
        """測試解析純空白字元"""
        result = parser.parse("   ")
        assert result.command_type == CommandType.UNKNOWN
        assert result.error == "空白訊息"
    
    # =========================================================================
    # 幫助指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text", [
        "help",
        "幫助",
        "說明",
        "指令",
        "commands",
        "怎麼用",
        "如何使用",
    ])
    def test_parse_help_command(self, parser: CommandParser, text: str):
        """測試解析幫助指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.HELP
        assert result.is_valid()
        assert result.confidence == 1.0
    
    # =========================================================================
    # 待辦事項指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text,expected_content", [
        ("todo 買牛奶", "買牛奶"),
        ("待辦 開會", "開會"),
        ("新增待辦 寫報告", "寫報告"),
        ("記住要運動", "要運動"),
        ("記得要買菜", "要買菜"),
    ])
    def test_parse_add_todo_command(
        self, parser: CommandParser, text: str, expected_content: str
    ):
        """測試解析新增待辦指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.ADD_TODO
        assert result.is_valid()
        assert result.parameters.get("content") == expected_content
    
    def test_parse_todo_with_chinese_content(self, parser: CommandParser):
        """測試解析中文內容的待辦"""
        result = parser.parse("待辦 下午三點開會討論專案進度")
        assert result.command_type == CommandType.ADD_TODO
        assert "下午三點開會討論專案進度" in result.parameters.get("content", "")
    
    # =========================================================================
    # 筆記指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text,expected_content", [
        ("note 今天很開心", "今天很開心"),
        ("筆記 會議重點", "會議重點"),
        ("記錄 重要事項", "重要事項"),
        ("memo 備忘", "備忘"),
        ("記下 這個想法", "這個想法"),
    ])
    def test_parse_add_note_command(
        self, parser: CommandParser, text: str, expected_content: str
    ):
        """測試解析新增筆記指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.ADD_NOTE
        assert result.is_valid()
        assert result.parameters.get("content") == expected_content
    
    # =========================================================================
    # 支出記錄指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text,expected_amount,expected_desc", [
        ("花費 150 午餐", 150, "午餐"),
        ("支出 200 晚餐", 200, "晚餐"),
        ("花了 50 飲料", 50, "飲料"),
        ("$300 交通費", 300, "交通費"),
        ("150 元 零食", 150, "零食"),
    ])
    def test_parse_add_expense_command(
        self,
        parser: CommandParser,
        text: str,
        expected_amount: int,
        expected_desc: str,
    ):
        """測試解析支出記錄指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.ADD_EXPENSE
        assert result.is_valid()
        assert result.parameters.get("amount") == expected_amount
        assert expected_desc in result.parameters.get("description", "")
    
    def test_parse_expense_without_description(self, parser: CommandParser):
        """測試解析無說明的支出"""
        result = parser.parse("花費 100")
        assert result.command_type == CommandType.ADD_EXPENSE
        assert result.parameters.get("amount") == 100
    
    # =========================================================================
    # 提醒指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text,expected_content", [
        ("提醒我 開會", "開會"),
        ("提醒 打電話", "打電話"),
        ("remind 買東西", "買東西"),
    ])
    def test_parse_reminder_command(
        self, parser: CommandParser, text: str, expected_content: str
    ):
        """測試解析提醒指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.SET_REMINDER
        assert result.is_valid()
        assert expected_content in result.parameters.get("content", "")
    
    def test_parse_reminder_with_time(self, parser: CommandParser):
        """測試解析帶時間的提醒"""
        result = parser.parse("提醒我 開會 在 下午3點")
        assert result.command_type == CommandType.SET_REMINDER
        assert "開會" in result.parameters.get("content", "")
        assert "下午3點" in result.parameters.get("time", "")
    
    # =========================================================================
    # 工作流程指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text,expected_name", [
        ("建立流程 早安提醒", "早安提醒"),
        ("新增工作流程 每日報告", "每日報告"),
        ("create workflow morning routine", "morning routine"),
    ])
    def test_parse_create_workflow_command(
        self, parser: CommandParser, text: str, expected_name: str
    ):
        """測試解析建立工作流程指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.CREATE_WORKFLOW
        assert result.is_valid()
        assert expected_name in result.parameters.get("name", "")
    
    @pytest.mark.parametrize("text,expected_name", [
        ("執行流程 早安提醒", "早安提醒"),
        ("run workflow test", "test"),
        ("流程 每日報告", "每日報告"),
    ])
    def test_parse_run_workflow_command(
        self, parser: CommandParser, text: str, expected_name: str
    ):
        """測試解析執行工作流程指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.RUN_WORKFLOW
        assert result.is_valid()
        assert expected_name in result.parameters.get("name", "")
    
    @pytest.mark.parametrize("text", [
        "列出流程",
        "list workflows",
        "我的流程",
        "顯示所有工作流程",
    ])
    def test_parse_list_workflows_command(self, parser: CommandParser, text: str):
        """測試解析列出工作流程指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.LIST_WORKFLOWS
        assert result.is_valid()
    
    # =========================================================================
    # 整合服務指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text,expected_service", [
        ("連接 google", "google"),
        ("connect notion", "notion"),
        ("綁定 github", "github"),
    ])
    def test_parse_connect_service_command(
        self, parser: CommandParser, text: str, expected_service: str
    ):
        """測試解析連接服務指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.CONNECT_SERVICE
        assert result.is_valid()
        assert result.parameters.get("service") == expected_service
    
    @pytest.mark.parametrize("text", [
        "列出服務",
        "list services",
        "我的服務",
        "顯示已連接服務",
    ])
    def test_parse_list_services_command(self, parser: CommandParser, text: str):
        """測試解析列出服務指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.LIST_SERVICES
        assert result.is_valid()
    
    # =========================================================================
    # 系統指令測試
    # =========================================================================
    
    @pytest.mark.parametrize("text", [
        "status",
        "狀態",
        "stat",
    ])
    def test_parse_status_command(self, parser: CommandParser, text: str):
        """測試解析狀態指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.STATUS
        assert result.is_valid()
    
    @pytest.mark.parametrize("text", [
        "history",
        "歷史",
        "紀錄",
    ])
    def test_parse_history_command(self, parser: CommandParser, text: str):
        """測試解析歷史指令"""
        result = parser.parse(text)
        assert result.command_type == CommandType.HISTORY
        assert result.is_valid()
    
    # =========================================================================
    # 未知指令和 AI 解析測試
    # =========================================================================
    
    def test_parse_unknown_command(self, parser: CommandParser):
        """測試解析未知指令"""
        result = parser.parse("這是一段無法識別的文字 asdfgh")
        assert result.command_type == CommandType.UNKNOWN
        assert result.needs_ai is True
        assert result.confidence == 0.0
    
    def test_parse_natural_language_needs_ai(self, parser: CommandParser):
        """測試自然語言需要 AI 解析"""
        result = parser.parse("幫我規劃一個明天的行程")
        # 這種複雜的自然語言應該標記為需要 AI 解析
        assert result.needs_ai is True or result.command_type != CommandType.UNKNOWN
    
    # =========================================================================
    # 大小寫不敏感測試
    # =========================================================================
    
    @pytest.mark.parametrize("text", [
        "HELP",
        "Help",
        "hElP",
    ])
    def test_parse_case_insensitive(self, parser: CommandParser, text: str):
        """測試大小寫不敏感"""
        result = parser.parse(text)
        assert result.command_type == CommandType.HELP
    
    # =========================================================================
    # ParsedCommand 類別測試
    # =========================================================================
    
    def test_parsed_command_is_valid(self):
        """測試 ParsedCommand.is_valid() 方法"""
        valid_cmd = ParsedCommand(
            command_type=CommandType.HELP,
            raw_text="help",
        )
        assert valid_cmd.is_valid() is True
        
        invalid_cmd = ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text="???",
        )
        assert invalid_cmd.is_valid() is False
        
        error_cmd = ParsedCommand(
            command_type=CommandType.HELP,
            raw_text="help",
            error="some error",
        )
        assert error_cmd.is_valid() is False


class TestCommandParserAI:
    """指令解析器 AI 功能測試"""
    
    @pytest.fixture
    def parser(self) -> CommandParser:
        """建立解析器實例"""
        return CommandParser()
    
    @pytest.mark.asyncio
    async def test_parse_with_ai_not_implemented(self, parser: CommandParser):
        """測試 AI 解析（尚未實作）"""
        result = await parser.parse_with_ai("這是一段需要 AI 理解的文字")
        assert result.needs_ai is True
        assert result.error is not None  # 應該有錯誤訊息說明尚未實作
