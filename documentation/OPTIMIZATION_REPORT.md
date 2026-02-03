# DataVue 專案優化檢查報告

產生日期：2026-01-30

## 掃描範圍
- 後端入口與啟動流程（[backend/main.py](backend/main.py)、[backend/core/startup.py](backend/core/startup.py)）
- 資料庫連線與 ORM 模型（[backend/database.py](backend/database.py)）
- 前端建置與依賴（[frontend/package.json](frontend/package.json)）
- 專案結構與可疑臨時檔

---

## 立即可做（低風險）
1. **將 Debug Router 以環境變數控制**
   - 目前 Debug Router 直接載入（[backend/main.py](backend/main.py)）。
   - 建議：在 production 停用或加上 `DEBUG=true` 開關，避免暴露除錯端點。

2. **限制 CORS 範圍**
   - 目前 `allow_origins=["*"]`（[backend/main.py](backend/main.py)）。
   - 建議：以環境變數配置允許來源，避免生產環境過度開放。

3. **統一日誌（logging）**
   - 目前大量 `print()`（[backend/main.py](backend/main.py)、[backend/core/startup.py](backend/core/startup.py)）。
   - 建議：使用 `logging` 設定 log level 與格式，方便觀測與排錯。

4. **整理非核心腳本位置**
   - 根目錄與 backend 內仍有大量一次性 debug/維運腳本（如 [backend/debug_start.py](backend/debug_start.py)、[backend/list_rows.py](backend/list_rows.py) 等）。
   - 建議：集中到 `backend/scripts/` 或標記為維運工具，避免混淆主要程式邏輯。

---

## 中期改善（中風險）
1. **啟動時資料表修補（schema patching）應移出 runtime**
   - 目前在啟動流程中執行自動 schema patching（[backend/core/startup.py](backend/core/startup.py)）。
   - 建議：將 schema 修改集中到 Alembic migration，避免 runtime 自動修補造成意外資料結構變動。

2. **`init_db()` 與 Alembic 的責任分離**
   - `Base.metadata.create_all()` 在非生產仍會執行（[backend/database.py](backend/database.py)）。
   - 建議：開發模式才使用 `create_all()`，正式環境僅由 Alembic 管理。

3. **PostgreSQL 連線失敗時應直接 fail-fast**
   - 目前 DATABASE_URL 失敗時 `engine=None` 仍可繼續啟動（[backend/database.py](backend/database.py)）。
   - 建議：在生產環境改為直接中止啟動並提示錯誤。

4. **環境變數驗證應能阻擋啟動**
   - `validate_environment()` 目前只警告不終止（[backend/core/startup.py](backend/core/startup.py)）。
   - 建議：在 production 模式下缺失必要變數直接終止。

---

## 長期改善（較高風險/需規劃）
1. **拆分 `main.py` 的責任**
   - `main.py` 目前同時包含 router 註冊、auth endpoints、health check（[backend/main.py](backend/main.py)）。
   - 建議：將 auth endpoints 與 health check 拆到 router 模組，維持入口檔簡潔。

2. **安全憑證與 Token 儲存一致化**
   - DB 內已有加密欄位，但建議確認所有 token 都透過同一加解密層處理（[backend/database.py](backend/database.py)）。

3. **API 統一錯誤碼/錯誤格式**
   - 目前部分 endpoint 直接拋出 `HTTPException`，與 `AppException` 格式不一致（[backend/main.py](backend/main.py)）。
   - 建議：統一錯誤響應格式與錯誤碼規範。

---

## 清理結果（已移除暫存/測試檔）
- [backend/start_backend.log](backend/start_backend.log)
- [backend/tokens.json.bak](backend/tokens.json.bak)
- [backend/facebook_dashboard.db.bak](backend/facebook_dashboard.db.bak)
- [backend/__pycache__](backend/__pycache__)
- [scripts/check_dbs.py](scripts/check_dbs.py)

---

## 後續可選項
- 若需要我可以：
  - 將 Debug/維運腳本集中整理到 `backend/scripts/` 並補上 README。
  - 把 `start.ps1` 與 `start-frontend.ps1` 啟動流程統一化。
  - 新增 pre-commit 或 lint/format 流程。
