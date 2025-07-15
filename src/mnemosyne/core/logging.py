"""
日誌配置模組

統一配置結構化日誌，支持多種輸出格式和處理器。
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    handlers_config: list[Dict[str, Any]] = None,
) -> None:
    """
    設置結構化日誌

    Args:
        level: 日誌級別
        format_type: 格式類型 (json, console)
        handlers_config: 處理器配置列表
    """

    # 設置 structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if format_type == "json"
                else structlog.dev.ConsoleRenderer(colors=True)
            ),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 配置標準庫日誌
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # 設置根日誌記錄器
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # 默認處理器配置
    if handlers_config is None:
        handlers_config = [
            {"type": "console", "level": level},
        ]

    # 添加配置的處理器
    for handler_config in handlers_config:
        handler = create_handler(handler_config, format_type)
        if handler:
            root_logger.addHandler(handler)

    # 設置第三方庫的日誌級別
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("falkordb").setLevel(logging.WARNING)


def create_handler(
    config: Dict[str, Any], format_type: str = "json"
) -> logging.Handler:
    """
    根據配置創建日誌處理器

    Args:
        config: 處理器配置
        format_type: 格式類型

    Returns:
        logging.Handler: 日誌處理器
    """
    handler_type = config.get("type", "console")
    level = config.get("level", "INFO")

    if handler_type == "console":
        handler = logging.StreamHandler(sys.stdout)

    elif handler_type == "file":
        filename = config.get("filename", "logs/mnemosyne.log")
        max_bytes = config.get("max_bytes", 10 * 1024 * 1024)  # 10MB
        backup_count = config.get("backup_count", 5)

        # 確保日誌目錄存在
        log_file = Path(filename)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )

    elif handler_type == "syslog":
        handler = logging.handlers.SysLogHandler()

    else:
        print(f"Warning: Unknown handler type '{handler_type}', using console handler")
        handler = logging.StreamHandler(sys.stdout)

    # 設置日誌級別
    handler.setLevel(getattr(logging, level.upper()))

    # 設置格式器
    if format_type == "json":
        formatter = logging.Formatter("%(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)

    return handler


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    獲取結構化日誌記錄器

    Args:
        name: 日誌記錄器名稱

    Returns:
        structlog.BoundLogger: 結構化日誌記錄器
    """
    return structlog.get_logger(name)


class LoggingMiddleware:
    """
    FastAPI 日誌中間件

    記錄請求和響應信息
    """

    def __init__(self, app):
        self.app = app
        self.logger = get_logger("api.middleware")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 記錄請求開始
        request_id = self._generate_request_id()
        start_time = self._get_current_time()

        self.logger.info(
            "Request started",
            request_id=request_id,
            method=scope["method"],
            path=scope["path"],
            query_string=scope.get("query_string", b"").decode(),
            client=scope.get("client"),
        )

        # 包裝 send 函數以記錄響應
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message["status"]
                duration = self._get_current_time() - start_time

                self.logger.info(
                    "Request completed",
                    request_id=request_id,
                    status_code=status_code,
                    duration_ms=duration * 1000,
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _generate_request_id(self) -> str:
        """生成請求ID"""
        import uuid

        return str(uuid.uuid4())[:8]

    def _get_current_time(self) -> float:
        """獲取當前時間戳"""
        import time

        return time.time()


def configure_uvicorn_logging():
    """配置 Uvicorn 日誌"""

    # 禁用 Uvicorn 的默認日誌配置
    logging.getLogger("uvicorn.error").handlers = []
    logging.getLogger("uvicorn.access").handlers = []

    # 使用我們的日誌配置
    uvicorn_logger = get_logger("uvicorn")
    access_logger = get_logger("uvicorn.access")

    # 重定向 Uvicorn 日誌到我們的日誌系統
    class StructlogHandler(logging.Handler):
        def __init__(self, logger):
            super().__init__()
            self.struct_logger = logger

        def emit(self, record):
            self.struct_logger.info(record.getMessage())

    logging.getLogger("uvicorn.error").addHandler(StructlogHandler(uvicorn_logger))
    logging.getLogger("uvicorn.access").addHandler(StructlogHandler(access_logger))
