FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv
RUN pip install uv

# 複製專案配置和源碼
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY configs/ ./configs/

# 安裝依賴（不包含開發依賴）
RUN uv pip install --system -e .

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
CMD ["python", "-m", "uvicorn", "mnemosyne.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
