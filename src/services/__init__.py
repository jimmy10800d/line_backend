# 業務邏輯服務模組
# Business Logic Services Module
"""
服務套件
========

包含所有業務邏輯服務：
- line_service.py: LINE 訊息處理服務
- logging_service.py: 結構化日誌服務
- ai_service.py: AI 對話服務（OpenAI）
- task_executor.py: 任務執行器
- workflow_service.py: 工作流程引擎
- scheduler_service.py: 排程服務
- execution_log_service.py: 執行日誌服務

注意：為避免循環匯入，ai_service 和 task_executor 需要直接匯入。
例如：from src.services.ai_service import AIService
"""

from .line_service import LineService, get_line_service
from .logging_service import get_logger, setup_logging

# 延遲匯入，避免循環匯入問題
# from .ai_service import AIService, AIIntent, get_ai_service
# from .task_executor import TaskExecutor, AsyncTaskExecutor, get_task_executor

__all__ = [
    "LineService",
    "get_line_service",
    "get_logger",
    "setup_logging",
]
