# P2：短期優化（2 週內完成）

> **優先級**：🟡 P2 — 兩週內完成  
> **預估工時**：1-2 週  
> **涵蓋項目**：3.1、3.3、6.4、7.1、7.3、3.11

---

## 目錄

1. [3.1 — 統一 Token 驗證邏輯至 core/security.py](#31--統一-token-驗證邏輯至-coresecuritypy)
2. [3.3 — 拆分 get_current_user 函式](#33--拆分-get_current_user-函式)
3. [6.4 — 新增速率限制（slowapi）](#64--新增速率限制slowapi)
4. [7.1 — 升級 Dockerfile Python 至 3.12](#71--升級-dockerfile-python-至-312)
5. [7.3 — 新增 /health 端點與 Docker HEALTHCHECK](#73--新增-health-端點與-docker-healthcheck)
6. [3.11 — 統一 Session 使用 Depends(get_db)](#311--統一-session-使用-dependsget_db)

---

## 3.1 — 統一 Token 驗證邏輯至 `core/security.py`

### 問題說明

`dependencies.py` 與 `routers/auth.py` 各有一套 Google Token 驗證邏輯，邏輯幾乎相同但返回格式不同，造成維護困難。

### 實作步驟

**步驟 1：在 `core/security.py` 建立統一驗證函式**

```python
# backend/core/security.py（新增以下函式）

import logging
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from cachetools import TTLCache, cached
import threading

from core.config import settings

logger = logging.getLogger(__name__)

# TTL 快取：5 分鐘（確保撤銷的 Token 不會被快取太久）
_token_cache: TTLCache = TTLCache(maxsize=128, ttl=300)
_token_cache_lock = threading.Lock()


@cached(cache=_token_cache, lock=_token_cache_lock)
def _verify_google_token_raw(token: str) -> dict:
    """
    底層 Token 驗證（帶快取）。
    不應直接呼叫此函式，請使用下方的公開函式。
    """
    return id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        settings.GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=60,
    )


def verify_google_token(token: str) -> dict:
    """
    驗證 Google ID Token 並返回完整的 id_info 字典。
    
    Args:
        token: Google ID Token 字串
        
    Returns:
        包含使用者資訊的字典，例如：
        {
            "sub": "123456789",
            "email": "user@example.com",
            "name": "User Name",
            "picture": "https://...",
            "email_verified": True,
            "exp": 1234567890
        }
        
    Raises:
        ValueError: Token 無效時（已過期、簽名不符、來源不正確）
    """
    try:
        id_info = _verify_google_token_raw(token)
        
        # 額外驗證：確認 email 已驗證
        if not id_info.get("email_verified", False):
            raise ValueError("Google 帳號 email 尚未驗證")
        
        return id_info
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"[Security] Token 驗證失敗: {e}")
        raise ValueError(f"Token 驗證失敗: {e}")


def verify_google_token_and_get_sub(token: str) -> str:
    """
    驗證 Google ID Token 並只返回 Google User ID（sub）。
    
    適用於只需要用戶 ID 的場景（如 routers/auth.py 的 exchange_token）。
    
    Returns:
        Google User ID 字串
    """
    id_info = verify_google_token(token)
    return id_info["sub"]
```

**步驟 2：更新 `dependencies.py` 使用統一函式**

```python
# backend/dependencies.py（修改現有程式碼）

# ❌ 移除重複的驗證邏輯
# from functools import lru_cache
# @lru_cache(maxsize=128)
# def _verify_token_cached(token: str): ...

# ✅ 改為引入統一驗證函式
from core.security import verify_google_token

# 原本的呼叫位置
async def get_current_user(token: str = ..., db: Session = ...):
    try:
        # ❌ 舊：id_info = _verify_token_cached(token)
        id_info = verify_google_token(token)  # ✅ 新
        ...
```

**步驟 3：更新 `routers/auth.py` 使用統一函式**

```python
# backend/routers/auth.py（修改現有程式碼）

# ❌ 移除本地 verify_google_token 函式
# def verify_google_token(token: str) -> str:
#     id_info = id_token.verify_oauth2_token(...)
#     return id_info["sub"]

# ✅ 引入統一函式
from core.security import verify_google_token_and_get_sub

@router.post("/exchange-token")
async def exchange_token(request: TokenRequest, db: Session = Depends(get_db)):
    try:
        # ❌ 舊：google_id = verify_google_token(request.token)
        google_id = verify_google_token_and_get_sub(request.token)  # ✅ 新
        ...
```

**步驟 4：處理 `backend/auth.py` 根層別名**

```python
# backend/auth.py（保留向後相容，但標記為 deprecated）
# 此檔案未來將刪除，請直接使用 modules.auth.service

import warnings
warnings.warn(
    "直接從 'auth' 匯入已棄用，請改用 'from modules.auth.service import TokenManager'",
    DeprecationWarning,
    stacklevel=2
)

from modules.auth.service import TokenManager as StandardTokenManager
TokenManager = StandardTokenManager
```

### 驗收標準

- [ ] `core/security.py` 包含 `verify_google_token()` 與 `verify_google_token_and_get_sub()`
- [ ] `dependencies.py` 不再有獨立的 Token 驗證邏輯
- [ ] `routers/auth.py` 不再有獨立的 Token 驗證邏輯
- [ ] 兩個呼叫點都使用 `core/security.py` 的函式
- [ ] Token 快取依然有效（TTLCache 於 core/security.py 中）

---

## 3.3 — 拆分 `get_current_user` 函式

### 問題說明

`dependencies.py` 的 `get_current_user()` 高達 135 行，混合認證、使用者建立、Super Admin 同步、模組授權四個職責。

### 實作步驟

**步驟 1：建立 `services/user_service.py`（或更新現有）**

```python
# backend/services/user_service.py

import logging
from sqlalchemy.orm import Session
from database import User, UserModuleAccess, Module
from core.config import settings

logger = logging.getLogger(__name__)


def get_or_create_user(db: Session, google_id: str, email: str, 
                        name: str, picture: str) -> tuple[User, bool]:
    """
    依 google_id 取得使用者，若不存在則建立。
    
    Returns:
        (user, created): user 物件與是否新建立的布林值
    """
    user = db.query(User).filter(User.google_id == google_id).first()

    if user:
        # 更新使用者資料（名稱或頭像可能變更）
        changed = False
        if user.name != name:
            user.name = name
            changed = True
        if user.picture != picture:
            user.picture = picture
            changed = True
        if changed:
            db.commit()
            db.refresh(user)
        return user, False

    # 建立新使用者
    new_user = User(
        google_id=google_id,
        email=email,
        name=name,
        picture=picture,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"[UserService] 新使用者已建立: {email}")
    return new_user, True


def sync_super_admin_status(db: Session, user: User) -> bool:
    """
    依設定檢查並同步 Super Admin 狀態。
    
    Returns:
        若狀態有變更返回 True
    """
    super_admin_emails = {
        e.strip().lower() 
        for e in settings.SUPER_ADMIN_EMAILS.split(",") 
        if e.strip()
    }
    
    should_be_super_admin = user.email.lower() in super_admin_emails
    
    if user.is_super_admin != should_be_super_admin:
        user.is_super_admin = should_be_super_admin
        db.commit()
        action = "授予" if should_be_super_admin else "撤銷"
        logger.info(f"[UserService] {action} Super Admin: {user.email}")
        return True
    
    return False


def grant_default_module_access(db: Session, user: User) -> list[str]:
    """
    為新使用者授予預設模組存取權限。
    
    Returns:
        已授予的模組名稱列表
    """
    default_modules = ["facebook_ads", "gsc", "ga4"]  # 或從設定讀取
    granted = []
    
    for module_name in default_modules:
        module = db.query(Module).filter(Module.name == module_name).first()
        if not module:
            continue
        
        existing = db.query(UserModuleAccess).filter(
            UserModuleAccess.user_id == user.id,
            UserModuleAccess.module_id == module.id,
        ).first()
        
        if not existing:
            access = UserModuleAccess(user_id=user.id, module_id=module.id)
            db.add(access)
            granted.append(module_name)
    
    if granted:
        db.commit()
        logger.info(f"[UserService] 為 {user.email} 授予模組: {granted}")
    
    return granted
```

**步驟 2：重構 `dependencies.py` 的 `get_current_user`**

```python
# backend/dependencies.py（重構 get_current_user）

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.security import verify_google_token
from database import get_db, User
from services.user_service import (
    get_or_create_user,
    sync_super_admin_status,
    grant_default_module_access,
)

logger = logging.getLogger(__name__)
security = HTTPBearer()


def _extract_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """從 Bearer Token 中提取 JWT 字串"""
    return credentials.credentials


async def get_current_user(
    token: str = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI 依賴注入：驗證 Token 並返回當前使用者。
    
    職責：
    1. 驗證 Google ID Token
    2. 取得或建立使用者記錄
    3. 同步 Super Admin 狀態
    4. 首次登入時授予預設模組
    
    Raises:
        HTTPException 401: Token 無效
        HTTPException 403: 帳號已停用
    """
    # 步驟 1：驗證 Token
    try:
        id_info = verify_google_token(token)
    except ValueError as e:
        logger.warning(f"[Auth] Token 驗證失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證 Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 步驟 2：取得或建立使用者
    user, is_new = get_or_create_user(
        db=db,
        google_id=id_info["sub"],
        email=id_info.get("email", ""),
        name=id_info.get("name", ""),
        picture=id_info.get("picture", ""),
    )

    # 步驟 3：檢查帳號狀態
    if hasattr(user, "status") and user.status == "disabled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="帳號已被停用，請聯繫管理員",
        )

    # 步驟 4：同步 Super Admin 狀態
    sync_super_admin_status(db=db, user=user)

    # 步驟 5：新使用者授予預設模組
    if is_new:
        grant_default_module_access(db=db, user=user)

    return user


async def get_super_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求 Super Admin 權限的依賴"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要 Super Admin 權限",
        )
    return current_user
```

### 驗收標準

- [ ] `services/user_service.py` 包含 `get_or_create_user`、`sync_super_admin_status`、`grant_default_module_access`
- [ ] `dependencies.py` 的 `get_current_user` 縮短至 50 行以內
- [ ] 所有 `print(... file=sys.stderr)` 已替換為 `logger.xxx()`
- [ ] 功能測試：登入、新使用者建立、Super Admin 存取均正常

---

## 6.4 — 新增速率限制（slowapi）

### 問題說明

認證端點無速率限制，可能遭受暴力攻擊或 DDoS。

### 實作步驟

**步驟 1：安裝 slowapi**

```bash
pip install slowapi
```

```txt
# requirements.txt 新增
slowapi>=0.1.9,<1.0.0
```

**步驟 2：在 `main.py` 設定 Limiter**

```python
# backend/main.py（新增速率限制）

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# 建立 Limiter 實例
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],   # 全域預設：每分鐘 200 次
    storage_uri=os.getenv("REDIS_URL"),  # 使用 Redis 儲存計數（多進程共享）
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
```

**步驟 3：在關鍵端點添加限制**

```python
# backend/routers/auth.py

from main import limiter
from fastapi import Request

@router.post("/exchange-token")
@limiter.limit("10/minute")       # 每 IP 每分鐘最多 10 次認證嘗試
async def exchange_token(request: Request, token_request: TokenRequest, ...):
    ...

@router.post("/logout")
@limiter.limit("30/minute")
async def logout(request: Request, ...):
    ...
```

```python
# backend/routers/ga4.py、gsc.py、facebook.py（AI 端點較貴需限制）

@router.post("/analyze")
@limiter.limit("20/minute")       # AI 分析端點
async def analyze(request: Request, ...):
    ...
```

**步驟 4：自訂速率限制錯誤回應格式**

```python
# backend/main.py

from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": "請求過於頻繁",
            "detail": f"已超過速率限制，請稍後再試",
            "retry_after": exc.retry_after,
        },
        headers={"Retry-After": str(exc.retry_after)},
    )
```

### 驗收標準

- [ ] `slowapi` 已安裝並加入 `requirements.txt`
- [ ] `main.py` 已設定全域速率限制（200/minute）
- [ ] `/api/auth/exchange-token` 設有嚴格限制（10/minute）
- [ ] 速率限制使用 Redis 儲存（多進程共享計數）
- [ ] 速率限制錯誤返回 HTTP 429 與 `Retry-After` 標頭

---

## 7.1 — 升級 Dockerfile Python 至 3.12

### 問題說明

Python 3.9 安全維護期已於 2025-10-05 終止。

### 實作步驟

**步驟 1：更新 `backend/Dockerfile`**

```dockerfile
# ❌ 舊版本
FROM python:3.9-slim

# ✅ 新版本
FROM python:3.12-slim
```

**步驟 2：清理 Dockerfile 中的注釋廢棄程式碼**

```dockerfile
# backend/Dockerfile（完整清理版本）

FROM python:3.12-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴（PostgreSQL 客戶端）
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

# 建立非 root 使用者（安全最佳實踐）
RUN useradd --system --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

# 暴露埠號
EXPOSE 8000

# 健康檢查（配合 7.3 項目）
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動命令
CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
```

**步驟 3：本地測試 Python 3.12 相容性**

```powershell
# 本地測試（若有 pyenv 或 conda）
# 建立 Python 3.12 虛擬環境
python3.12 -m venv venv312
.\venv312\Scripts\activate
pip install -r requirements.txt

# 執行應用程式測試
python -c "import fastapi, sqlalchemy, pydantic; print('所有依賴載入成功')"
uvicorn main:app --host 0.0.0.0 --port 8000
```

**步驟 4：確認 `pyproject.toml`（若存在）更新 Python 版本要求**

```toml
[tool.poetry.dependencies]
python = "^3.12"
```

### 驗收標準

- [ ] `Dockerfile` 使用 `python:3.12-slim`
- [ ] 本地以 Python 3.12 環境測試全部功能正常
- [ ] Docker 建置成功（`docker build -t datavue-backend .`）
- [ ] 所有 API 端點在升級後正常響應
- [ ] Dockerfile 已清理廢棄的注釋

---

## 7.3 — 新增 `/health` 端點與 Docker HEALTHCHECK

### 問題說明

缺乏健康檢查端點，Zeabur 和 Docker 無法判斷應用是否正常運作。

### 實作步驟

**步驟 1：在 `main.py` 新增 `/health` 端點**

```python
# backend/main.py（新增健康檢查端點）

import time
from datetime import datetime, timezone

START_TIME = time.time()

@app.get("/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    健康檢查端點（供 Load Balancer 和 Zeabur 使用）。
    
    Returns:
        200 OK：應用正常
        503 Service Unavailable：資料庫或關鍵服務異常
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.time() - START_TIME),
        "version": "2.1.0",
        "checks": {}
    }

    # 資料庫連線檢查
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {str(e)}"

    # Redis 連線檢查（若有設定）
    try:
        from redis_cache import get_redis_client
        redis = get_redis_client()
        if redis:
            redis.ping()
            health_status["checks"]["redis"] = "ok"
        else:
            health_status["checks"]["redis"] = "not_configured"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        # Redis 不健康不影響整體狀態（可選服務）

    if health_status["status"] == "unhealthy":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content=health_status)

    return health_status


@app.get("/health/ready", tags=["System"])
async def readiness_check():
    """
    就緒探針（Readiness Probe）：應用是否已準備好接受流量。
    在啟動初始化完成前返回 503。
    """
    return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}
```

**步驟 2：Dockerfile 添加 HEALTHCHECK**

（已包含於 7.1 的 Dockerfile 更新中）

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**步驟 3：Docker Compose 設定健康檢查**

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

### 驗收標準

- [ ] `GET /health` 端點可正常訪問
- [ ] 資料庫異常時 `/health` 返回 HTTP 503
- [ ] Dockerfile 已設定 `HEALTHCHECK`
- [ ] `docker inspect <container>` 顯示 Health: healthy

---

## 3.11 — 統一 Session 使用 `Depends(get_db)`

### 問題說明

`routers/auth.py` 直接建立 `SessionLocal()`，繞過了 FastAPI 依賴注入系統。

### 實作步驟

**找到並更新 `routers/auth.py`**

```python
# ❌ 舊寫法
@router.post("/exchange-token")
async def exchange_token(request: TokenRequest):
    session = SessionLocal()
    try:
        user = session.query(User).filter(...).first()
        ...
    finally:
        session.close()

# ✅ 新寫法
from fastapi import Depends
from database import get_db
from sqlalchemy.orm import Session

@router.post("/exchange-token")
async def exchange_token(
    request: TokenRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(...).first()
    ...
    # 不需要手動關閉，FastAPI 生命週期管理
```

### 驗收標準

- [ ] `routers/auth.py` 不再有直接的 `SessionLocal()` 呼叫
- [ ] 所有路由使用 `db: Session = Depends(get_db)`
- [ ] 搜尋全部 router 確認無其他直接 Session 建立
