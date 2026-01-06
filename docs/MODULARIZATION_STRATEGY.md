# 模組化重構實作計畫（整合版）

> **目標**：好維護 + 可複用的平衡方案  
> **策略**：漸進式重構，優先處理高複用價值模組

---

## 📊 現況分析

| 類型 | 檔案數 | 問題 |
|------|--------|------|
| Routers | 8 | 結構良好，已分離 ✅ |
| Services | 5 | 部分耦合 `auth.py` |
| main.py | 1554 行 | 過於龐大 ⚠️ |
| 工具腳本 | 15+ | 散落在根目錄 |

---

## 🎯 候選模組（依複用價值排序）

| 優先級 | 模組名稱 | 複用價值 | 維護價值 | 建議 |
|--------|----------|----------|----------|------|
| 🥇 P1 | **Auth/Security** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 立即拆分 |
| 🥇 P1 | **AI Services** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 立即拆分 |
| 🥈 P2 | **GSC Analytics** | ⭐⭐⭐⭐ | ⭐⭐⭐ | 次優先 |
| 🥈 P2 | **Permission System** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 次優先 |
| 🥉 P3 | **Team Management** | ⭐⭐ | ⭐⭐⭐ | 可稍後 |
| 🥉 P3 | **Facebook Ads** | ⭐⭐ | ⭐⭐⭐⭐ | 核心功能，謹慎處理 |

---

## 📁 建議目錄結構

```
backend/
├── core/                          # 🆕 共用核心（第一步）
│   ├── __init__.py
│   ├── config.py                  # 環境變數集中管理
│   ├── database.py                # 資料庫連線
│   ├── security.py                # 加密、Google OAuth
│   └── exceptions.py              # 統一例外處理
│
├── modules/                       # 🆕 可複用模組
│   ├── auth/                      # P1: 認證模組
│   │   ├── __init__.py
│   │   ├── router.py              # 登入/登出 API
│   │   ├── service.py             # Token 管理
│   │   ├── dependencies.py        # FastAPI 依賴
│   │   └── README.md              # 使用說明
│   │
│   ├── ai_hub/                    # P1: AI 整合模組
│   │   ├── __init__.py
│   │   ├── router.py              # /api/ai/* 端點
│   │   ├── clients/               # AI 客戶端
│   │   │   ├── gemini.py
│   │   │   └── zeabur.py
│   │   ├── intent_classifier.py
│   │   └── README.md
│   │
│   ├── gsc/                       # P2: GSC 分析模組
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── README.md
│   │
│   └── permissions/               # P2: 權限模組
│       ├── __init__.py
│       ├── router.py
│       ├── service.py
│       └── README.md
│
├── features/                      # 專案特定功能（不複用）
│   ├── facebook/                  # Facebook Ads 核心
│   ├── teams/                     # 團隊管理
│   └── analytics/                 # 分析報表
│
├── scripts/                       # 🆕 工具腳本整理
│   ├── manage_admin.py
│   ├── fix_local_db.py
│   └── seed_permissions.py
│
└── main.py                        # 精簡後的入口（< 200 行）
```

---

## 🔧 實作階段（建議 4-6 週）

### Phase 1：建立 Core 基礎 (Week 1)
- [ ] 建立 `core/config.py` - 集中環境變數
- [ ] 建立 `core/security.py` - 從 `auth.py` 抽取加密邏輯
- [ ] 建立 `core/exceptions.py` - 移動例外類別
- [ ] 整理 `scripts/` 資料夾

**驗收**：現有功能不受影響

---

### Phase 2：Auth 模組化 (Week 2)
- [ ] 建立 `modules/auth/`
- [ ] 移動 TokenManager、Google OAuth 邏輯
- [ ] 更新 main.py 使用新模組
- [ ] 撰寫 README.md 使用說明

**驗收**：登入功能正常，模組可獨立測試

---

### Phase 3：AI Hub 模組化 (Week 2-3)
- [ ] 建立 `modules/ai_hub/`
- [ ] 移動 Gemini/Zeabur 客戶端
- [ ] 移動 Intent Classifier
- [ ] 移動 AI Settings Router

**驗收**：AI 功能正常，可複製到其他專案

---

### Phase 4：GSC 模組化 (Week 3-4)
- [ ] 建立 `modules/gsc/`
- [ ] 移動 GSC Router 和 Service
- [ ] 整合 Intent 分析

**驗收**：GSC 分析功能正常

---

### Phase 5：精簡 main.py (Week 4-5)
- [ ] 移除重複代碼
- [ ] 使用模組導入方式
- [ ] 目標：< 200 行

**驗收**：main.py 乾淨可讀

---

## 🔌 模組使用方式

### 在新專案使用 AI Hub 模組

```python
# 1. 複製 modules/ai_hub/ 資料夾
# 2. 複製 core/security.py (加密相依)
# 3. 安裝依賴：pip install google-genai openai

from fastapi import FastAPI
from modules.ai_hub import router as ai_router

app = FastAPI()
app.include_router(ai_router, prefix="/api/ai")
```

---

## ⚠️ 風險管理

| 風險 | 對策 |
|------|------|
| 循環依賴 | 使用 core/ 作為底層，模組不互相引用 |
| 功能中斷 | 每階段完整測試後再進入下一階段 |
| 時間超支 | 可選擇只做 P1 模組，P2/P3 延後 |

---

## ✅ 建議下一步

1. **先不動程式碼**，Review 此計畫
2. 確認優先順序是否符合需求
3. 從 Phase 1 (Core) 開始執行

---

需要我開始執行 Phase 1 嗎？
