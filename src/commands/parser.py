# 指令解析器
# Command Parser
"""
指令解析器
==========

負責解析 LINE 訊息中的指令：
- 識別指令類型（預設任務、工作流程、整合）
- 提取參數和選項
- 支援自然語言輸入（透過 AI 解析）
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class CommandType(Enum):
    """指令類型列舉"""
    
    # 預設任務
    ADD_TODO = "add_todo"           # 新增待辦事項
    ADD_NOTE = "add_note"           # 新增筆記
    ADD_EXPENSE = "add_expense"     # 記錄支出
    SET_REMINDER = "set_reminder"   # 設定提醒
    WEATHER = "weather"             # 查詢天氣
    
    # 工作流程
    CREATE_WORKFLOW = "create_workflow"   # 建立工作流程
    RUN_WORKFLOW = "run_workflow"         # 執行工作流程
    LIST_WORKFLOWS = "list_workflows"     # 列出工作流程
    EDIT_WORKFLOW = "edit_workflow"       # 編輯工作流程
    DELETE_WORKFLOW = "delete_workflow"   # 刪除工作流程
    TOGGLE_WORKFLOW = "toggle_workflow"   # 切換工作流程狀態
    ADD_STEP = "add_step"                 # 新增步驟
    REMOVE_STEP = "remove_step"           # 移除步驟
    
    # 外部服務整合
    CONNECT_SERVICE = "connect_service"       # 連接外部服務
    DISCONNECT_SERVICE = "disconnect_service" # 斷開外部服務
    LIST_SERVICES = "list_services"           # 列出已連接服務
    
    # 系統指令
    HELP = "help"           # 顯示說明
    STATUS = "status"       # 顯示狀態
    HISTORY = "history"     # 查看歷史
    
    # 未知/需要 AI 解析
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    """解析後的指令資料結構"""
    
    command_type: CommandType
    """指令類型"""
    
    raw_text: str
    """原始文字"""
    
    parameters: Dict[str, Any] = field(default_factory=dict)
    """解析出的參數"""
    
    confidence: float = 1.0
    """解析信心度（0.0-1.0）"""
    
    needs_ai: bool = False
    """是否需要 AI 進一步解析"""
    
    error: Optional[str] = None
    """解析錯誤訊息（如果有）"""
    
    def is_valid(self) -> bool:
        """檢查指令是否有效"""
        return self.command_type != CommandType.UNKNOWN and self.error is None


class CommandParser:
    """
    指令解析器
    
    支援兩種模式：
    1. 規則匹配：使用正規表示式匹配預定義指令
    2. AI 解析：使用 GPT 理解自然語言（當規則匹配失敗時）
    """
    
    # 預設任務指令模式
    # 注意：順序很重要！更具體的模式應該放在前面
    PATTERNS = {
        # 系統指令 - 最先匹配
        CommandType.HELP: [
            r"^(?:help|幫助|說明|指令|commands?)$",
            r"^(?:怎麼用|如何使用|使用說明)$",
        ],
        
        CommandType.STATUS: [
            r"^(?:status|狀態|stat)$",
        ],
        
        CommandType.HISTORY: [
            r"^(?:history|歷史|紀錄)$",
        ],
        
        # 提醒 - 在 ADD_TODO 之前匹配
        CommandType.SET_REMINDER: [
            r"^(?:提醒我?|remind|reminder)\s+(.+)\s+(?:在|at|@)\s*(.+)$",
            r"^(?:提醒我?|remind|reminder)\s+(.+)$",
        ],
        
        # 天氣查詢
        CommandType.WEATHER: [
            r"^(?:weather|天氣|查天氣)\s+(.+)$",
            r"^(?:天氣|查天氣)$",  # 無參數時使用預設城市
        ],
        
        # 待辦事項：todo xxx, 待辦 xxx, 新增待辦 xxx
        # 注意：「提醒」開頭的指令由 SET_REMINDER 處理
        CommandType.ADD_TODO: [
            r"^(?:todo|待辦|新增待辦|新增todo)\s+(.+)$",
            r"^(?:記住|記得)\s*(.+)$",
        ],
        
        # 筆記：note xxx, 筆記 xxx, 記錄 xxx
        CommandType.ADD_NOTE: [
            r"^(?:note|筆記|記錄|memo)\s+(.+)$",
            r"^(?:記下|寫下)\s+(.+)$",
        ],
        
        # 支出：花費 xxx 元, $xxx, 支出 xxx
        CommandType.ADD_EXPENSE: [
            r"^(?:花費|支出|花了|消費)\s*\$?(\d+)\s*(?:元)?(?:\s+(.+))?$",
            r"^\$(\d+)\s*(.*)$",
            r"^(\d+)\s*(?:元|塊)\s+(.+)$",
        ],
        
        # 工作流程
        CommandType.LIST_WORKFLOWS: [
            r"^(?:列出|list|顯示)\s*(?:所有)?(?:工作)?(?:流程|workflows?)$",
            r"^list\s+workflows?$",
            r"^我的?流程$",
        ],
        
        CommandType.CREATE_WORKFLOW: [
            r"^(?:建立|新增|create)\s*(?:工作)?(?:流程|workflow)\s+(.+)$",
            r"^create\s+workflow\s+(.+)$",
        ],
        
        CommandType.RUN_WORKFLOW: [
            r"^(?:執行|run|start)\s*(?:工作)?(?:流程|workflow)\s+(.+)$",
            r"^run\s+workflow\s+(.+)$",
            r"^run\s+(.+)$",
            r"^流程\s+(.+)$",
        ],
        
        CommandType.EDIT_WORKFLOW: [
            r"^(?:編輯|edit|修改)\s*(?:工作)?(?:流程|workflow)\s+(.+)$",
            r"^edit\s+workflow\s+(.+)$",
        ],
        
        CommandType.DELETE_WORKFLOW: [
            r"^(?:刪除|delete|移除)\s*(?:工作)?(?:流程|workflow)\s+(.+)$",
            r"^delete\s+workflow\s+(.+)$",
        ],
        
        CommandType.TOGGLE_WORKFLOW: [
            r"^(?:切換|toggle)\s*(?:工作)?(?:流程|workflow)\s+(.+)$",
            r"^toggle\s+workflow\s+(.+)$",
            r"^(?:啟用|停用)\s*(?:工作)?(?:流程|workflow)\s+(.+)$",
        ],
        
        CommandType.ADD_STEP: [
            r"^(?:新增|add)\s*步驟\s+(.+?)\s+(.+)$",
            r"^add\s+step\s+(.+?)\s+(.+)$",
        ],
        
        CommandType.REMOVE_STEP: [
            r"^(?:移除|remove)\s*步驟\s+(.+?)\s+(\d+)$",
            r"^remove\s+step\s+(.+?)\s+(\d+)$",
        ],
        
        # 整合服務
        CommandType.LIST_SERVICES: [
            r"^(?:列出|list|顯示)\s*(?:已連接的?)?(?:服務|services?)$",
            r"^list\s+services?$",
            r"^我的?服務$",
        ],
        
        CommandType.CONNECT_SERVICE: [
            r"^(?:連接|connect|綁定)\s+(google|notion|github)$",
        ],
    }
    
    def __init__(self):
        """初始化解析器"""
        self._compiled_patterns: Dict[CommandType, List[re.Pattern]] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """編譯正規表示式模式"""
        for cmd_type, patterns in self.PATTERNS.items():
            self._compiled_patterns[cmd_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def parse(self, text: str) -> ParsedCommand:
        """
        解析指令文字
        
        Args:
            text: 原始訊息文字
        
        Returns:
            ParsedCommand: 解析結果
        """
        # 清理文字
        text = text.strip()
        
        if not text:
            return ParsedCommand(
                command_type=CommandType.UNKNOWN,
                raw_text=text,
                error="空白訊息",
            )
        
        logger.debug(f"Parsing command: {text}")
        
        # 嘗試規則匹配
        result = self._match_patterns(text)
        if result.command_type != CommandType.UNKNOWN:
            logger.info(
                f"Command parsed: {result.command_type.value}",
                extra={"parameters": result.parameters},
            )
            return result
        
        # 規則匹配失敗，標記需要 AI 解析
        logger.debug("Pattern matching failed, needs AI parsing")
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text=text,
            needs_ai=True,
            confidence=0.0,
        )
    
    def _match_patterns(self, text: str) -> ParsedCommand:
        """
        使用規則匹配解析指令
        
        Args:
            text: 原始訊息文字
        
        Returns:
            ParsedCommand: 匹配結果
        """
        for cmd_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                match = pattern.match(text)
                if match:
                    return self._extract_parameters(cmd_type, text, match)
        
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text=text,
        )
    
    def _extract_parameters(
        self,
        cmd_type: CommandType,
        text: str,
        match: re.Match
    ) -> ParsedCommand:
        """
        從正規表示式匹配結果提取參數
        
        Args:
            cmd_type: 指令類型
            text: 原始文字
            match: 正規表示式匹配結果
        
        Returns:
            ParsedCommand: 包含參數的解析結果
        """
        params: Dict[str, Any] = {}
        groups = match.groups()
        
        # 根據指令類型提取參數
        if cmd_type == CommandType.ADD_TODO:
            params["content"] = groups[0].strip() if groups else text
            
        elif cmd_type == CommandType.ADD_NOTE:
            params["content"] = groups[0].strip() if groups else text
            
        elif cmd_type == CommandType.ADD_EXPENSE:
            params["amount"] = int(groups[0]) if groups else 0
            params["description"] = groups[1].strip() if len(groups) > 1 and groups[1] else ""
            
        elif cmd_type == CommandType.SET_REMINDER:
            params["content"] = groups[0].strip() if groups else ""
            params["time"] = groups[1].strip() if len(groups) > 1 and groups[1] else None
        
        elif cmd_type == CommandType.WEATHER:
            params["city"] = groups[0].strip() if groups and groups[0] else "台北"  # 預設台北
            
        elif cmd_type in (CommandType.CREATE_WORKFLOW, CommandType.RUN_WORKFLOW, 
                          CommandType.EDIT_WORKFLOW, CommandType.DELETE_WORKFLOW,
                          CommandType.TOGGLE_WORKFLOW):
            params["name"] = groups[0].strip() if groups else ""
            
        elif cmd_type == CommandType.ADD_STEP:
            params["workflow_name"] = groups[0].strip() if groups else ""
            params["action"] = groups[1].strip() if len(groups) > 1 else ""
            
        elif cmd_type == CommandType.REMOVE_STEP:
            params["workflow_name"] = groups[0].strip() if groups else ""
            params["step_order"] = groups[1].strip() if len(groups) > 1 else ""
            
        elif cmd_type == CommandType.CONNECT_SERVICE:
            params["service"] = groups[0].lower() if groups else ""
        
        return ParsedCommand(
            command_type=cmd_type,
            raw_text=text,
            parameters=params,
            confidence=1.0,
        )
    
    async def parse_with_ai(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ParsedCommand:
        """
        使用 AI 解析自然語言指令
        
        Args:
            text: 原始訊息文字
            context: 額外的上下文資訊
        
        Returns:
            ParsedCommand: AI 解析結果
        """
        # TODO: 整合 OpenAI GPT-4o-mini（T030-T032）
        # 這裡先返回需要 AI 解析的標記
        logger.info(f"AI parsing required for: {text}")
        
        return ParsedCommand(
            command_type=CommandType.UNKNOWN,
            raw_text=text,
            needs_ai=True,
            confidence=0.0,
            error="AI 解析功能尚未實作",
        )


# 單例模式
_parser: Optional[CommandParser] = None


def get_parser() -> CommandParser:
    """取得指令解析器單例"""
    global _parser
    if _parser is None:
        _parser = CommandParser()
    return _parser
