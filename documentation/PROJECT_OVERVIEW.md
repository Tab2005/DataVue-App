# DataVue-App - 專案概覽

## 📌 專案簡介

DataVue-App 是一個**多平台數據分析儀表板**，整合 Facebook Ads、Google Search Console (GSC) 和 Google Analytics 4 (GA4) 的數據，提供團隊協作、權限管理、AI 智慧分析等功能。

**技術棧：**
- **後端：** FastAPI (Python)
- **前端：** React 19 + Vite
- **資料庫：** SQLAlchemy (支援 PostgreSQL / SQLite)
- **認證：** Google OAuth 2.0
- **AI 整合：** Google Gemini, Zeabur AI
- **部署：** Zeabur (支援)

---

## 🏗️ 系統架構

### 後端架構 (Modular Design - v2.0.0)

```
backend/
├── main.py                    # FastAPI 應用入口
├── core/                      # 核心共用模組
│   ├── config.py              # 環境變數管理
│   ├── security.py            # 加密/解密 (Fernet)
│   ├── exceptions.py          # 自訂例外類別
│   └── startup.py             # 啟動任務 (DB 初始化、遷移)
│
├── modules/                   # 可重用獨立模組
│   ├── auth/                  # 🔐 認證與權限管理
│   │   ├── __init__.py
│   │   ├── router.py          # /api/auth 端點
│   │   ├── service.py         # TokenManager
│   │   ├── dependencies.py    # get_current_user, require_module
│   │   └── README.md
│   │
│   ├── ai_hub/                # 🤖 AI 服務整合
│   │   ├── __init__.py
│   │   ├── router.py          # /api/ai 端點
│   │   ├── service.py         # AIService
│   │   └── README.md
│   │
│   ├── gsc/                   # 📊 Google Search Console
│   │   ├── __init__.py
│   │   ├── router.py          # /api/gsc 端點
│   │   ├── service.py         # GSCService
│   │   └── README.md
│   │
│   └── ga4/                   # 📈 Google Analytics 4
│       ├── __init__.py
│       ├── router.py          # /api/ga4 端點
│       └── service.py         # GA4Service
│
├── routers/                   # FastAPI 路由
│   ├── users.py               # 使用者管理
│   ├── teams.py               # 團隊管理
│   ├── invites.py             # 邀請系統
│   ├── admin.py               # 超級管理員
│   ├── permissions.py         # 權限管理
│   ├── ai.py                  # AI 分析
│   ├── gsc.py                 # GSC 數據
│   ├── ga4.py                 # GA4 數據
│   ├── facebook.py            # Facebook Ads 數據
│   ├── saved_views.py         # 儲存的視圖
│   └── debug.py               # 開發除錯端點
│
├── services/                  # 業務邏輯服務
├── scripts/                   # 管理腳本
├── seeds/                     # 資料庫種子資料
├── alembic/                   # 資料庫遷移
├── database.py                # SQLAlchemy ORM 模型
├── schemas.py                 # Pydantic 資料模型
├── dependencies.py            # 全域依賴注入
├── auth.py                    # Token 管理器
├── ai_service.py              # AI 服務核心
├── gsc_service.py             # GSC 服務核心
├── ga4_service.py             # GA4 服務核心
└── requirements.txt           # Python 依賴套件
```

### 前端架構

