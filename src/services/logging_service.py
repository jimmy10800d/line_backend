# 結構化日誌服務
# Structured Logging Service
"""
結構化日誌服務
==============

提供統一的日誌記錄功能：
- JSON 格式結構化日誌
- 自動添加時間戳記和上下文
- 支援不同日誌等級
- 可配置輸出目標
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from src.config import settings


class StructuredFormatter(logging.Formatter):
    """結構化 JSON 日誌格式器"""

    def format(self, record: logging.LogRecord) -> str:
        """
        將日誌記錄格式化為 JSON

        Args:
            record: 日誌記錄

        Returns:
            JSON 格式的日誌字串
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 添加額外的上下文資訊
        if hasattr(record, "extra"):
            log_data["context"] = record.extra
        elif record.__dict__.get("extra"):
            log_data["context"] = record.__dict__["extra"]

        # 從 record 中提取自定義欄位
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "extra",
            ]:
                if "context" not in log_data:
                    log_data["context"] = {}
                log_data["context"][key] = value

        # 添加例外資訊
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加位置資訊（僅 DEBUG 模式）
        if settings.debug:
            log_data["location"] = {
                "file": record.filename,
                "function": record.funcName,
                "line": record.lineno,
            }

        return json.dumps(log_data, ensure_ascii=False, default=str)


class SimpleFormatter(logging.Formatter):
    """簡單文字日誌格式器（用於開發環境）"""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """
        將日誌記錄格式化為可讀文字

        Args:
            record: 日誌記錄

        Returns:
            格式化的日誌字串
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET

        # 基本日誌訊息
        message = f"{color}[{timestamp}] {record.levelname:8s}{reset} | {record.name} | {record.getMessage()}"

        # 添加額外上下文
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "extra",
            ]:
                extra_data[key] = value

        if extra_data:
            message += f" | {json.dumps(extra_data, ensure_ascii=False, default=str)}"

        return message


class ContextLogger(logging.LoggerAdapter):
    """帶有上下文的日誌適配器"""

    def process(
        self, msg: str, kwargs: Dict[str, Any]
    ) -> tuple:
        """
        處理日誌訊息，添加上下文

        Args:
            msg: 日誌訊息
            kwargs: 關鍵字參數

        Returns:
            處理後的訊息和參數
        """
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


# 日誌器快取
_loggers: Dict[str, logging.Logger] = {}


def setup_logging() -> None:
    """
    設定應用程式日誌系統

    根據環境配置選擇適當的格式器和處理器
    """
    # 設定根日誌器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # 清除現有處理器
    root_logger.handlers.clear()

    # 建立控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # 根據環境選擇格式器
    if settings.debug:
        formatter = SimpleFormatter()
    else:
        formatter = StructuredFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 設定第三方庫日誌等級
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(
    name: str,
    context: Optional[Dict[str, Any]] = None
) -> ContextLogger:
    """
    取得日誌器實例

    Args:
        name: 日誌器名稱（通常使用 __name__）
        context: 可選的上下文資訊

    Returns:
        日誌器實例
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)

    return ContextLogger(_loggers[name], context or {})


# 初始化日誌系統
setup_logging()
