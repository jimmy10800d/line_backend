# 全域錯誤處理中介軟體
# Global Error Handler Middleware
"""
全域錯誤處理中介軟體
==================

提供統一的錯誤處理和回應格式：
- 捕獲未處理的例外
- 記錄錯誤日誌
- 返回標準化錯誤回應
"""

import traceback
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全域錯誤處理中介軟體"""

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        處理請求並捕獲任何未處理的例外

        Args:
            request: HTTP 請求
            call_next: 下一個處理器

        Returns:
            HTTP 回應
        """
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 記錄詳細錯誤資訊
            logger.error(
                "Unhandled exception",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "path": request.url.path,
                    "method": request.method,
                    "traceback": traceback.format_exc(),
                },
            )

            # 返回標準化錯誤回應
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                    },
                },
            )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    設定 FastAPI 例外處理器

    Args:
        app: FastAPI 應用程式實例
    """
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """處理 HTTP 例外"""
        logger.warning(
            "HTTP exception",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """處理請求驗證錯誤"""
        logger.warning(
            "Validation error",
            extra={
                "errors": exc.errors(),
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                },
            },
        )