```
frontend/
├── src/
│   ├── App.jsx                # 主應用程式 & 路由配置
│   ├── main.jsx               # React 入口
│   │
│   ├── components/            # React 元件
│   │   ├── Layout.jsx         # 主版面配置
│   │   ├── Header.jsx         # 導航列
│   │   ├── Sidebar.jsx        # 側邊欄
│   │   ├── ProtectedRoute.jsx # 路由保護
│   │   ├── ErrorBoundary.jsx  # 錯誤邊界
│   │   ├── GA4Stats.jsx       # GA4 統計元件
│   │   ├── GSCStats.jsx       # GSC 統計元件
│   │   ├── ContentGroupModal.jsx  # 內容分組模態框
│   │   ├── SourceGroupModal.jsx   # 來源分組模態框
│   │   └── ...                # 其他元件
│   │
│   ├── pages/                 # 頁面元件
│   │   ├── Login.jsx          # 登入頁
│   │   ├── Dashboard.jsx      # Facebook Ads 儀表板
│   │   ├── Analytics.jsx      # Facebook Ads 分析
│   │   ├── SearchConsole.jsx  # GSC 分析
│   │   ├── GA4Analytics.jsx   # GA4 分析
│   │   ├── TeamSettings.jsx   # 團隊設定
│   │   ├── UserManagement.jsx # 使用者管理
│   │   ├── AdminDashboard.jsx # 管理員儀表板
│   │   └── ...
│   │
│   ├── services/              # API 服務層
│   │   ├── aiService.js       # AI API 呼叫
│   │   └── ...
│   │
│   ├── hooks/                 # 自訂 Hooks
│   │   └── index.js           # ProtectedModule
│   │
│   ├── utils/                 # 工具函式
│   │   ├── contentGroups.js   # 內容分組工具
│   │   └── ...
│   │
│   └── styles/                # 全域樣式
│
├── public/                    # 靜態資源
├── package.json               # 前端依賴
├── vite.config.js             # Vite 配置
└── index.html                 # HTML 模板
```

---

## 🗄️ 資料庫設計

### 核心資料表

| 資料表 | 說明 | 關鍵欄位 |
|--------|------|----------|
| **users** | 使用者帳號 | `google_id`, `email`, `role`, `is_super_admin` |
| **teams** | 團隊/組織 | `name`, `owner_id`, `fb_access_token` |
| **team_members** | 團隊成員關聯 | `team_id`, `user_id`, `role` |
| **team_invites** | 團隊邀請碼 | `team_id`, `code`, `expires_at` |
| **modules** | 功能模組定義 | `name` (fb_ads, gsc, ga4, ai_hub) |
| **user_module_access** | 使用者模組權限 | `user_id`, `module_id`, `granted_by` |
| **permissions** | 權限定義 | `name`, `description` |
| **roles** | 角色定義 | `name`, `description` |
| **user_permissions** | 使用者細粒度權限 | `user_id`, `permission_id` |
| **saved_views** | 儲存的視圖/查詢 | `user_id`, `name`, `filters` |
| **page_titles** | GSC 頁面標題快取 | `url`, `title`, `team_id` |

### 資料關聯

```
User (1) ─── (N) TeamMember (N) ─── (1) Team
User (1) ─── (N) UserModuleAccess (N) ─── (1) Module
User (1) ─── (N) UserPermission (N) ─── (1) Permission
Team (1) ─── (N) TeamInvite
```

---

## 🔑 核心功能

### 1. 多平台數據整合

#### Facebook Ads
- **儀表板：** 廣告帳戶總覽、花費、觸及、互動
- **分析頁面：** 多維度數據篩選、圖表視覺化
- **批次分析：** 支援批次請求優化效能

#### Google Search Console (GSC)
- **認證流程：** OAuth2 授權、網站列表
- **數據查詢：** 點擊數、曝光數、CTR、排名
- **頁面分析：** 自動抓取頁面標題、AI 意圖分類
- **比較模式：** 時段/網站對比分析 (計畫中)

#### Google Analytics 4 (GA4)
- **流量分析：** 使用者、工作階段、事件數據
- **行為分析：** 頁面瀏覽、跳出率、參與度
- **內容分組：** 自訂內容分組、來源分組
- **電商分析：** 購買轉換、收益追蹤 (計畫中)

### 2. 團隊協作系統

- **團隊管理：** 建立/編輯/刪除團隊
- **成員管理：** 邀請連結、角色指派 (Owner/Admin/Member/Viewer)
- **Token 共用：** 團隊層級的 Facebook Token 管理
- **權限繼承：** 團隊成員繼承團隊權限

### 3. 權限與模組化

- **模組權限：** fb_ads, gsc, ga4, ai_hub 獨立開關
- **角色權限：** Admin, Member, Viewer 三級權限
- **超級管理員：** 系統級管理、全域使用者/團隊管理
- **細粒度控制：** 自訂權限分配

