# P4：低優先級改善（可排程執行）

> **優先級**：🟢 P4 — 低優先級，可在空檔期排程  
> **預估工時**：2-4 天  
> **涵蓋項目**：4.5、3.12、4.6、3.8、3.10、3.14

---

## 目錄

1. [4.5 — 刪除備份檔案並防止再次提交](#45--刪除備份檔案並防止再次提交)
2. [3.12 — 統一日誌系統（print → logger）](#312--統一日誌系統print--logger)
3. [4.6 — 後端提供 Metrics Registry API 端點](#46--後端提供-metrics-registry-api-端點)
4. [3.8 — 清理 auth.py 根層間接層](#38--清理-authpy-根層間接層)
5. [3.10 — 修復 CORS 正則允許 HTTP](#310--修復-cors-正則允許-http)
6. [3.14 — 清理 debug_fields.log](#314--清理-debug_fieldslog)

---

## 4.5 — 刪除備份檔案並防止再次提交

### 需刪除的檔案

- `frontend/src/components/GSCStats.jsx.backup`
- `frontend/src/components/SettingsModal_orig.jsx`

### 實作步驟

**步驟 1：確認這些文件的當前狀態**

```powershell
# 確認文件存在且被 Git 追蹤
git ls-files "frontend/src/components/GSCStats.jsx.backup"
git ls-files "frontend/src/components/SettingsModal_orig.jsx"

# 查看最後修改時間（確認是廢棄備份）
git log --follow --oneline -- "frontend/src/components/GSCStats.jsx.backup"
```

**步驟 2：從 Git 移除並刪除文件**

```powershell
# 從 Git 追蹤中移除並刪除本地文件
git rm frontend/src/components/GSCStats.jsx.backup
git rm frontend/src/components/SettingsModal_orig.jsx

# 或若只想停止追蹤但保留本地文件：
# git rm --cached frontend/src/components/GSCStats.jsx.backup
```

**步驟 3：更新 `.gitignore` 防止類似文件再次提交**

```gitignore
# frontend/.gitignore 或根目錄 .gitignore

# 備份與臨時文件
*.backup
*.bak
*.orig
*_orig.*
*_backup.*
*.tmp
.DS_Store
Thumbs.db

# 編輯器暫存
*.swp
*.swo
*~
```

**步驟 4：提交變更**

```powershell
git add .gitignore
git commit -m "clean: remove stale backup files, update .gitignore"
```

**步驟 5：建立 Git Hooks 防止意外提交（選配）**

```bash
# .git/hooks/pre-commit（手動建立或使用 Husky）
#!/bin/bash

# 檢查是否有備份文件被暫存
BACKUP_FILES=$(git diff --cached --name-only | grep -E '\.(backup|bak|orig)$|_orig\.|_backup\.')
if [ -n "$BACKUP_FILES" ]; then
    echo "❌ 錯誤：偵測到備份文件！請移除以下文件再提交："
    echo "$BACKUP_FILES"
    exit 1
fi
```

```bash
chmod +x .git/hooks/pre-commit
```

### 驗收標準

- [ ] `GSCStats.jsx.backup` 與 `SettingsModal_orig.jsx` 已從 Git 移除
- [ ] `.gitignore` 已添加 `*.backup`、`*.orig` 等規則
- [ ] `git ls-files "*.backup" "*.orig"` 返回空結果
- [ ] 提交成功並推送至遠端

---

## 3.12 — 統一日誌系統（`print` → `logger`）

### 問題說明

`dependencies.py` 等多處使用 `print(... file=sys.stderr)` 代替結構化日誌，無法設定日誌層級或導向外部日誌服務。

### 實作步驟

**步驟 1：建立統一的日誌設定**

```python
# backend/core/logging.py

import logging
import sys
from core.config import settings


def setup_logging():
    """設定應用程式日誌系統"""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # 格式：時間 - 模組 - 層級 - 訊息
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # 標準輸出 Handler（供 Docker 收集）
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)
    
    # 設定根 Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    
    # 降低第三方庫的日誌噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    
    return root_logger
```

**步驟 2：在每個模組頂部使用模組 Logger**

```python
# 每個 Python 文件頂部（以 dependencies.py 為例）
import logging

logger = logging.getLogger(__name__)

# 取代 print(..., file=sys.stderr) 的寫法：
# print(f"DEBUG: User {user.email} created", file=sys.stderr)
logger.debug(f"使用者已建立: {user.email}")

# print(f"ERROR: Token 驗證失敗 {e}", file=sys.stderr)
logger.error(f"Token 驗證失敗: {e}", exc_info=True)

# print(f"INFO: New user registered: {email}", file=sys.stderr)
logger.info(f"新使用者已註冊: {email}")

# print(f"WARNING: Rate limit approaching", file=sys.stderr)
logger.warning("速率限制即將達到")
```

**步驟 3：批量替換 `print` 呼叫**

```powershell
# 在 Windows PowerShell 中搜尋所有 print 呼叫
cd "d:\users\Qoo\Documents\python\DataVue-App\backend"
Select-String -Path "*.py" -Pattern "print\(" -Recurse | Select-Object Path, LineNumber, Line

# 找出特別是 print(..., file=sys.stderr) 的使用
Select-String -Path "*.py" -Pattern "print\(.*sys\.stderr" -Recurse
```

**步驟 4：建立替換清單**

優先替換以下文件中的 `print()`：

| 文件 | 預估替換次數 | 替換方式 |
|------|------------|----------|
| `dependencies.py` | ~15 次 | `logger.debug/info/warning` |
| `main.py` | ~5 次 | `logger.info` |
| `routers/auth.py` | ~8 次 | `logger.info/warning/error` |
| `async_services.py` | ~20 次 | `logger.debug/info/error` |

**步驟 5：在 `main.py` 的啟動時初始化日誌**

```python
# backend/main.py

from core.logging import setup_logging

# 應用程式啟動時初始化日誌
setup_logging()

logger = logging.getLogger(__name__)
logger.info("DataVue App 啟動中...")
```

### 驗收標準

- [ ] `core/logging.py` 已建立
- [ ] `main.py` 啟動時呼叫 `setup_logging()`
- [ ] `dependencies.py` 所有 `print(... file=sys.stderr)` 已替換為 `logger.xxx()`
- [ ] `grep -r "print(" backend/ --include="*.py"` 結果只剩合理的 `print()` 使用（如測試或 CLI 腳本）
- [ ] 應用程式日誌輸出至 stdout（而非 stderr），供 Docker 收集

---

## 4.6 — 後端提供 Metrics Registry API 端點

### 問題說明

廣告指標定義在前端 `metricsRegistry.js` 和後端 `async_services.py` 各維護一份，新增指標需在兩處同步更新。

### 實作步驟

**步驟 1：在後端建立 Metrics Registry 資源**

```python
# backend/service_modules/metrics.py（更新現有文件或建立新文件）

from typing import Optional

# 統一的指標定義（後端做為 Single Source of Truth）
METRICS_REGISTRY: dict[str, dict] = {
    "impressions": {
        "key": "impressions",
        "label": "曝光次數",
        "label_en": "Impressions",
        "category": "delivery",
        "type": "integer",
        "format": "number",
        "description": "廣告被展示的次數",
        "breakdown_compatible": True,
    },
    "clicks": {
        "key": "clicks",
        "label": "點擊次數",
        "label_en": "Clicks",
        "category": "delivery",
        "type": "integer",
        "format": "number",
        "description": "使用者點擊廣告的次數",
        "breakdown_compatible": True,
    },
    "spend": {
        "key": "spend",
        "label": "花費",
        "label_en": "Spend",
        "category": "cost",
        "type": "float",
        "format": "currency",
        "description": "廣告投放總花費金額",
        "breakdown_compatible": True,
    },
    "reach": {
        "key": "reach",
        "label": "觸及人數",
        "label_en": "Reach",
        "category": "delivery",
        "type": "integer",
        "format": "number",
        "description": "看過廣告的不重複使用者數量",
        "breakdown_compatible": True,
    },
    "ctr": {
        "key": "ctr",
        "label": "點擊率",
        "label_en": "CTR",
        "category": "performance",
        "type": "float",
        "format": "percentage",
        "description": "點擊次數 / 曝光次數 × 100%",
        "breakdown_compatible": False,
    },
    "cpc": {
        "key": "cpc",
        "label": "每次點擊成本",
        "label_en": "CPC",
        "category": "cost",
        "type": "float",
        "format": "currency",
        "description": "每次點擊的平均成本",
        "breakdown_compatible": False,
    },
    "cpm": {
        "key": "cpm",
        "label": "每千次曝光成本",
        "label_en": "CPM",
        "category": "cost",
        "type": "float",
        "format": "currency",
        "description": "每 1000 次曝光的平均成本",
        "breakdown_compatible": False,
    },
    "frequency": {
        "key": "frequency",
        "label": "頻率",
        "label_en": "Frequency",
        "category": "delivery",
        "type": "float",
        "format": "decimal",
        "description": "每個人平均看到廣告的次數",
        "breakdown_compatible": False,
    },
    "conversions": {
        "key": "conversions",
        "label": "轉換次數",
        "label_en": "Conversions",
        "category": "conversion",
        "type": "integer",
        "format": "number",
        "description": "使用者完成目標行動的次數",
        "breakdown_compatible": True,
    },
    "cost_per_conversion": {
        "key": "cost_per_conversion",
        "label": "每次轉換成本",
        "label_en": "Cost per Conversion",
        "category": "cost",
        "type": "float",
        "format": "currency",
        "description": "每次轉換的平均花費",
        "breakdown_compatible": False,
    },
    "purchase_roas": {
        "key": "purchase_roas",
        "label": "廣告投資回報率",
        "label_en": "Purchase ROAS",
        "category": "conversion",
        "type": "float",
        "format": "multiplier",
        "description": "廣告帶來的購買收益 / 廣告花費",
        "breakdown_compatible": False,
    },
}


def get_metrics_by_category(category: Optional[str] = None) -> list[dict]:
    """依分類篩選指標"""
    metrics = list(METRICS_REGISTRY.values())
    if category:
        metrics = [m for m in metrics if m["category"] == category]
    return sorted(metrics, key=lambda m: m["label"])


def get_metric(key: str) -> Optional[dict]:
    """取得單一指標定義"""
    return METRICS_REGISTRY.get(key)
```

**步驟 2：建立 API 端點**

```python
# backend/routers/metrics.py（新建文件）

from fastapi import APIRouter, Depends, Query
from typing import Optional
from database import User
from dependencies import get_current_user
from service_modules.metrics import get_metrics_by_category, METRICS_REGISTRY

router = APIRouter(prefix="/api/metrics", tags=["Metrics"])


@router.get("/registry")
async def get_metrics_registry(
    category: Optional[str] = Query(None, description="篩選指標分類"),
    current_user: User = Depends(get_current_user),
):
    """
    取得廣告指標定義列表。
    前端使用此端點動態取得指標設定，避免雙重維護。
    
    Args:
        category: 可選，篩選特定分類（delivery, cost, performance, conversion）
    """
    return {
        "metrics": get_metrics_by_category(category),
        "categories": ["delivery", "cost", "performance", "conversion"],
        "total": len(METRICS_REGISTRY),
    }


@router.get("/registry/{metric_key}")
async def get_metric_detail(
    metric_key: str,
    current_user: User = Depends(get_current_user),
):
    """取得單一指標的詳細定義"""
    metric = METRICS_REGISTRY.get(metric_key)
    if not metric:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"指標 '{metric_key}' 不存在")
    return metric
```

**步驟 3：在 `main.py` 引入新路由**

```python
# backend/main.py
from routers.metrics import router as metrics_router
app.include_router(metrics_router)
```

**步驟 4：更新前端使用後端 API**

```javascript
// frontend/src/hooks/queries/useMetricsRegistry.js

import { useQuery } from '@tanstack/react-query';
import apiClient from '../../services/apiClient';

export function useMetricsRegistry(category = null) {
  return useQuery({
    queryKey: ['metrics', 'registry', category],
    queryFn: () => apiClient.get(
      `/api/metrics/registry${category ? `?category=${category}` : ''}`
    ),
    // 指標定義不常變更，快取 1 小時
    staleTime: 60 * 60 * 1000,
    gcTime: 2 * 60 * 60 * 1000,
  });
}
```

```javascript
// frontend/src/constants/metricsRegistry.js（更新為從後端取得，保留本地備份）

import { useMetricsRegistry } from '../hooks/queries/useMetricsRegistry';

// 本地備份（當 API 請求失敗時使用）
export const LOCAL_METRICS_FALLBACK = {
  impressions: { key: 'impressions', label: '曝光次數', format: 'number' },
  clicks: { key: 'clicks', label: '點擊次數', format: 'number' },
  spend: { key: 'spend', label: '花費', format: 'currency' },
  // ... 精簡版備份
};

// 使用 Hook 的元件可直接呼叫：
// const { data: registry } = useMetricsRegistry();
// const metric = registry?.metrics?.find(m => m.key === 'impressions');
```

### 驗收標準

- [ ] `service_modules/metrics.py` 已建立統一的 METRICS_REGISTRY
- [ ] `GET /api/metrics/registry` 端點已建立並可正常訪問
- [ ] 前端 `useMetricsRegistry` hook 已建立
- [ ] 前端可從後端取得指標定義（在網路正常時）
- [ ] 本地備份仍保留（網路異常時降級使用）

---

## 3.8 — 清理 `auth.py` 根層間接層

### 問題說明

`backend/auth.py` 僅是 `modules.auth.service.TokenManager` 的別名，是不必要的間接層。

### 實作步驟

**步驟 1：確認哪些文件依賴 `backend/auth.py`**

```powershell
cd "d:\users\Qoo\Documents\python\DataVue-App\backend"
Select-String -Path "*.py" -Pattern "from auth import|import auth" -Recurse
```

**步驟 2：逐一更新引用**

```python
# 找到類似這樣的引用：
# from auth import TokenManager

# 替換為：
from modules.auth.service import TokenManager
```

**步驟 3：刪除 `backend/auth.py`**

```powershell
git rm backend/auth.py
git commit -m "refactor: remove unnecessary auth.py indirection layer"
```

### 驗收標準

- [ ] `backend/auth.py` 已刪除
- [ ] 所有原本引用 `from auth import TokenManager` 的地方已更新
- [ ] 應用程式啟動正常

---

## 3.10 — 修復 CORS 正則允許 HTTP

### 問題說明

`main.py` 的 CORS 正則表達式允許生產域名使用不安全的 HTTP 連線。

### 實作步驟

**修改 `backend/main.py`**

```python
# ❌ 現有設定（允許生產域名的 HTTP）
allow_origin_regex = r"https?://.*\.?(tabisme\.com|zeabur\.app|localhost)(:\d+)?$"

# ✅ 修正後設定（生產域名僅允許 HTTPS，localhost 允許 HTTP/HTTPS）
allow_origin_regex = (
    r"https://.*\.?(tabisme\.com|zeabur\.app)(:\d+)?$"   # 生產：僅 HTTPS
    r"|https?://localhost(:\d+)?$"                         # 本地開發：允許 HTTP
    r"|https?://127\.0\.0\.1(:\d+)?$"                     # 本地 IP
)
```

### 驗收標準

- [ ] `main.py` CORS 正則已更新
- [ ] 本地開發（localhost:5173）仍可正常存取 API
- [ ] 生產環境（tabisme.com, zeabur.app）的 HTTP 請求被 CORS 拒絕
- [ ] 前端生產環境使用 HTTPS 連線正常

---

## 3.14 — 清理 `debug_fields.log`

### 問題說明

`backend/debug_fields.log` 是開發中產生的除錯日誌，不應進入版本控制。

### 實作步驟

```powershell
# 從 Git 追蹤中移除
git rm --cached backend/debug_fields.log 2>$null

# 確認 .gitignore 已包含日誌文件規則
$gitignoreContent = Get-Content ".gitignore" -ErrorAction SilentlyContinue
if ($gitignoreContent -notcontains "*.log") {
    Add-Content ".gitignore" "`n# 日誌文件`n*.log`ndebug_*.log`n"
}

git add .gitignore
git commit -m "clean: remove debug_fields.log from git tracking"
```

### 驗收標準

- [ ] `backend/debug_fields.log` 不在 `git ls-files` 結果中
- [ ] `.gitignore` 包含 `*.log` 規則

---

## 執行清單總結

```
P4 項目（可在空檔期排程）：

□ [4.5]  git rm 刪除 GSCStats.jsx.backup 和 SettingsModal_orig.jsx
□ [4.5]  更新 .gitignore 防止 *.backup *.orig 再次提交
□ [3.12] 建立 core/logging.py 統一日誌設定
□ [3.12] 替換 dependencies.py 中的所有 print()
□ [3.12] 替換其他模組中的 print(... file=sys.stderr)
□ [4.6]  在 service_modules/metrics.py 建立 METRICS_REGISTRY
□ [4.6]  建立 GET /api/metrics/registry 端點
□ [4.6]  建立前端 useMetricsRegistry hook
□ [3.8]  確認並更新 from auth import 的引用
□ [3.8]  刪除 backend/auth.py
□ [3.10] 修正 main.py CORS 正則表達式
□ [3.14] git rm --cached backend/debug_fields.log
```
