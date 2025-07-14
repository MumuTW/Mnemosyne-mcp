FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Poetry
RUN pip install poetry

# 配置 Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# 複製 Poetry 配置文件
COPY pyproject.toml poetry.lock* ./

# 安裝依賴
RUN poetry install --only=main && rm -rf $POETRY_CACHE_DIR

# 複製應用程式碼
COPY src/ ./src/
COPY configs/ ./configs/

# 創建日誌目錄
RUN mkdir -p /app/logs

# 暴露端口
EXPOSE 8000 50051

# 設置環境變數
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動命令
CMD ["poetry", "run", "uvicorn", "mnemosyne.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
