# 請求日誌中介軟體
# Request Logger Middleware
"""
請求日誌中介軟體
================

記錄所有 HTTP 請求和回應：
- 請求方法、路徑、查詢參數
- 回應狀態碼和處理時間
- 結構化 JSON 日誌格式
"""

import time
import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """請求日誌中介軟體"""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        記錄請求和回應資訊

        Args:
            request: HTTP 請求
            call_next: 下一個處理器

        Returns:
            HTTP 回應
        """
        # 生成請求 ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # 記錄開始時間
        start_time = time.time()

        # 請求開始日誌
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            },
        )

        # 處理請求
        response = await call_next(request)

        # 計算處理時間
        process_time = time.time() - start_time

        # 請求完成日誌
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            },
        )

        # 添加請求 ID 到回應標頭
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        return response
