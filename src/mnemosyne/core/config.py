"""
配置管理模組

統一管理應用程式的配置，支持環境變數和配置文件。
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..interfaces.graph_store import ConnectionConfig


class DatabaseSettings(BaseSettings):
    """資料庫配置"""

    model_config = SettingsConfigDict(env_prefix="FALKORDB_", case_sensitive=False)

    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    database: str = Field(default="mnemosyne")
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    connection_pool_size: int = Field(default=10)
    connection_timeout: int = Field(default=30)
    query_timeout: int = Field(default=60)

    def to_connection_config(self) -> ConnectionConfig:
        """轉換為 ConnectionConfig"""
        return ConnectionConfig(
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            password=self.password,
            connection_pool_size=self.connection_pool_size,
            connection_timeout=self.connection_timeout,
            query_timeout=self.query_timeout,
        )


class APISettings(BaseSettings):
    """API 配置"""

    model_config = SettingsConfigDict(env_prefix="API_", case_sensitive=False)

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    grpc_port: int = Field(default=50051, alias="GRPC_PORT")

    # CORS 配置
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])

    # 安全配置
    secret_key: str = Field(default="dev-secret-key", alias="SECRET_KEY")
    api_key_header: str = Field(default="X-API-Key", alias="API_KEY_HEADER")


class LoggingSettings(BaseSettings):
    """日誌配置"""

    model_config = SettingsConfigDict(env_prefix="LOG_", case_sensitive=False)

    level: str = Field(default="INFO")
    format: str = Field(default="json")

    # 處理器配置
    handlers: List[Dict[str, Any]] = Field(
        default_factory=lambda: [
            {"type": "console", "level": "INFO"},
            {"type": "file", "level": "DEBUG", "filename": "logs/mnemosyne.log"},
        ]
    )


class SecuritySettings(BaseSettings):
    """安全配置"""

    model_config = SettingsConfigDict(case_sensitive=False)

    secret_key: str = Field(
        default="dev-secret-key-change-in-production", alias="SECRET_KEY"
    )
    api_key_header: str = Field(default="X-API-Key", alias="API_KEY_HEADER")

    # JWT 配置（為未來功能預留）
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=30)


class FeatureSettings(BaseSettings):
    """功能開關配置"""

    model_config = SettingsConfigDict(case_sensitive=False)

    enable_metrics: bool = Field(default=False, alias="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, alias="METRICS_PORT")
    enable_tracing: bool = Field(default=False)
    enable_debug_queries: bool = Field(default=True)


class Settings(BaseSettings):
    """主配置類"""

    # 環境配置
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    features: FeatureSettings = Field(default_factory=FeatureSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """驗證環境配置"""
        valid_envs = ["development", "testing", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v

    @property
    def is_development(self) -> bool:
        """是否為開發環境"""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """是否為生產環境"""
        return self.environment == "production"

    @property
    def config_file_path(self) -> Path:
        """獲取配置文件路徑"""
        return Path(f"configs/{self.environment}.yaml")


def load_yaml_config_if_exists() -> Dict[str, Any]:
    """
    從 YAML 配置文件加載配置（如果存在）

    提供回退處理，確保應用可以在沒有配置文件的情況下啟動
    """
    environment = os.getenv("ENVIRONMENT", "development")
    config_file = Path(f"configs/{environment}.yaml")

    # 如果 configs 目錄不存在，創建它
    config_file.parent.mkdir(parents=True, exist_ok=True)

    if not config_file.exists():
        print(
            f"Info: Config file {config_file} not found, "
            "using defaults and environment variables"
        )
        return {}

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        print(f"Info: Loaded config from {config_file}")
        return config_data

    except Exception as e:
        # 配置文件讀取失敗時記錄錯誤但不中斷啟動
        print(f"Warning: Failed to load config file {config_file}: {e}")
        print("Info: Continuing with defaults and environment variables")
        return {}


@lru_cache()
def get_settings() -> Settings:
    """
    獲取配置實例

    使用 lru_cache 確保單例模式
    """
    # 簡單地使用 Pydantic Settings 的默認行為
    # 它會自動從 .env 文件和環境變數加載配置
    return Settings()


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    從指定文件加載配置

    Args:
        config_path: 配置文件路徑

    Returns:
        Dict[str, Any]: 配置字典
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        if config_file.suffix.lower() in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        elif config_file.suffix.lower() == ".json":
            import json

            return json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_file.suffix}")


def validate_config(settings: Settings) -> List[str]:
    """
    驗證配置的完整性和合理性

    Args:
        settings: 配置實例

    Returns:
        List[str]: 驗證錯誤列表，空列表表示驗證通過
    """
    errors = []

    # 驗證資料庫配置
    if not settings.database.host:
        errors.append("Database host is required")

    if settings.database.port <= 0 or settings.database.port > 65535:
        errors.append("Database port must be between 1 and 65535")

    # 驗證 API 配置
    if settings.api.port <= 0 or settings.api.port > 65535:
        errors.append("API port must be between 1 and 65535")

    if settings.api.grpc_port <= 0 or settings.api.grpc_port > 65535:
        errors.append("gRPC port must be between 1 and 65535")

    if settings.api.port == settings.api.grpc_port:
        errors.append("API port and gRPC port cannot be the same")

    # 驗證安全配置
    if (
        settings.is_production
        and settings.security.secret_key == "dev-secret-key-change-in-production"
    ):
        errors.append("Secret key must be changed in production environment")

    # 驗證日誌配置
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.logging.level.upper() not in valid_log_levels:
        errors.append(f"Log level must be one of: {valid_log_levels}")

    return errors
