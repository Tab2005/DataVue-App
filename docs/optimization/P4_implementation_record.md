# P4 低優先度優化 — 實作紀錄

**實作分支**：`dev-saas`  
**實作日期**：2025-07  
**參考文件**：`06_P4_low_priority.md`

---

## 摘要

本次實作涵蓋 P4 低優先度優化清單中的 6 個項目，主要方向：

| 項目 | 標題 | 狀態 |
|------|------|------|
| 4.5  | 備份殘留檔案清理 | ✅ 完成 |
| 3.14 | debug_fields.log 追蹤清理 | ✅ 完成 |
| 3.12 | 統一日誌系統（logging） | ✅ 完成 |
| 3.10 | CORS 正規表達式修正 | ✅ 完成 |
| 3.8  | 移除 auth.py 間接層 | ✅ 完成 |
| 4.6  | Metrics Registry API | ✅ 完成 |

---

## 項目 4.5 — 備份殘留檔案清理

### 問題
專案中存在被 git 追蹤的備份檔案，污染版本歷史並增加混淆風險。

### 變更

**刪除檔案（git rm）：**
- `frontend/src/components/GSCStats.jsx.backup`
- `frontend/src/components/SettingsModal_orig.jsx`（已在刪除時從 staging 移除）

**更新 `.gitignore`：**
```
# 備份與暫存檔
*.backup
*.bak
*.orig
*_orig.*
*_backup.*
*.tmp
Thumbs.db
```

### 備注
`backend/debug_fields.log` 已由既有的 `*.log` 規則覆蓋，無需額外處理（項目 3.14）。

---

## 項目 3.12 — 統一日誌系統

### 問題
- `backend/main.py` 使用 `logging.basicConfig()` 輸出至 `stderr`，但 Docker 容器建議使用 `stdout`
- 18+ 個後端模組混用 `print(..., file=sys.stderr)` 直接輸出，無法統一控管 log 等級與格式

### 新增：`backend/core/logging.py`

```python
import logging
import sys
import os

def setup_logging(debug: bool | None = None) -> None:
    """初始化統一日誌系統，輸出至 stdout 供 Docker 收集。"""
    if debug is None:
        debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes") or \
                os.environ.get("DEBUG_MODE", "").lower() in ("1", "true", "yes")

    level = logging.DEBUG if debug else logging.INFO
    fmt   = "%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s"

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    root.setLevel(level)

    # 抑制第三方嘈雜 logger
    for noisy in ("httpx", "httpcore", "hpack", "urllib3", "googleapiclient"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
```

### 修改：`backend/main.py`

**Before：**
```python
import logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    stream=sys.stderr,
)
```

**After：**
```python
from core.logging import setup_logging
setup_logging()
```

### print() → logger() 替換清單

以下 18 個檔案已完成 `print(..., file=sys.stderr)` → `logger.*()` 轉換：

| 檔案 | 替換數量 | 備注 |
|------|---------|------|
| `backend/batch_api.py` | 3 | logger.debug / info |
| `backend/cache.py` | 2 | logger.debug |
| `backend/modules/auth/dependencies.py` | 10 | logger.debug / info / warning / error |
| `backend/modules/auth/service.py` | 5 | logger.info / error |
| `backend/modules/fb_ads/accounts_service.py` | 4 | logger.debug / warning |
| `backend/modules/fb_ads/analytics_service.py` | 3 | logger.debug |
| `backend/modules/fb_ads/insights_service.py` | 5 | logger.debug / warning |
| `backend/modules/fb_ads/metrics_registry.py` | 2 | logger.debug |
| `backend/modules/fb_ads/trends_service.py` | 4 | logger.debug |
| `backend/routers/ai.py` | 4 | logger.info / error |
| `backend/routers/facebook.py` | 3 | logger.debug / info |
| `backend/routers/gsc.py` | 9 | logger.debug / info / warning |
| `backend/routers/permissions.py` | 2 | logger.debug |
| `backend/routers/saved_views.py` | 2 | logger.debug |
| `backend/services/ai/gemini_client.py` | 3 | logger.debug / error |
| `backend/services/ai/intent_classifier.py` | 2 | logger.debug |
| `backend/services/facebook_service.py` | 2 | logger.debug |
| `backend/service_modules/facebook_api.py` | 3 | logger.debug / warning |