### 4. AI 智慧分析

- **多供應商支援：** Google Gemini, Zeabur AI
- **意圖分類：** GSC 頁面意圖分析 (資訊/交易/導航)
- **數據洞察：** 自訂提示詞分析數據
- **串流回應：** 支援 SSE 串流輸出
- **加密儲存：** API Key 使用 Fernet 加密儲存

### 5. 進階功能

- **儲存視圖：** 儲存常用篩選條件、快速載入
- **匯出功能：** PDF 報表匯出
- **快取機制：** 頁面標題快取、減少 API 呼叫
- **錯誤處理：** 統一例外處理、友善錯誤訊息
- **健康檢查：** `/api/health` 端點、系統診斷

---

## 🔐 認證與授權流程

### 1. 使用者登入
```
前端 → Google OAuth → 取得 ID Token → 後端驗證 → 建立/更新 User → 返回使用者資訊
```

### 2. Facebook Token 管理
```
使用者 → 提供 App ID/Secret/Short Token → 後端交換 Long-lived Token → 儲存到 User/Team
```

### 3. GSC 授權
```
前端 → Google OAuth (GSC Scope) → 授權碼 → 後端交換 Refresh Token → 儲存到 User
```

### 4. GA4 授權
```
前端 → Google OAuth (GA Scope) → 授權碼 → 後端交換 Refresh Token → 儲存到 User/Team
```

### 5. 權限檢查
```python
# 模組權限
@app.get("/api/gsc/analytics")
def gsc_analytics(_: bool = Depends(require_module("gsc"))):
    pass

# 使用者認證
def protected_endpoint(user: User = Depends(get_current_user)):
    pass

# 管理員權限
def admin_endpoint(admin: User = Depends(get_admin_user)):
    pass
```

---

## 📡 API 端點總覽

### 認證端點
- `POST /api/auth/exchange-token` - 交換 Facebook Long-lived Token
- `GET /api/auth/token-status` - 檢查 Token 狀態
- `GET /api/auth/me` - 取得當前使用者資訊

### 使用者管理
- `GET /api/users/me` - 取得個人資料
- `GET /api/users/` - 列出所有使用者 (Admin)
- `POST /api/users/` - 建立使用者 (Admin)

### 團隊管理
- `GET /api/teams/me` - 取得我的團隊列表
- `POST /api/teams/` - 建立團隊
- `GET /api/teams/{team_id}` - 取得團隊詳情
- `PUT /api/teams/{team_id}` - 更新團隊
- `DELETE /api/teams/{team_id}` - 刪除團隊
- `GET /api/teams/{team_id}/members` - 列出成員
- `POST /api/teams/{team_id}/members` - 新增成員
- `PUT /api/teams/{team_id}/members/{user_id}` - 更新成員角色

### 邀請系統
- `POST /api/invites/` - 建立邀請連結
- `GET /api/invites/{code}` - 取得邀請詳情
- `POST /api/invites/{code}/accept` - 接受邀請

### Facebook Ads
- `GET /api/ad-accounts` - 列出廣告帳戶
- `GET /api/dashboard-data` - 儀表板數據
- `GET /api/analytics` - 分析數據

### Google Search Console
- `POST /api/gsc/authorize` - GSC 授權
- `GET /api/gsc/sites` - 列出網站
- `GET /api/gsc/analytics` - GSC 數據
- `POST /api/gsc/page-titles` - 批次抓取頁面標題
- `POST /api/gsc/page-intents` - AI 頁面意圖分析

### Google Analytics 4
- `POST /api/ga4/authorize` - GA4 授權
- `GET /api/ga4/accounts` - 列出帳戶
- `GET /api/ga4/properties` - 列出資源
- `GET /api/ga4/analytics` - GA4 數據

### AI 服務
- `GET /api/ai/providers` - 列出 AI 供應商
- `GET /api/ai/models` - 列出可用模型
- `POST /api/ai/test-connection` - 測試連線
- `POST /api/ai/analyze` - 分析數據
- `POST /api/ai/analyze-stream` - 串流分析
- `GET /api/ai/settings` - 取得 AI 設定
- `POST /api/ai/settings` - 儲存 AI 設定 (加密)

