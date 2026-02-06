# 模組化實作計畫（執行版）

**目標**：把目前專案逐步從單體／低模組化狀態，轉為清晰分離、可獨立開發 / 測試 / 部署的模組化系統（包含 backend 與 frontend）。

> 注意：目前**不會直接修改任何程式碼**。本檔為實作計畫與驗收標準，供評估與後續 PR 執行使用。

---

## 一、範圍與交付物 ✅

- 範圍：backend（主要）、frontend（次要）、CI/CD 與文件。
- 交付物：
  - 模組化設計文件（本檔）
  - 依賴圖與候選模組清單（*.svg / *.png / markdown）
  - 每階段驗收準則與測試清單
  - 範例模組（PoC）與部署步驟

---

## 二、原則（Guiding Principles） 💡

- 小步漸進、保持相容（adapter / ports pattern）
- 明確責任邊界（資料擁有權、API/事件介面）
- 共享基礎套件集中管理（logger、auth、config、types）
- 可測試、可部署、可回滾（強化測試與 pipeline 門檻）

---

## 三、分階段實作計畫（每階段含驗收標準） 🔧

### 階段 0 — 分析（當前）🔎
- 動作：靜態與動態程式碼掃描（backend + frontend）、產生依賴圖與耦合度報告。列出每個候選模組的「擁有者」與相關 DB table。
- 工具：pydeps / depcruise / 自訂 Python AST 分析 / 執行 trace
- 驗收：交付依賴圖、候選模組清單（含理由與優先度）

### 階段 1 — 規格與設計 🧭
- 動作：為每個候選模組定義責任、公開 API（HTTP/函式/事件）、設定與 env 需求。
- 產出：模組規格文件（含 OpenAPI / typed interfaces / usage examples）
- 驗收：每個模組有明確規格與 stub 接口，團隊同意契約

### 階段 2 — 資料與遷移準備 🗃️
- 動作：定義 DB schema ownership、migration 路徑，撰寫備援與驗證腳本（alembic 調整）
- 驗收：每個 DB 變更有 migration、回滾步驟與驗證測試

### 階段 3 — 小步驟重構（PoC）🔁
- 動作：選 1–2 個低風險模組做 PoC（例如 AI settings、GSC），採 Adapter pattern 保持相容層，撰寫單元 + 整合測試
- 驗收：PoC 模組能獨立在 dev/staging environment 部署且功能正確

### 階段 4 — 前端模組化與共用元件 🧩
- 動作：調整前端為 feature-based folders、抽出 component library、定義 per-module API client
- 驗收：至少一個前端 feature 可被拆分並單獨打包

### 階段 5 — CI/CD 與自動化 📦
- 動作：修改 CI 支援 per-module tests、per-module publish、canary / blue-green 策略
- 驗收：pipeline 能在 PR 階段自動驗證模組契約與測試

### 階段 6 — 上線 / 監控 / 回滾 🟢
- 動作：制定逐步上線與監控指標，實作告警與自動回滾腳本
- 驗收：完成一次模擬上線演練並驗證回滾

---

## 四、驗收準則（每階段）✅
- 規格文件與測試存在且綠燈
- 模組能獨立被部署（或在逐步部署策略下安全釋出）
- 回滾步驟與資料備援被測試

---

## 五、風險與對策 ⚠️
- 循環依賴：採用依賴注入與 interface-first 設計
- 資料庫相容性：採用 shadow table 與遷移驗證
- 測試不足：強制 PR pipeline 包含單元/整合測試

---

## 六、初步時間估算（粗略） ⏱️
- 分析與設計：1–2 週
- PoC（1–2 模組）：2–4 週
- 全面分階段重構：視範圍 2–3 個月（拆成多個 sprint）

（完成依賴掃描後可提供更精確估算）

---

## 七、下一步行動（建議）➡️
1. 完成全面依賴掃描並交付依賴圖與候選模組清單（優先）
2. 根據優先清單選一個模組做 PoC（含測試與 pipeline）
3. 實作共用基礎套件（logger、config、auth、types）

---

## 八、檔案位置與使用方式
- 檔案：`/docs/MODULARIZATION_IMPLEMENTATION_PLAN.md`（本檔）
- 使用：任何重構相關 PR 應在描述中引用本計畫對應的階段與驗收準則。

---

如果你同意，我會接著：
- 把本計畫同步到任何相關議題（issue）與 PR 範本（需你同意再做），
- 然後繼續程式碼掃描並回報依賴圖與候選模組清單（不修改程式碼）。