**每個檔案標準模式：**
```python
import logging
logger = logging.getLogger(__name__)
# 使用模組完整路徑作為 logger 名稱，例如：backend.modules.fb_ads.insights_service
```

**刻意保留：**
- `backend/crash_reporter.py` — 作為程序監控工具，必須寫入 `stderr` 才能被父程序捕獲
- `scripts/maintenance/` 下的遺留腳本 — 不在主應用執行路徑內

---

## 項目 3.10 — CORS 正規表達式修正

### 問題
原始 CORS `allow_origin_regex` 允許 `http://` 存取正式域名，產生安全風險：
```python
# 危險：正式環境允許 HTTP
r"https?://.*\.(tabisme\.com|zeabur\.app)(:\d+)?$"
```

### 修改：`backend/main.py`

**After：**
```python
allow_origin_regex = (
    r"https://.*\.?(tabisme\.com|zeabur\.app)(:\d+)?$"   # 正式環境：HTTPS only
    r"|https?://localhost(:\d+)?$"                         # 本地開發：允許 HTTP
    r"|https?://127\.0\.0\.1(:\d+)?$"                      # 本地 IP：允許 HTTP
)
```

### 說明
- 生產域名（tabisme.com、zeabur.app）強制 HTTPS
- localhost 與 127.0.0.1 允許 HTTP，方便本地開發

---

## 項目 3.8 — 移除 auth.py 間接層

### 問題
`backend/auth.py` 是純轉發模組，無業務邏輯：
```python
# backend/auth.py（已刪除）
from modules.auth.service import TokenManager as StandardTokenManager
TokenManager = StandardTokenManager
```
所有模組都透過此間接層匯入，造成維護負擔。

### 刪除
```
git rm backend/auth.py
```

### 更新的匯入檔案（6個）

| 檔案 | Before | After |
|------|--------|-------|
| `backend/batch_api.py` | `from auth import TokenManager` | `from modules.auth.service import TokenManager` |
| `backend/gsc_service.py` | `from auth import TokenManager` | `from modules.auth.service import TokenManager` |
| `backend/modules/fb_ads/_base.py` | `from auth import TokenManager` | `from modules.auth.service import TokenManager` |
| `backend/routers/auth.py` | `from auth import TokenManager` | `from modules.auth.service import TokenManager` |
| `backend/services/facebook_service.py` | `from auth import TokenManager` | `from modules.auth.service import TokenManager` |
| `backend/service_modules/facebook_api.py` | `from auth import TokenManager` | `from modules.auth.service import TokenManager` |
| `backend/routers/ai.py` | 4 個函數內部 inline import | 移至檔頭 top-level import |

**遺留腳本（未修改）：**
- `scripts/maintenance/main_legacy.py` — 已廢棄腳本，不影響主應用

---

## 項目 4.6 — Metrics Registry API

### 問題
前端目前 hardcode 指標中繼資料（label、format、category），難以維護且前後端容易脫節。

### 新增：`backend/routers/metrics.py`

提供 30+ 個 Facebook Ads 指標的完整 Registry API。

**端點：**

| Method | Path | 說明 |
|--------|------|------|
| `GET` | `/api/metrics/registry` | 取得全部指標，支援 `?category=` 篩選 |
| `GET` | `/api/metrics/registry/{metric_key}` | 取得單一指標詳情 |

**回應結構範例：**
```json
{
  "impressions": {
    "key": "impressions",
    "label": "曝光次數",
    "label_en": "Impressions",
    "category": "delivery",
    "type": "integer",
    "format": "number",
    "description": "廣告被展示的總次數",
    "breakdown_compatible": true
  }
}
```

**涵蓋類別：**
- `delivery` — 曝光、觸及、頻率
- `cost` — 花費、各種 CPM/CPC/CPR
- `performance` — 點擊率、相關性
- `conversion` — 轉換、ROAS、購買相關
- `engagement` — 互動、留言、分享
- `video` — 影片觀看、完播率
- `messaging` — 訊息相關指標

**已在 `main.py` 註冊：**
```python
from routers.metrics import router as metrics_router
app.include_router(metrics_router)
```

### 新增：`frontend/src/hooks/queries/useMetricsRegistry.js`

React Query hook，讓前端可動態取得指標定義：

