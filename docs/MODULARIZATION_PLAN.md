# 後端模組化重構計劃

> **目標**: 將後端功能拆分為獨立模組，便於移植到其他專案  
> **預估工時**: 4-6 小時  
> **風險等級**: 中（需確保現有功能不受影響）

---

## 目標結構

```
backend/
├── modules/                      # 🆕 獨立功能模組
│   ├── ai_settings/              # AI API Key 管理
│   │   ├── __init__.py
│   │   ├── router.py             # /api/ai/* 端點
│   │   ├── models.py             # Pydantic schemas
│   │   ├── encryption.py         # Fernet 加密/解密
│   │   ├── service.py            # 業務邏輯
│   │   └── README.md             # 模組使用說明
│   ├── gsc/                      # Google Search Console
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── intent_analysis/
│   │       ├── classifier.py
│   │       ├── gemini_client.py
│   │       └── zeabur_client.py
│   └── facebook/                 # Facebook Ads (未來)
│       └── ...
├── core/                         # 🆕 共用核心
│   ├── __init__.py
│   ├── database.py               # 資料庫連接
│   ├── config.py                 # 環境變數配置
│   └── security.py               # 認證邏輯
├── main.py                       # 應用入口 (組裝模組)
└── requirements.txt
```

---

## 實作階段

### Phase 1: AI Settings 模組 (2小時)

| 步驟 | 檔案 | 動作 |
|------|------|------|
| 1.1 | `modules/ai_settings/__init__.py` | 建立模組入口 |
| 1.2 | `modules/ai_settings/encryption.py` | 從 `auth.py` 抽取 Fernet 加密 |
| 1.3 | `modules/ai_settings/models.py` | 從 `routers/ai.py` 抽取 Schemas |
| 1.4 | `modules/ai_settings/service.py` | 從 `auth.py` 抽取 AI 相關 TokenManager |
| 1.5 | `modules/ai_settings/router.py` | 移動 `routers/ai.py` 內容 |
| 1.6 | `main.py` | 改用模組導入方式 |

**驗證**: AI 設定、連線測試功能正常

---

### Phase 2: GSC 模組 (2小時)

| 步驟 | 檔案 | 動作 |
|------|------|------|
| 2.1 | `modules/gsc/__init__.py` | 建立模組入口 |
| 2.2 | `modules/gsc/router.py` | 移動 `routers/gsc.py` |
| 2.3 | `modules/gsc/service.py` | 抽取 GSC API 邏輯 |
| 2.4 | `modules/gsc/intent_analysis/` | 移動 `services/ai/` |

**驗證**: GSC 分析、意圖分析功能正常

---

### Phase 3: 核心模組整合 (1小時)

| 步驟 | 檔案 | 動作 |
|------|------|------|
| 3.1 | `core/database.py` | 保留資料庫連接 |
| 3.2 | `core/config.py` | 集中環境變數 |
| 3.3 | `core/security.py` | 保留 Google 認證 |
| 3.4 | 清理舊檔案 | 刪除重複代碼 |

**驗證**: 所有功能正常運作

---

## 模組使用方式（重構後）

### 在新專案使用 AI Settings 模組

```python
# 新專案 main.py
from fastapi import FastAPI

# 直接複製 modules/ai_settings 資料夾到新專案
from modules.ai_settings import ai_router

app = FastAPI()
app.include_router(ai_router, prefix="/api/ai")
```

### 模組依賴

```python
# modules/ai_settings/__init__.py
from .router import router as ai_router
from .service import AISettingsService
from .encryption import encrypt, decrypt

__all__ = ["ai_router", "AISettingsService", "encrypt", "decrypt"]
```

---

## 風險與對策

| 風險 | 影響 | 對策 |
|------|------|------|
| 循環依賴 | 模組無法載入 | 使用依賴注入 |
| 資料庫遷移 | 表結構不相容 | 使用 Mixin 模式 |
| 測試失敗 | 功能中斷 | 每階段完整測試 |

---

## 不重構的替代方案

如果時間有限，可以只做「文件化」：

1. 建立 `docs/FEATURE_EXTRACTION.md`
2. 記錄每個功能涉及的檔案清單
3. 提供複製指南和修改說明

---

## 建議

- **如果只是偶爾複用**: 使用替代方案（文件化）
- **如果預計多次複用**: 執行完整模組化重構
- **如果專案會持續擴大**: 強烈建議模組化
