# P1：高優先級問題修復

> **優先級**：🟠 P1 — 本週內完成  
> **預估工時**：2-3 天  
> **涵蓋項目**：4.1、4.2、3.4、3.5

---

## 目錄

1. [4.1 — 建立統一 Frontend API Client](#41--建立統一-frontend-api-client)
2. [4.2 — 實作 Frontend Token 過期偵測](#42--實作-frontend-token-過期偵測)
3. [3.4 — 釘定 requirements.txt 套件版本](#34--釘定-requirementstxt-套件版本)
4. [3.5 — 整合 Redis 作為主要快取層](#35--整合-redis-作為主要快取層)

---

## 4.1 — 建立統一 Frontend API Client

### 問題說明

目前每個 service 檔案各自實作 `fetch()` 呼叫，導致錯誤處理邏輯重複、無法統一攔截 401 回應。

### 實作步驟

**步驟 1：建立 `src/services/apiClient.js`**

```javascript
// frontend/src/services/apiClient.js

import { getAuthToken, clearAuthToken, isTokenExpired } from '../utils/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * 全局 API 請求統計（可用於監控）
 */
let requestCount = 0;
let errorCount = 0;

/**
 * 重試設定
 */
const RETRY_CONFIG = {
  maxRetries: 2,
  retryDelay: 1000,        // 毫秒
  retryableStatuses: [502, 503, 504],
};

/**
 * 延遲輔助函式
 */
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * 統一 API 請求函式
 * 
 * @param {string} method - HTTP 方法（GET, POST, PUT, DELETE）
 * @param {string} path - API 路徑（如 /api/users/）
 * @param {object} options - 額外選項
 * @param {object} [options.body] - 請求 body（會自動 JSON.stringify）
 * @param {object} [options.headers] - 額外 headers
 * @param {boolean} [options.skipAuth=false] - 是否跳過認證 header
 * @param {number} [options.timeout=30000] - 逾時毫秒數
 * @returns {Promise<any>} - 解析後的 JSON 回應
 */
async function request(method, path, options = {}) {
  const {
    body,
    headers: extraHeaders = {},
    skipAuth = false,
    timeout = 30000,
    _retryCount = 0,
  } = options;

  // Token 過期檢查（在發送請求前）
  if (!skipAuth) {
    const token = getAuthToken();
    if (!token) {
      redirectToLogin('無認證 Token');
      throw new Error('未登入');
    }
    if (isTokenExpired(token)) {
      redirectToLogin('Token 已過期');
      throw new Error('登入已過期，請重新登入');
    }
  }

  // 建構 headers
  const headers = {
    'Content-Type': 'application/json',
    ...(!skipAuth && { Authorization: `Bearer ${getAuthToken()}` }),
    ...extraHeaders,
  };

  // 建構請求設定
  const fetchOptions = {
    method,
    headers,
    ...(body !== undefined && { body: JSON.stringify(body) }),
  };

  // 倒數計時器（逾時處理）
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  fetchOptions.signal = controller.signal;

  requestCount++;

  try {
    const response = await fetch(`${API_URL}${path}`, fetchOptions);
    clearTimeout(timeoutId);

    // 401：Token 無效或已在伺服器端失效
    if (response.status === 401) {
      clearAuthToken();
      redirectToLogin('伺服器拒絕認證');
      throw new Error('登入已失效，請重新登入');
    }

    // 需要重試的狀態碼（伺服器暫時不可用）
    if (
      RETRY_CONFIG.retryableStatuses.includes(response.status) &&
      _retryCount < RETRY_CONFIG.maxRetries
    ) {
      await sleep(RETRY_CONFIG.retryDelay * (_retryCount + 1));
      return request(method, path, { ...options, _retryCount: _retryCount + 1 });
    }

    // 其他錯誤回應
    if (!response.ok) {
      errorCount++;
      let errorMessage = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
      } catch {
        // 無法解析 JSON 錯誤回應，使用預設訊息
      }
      throw new ApiError(errorMessage, response.status, path);
    }

    // 204 No Content
    if (response.status === 204) {
      return null;
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
      throw new ApiError(`請求逾時（>${timeout}ms）`, 0, path);
    }

    throw error;
  }
}

/**
 * 自訂 API 錯誤類別
 */
export class ApiError extends Error {
  constructor(message, statusCode, path) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.path = path;
  }
}

/**
 * 重導向至登入頁
 */
function redirectToLogin(reason) {
  console.warn(`[ApiClient] 重導向至登入頁：${reason}`);
  // 儲存當前路徑，登入後可返回
  const currentPath = window.location.pathname + window.location.search;
  if (currentPath !== '/login' && currentPath !== '/') {
    sessionStorage.setItem('redirectAfterLogin', currentPath);
  }
  window.location.href = '/login';
}

/**
 * 統一 API Client 物件
 */
const apiClient = {
  get: (path, options) => request('GET', path, options),
  post: (path, body, options) => request('POST', path, { body, ...options }),
  put: (path, body, options) => request('PUT', path, { body, ...options }),
  patch: (path, body, options) => request('PATCH', path, { body, ...options }),
  delete: (path, options) => request('DELETE', path, options),

  /** 取得請求統計 */
  getStats: () => ({ requestCount, errorCount }),
};

export default apiClient;
```

**步驟 2：更新各 service 使用 apiClient**

以 `userService.js` 為例（其他 service 依此類推）：

```javascript
// frontend/src/services/userService.js

// ❌ 舊寫法
import { getAuthHeaders } from '../utils/auth';
const API_URL = import.meta.env.VITE_API_URL;

export async function getCurrentUser() {
  const response = await fetch(`${API_URL}/api/users/me`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error('Failed to fetch user');
  return response.json();
}

// ✅ 新寫法
import apiClient from './apiClient';

export async function getCurrentUser() {
  return apiClient.get('/api/users/me');
}
```

**步驟 3：建立全局錯誤邊界（React Error Boundary）**

```jsx
// frontend/src/components/ErrorBoundary.jsx
import React from 'react';
import { ApiError } from '../services/apiClient';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const isApiError = this.state.error instanceof ApiError;
      return (
        <div className="error-boundary">
          <h2>發生錯誤</h2>
          <p>{isApiError ? this.state.error.message : '請重新整理頁面'}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            重試
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
```

### 驗收標準

- [ ] `src/services/apiClient.js` 已建立並包含統一的 fetch 邏輯
- [ ] 所有 service 檔案已改用 apiClient（不再直接呼叫 `fetch()`）
- [ ] 401 回應會自動清除 Token 並重導向至登入頁
- [ ] 網路錯誤（連線失敗、逾時）有適當的錯誤訊息
- [ ] 502/503/504 有自動重試邏輯

---

## 4.2 — 實作 Frontend Token 過期偵測

### 問題說明

Google ID Token 有效期僅 1 小時，前端未檢查 Token 是否已過期，導致使用者在 1 小時後所有請求返回 401。

### 實作步驟

**步驟 1：更新 `src/utils/auth.js`**

```javascript
// frontend/src/utils/auth.js

const TOKEN_KEY = 'google_token';
const TOKEN_EXPIRY_KEY = 'google_token_expiry';

/**
 * 解析 JWT Payload（不需要驗證簽名，僅讀取宣告）
 * @param {string} token - JWT token 字串
 * @returns {object|null} - 解析後的 payload 或 null
 */
export function parseJwtPayload(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const payload = parts[1];
    // 補齊 base64 padding
    const padded = payload + '='.repeat((4 - (payload.length % 4)) % 4);
    const decoded = atob(padded.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

/**
 * 儲存認證 Token 並同時儲存過期時間
 * @param {string} token - Google ID Token
 */
export function saveAuthToken(token) {
  localStorage.setItem(TOKEN_KEY, token);

  // 從 JWT payload 讀取過期時間
  const payload = parseJwtPayload(token);
  if (payload?.exp) {
    localStorage.setItem(TOKEN_EXPIRY_KEY, String(payload.exp * 1000)); // 轉為毫秒
  }
}

/**
 * 取得儲存的認證 Token
 * @returns {string|null}
 */
export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * 清除認證 Token（登出時使用）
 */
export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
  sessionStorage.removeItem('redirectAfterLogin');
}

/**
 * 檢查 Token 是否已過期
 * @param {string} [token] - 若未提供則使用 localStorage 中的 Token
 * @returns {boolean} - true 表示已過期或無法確認
 */
export function isTokenExpired(token) {
  const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY);

  if (!expiryStr) {
    // 無過期時間記錄，嘗試從 Token 解析
    const targetToken = token || getAuthToken();
    if (!targetToken) return true;
    const payload = parseJwtPayload(targetToken);
    if (!payload?.exp) return false; // 無法確認，視為未過期
    return Date.now() > payload.exp * 1000;
  }

  return Date.now() > parseInt(expiryStr, 10);
}

/**
 * 取得 Token 剩餘有效時間（毫秒）
 * @returns {number} - 剩餘毫秒數，<=0 表示已過期
 */
export function getTokenRemainingTime() {
  const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY);
  if (!expiryStr) return -1;
  return parseInt(expiryStr, 10) - Date.now();
}

/**
 * 取得認證 headers
 * @returns {object}
 */
export function getAuthHeaders() {
  const token = getAuthToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
```

**步驟 2：建立 Token 自動續期 Hook**

```javascript
// frontend/src/hooks/useTokenRefresh.js
import { useEffect, useCallback } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { getTokenRemainingTime, saveAuthToken, clearAuthToken } from '../utils/auth';

const REFRESH_THRESHOLD = 5 * 60 * 1000; // 到期前 5 分鐘觸發自動刷新

/**
 * 自動監控 Token 有效期並在過期前觸發重新登入
 * 
 * @param {function} onExpired - Token 過期時的回調（通常是導向登入頁）
 */
export function useTokenRefresh(onExpired) {
  const handleExpired = useCallback(() => {
    clearAuthToken();
    onExpired?.();
  }, [onExpired]);

  useEffect(() => {
    const checkInterval = setInterval(() => {
      const remaining = getTokenRemainingTime();

      if (remaining <= 0) {
        console.warn('[TokenRefresh] Token 已過期');
        handleExpired();
        clearInterval(checkInterval);
        return;
      }

      if (remaining <= REFRESH_THRESHOLD) {
        console.info(`[TokenRefresh] Token 將在 ${Math.round(remaining / 1000)} 秒後過期`);
        // TODO: 若使用 implicit flow，可在此觸發靜默登入
        // 目前方案：顯示提示讓使用者手動刷新
      }
    }, 60 * 1000); // 每分鐘檢查一次

    return () => clearInterval(checkInterval);
  }, [handleExpired]);
}
```

**步驟 3：在 App.jsx 整合 Token 監控**

```jsx
// frontend/src/App.jsx（相關片段）
import { useNavigate } from 'react-router-dom';
import { useTokenRefresh } from './hooks/useTokenRefresh';
import { isTokenExpired, getAuthToken } from './utils/auth';

function App() {
  const navigate = useNavigate();

  const handleTokenExpired = useCallback(() => {
    // Toast 通知（可搭配 react-hot-toast 或 chakra-ui）
    alert('您的登入已過期，請重新登入');
    navigate('/login');
  }, [navigate]);

  useTokenRefresh(handleTokenExpired);

  // 初始載入時也檢查 Token
  useEffect(() => {
    const token = getAuthToken();
    if (token && isTokenExpired(token)) {
      handleTokenExpired();
    }
  }, [handleTokenExpired]);

  // ... 其餘程式碼
}
```

### 驗收標準

- [ ] `src/utils/auth.js` 的 `saveAuthToken()` 已同時儲存過期時間
- [ ] `isTokenExpired()` 函式已實作並在 apiClient 中調用
- [ ] `useTokenRefresh` hook 已建立並在 App.jsx 中啟用
- [ ] Token 過期後會顯示提示並自動導向登入頁
- [ ] 登入後能返回原本的目標頁面（`sessionStorage.redirectAfterLogin`）

---

## 3.4 — 釘定 `requirements.txt` 套件版本

### 問題說明

`requirements.txt` 未指定版本，每次部署可能安裝不同版本的套件。

### 實作步驟

**步驟 1：在開發環境生成精確版本清單**

```powershell
cd "d:\users\Qoo\Documents\python\DataVue-App\backend"

# 若使用虛擬環境
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 生成精確版本鎖定文件
pip freeze > requirements.lock
```

**步驟 2：更新 `requirements.txt` 使用最低版本約束**

審查現有依賴並設定合理的版本範圍（寬鬆約束，比 `pip freeze` 的精確版本更具彈性）：

```txt
# backend/requirements.txt（版本約束範例）

# Web Framework
fastapi>=0.115.0,<0.116.0
uvicorn[standard]>=0.32.0,<1.0.0

# 資料庫
sqlalchemy>=2.0.0,<3.0.0
alembic>=1.14.0,<2.0.0

# 非同步資料庫驅動
aiosqlite>=0.20.0,<1.0.0          # SQLite 非同步
asyncpg>=0.30.0,<1.0.0            # PostgreSQL 非同步（生產）
psycopg2-binary>=2.9.0,<3.0.0    # PostgreSQL 同步（Alembic 遷移用）

# 認證
google-auth>=2.37.0,<3.0.0
google-auth-oauthlib>=1.2.0,<2.0.0
google-auth-httplib2>=0.2.0,<1.0.0

# Facebook SDK
facebook-sdk>=3.1.0,<4.0.0

# 快取
cachetools>=5.3.0,<6.0.0
redis>=5.2.0,<6.0.0               # Redis 客戶端

# 加密
cryptography>=44.0.0,<45.0.0

# HTTP 客戶端
httpx>=0.28.0,<1.0.0
aiohttp>=3.11.0,<4.0.0

# 工具
python-dotenv>=1.0.0,<2.0.0
pydantic>=2.10.0,<3.0.0
pydantic-settings>=2.7.0,<3.0.0
python-jose[cryptography]>=3.3.0,<4.0.0

# AI 服務
google-generativeai>=0.8.0,<1.0.0

# 速率限制
slowapi>=0.1.9,<1.0.0             # P2：將新增

# 開發/測試（應移至 requirements-dev.txt）
pytest>=8.3.0,<9.0.0
pytest-asyncio>=0.24.0,<1.0.0
httpx>=0.28.0,<1.0.0              # TestClient
```

**步驟 3：分離開發與生產依賴**

```txt
# backend/requirements-dev.txt（開發工具，不部署至生產）
-r requirements.txt

# 測試
pytest>=8.3.0,<9.0.0
pytest-asyncio>=0.24.0,<1.0.0
pytest-cov>=6.0.0,<7.0.0

# 程式碼品質
black>=24.0.0,<25.0.0
ruff>=0.8.0,<1.0.0
mypy>=1.14.0,<2.0.0
```

**步驟 4：更新 Dockerfile 使用對應的 requirements 文件**

```dockerfile
# 生產環境使用 requirements.txt（不含開發工具）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### 驗收標準

- [ ] `requirements.txt` 所有套件都有版本範圍約束
- [ ] `requirements.lock` 已建立（精確版本，供生產環境使用）
- [ ] `requirements-dev.txt` 已建立（測試與開發工具分離）
- [ ] Dockerfile 使用 `requirements.txt` 而非鬆散的套件清單
- [ ] CI/CD（若有）已更新使用 `requirements.lock` 進行部署

---

## 3.5 — 整合 Redis 作為主要快取層

### 問題說明

目前使用 `cachetools.TTLCache`（進程內記憶體快取），在多進程生產環境（多 Uvicorn workers 或多個 Docker 實例）下，各進程快取相互獨立，快取命中率低且可能對 Facebook API 造成過多請求。

### 實作步驟

**步驟 1：實作雙層快取架構**

```python
# backend/cache.py（完整重構）

import json
import logging
from functools import wraps
from typing import Any, Optional, Callable
from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)

# ============================
# L1：本地記憶體快取（極短 TTL）
# ============================
_L1_TTL = 10  # 秒（同一進程內的超短快取）
_l1_cache: TTLCache = TTLCache(maxsize=200, ttl=_L1_TTL)
_l1_lock = threading.Lock()


# ============================
# L2：Redis 快取（主要快取層）
# ============================
def _get_redis_client():
    """延遲初始化 Redis 客戶端"""
    try:
        from redis_cache import get_redis_client
        return get_redis_client()
    except Exception:
        return None


def cache_get(key: str) -> Optional[Any]:
    """
    雙層快取讀取：先查 L1（本地），再查 L2（Redis）
    
    Returns:
        快取的值（已反序列化），或 None（若未命中）
    """
    # L1 查詢
    with _l1_lock:
        if key in _l1_cache:
            logger.debug(f"[Cache] L1 命中: {key}")
            return _l1_cache[key]

    # L2 查詢（Redis）
    redis = _get_redis_client()
    if redis:
        try:
            cached = redis.get(key)
            if cached:
                value = json.loads(cached)
                # 回填 L1
                with _l1_lock:
                    _l1_cache[key] = value
                logger.debug(f"[Cache] L2 命中: {key}")
                return value
        except Exception as e:
            logger.warning(f"[Cache] Redis 讀取失敗 {key}: {e}")

    logger.debug(f"[Cache] 未命中: {key}")
    return None


def cache_set(key: str, value: Any, ttl: int = 120) -> None:
    """
    雙層快取寫入
    
    Args:
        key: 快取鍵
        value: 要快取的值（必須可 JSON 序列化）
        ttl: 存活秒數（L2 使用此值，L1 固定使用 10 秒）
    """
    # 寫入 L1
    with _l1_lock:
        _l1_cache[key] = value

    # 寫入 L2（Redis）
    redis = _get_redis_client()
    if redis:
        try:
            redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.warning(f"[Cache] Redis 寫入失敗 {key}: {e}")


def cache_delete(key: str) -> None:
    """刪除快取（L1 + L2）"""
    with _l1_lock:
        if key in _l1_cache:
            del _l1_cache[key]

    redis = _get_redis_client()
    if redis:
        try:
            redis.delete(key)
        except Exception as e:
            logger.warning(f"[Cache] Redis 刪除失敗 {key}: {e}")


def cache_delete_pattern(pattern: str) -> int:
    """依模式刪除 Redis 快取（使用 SCAN 避免阻塞）"""
    redis = _get_redis_client()
    if not redis:
        return 0

    deleted = 0
    try:
        for key in redis.scan_iter(pattern):
            redis.delete(key)
            deleted += 1
    except Exception as e:
        logger.warning(f"[Cache] Redis 模式刪除失敗 {pattern}: {e}")

    return deleted


def cached(ttl: int = 120, key_prefix: str = ""):
    """
    快取裝飾器
    
    使用範例：
        @cached(ttl=300, key_prefix="fb_accounts")
        async def get_accounts(user_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 建立快取鍵
            cache_key = f"{key_prefix}:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # 嘗試從快取取得
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value

            # 執行原函式
            result = await func(*args, **kwargs)
            
            # 寫入快取
            if result is not None:
                cache_set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


# ============================
# 向後相容：保留舊介面
# ============================
# 舊程式碼使用 ad_accounts_cache[key] 存取
# 這些快取實例現在包裝雙層快取功能

class CompatCache:
    """向後相容的快取類別，底層使用雙層快取"""
    def __init__(self, prefix: str, ttl: int):
        self._prefix = prefix
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        return cache_get(f"{self._prefix}:{key}")

    def set(self, key: str, value: Any) -> None:
        cache_set(f"{self._prefix}:{key}", value, ttl=self._ttl)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)


ad_accounts_cache = CompatCache(prefix="fb_accounts", ttl=300)
insights_cache = CompatCache(prefix="fb_insights", ttl=120)
```

**步驟 2：更新 `redis_cache.py` 確保連線穩健**

```python
# backend/redis_cache.py

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_redis_client = None
_redis_available = False


def get_redis_client():
    """取得 Redis 客戶端，若 Redis 不可用則返回 None"""
    global _redis_client, _redis_available

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.info("[Redis] REDIS_URL 未設定，使用本地記憶體快取")
        _redis_available = False
        return None

    try:
        import redis
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            retry_on_timeout=True,
        )
        # 測試連線
        client.ping()
        _redis_client = client
        _redis_available = True
        logger.info(f"[Redis] 連線成功: {redis_url}")
        return _redis_client
    except Exception as e:
        logger.warning(f"[Redis] 連線失敗，降級至本地快取: {e}")
        _redis_available = False
        return None
```

**步驟 3：在 Zeabur 或 Docker Compose 中部署 Redis**

```yaml
# docker-compose.dev.yml（開發環境）
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

```yaml
# zeabur.toml（追加 Redis 服務）
# 在 Zeabur Dashboard 新增 Redis 服務後，環境變數 REDIS_URL 會自動注入
```

### 驗收標準

- [ ] `cache.py` 已實作雙層快取（L1 本地 10s + L2 Redis）
- [ ] `redis_cache.py` 有防護性連線處理（Redis 不可用時自動降級）
- [ ] 快取鍵有前綴以避免不同功能間的衝突
- [ ] `docker-compose.dev.yml` 已包含 Redis 服務
- [ ] 本地開發時不設定 `REDIS_URL` 也能正常運作（降級至 L1）
- [ ] Facebook API 請求次數明顯降低（可透過 Facebook API 速率限制頁面監控）
