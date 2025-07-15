"""
FastAPI 主應用

這是 Mnemosyne MCP 的 REST API 入口點，提供 HTTP/JSON 接口。
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.config import Settings, get_settings, validate_config
from ..core.logging import LoggingMiddleware, get_logger, setup_logging
from ..drivers.falkordb_driver import FalkorDBDriver
from ..interfaces.graph_store import ConnectionError, GraphStoreClient
from ..schemas.api import ErrorResponse, HealthResponse, HealthStatus

# 全局變數
graph_client: GraphStoreClient = None
app_start_time: float = None
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用生命週期管理

    處理應用啟動和關閉時的初始化和清理工作。
    """
    global graph_client, app_start_time

    # 啟動時初始化
    settings = get_settings()

    # 設置日誌
    setup_logging(
        level=settings.logging.level,
        format_type=settings.logging.format,
        handlers_config=settings.logging.handlers,
    )

    logger.info(
        "Starting Mnemosyne MCP API", version="0.1.0", environment=settings.environment
    )

    # 驗證配置
    config_errors = validate_config(settings)
    if config_errors:
        logger.error("Configuration validation failed", errors=config_errors)
        raise RuntimeError(f"Configuration errors: {config_errors}")

    # 初始化圖資料庫客戶端
    try:
        db_config = settings.database.to_connection_config()
        graph_client = FalkorDBDriver(db_config)
        await graph_client.connect()
        logger.info("Successfully connected to graph database")
    except Exception as e:
        logger.error("Failed to connect to graph database", error=str(e))
        # 在開發環境中，我們允許在沒有資料庫的情況下啟動
        if not settings.is_development:
            raise
        graph_client = None

    app_start_time = time.time()
    logger.info("Mnemosyne MCP API started successfully")

    yield

    # 關閉時清理
    logger.info("Shutting down Mnemosyne MCP API")

    if graph_client:
        try:
            await graph_client.disconnect()
            logger.info("Graph database connection closed")
        except Exception as e:
            logger.error("Error closing graph database connection", error=str(e))

    logger.info("Mnemosyne MCP API shutdown complete")


# 創建 FastAPI 應用
app = FastAPI(
    title="Mnemosyne MCP API",
    description="主動的、有狀態的軟體知識圖譜引擎",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# 添加中間件
settings = get_settings()

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=settings.api.cors_allow_credentials,
    allow_methods=settings.api.cors_allow_methods,
    allow_headers=settings.api.cors_allow_headers,
)

# 日誌中間件
app.add_middleware(LoggingMiddleware)


def get_graph_client() -> GraphStoreClient:
    """
    依賴注入：獲取圖資料庫客戶端

    Returns:
        GraphStoreClient: 圖資料庫客戶端實例

    Raises:
        HTTPException: 當資料庫連接不可用時
    """
    if graph_client is None:
        raise HTTPException(
            status_code=503, detail="Graph database connection not available"
        )
    return graph_client


def get_current_settings() -> Settings:
    """
    依賴注入：獲取當前配置

    Returns:
        Settings: 配置實例
    """
    return get_settings()


# 全局異常處理器
@app.exception_handler(ConnectionError)
async def connection_error_handler(request, exc: ConnectionError):
    """處理資料庫連接錯誤"""
    logger.error("Database connection error", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error="DatabaseConnectionError",
            message="Unable to connect to graph database",
            details={"original_error": str(exc)},
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """處理一般異常"""
    logger.error(
        "Unhandled exception", error=str(exc), path=request.url.path, exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__},
        ).model_dump(),
    )


# API 端點
@app.get("/", response_model=Dict[str, Any])
async def root():
    """根端點，提供 API 基本信息"""
    return {
        "name": "Mnemosyne MCP API",
        "version": "0.1.0",
        "description": "主動的、有狀態的軟體知識圖譜引擎",
        "docs_url": "/docs",
        "health_url": "/health",
        "status": "running",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check(
    client: GraphStoreClient = Depends(get_graph_client),
    settings: Settings = Depends(get_current_settings),
):
    """
    健康檢查端點

    檢查服務和依賴組件的健康狀態。
    """

    logger.debug("Health check requested")

    # 計算運行時間
    uptime_seconds = time.time() - app_start_time if app_start_time else 0

    # 檢查圖資料庫健康狀態
    db_health = await client.healthcheck()

    # 獲取內存使用情況
    try:
        import psutil

        process = psutil.Process()
        memory_usage_mb = process.memory_info().rss / 1024 / 1024
    except ImportError:
        memory_usage_mb = None

    # 組件狀態
    components = {
        "database": db_health,
        "api": {
            "status": "healthy",
            "host": settings.api.host,
            "port": settings.api.port,
            "environment": settings.environment,
        },
    }

    # 確定整體健康狀態
    overall_status = HealthStatus.HEALTHY
    if db_health.get("status") != "healthy":
        overall_status = HealthStatus.UNHEALTHY

    response = HealthResponse(
        status=overall_status,
        uptime_seconds=uptime_seconds,
        memory_usage_mb=memory_usage_mb,
        components=components,
    )

    logger.debug("Health check completed", status=overall_status.value)

    return response


@app.get("/version")
async def get_version():
    """獲取版本信息"""
    return {
        "version": "0.1.0",
        "build": "sprint-0",
        "api_version": "v1",
        "environment": get_settings().environment,
    }


# 包含其他路由模組（為未來的端點預留）
# from .routes import projects, search, analysis
# app.include_router(projects.router, prefix="/v1/projects", tags=["projects"])
# app.include_router(search.router, prefix="/v1/search", tags=["search"])
# app.include_router(analysis.router, prefix="/v1/analysis", tags=["analysis"])


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "mnemosyne.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.is_development,
        log_config=None,  # 使用我們自己的日誌配置
    )
