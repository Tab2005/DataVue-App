# Facebook Dashboard Web App - 專案資料總覽

> **版本**: v1.5.3 | **最後更新**: 2025-12-17

---

## 📋 專案概述

**Facebook Dashboard Web App** 是一個高效能的 Facebook 廣告數據儀表板 SaaS 平台，提供行銷人員整合、視覺化且具備深度分析能力的監控工具。

### 核心價值
- 🎯 **多帳號管理** - 支援跨廣告帳號切換與數據整合
- 📊 **進階分析** - Campaign / Ad Set / Ad 四層級深度報表
- 👥 **團隊協作** - 完整的團隊工作區與角色權限控制
- 🤖 **AI 智慧分析** - Google Gemini 整合的診斷助理

---

## 🛠️ 技術架構

### 前端 (Frontend)
| 項目 | 技術 |
|------|------|
| 框架 | React 19 + Vite 7 |
| 語言 | JavaScript (ES6+) |
| 路由 | React Router v7 |
| 圖表 | Recharts |
| 樣式 | CSS Modules (Glassmorphism 風格) |
| 認證 | @react-oauth/google |

### 後端 (Backend)
| 項目 | 技術 |
|------|------|
| 框架 | FastAPI (Python 3.9+) |
| 伺服器 | Uvicorn (ASGI) |
| ORM | SQLAlchemy + Alembic |
| 資料庫 | SQLite (Local) / PostgreSQL (Production) |
| API 整合 | Facebook Graph API v24.0 |
| 非同步 HTTP | httpx (aiohttp) |
| 快取 | cachetools (TTL-based Memory Cache) |
| 加密 | Fernet 對稱式加密 |
| AI | Google Gemini (genai) |

### 部署
- **平台**: Zeabur
- **前端**: Static Site Hosting
- **後端**: Dockerized Service
- **資料庫**: PostgreSQL Service

---

## 📁 專案結構

```
Facebook Dashboard Web App/
├── backend/                    # FastAPI 後端
│   ├── main.py                 # 主應用程式 & API 端點
│   ├── services.py             # Facebook API 整合服務
│   ├── async_services.py       # 非同步 API 服務 (httpx)
│   ├── cache.py                # 快取管理服務
│   ├── exceptions.py           # 統一例外處理
│   ├── auth.py                 # 認證邏輯
│   ├── database.py             # 資料庫模型
│   ├── ai_service.py           # AI 分析服務
│   ├── routers/                # API 路由模組
│   │   ├── users.py
│   │   ├── teams.py
│   │   ├── invites.py
│   │   ├── ai.py
│   │   └── admin.py
│   ├── service_modules/        # 模組化服務 (重構後)
│   │   ├── facebook_api.py     # 純 API 呼叫
│   │   └── metrics.py          # 指標計算邏輯
│   ├── alembic/                # 資料庫遷移
│   └── requirements.txt        # Python 相依套件
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.jsx             # 主應用程式 (Code Splitting)
│   │   ├── components/         # UI 元件
│   │   │   ├── Analytics/      # 模組化分析元件
│   │   │   ├── ErrorBoundary.jsx
│   │   │   ├── Skeleton.jsx    # 載入骨架屏
│   │   │   └── PageLoading.jsx
│   │   ├── pages/              # 頁面元件 (React.lazy 延遲載入)
│   │   ├── hooks/              # 自訂 Hooks
│   │   │   ├── useOptimistic.js
│   │   │   └── useAnalyticsFilters.js
│   │   ├── constants/          # 常數配置
│   │   │   └── analyticsConfig.js
│   │   ├── services/           # API 服務
│   │   └── utils/              # 工具函式
│   ├── package.json
│   └── vite.config.js
│
├── docs/                       # 文件目錄
├── SPECIFICATION.md            # 專案規格書
├── CHANGELOG.md                # 版本更新紀錄
├── IDEAS.md                    # 開發路線圖
├── OPTIMIZATION_PLAN.md        # 優化計畫與進度
├── DEPLOYMENT.md               # 部署指南
└── zeabur.toml                 # Zeabur 部署配置
```

---

## ✨ 核心功能

### 1. 認證與授權
- ✅ Google OAuth 2.0 登入
- ✅ Facebook Long-Lived Token 自動交換 (60 天)
- ✅ Token 過期預警通知 (3 天內 Header 紅點提示)

### 2. 數據儀表板
- ✅ 8-Grid KPI 卡片佈局
- ✅ 同期比較模式 (Previous Period)
- ✅ 每日趨勢圖表

### 3. 進階分析
- ✅ 四層級報表: Account / Campaign / Ad Set / Ad
- ✅ 自訂指標選擇器 (General / E-commerce / Funnel / CPAS)
- ✅ 漏斗轉換率計算
- ✅ 雙軸趨勢比較圖
- ✅ 表格排序與關鍵字篩選

### 4. 團隊協作 (SaaS)
- ✅ 團隊工作區 CRUD
- ✅ 24小時邀請連結
- ✅ 角色權限控制 (Owner / Admin / Member / Viewer)
- ✅ 廣告帳號白名單

### 5. AI 智慧分析
- ✅ Google Gemini 整合
- ✅ 自動診斷模式
- 🚧 對話式助理 (開發中)

---

## 📊 支援的數據指標

| 分類 | 指標 |
|------|------|
| **General** | Spend, Impressions, Reach, CPM, CPC, CTR, Link Clicks |
| **E-commerce** | Purchases, Purchase Value, ROAS, CPA |
| **Funnel** | View Content, Add to Cart, Initiate Checkout, Add Payment Info |
| **CPAS** | Shared Purchases, Shared ROAS, Shared ATC |
| **Engagement** | Comments, Shares, Saves, Reactions, Page Likes |
| **Diagnosis** | Quality Ranking, Engagement Ranking, Conversion Ranking |

---

## 🔌 API 端點

| 方法 | 端點 | 說明 |
|------|------|------|
| `GET` | `/api/auth/token-status` | Token 過期狀態 |
| `POST` | `/api/auth/exchange-token` | 交換 Long-Lived Token |
| `GET` | `/api/ad-accounts` | 廣告帳號列表 |
| `GET` | `/api/dashboard-data` | Dashboard KPI 數據 |
| `GET` | `/api/analytics-data` | Analytics 詳細報表 |
| `GET` | `/api/analytics-trend` | 趨勢圖數據 |
| `GET` | `/api/teams` | 團隊管理 |
| `POST` | `/api/ai/analyze` | AI 分析 |

---

## 🚀 版本歷程

| 版本 | 日期 | 重點更新 |
|------|------|----------|
| v1.5.3 | 2025-12-17 | **效能優化大更新 (13項)** |
| v1.5.2 | 2025-12-16 | API 設定介面優化 |
| v1.5.1 | 2025-12-15 | Mobile UX 增強 |
| v1.5.0 | 2025-12-13 | **Hybrid SaaS 架構 & 團隊管理** |
| v1.4.x | 2025-12-11~12 | Token 通知、趨勢比較圖 |
| v1.3.x | 2025-12-10~11 | 進階分析、CPAS、素材預覽 |
| v1.2.0 | 2025-12-10 | Performance Dashboard |
| v1.0.0 | 2024-12-08 | 初始版本 |

---

## 📈 未來規劃

1. **AI 演進**
   - Copilot 對話式助理
   - Autopilot 自動化規則

2. **商業化**
   - Stripe 訂閱制整合
   - 用量配額管理

3. **渠道擴充**
   - GA4 整合
   - 全漏斗歸因分析
