# LINE 自動化流程引擎 - FastAPI 應用程式入口
# LINE Workflow Automation Engine - FastAPI Application Entry Point
"""
FastAPI 應用程式主模組
======================

這是應用程式的主要入口點，負責：
1. 建立 FastAPI 應用程式實例
2. 配置中介軟體（CORS、錯誤處理等）
3. 註冊 API 路由
4. 配置靜態檔案和模板
5. 設定應用程式生命週期事件

啟動方式：
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import engine, logger, settings
from src.models.base import Base


# =============================================================================
# 應用程式生命週期
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    應用程式生命週期管理
    
    在應用程式啟動和關閉時執行初始化和清理工作。
    
    啟動時：
    - 建立資料庫連線
    - 初始化資料表（如果不存在）
    - 啟動排程器
    
    關閉時：
    - 關閉資料庫連線
    - 停止排程器
    """
    # ===== 啟動 =====
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.app_name} 啟動中...")
    logger.info(f"📍 環境：{settings.app_env}")
    logger.info(f"🔧 除錯模式：{settings.debug}")
    logger.info("=" * 50)
    
    # 註冊處理器
    from src.commands.handlers.registry import register_all_handlers
    register_all_handlers()
    logger.info("✅ 指令處理器註冊完成")
    
    # 建立資料表（如果不存在）
    async with engine.begin() as conn:
        # 匯入所有模型
        from src.models.user import User
        from src.models.workflow import Workflow
        from src.models.execution_log import ExecutionLog
        from src.models.integration import Integration
        from src.models.schedule import Schedule
        
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ 資料庫初始化完成")
    
    # TODO: 啟動排程器（Phase 6 實作）
    
    logger.info("✅ 應用程式啟動完成！")
    logger.info(f"📡 API 文檔：http://{settings.host}:{settings.port}/docs")
    
    yield  # 應用程式運行中
    
    # ===== 關閉 =====
    logger.info("🛑 應用程式關閉中...")
    
    # 關閉資料庫連線
    await engine.dispose()
    logger.info("✅ 資料庫連線已關閉")
    
    # TODO: 停止排程器（Phase 6 實作）
    
    logger.info("👋 應用程式已關閉")


# =============================================================================
# 建立 FastAPI 應用程式
# =============================================================================


app = FastAPI(
    title=settings.app_name,
    description="""
    ## LINE 自動化流程引擎 API
    
    以 LINE 為操作介面的個人自動化助手，整合 AI 對話理解，
    支援 Google Calendar、Notion、GitHub 外部服務整合。
    
    ### 主要功能
    
    - **LINE Webhook**: 接收和處理 LINE 訊息
    - **工作流程管理**: 建立、編輯、執行自訂工作流程
    - **外部服務整合**: OAuth 授權和 API 整合
    - **排程任務**: 定時執行工作流程
    - **執行歷史**: 查看任務執行紀錄
    
    ### 開發方法
    
    本專案採用 **BDD + TDD** 開發方法論。
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# =============================================================================
# 中介軟體配置
# =============================================================================


# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],  # 生產環境應限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 請求日誌和錯誤處理中介軟體
from src.middleware.error_handler import (
    ErrorHandlerMiddleware,
    setup_exception_handlers,
)
from src.middleware.request_logger import RequestLoggerMiddleware

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RequestLoggerMiddleware)

# 設定例外處理器
setup_exception_handlers(app)


# =============================================================================
# 錯誤處理
# =============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全域例外處理器
    
    捕捉所有未處理的例外，記錄錯誤並返回統一格式的錯誤回應。
    
    Args:
        request: HTTP 請求
        exc: 例外物件
    
    Returns:
        JSONResponse: 錯誤回應
    """
    logger.error(
        "未處理的例外",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    
    # 開發環境顯示詳細錯誤，生產環境隱藏
    detail = str(exc) if settings.debug else "內部伺服器錯誤"
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": detail,
        }
    )


# =============================================================================
# 健康檢查端點
# =============================================================================


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    健康檢查端點
    
    用於監控系統是否正常運行。
    
    Returns:
        dict: 健康狀態資訊
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "0.1.0",
        "environment": settings.app_env,
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    根路徑端點
    
    返回 API 基本資訊和文檔連結。
    
    Returns:
        dict: API 資訊
    """
    return {
        "message": f"歡迎使用 {settings.app_name} API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


# =============================================================================
# 註冊 API 路由
# =============================================================================


# 註冊 LINE Webhook 路由
from src.api.webhook import router as webhook_router
app.include_router(webhook_router)

# TODO: 註冊工作流程 API（Phase 4）
# from src.api.workflows import router as workflows_router
# app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])

# TODO: 註冊整合服務 API（Phase 5）
# from src.api.integrations import router as integrations_router
# app.include_router(integrations_router, prefix="/api/integrations", tags=["Integrations"])

# TODO: 註冊排程 API（Phase 6）
# from src.api.schedules import router as schedules_router
# app.include_router(schedules_router, prefix="/api/schedules", tags=["Schedules"])

# TODO: 註冊歷史 API（Phase 7）
# from src.api.history import router as history_router
# app.include_router(history_router, prefix="/api/history", tags=["History"])

# TODO: 註冊網頁路由（Phase 8）
# from src.web.routes import router as web_router
# app.include_router(web_router)


# =============================================================================
# 主程式入口
# =============================================================================


def main() -> None:
    """
    主程式入口
    
    使用 uvicorn 啟動應用程式。
    主要用於 `python -m src.main` 或 pyproject.toml 中的 scripts 入口。
    """
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