### 權限管理
- `GET /api/permissions/modules` - 列出所有模組
- `GET /api/permissions/user/{user_id}/modules` - 取得使用者模組權限
- `POST /api/permissions/user/{user_id}/modules` - 授予模組權限
- `DELETE /api/permissions/user/{user_id}/modules/{module_name}` - 撤銷模組權限

### 系統管理
- `GET /api/admin/stats` - 系統統計
- `GET /api/admin/users` - 所有使用者 (Super Admin)
- `GET /api/admin/teams` - 所有團隊 (Super Admin)
- `DELETE /api/admin/users/{user_id}` - 強制刪除使用者

### 其他
- `GET /api/health` - 健康檢查
- `GET /api/saved-views` - 儲存的視圖
- `POST /api/saved-views` - 新增視圖
- `DELETE /api/saved-views/{view_id}` - 刪除視圖

---

## 🚀 部署與啟動

### 本地開發環境

#### 1. 後端啟動
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# 設定環境變數 (.env 檔)
cp .env.example .env
# 編輯 .env 填入必要資訊

# 啟動開發伺服器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. 前端啟動
```bash
cd frontend
npm install
npm run dev
```

### 生產環境部署 (Zeabur)

1. **環境變數設定：**
   - `DATABASE_URL`: PostgreSQL 連線字串
   - `GOOGLE_CLIENT_ID`: Google OAuth Client ID
   - `GOOGLE_CLIENT_SECRET`: Google OAuth Client Secret
   - `ENCRYPTION_KEY`: Fernet 加密金鑰

2. **資料庫遷移：**
   ```bash
   alembic upgrade head
   ```

3. **Docker 部署：**
   ```bash
   docker build -t datavue-backend ./backend
   docker run -p 8000:8000 datavue-backend
   ```

---

## 🛠️ 開發指南

### 新增模組

1. 在 `backend/modules/` 建立模組資料夾
2. 實作 `router.py`, `service.py`, `__init__.py`
3. 在 `main.py` 註冊 Router
4. 在 `database.py` 新增 Module 種子資料

### 資料庫遷移

```bash
# 建立新遷移
alembic revision --autogenerate -m "描述變更"

# 執行遷移
alembic upgrade head

# 回退遷移
alembic downgrade -1
```

### 測試 API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📊 技術亮點

1. **模組化設計：** 可獨立重用的 modules (auth, ai_hub, gsc, ga4)
2. **多資料庫支援：** SQLite (開發) / PostgreSQL (生產)
3. **安全性：** 加密儲存敏感資料、OAuth2 認證、依賴注入權限檢查
4. **效能優化：** 快取機制、批次請求、Lazy Loading
5. **錯誤處理：** 統一例外處理、詳細錯誤日誌
6. **文件完整：** API 文件、README、架構說明
7. **CI/CD：** Zeabur 自動部署支援

---

## 📝 版本資訊

- **當前版本：** v2.0.0
- **前端版本：** v1.5.0
- **Python 版本：** 3.8+
- **Node 版本：** 16+
- **資料庫版本：** SQLAlchemy 2.x

---

## 🔮 未來規劃

請參考 [ROADMAP.md](ROADMAP.md) 了解完整規劃。

**近期計畫：**
- GA4 行為分析、內容分析、電商分析頁籤
- GSC 比較模式功能
- 多語系支援
- 更多 AI 分析場景
- 效能監控與告警

---

## 📚 相關文件

- [架構文件](architecture.md)
- [資料庫設計](database.md)
- [部署指南](deployment.md)
- [開發指南](DEVELOPMENT_GUIDELINES.md)
- [權限系統設計](permission_system_design.md)
- [模組化策略](MODULARIZATION_STRATEGY.md)
- [疑難排解](troubleshooting.md)

---

**維護者：** Tab2005  
**授權：** MIT License  
**最後更新：** 2026-01-15
