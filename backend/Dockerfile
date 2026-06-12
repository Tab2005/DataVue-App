FROM python:3.12-slim

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴（PostgreSQL 客戶端與 curl 供健康檢查使用）
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

RUN chmod +x /app/entrypoint.sh

# 建立非 root 使用者（安全最佳實踐）
RUN useradd --system --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# 暴露埠號
EXPOSE 8000

# 健康檢查（配合 /health 端點）
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動命令
CMD ["sh", "/app/entrypoint.sh"]
