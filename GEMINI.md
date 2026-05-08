# DataVue 專案開發規範 (GEMINI.md)

本文件定義了 DataVue 專案的架構原則、代碼風格與開發流程，旨在保持前後端代碼的一致性與可維護性。

---

## 🏗️ 系統架構概覽

### 後端 (Backend) - FastAPI
- **入口點**: `backend/main.py` (保持在 200 行以內)。
- **啟動邏輯**: 統一由 `backend/core/startup.py` 處理，包含環境驗證、資料庫遷移 (Alembic) 與權限初始化。
- **路由器 (Routers)**: 位於 `backend/routers/`，必須定義 `prefix` (建議為 `/api/...`) 與 `tags`。
- **服務層 (Services)**: 核心業務邏輯位於 `backend/services/`；第三方 API 整合位於 `backend/service_modules/`。
- **資料庫**: 使用 SQLAlchemy 2.0。模型定義於 `backend/database/models/`。
- **遷移**: 所有的 Schema 變動必須透過 Alembic (`backend/alembic/`) 進行。

### 前端 (Frontend) - React 19 + Vite 7
- **路由**: 使用 React Router 7。除 Login 與 Layout 外，所有頁面元件應使用 `lazy()` 進行延遲載入。
- **數據獲取**: 統一使用 `@tanstack/react-query` 進行狀態管理與快取。
- **樣式**: 採用 Glassmorphism (磨砂玻璃) 設計風格，使用 Vanilla CSS。
- **元件**: 位於 `src/components/`，按功能模組分類 (如 `Analytics`, `Reports`)。

---

## 🎨 代碼風格與慣例

### 通用規範
- **語言**: 所有的開發文件 (Markdown)、Docstrings 以及複雜邏輯的註解，應優先使用 **繁體中文**。
- **Git**: 提交訊息應簡明扼要，描述變更的原因而非僅僅是變更的內容。

### 後端規範 (Python)
- **命名**: 變數與函數使用 `snake_case`，類別使用 `PascalCase`。
- **日誌**: 禁止使用 `print()`，請統一使用 `logging.getLogger(__name__)`。
- **異常處理**: 使用自定義異常 (`AppException`)，並在關鍵路徑上記錄 Traceback。
- **型別提示**: 所有的 API 端點、函數參數與回傳值均應標註 Type Hints。
- **Pydantic**: 統一使用 Pydantic v2 進行 Schema 驗證。

### 前端規範 (JavaScript/React)
- **命名**: 元件檔案與類別使用 `PascalCase` (如 `KPICard.jsx`)，變數與一般函數使用 `camelCase`。
- **樣式**: 元件應有對應的 `.css` 檔案，或使用 CSS Modules (若專案已啟用)。
- **Props**: 雖然目前使用 `.jsx`，但鼓勵對 Props 進行清晰的命名與（若可能）解構處理。

---

## 🚀 開發工作流

### 環境啟動
- 啟動前後端：在根目錄執行 `.\run-all.ps1`。
- 停止服務：執行 `.\stop-all.ps1`。

### 資料庫變動
1. 在 `backend/database/models/` 修改模型。
2. 執行 `alembic revision --autogenerate -m "描述"` 產生遷移檔。
3. 啟動應用程式時會自動執行 `alembic upgrade head`，或手動執行相關腳本。

### 新增 API 端點
1. 在 `backend/routers/` 建立或修改 Router。
2. 在 `backend/services/` 實作業務邏輯。
3. 在 `backend/main.py` 註冊新的 Router。
4. (前端) 使用 `useQuery` 或 `useMutation` 串接新端點。

---

## 🔒 安全性規範
- **Token 儲存**: 第三方 Access Tokens 必須加密儲存 (使用 `Fernet` 加密，定義於 `UserIntegration` 模型)。
- **環境變數**: 敏感資訊 (API Keys, Secrets) 嚴禁寫死在代碼中，必須透過 `.env` 讀取。
- **速率限制**: 敏感或高消耗的 API 端點應掛載 `limiter` (SlowAPI)。
