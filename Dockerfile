# LINE 自動化流程引擎 - Docker 配置
# LINE Workflow Automation Engine - Dockerfile
#
# 建置方式：docker build -t line-workflow .
# 執行方式：docker run -p 8000:8000 --env-file .env line-workflow

# ===== 基礎映像 =====
FROM python:3.11-slim as base

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 設定工作目錄
WORKDIR /app

# ===== 建置階段 =====
FROM base as builder

# 安裝建置依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴清單
COPY requirements.txt .

# 安裝 Python 依賴到虛擬環境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ===== 執行階段 =====
FROM base as runtime

# 建立非 root 使用者（安全性）
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# 從建置階段複製虛擬環境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 複製應用程式碼
COPY --chown=appuser:appgroup . .

# 建立資料目錄
RUN mkdir -p /app/data && chown -R appuser:appgroup /app/data

# 切換到非 root 使用者
USER appuser

# 暴露埠號
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# 啟動指令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
