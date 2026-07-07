FROM python:3.12-slim

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴（PostgreSQL 客戶端、curl 供健康檢查使用、ffmpeg 供 Meta Andromeda
# 影片素材抽取關鍵影格使用，見 modules/meta_andromeda/video_utils.py）
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 建立非 root 使用者（安全最佳實踐）
RUN useradd --system --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# 暴露埠號
EXPOSE 8000

# 健康檢查：SERVICE_ROLE=worker 時走 worker_main.py 的 /healthz，其餘走 main.py 的 /health
# （docs/24 Wave 2 獨立 Meta Andromeda Worker）
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD sh -c 'if [ "$SERVICE_ROLE" = "worker" ]; then curl -f http://localhost:8000/healthz; else curl -f http://localhost:8000/health; fi' || exit 1

# 啟動命令：SERVICE_ROLE=worker 時只跑獨立的 Meta Andromeda worker process，
# 不重跑 migrations（避免跟同時啟動的 web process 搶著跑 alembic upgrade，見
# worker_main.py 的說明）；其餘角色（web / all，預設）維持原本行為不變。
CMD ["sh", "-c", "if [ \"$SERVICE_ROLE\" = \"worker\" ]; then exec python worker_main.py; else python run_migration.py && export DATAVUE_SKIP_STARTUP_MIGRATIONS=1 && exec python main.py; fi"]