```javascript
// 取得所有指標
const { data: allMetrics } = useMetricsRegistry();

// 依類別篩選
const { data: costMetrics } = useMetricsRegistry('cost');

// 取得單一指標
const { data: metric } = useMetricDetail('impressions');
```

**特性：**
- `staleTime: 60 * 60 * 1000`（1小時快取，指標定義不常變）
- `gcTime: 2 * 60 * 60 * 1000`（2小時 GC）
- 本地 fallback data（網路失敗時仍可正常顯示）

### 更新：`frontend/src/constants/queryKeys.js`

```javascript
metrics: {
  registry: (category) => ['metrics', 'registry', category ?? null],
  detail: (key)         => ['metrics', 'registry', 'detail', key],
},
```

### 更新：`frontend/src/hooks/queries/index.js`

```javascript
export { useMetricsRegistry, useMetricDetail } from './useMetricsRegistry';
```

---

## 受影響檔案彙整

### 新增檔案

| 檔案 | 用途 |
|------|------|
| `backend/core/logging.py` | 統一日誌設定模組 |
| `backend/routers/metrics.py` | Metrics Registry API |
| `frontend/src/hooks/queries/useMetricsRegistry.js` | 前端 React Query hook |

### 刪除檔案

| 檔案 | 原因 |
|------|------|
| `backend/auth.py` | 純轉發間接層，已無存在意義 |
| `frontend/src/components/GSCStats.jsx.backup` | 殘留備份檔 |
| `frontend/src/components/SettingsModal_orig.jsx` | 殘留備份檔 |

### 修改檔案（後端）

- `backend/main.py` — logging 初始化、CORS 修正、metrics router 註冊
- `.gitignore` — 加入備份檔規則
- `backend/batch_api.py`
- `backend/cache.py`
- `backend/gsc_service.py`
- `backend/modules/auth/dependencies.py`
- `backend/modules/auth/service.py`
- `backend/modules/fb_ads/_base.py`
- `backend/modules/fb_ads/accounts_service.py`
- `backend/modules/fb_ads/analytics_service.py`
- `backend/modules/fb_ads/insights_service.py`
- `backend/modules/fb_ads/metrics_registry.py`
- `backend/modules/fb_ads/trends_service.py`
- `backend/routers/ai.py`
- `backend/routers/auth.py`
- `backend/routers/facebook.py`
- `backend/routers/gsc.py`
- `backend/routers/permissions.py`
- `backend/routers/saved_views.py`
- `backend/services/ai/gemini_client.py`
- `backend/services/ai/intent_classifier.py`
- `backend/services/facebook_service.py`
- `backend/service_modules/facebook_api.py`

### 修改檔案（前端）

- `frontend/src/constants/queryKeys.js`
- `frontend/src/hooks/queries/index.js`

---

## 驗收標準

| 項目 | 驗收標準 | 結果 |
|------|---------|------|
| 4.5 備份清理 | `git ls-files \| grep -E '\.(backup\|orig\|bak)'` 無輸出 | ✅ |
| 3.14 log 清理 | `.gitignore` 包含 `*.log` 規則 | ✅ 既有規則已涵蓋 |
| 3.12 統一日誌 | `grep -r "print.*sys.stderr" backend/` 僅剩 legacy/crash_reporter 相關 | ✅ |
| 3.10 CORS 修正 | main.py 中 HTTP 不允許存取正式域名 | ✅ |
| 3.8 auth.py 移除 | `python -c "import auth"` → ImportError | ✅ 已刪除 |
| 4.6 Metrics API | `GET /api/metrics/registry` 回傳 30+ 項目 | ✅ |

---

## 注意事項

1. **crash_reporter.py**：刻意保留 `print(..., file=sys.stderr)`，因為此模組作為子程序被父程序的 `subprocess.PIPE` 捕獲，必須寫 stderr。

2. **scripts/maintenance/ 遺留腳本**：`main_legacy.py`、`main_v2.py` 保留原有 import 與 print，這些腳本不在生產執行路徑中，修改風險大於收益。

3. **Metrics Registry 延伸**：前端目前仍有部分 hardcode 指標定義（如 `fb_ads` 模組中的常數），可在後續 P3/P2 優化中逐步遷移至使用 `useMetricsRegistry` hook。
