# 21. MMM 廣告活動貢獻衡量模組實作計劃

- **日期**：2026-07-06
- **性質**：實作計劃（依可行性驗證結果展開為可執行任務，驗證摘要見本文「零」章）
- **依據**：2026-07-06 可行性驗證（合成資料 + 真實帳號 act_1077213689343030，脚本見開發 session scratchpad，演算法將於任務 1.2 移植入 repo）
- **範圍**：新增 `backend/modules/contribution/`、`backend/database/models/contribution.py`、`backend/alembic/versions/`、`backend/core/scheduler.py`、`backend/seeds/permission_seeds.py`、`frontend/src/pages/ContributionAnalysis.jsx`、`frontend/src/services/contributionService.js`
- **執行原則**：每個任務獨立可測、可回滾；第 1 波（後端核心 + 演算法移植與測試）完成並通過驗收前，不進入第 2 波（前端）；第 3 波（自動化與 Andromeda 整合）為選配，依使用回饋決定。

---

## 零、背景與可行性驗證摘要

### 0.1 模組定位

回答「**哪個廣告活動真正帶來增量轉換、下一塊錢該投給誰**」。與既有模組的分工：

| 模組 | 層次 | 回答的問題 |
|---|---|---|
| Meta Andromeda | 素材層（micro） | 這支素材上線前預估表現如何？ |
| **Contribution（本模組）** | 活動層（macro） | 各活動的真實增量貢獻是多少？預算怎麼調？ |
| fb_ads | 資料層 | 平台自報的成效數字是什麼？ |

### 0.2 為什麼是 MMM 而不是路徑歸因

六種歸因模型（首次/最後點擊、線性、時間遞減、位置、馬可夫鏈）需要使用者層級接觸路徑，Meta Marketing API 不提供（Meta Attribution 工具已於 2022 下線）。MMM（Marketing Mix Modeling，Meta 官方開源 Robyn 即同路線）只需**活動層每日聚合資料**，現有 API 即可取得。原理：從「各活動花費的時間序列共變」估計增量貢獻，可暴露 always-on／再行銷活動「收割功勞」的自報偏差。

### 0.3 可行性驗證結果（2026-07-06）

**合成資料**（已知真實貢獻、4 活動 × 180 天 × 5 seeds）：貢獻比例平均絕對誤差 MMM **5.4%** vs 平台自報 **15.8%**；再行銷收割偏差（自報 40.8% vs 真實 9.2%）5/5 次被糾正至 ~12%。

**真實帳號**（act_1077213689343030，180 天、15 活動、3,246 筆購買、日均 18）：

| 組別 | 花費占比 | 自報購買占比 | MMM 貢獻（5 次重啟中位/範圍） | 邊際購買 /+100元 |
|---|---|---|---|---|
| G1 主力常態（always-on） | 46.9% | 49.1% | 29.3%（28.1–39.3%） | 0.164 |
| G2 主力影片 | 13.1% | 13.5% | 10.8% | 0.168 |
| G3 官網檔期 | 13.1% | 12.4% | 16.2% | 0.165 |
| G4 社群自投 | 9.5% | 11.1% | 16.6% | 0.300 |
| G5 大包裝 | 7.2% | 6.6% | 11.2% | 0.358 |
| G6 小額常態 | 7.0% | 6.4% | 0%（共線假象，存疑） | — |
| G7 測試導流 | 3.1% | 1.0% | 0% | — |
| 基線+週期 | — | — | 17.8% | — |

診斷：in-sample R² 0.77（Poisson 雜訊天花板 0.86）、holdout R² 0.16（天花板 0.58）；花費共線嚴重（G1×G5 r=0.76、G3×G5 r=0.86、G6 與所有組負相關 -0.6 ~ -0.67）。

### 0.4 驗證結論對產品範圍的約束（本計劃的邊界）

1. **只做組別層級**：單活動點估計在共線資料下不可信 → 活動須分組（自動建議 + 使用者可調）。
2. **只給區間，不給單點**：貢獻一律以多次重啟的中位數 + 範圍呈現。
3. **附帶診斷**：共線性警告、資料量檢查（最少天數/日轉換量）為一級輸出，不是隱藏細節。
4. **y 先用 Meta 自報總購買**：整體量級仍含平台偏差，但活動「之間」的相對貢獻由時間共變學出、是去偏的；未來可換 GA4/CRM 訂單數，模型不需改。

---

## 一、系統架構總覽

```
┌────────────────────────────────────────────────────┐
│                 前端 (React)                        │
│        ContributionAnalysis（貢獻分析頁）            │
│   貢獻對比圖 │ 邊際報酬排序 │ 分組編輯 │ 診斷警告卡    │
└───────────────────────┬────────────────────────────┘
                        │ HTTP /api/contribution
┌───────────────────────▼────────────────────────────┐
│          後端 FastAPI modules/contribution          │
│  router.py → service.py → repository.py            │
│                                                     │
│  ┌────────────┐ ┌────────────┐ ┌────────────────┐  │
│  │ data_source │ │ engine.py  │ │ grouping.py    │  │
│  │ .py (FB     │ │ (adstock + │ │ (活動自動分組  │  │
│  │  每日抓取)  │ │  hill + 非 │ │  規則)         │  │
│  │            │ │  負ridge)  │ │                │  │
│  └────────────┘ └────────────┘ └────────────────┘  │
│                                                     │
│  core/scheduler.py: add_contribution_analysis_job   │
│  （分析為背景任務，狀態輪詢，同 Andromeda 評分模式）  │
└───────────────────────┬────────────────────────────┘
                        │ SQLAlchemy ORM
┌───────────────────────▼────────────────────────────┐
│   PostgreSQL：3 張 contribution_* 資料表             │
└────────────────────────────────────────────────────┘
```

**與 Andromeda 的共用邊界**：共用「模式」（模組骨架、`require_module` 權限、背景任務 + 狀態輪詢、TokenManager 取 token），**不共用**引擎與資料表（Andromeda 是 LLM 素材評分，本模組是確定性統計計算；互相 import 僅限第 3 波的資料層整合，且方向為 Contribution → Andromeda 單向）。

---

## 二、資料庫設計（3 張資料表）

定義於新檔 `backend/database/models/contribution.py`，並在 `database/models/__init__.py` 註冊。

### 2.1 ContributionDailyMetric（活動每日數據快取）

**資料表名**：`contribution_daily_metrics`

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | `cda_` 前綴 + 12 位 hex |
| `account_id` | String(120) index | 廣告帳戶 ID（`act_` 格式） |
| `date` | String(10) | `YYYY-MM-DD` |
| `campaign_id` | String(120) | 活動 ID |
| `campaign_name` | String | 活動名稱（抓取當下快照） |
| `spend` | Float | 當日花費 |
| `impressions` | Integer | 曝光 |
| `conversions` | Float | 主要轉換數（依 `metric_key`） |
| `conversion_value` | Float | 轉換價值 |
| `metric_key` | String(50) | 轉換指標鍵，預設 `omni_purchase` |
| `actions_payload` | JSON | 原始 actions 陣列（保留完整訊號供未來換指標） |
| `fetched_at` | DateTime | 抓取時間 |

**唯一約束**：`(account_id, date, campaign_id, metric_key)`。重抓時 upsert，避免重複。

### 2.2 ContributionCampaignGroup（活動分組設定）

**資料表名**：`contribution_campaign_groups`

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | `cgr_` 前綴 |
| `account_id` | String(120) index | 廣告帳戶 ID |
| `group_key` | String(50) | 組別代碼（如 `G1`） |
| `group_name` | String(120) | 顯示名稱（如「主力常態」） |
| `campaign_ids` | JSON | 活動 ID 陣列 |
| `source` | String(20) | `auto`（規則建議）或 `manual`（使用者調整） |
| `updated_by` | String FK → users.id | 最後修改者 |
| `created_at` / `updated_at` | DateTime | 時間戳 |

### 2.3 ContributionSnapshot（分析結果快照）

**資料表名**：`contribution_snapshots`

| 欄位 | 類型 | 說明 |
|---|---|---|
| `id` | String PK | `csn_` 前綴 |
| `account_id` | String(120) index | 廣告帳戶 ID |
| `status` | String(20) | `queued` / `processing` / `completed` / `failed` |
| `date_start` / `date_end` | String(10) | 分析期間 |
| `config` | JSON | 分析參數（metric_key、holdout 天數、重啟次數、theta/K 網格、lambda、分組快照） |
| `results` | JSON | 每組：貢獻中位數/min/max、自報占比、花費占比、邊際轉換、theta/K 選中值；基線占比 |
| `diagnostics` | JSON | holdout/full R²、Poisson 天花板、共線性矩陣與警告清單、資料量檢查結果 |
| `error_message` | Text | 失敗原因（status=failed 時） |
| `runtime_job_id` | String(120) | 調度器任務 ID |
| `created_by` | String FK → users.id | 發起者 |
| `created_at` / `completed_at` | DateTime | 時間戳 |

**Alembic migration**：`20260706_contribution_module_tables.py`（建 3 表 + 唯一約束 + 索引）。

---

## 三、後端模組設計（`backend/modules/contribution/`）

```
contribution/
  __init__.py
  router.py          # API 端點
  dependencies.py    # require_contribution_module = require_module("contribution")
  schemas.py         # Pydantic request/response
  service.py         # 編排：抓資料 → 分組 → 引擎 → 寫快照
  repository.py      # ORM 存取（daily metrics upsert、snapshot CRUD、group CRUD）
  data_source.py     # Meta Insights 每日抓取（level=campaign, time_increment=1, 分頁）
  grouping.py        # 活動自動分組規則
  engine.py          # MMM 引擎（純函數、無 I/O、可單獨測試）
```

### 3.1 engine.py — MMM 引擎規格（自可行性驗證腳本移植）

純 numpy 實作，全部為無副作用函數：

| 函數 | 規格 |
|---|---|
| `adstock(x, theta)` | 幾何遞延：`out[t] = x[t] + theta * out[t-1]` |
| `hill(x, K)` | 飽和曲線：`x / (x + K)` |
| `nonneg_ridge(X, y, lam, iters)` | 非負 ridge：投影梯度下降（Lipschitz 步長） |
| `fit(spend_by_group, y, config)` | 隨機搜尋 θ∈{0,0.15,…,0.75} × K∈{P25,P50,P75}（各組獨立），時間序列前段訓練 / 末段（預設 45 天）驗證選模；預設 800 trials |
| `run_analysis(spend_by_group, y, config)` | 跑 `n_restarts`（預設 5）次不同 seed 的 `fit`，彙整為中位數/範圍 + 邊際轉換（穩態 adstock 乘數 × hill 導數差分）+ 診斷 |
| `diagnose(spend_by_group, y)` | 共線性矩陣（日花費 Pearson r，\|r\|>0.7 列警告）、Poisson 天花板 `1 - mean/var`、資料量檢查 |

**資料量守門（guardrails，不符合即拒絕分析並回明確錯誤）**：
- 天數 ≥ 90（建議 180）
- 日均轉換 ≥ 5
- 每組總花費占比 ≥ 3%（不足自動併入「其他」組）
- 特徵欄位：各組轉換後花費 + 截距 + 週一至週六 6 個 dummy

### 3.2 data_source.py — 資料抓取

- 复用 `modules/fb_ads/_base.py` 的 `BASE_URL` 與 `get_headers()`（TokenManager 解密，支援 user/team token 與 fallback），不自建 token 邏輯。
- `GET /{account_id}/insights`：`level=campaign`、`time_increment=1`、`fields=campaign_id,campaign_name,spend,impressions,actions,action_values`、`time_range` 最多 180 天、`limit=500` + 分頁。
- 寫入 `contribution_daily_metrics`（upsert）；增量抓取：已有資料的日期區間只補缺口與最近 3 天（歸因回補窗口）。
- httpx 非同步、逐頁 sleep 300ms 避免 rate limit（沿用 fb_ads 現行風格）。

### 3.3 grouping.py — 自動分組規則

初版規則（來自真實驗證的分組經驗，使用者可在前端改）：
1. 按活動名稱關鍵詞聚類（`常態`/`檔期`/`測試`/`導流`/`曝光` 等 token + 相同前綴）。
2. 花費占比 < 3% 的活動自動併入 `G_other`。
3. 目標組數 5–8 組；無法規則分組時退回「花費 Top 6 + 其他」。
4. 產出存入 `contribution_campaign_groups`（`source=auto`），使用者調整後 `source=manual`，後續分析優先用 manual。

### 3.4 service.py + 背景任務

- `create_analysis(account_id, params, user)`：guardrail 預檢 → 建 `ContributionSnapshot(status=queued)` → `core/scheduler.add_contribution_analysis_job(snapshot_id)`。
- `core/scheduler.py` 新增 `add_contribution_analysis_job()` 與 `process_contribution_analysis()`（同 `add_meta_andromeda_score_job` 模式：date-trigger 一次性 job、失敗寫回 snapshot.status=failed + error_message）。分析耗時估 10–60 秒（800 trials × 5 restarts，numpy 向量化），不需 Redis 佇列，APScheduler 即可；scheduler 不可用時走 local async fallback（沿用 Andromeda 的 host 判斷模式，簡化為兩層）。
- 完成後寫 `results` + `diagnostics`，`status=completed`。

### 3.5 API 端點（前綴 `/api/contribution`，全部掛 `require_module("contribution")`）

| 方法 | 路徑 | 說明 |
|---|---|---|
| GET | `/campaigns` | 列出帳戶近 N 天活動（含花費/轉換彙總），供分組 UI |
| GET | `/groups?account_id=` | 讀取分組（無則觸發自動分組並回傳） |
| PUT | `/groups` | 覆寫分組（前端編輯後整批提交） |
| POST | `/analyses` | 發起分析（body：account_id、date range、metric_key、n_restarts）→ 202 + snapshot_id |
| GET | `/analyses?account_id=` | 分析列表（分頁） |
| GET | `/analyses/{snapshot_id}` | 單筆結果（含 results/diagnostics；processing 時前端輪詢） |
| POST | `/data/refresh` | 手動觸發每日資料補抓（背景執行） |

### 3.6 模組註冊

- `seeds/permission_seeds.py`：新增 `{"key": "contribution", "name": "貢獻分析", "icon": "📊", "sort_order": 5, "enabled": True}`。
- `main.py`：`app.include_router(contribution_router, prefix="/api/contribution", tags=["contribution"])`。
- `requirements.txt`：新增 `numpy>=2.0,<3.0`（可行性驗證已確認 2.5.1 於 Python 3.12 可用）。

---

## 四、前端設計

### 4.1 頁面與路由

- `pages/ContributionAnalysis.jsx`，路由 `/contribution`（App.jsx lazy import + ProtectedRoute）。
- `Sidebar.jsx`：新增 `requiredModule: 'contribution'` 的選單項「貢獻分析」。
- `services/contributionService.js`：包裝 3.5 的端點（沿用 `apiClient.js`）。

### 4.2 頁面區塊（單頁、由上而下）

| 區塊 | 內容 |
|---|---|
| 帳戶與期間選擇 | 复用 `AdAccountSelector`；期間預設近 180 天；「開始分析」按鈕（POST /analyses 後輪詢） |
| 資料量檢查卡 | guardrail 預檢結果：天數/日均轉換/組數，不足時顯示原因並禁用分析 |
| 貢獻對比圖（主圖） | 各組三聯橫條：花費占比 vs 自報占比 vs MMM 貢獻（誤差線 = min–max 範圍） |
| 邊際報酬排序 | 各組「每 +100 元的邊際轉換」由高至低，直接回答加碼順位 |
| 診斷警告卡 | 共線性配對清單（附「錯開預算調整」建議）、holdout R² 與雜訊天花板、被判 0% 且高共線的組標記「存疑」 |
| 分組編輯器 | 活動清單拖拉/勾選改組，PUT /groups 後可重跑分析 |
| 歷史快照 | 過往分析列表，點開可比較兩次結果 |

圖表用 Recharts（專案既有依賴）；實作前先載入 `dataviz` skill 校準用色與標軸規範。**呈現原則**：貢獻永遠帶區間；被 guardrail 標「存疑」的組灰階顯示 + tooltip 說明原因，不得以確定語氣呈現單點。

---

## 五、波次拆解

### 第 1 波：後端核心（完成並驗收後才進第 2 波）

#### 任務 1.1 — 資料表與模組骨架

**變更檔案**：`database/models/contribution.py`（新增）、`database/models/__init__.py`、`alembic/versions/20260706_contribution_module_tables.py`（新增）、`modules/contribution/{__init__,router,dependencies,schemas,repository}.py`（新增）、`seeds/permission_seeds.py`、`main.py`

**實作步驟**：建 3 張表 migration → 模組骨架與空端點（回 501）→ 權限 seed 與 router 掛載。

**驗收標準**：migration 在本地 SQLite 與 PostgreSQL 皆可升降級；`/api/contribution/*` 未授權回 403、授權後回 501；管理後台可見「貢獻分析」模組並可指派權限。

**風險/回滾**：純新增，降級 migration 即可移除；不觸碰既有表。

#### 任務 1.2 — MMM 引擎移植 + 單元測試（本計劃核心）

**變更檔案**：`modules/contribution/engine.py`（新增）、`tests/test_contribution_engine.py`（新增）、`requirements.txt`

**實作步驟**：
1. 將可行性驗證腳本的 `adstock/hill/nonneg_ridge/fit` 移植為 3.1 規格的純函數，參數全部走 config dict（不散落常數）。
2. 把合成資料產生器一併移植為測試 fixture（**已知真實貢獻的合成資料就是引擎的迴歸測試**）。
3. 測試斷言（依可行性驗證實測數字放寬）：5 seeds 平均貢獻 MAE < 8%；收割組（真實 9%、自報 41%）的 MMM 估計 < 20%；重啟間中位數貢獻極差 < 15pp；guardrail 各拒絕條件觸發正確。
4. `diagnose()` 共線性/天花板計算的獨立測試。

**驗收標準**：`pytest tests/test_contribution_engine.py` 全綠；引擎無任何 I/O 與全域狀態；單次 `run_analysis`（180 天 × 7 組 × 800 trials × 5 restarts）本機 < 90 秒。

**風險/回滾**：純新增。效能不達標時降 trials 至 400（可行性驗證顯示 400 已收斂）。

#### 任務 1.3 — 資料抓取與快取

**變更檔案**：`modules/contribution/data_source.py`（新增）、`repository.py`（upsert）、`router.py`（`/data/refresh`、`/campaigns`）

**實作步驟**：按 3.2 實作抓取與增量補抓；`/campaigns` 由快取表彙總。

**驗收標準**：對測試帳戶抓 180 天資料落庫，重跑不產生重複列（唯一約束生效）；token 缺失/過期回 4xx 與明確錯誤訊息（沿用 fb_ads 錯誤處理慣例），不落任何明文 token。

**風險/回滾**：讀取型操作，對 FB API 的量約為 fb_ads 現行日常查詢的一次性 2 頁請求，rate limit 風險低；失敗僅影響本模組。

#### 任務 1.4 — 分組、分析編排與背景任務

**變更檔案**：`modules/contribution/{grouping,service}.py`（新增）、`router.py`（其餘端點）、`core/scheduler.py`

**實作步驟**：按 3.3/3.4 實作；scheduler 新增 job 函數（比照 `add_meta_andromeda_calibration_job` 的錯誤處理與 log 風格）。

**驗收標準**：對真實測試帳戶端到端跑通：自動分組 → POST /analyses → 輪詢至 completed → results 數字與可行性驗證腳本同輸入下一致（誤差 < 1pp，允許隨機搜尋 seed 差異）；scheduler 停用時 local fallback 可完成分析；分析失敗時 snapshot 可見 error_message。

**風險/回滾**：scheduler 僅新增 job 類型；出錯不影響 Andromeda 與週報既有 job。

### 第 2 波：前端

#### 任務 2.1 — 頁面與服務層
按第四章實作頁面全部區塊。**驗收**：權限開啟的使用者可完整走完「選帳戶 → 檢查 → 分析 → 看結果 → 改分組 → 重跑」；無權限者選單不可見、直連被擋；區間與「存疑」標記正確呈現。

#### 任務 2.2 — 視覺化細節
載入 `dataviz` skill 後實作三聯對比圖與邊際排序圖；深淺色主題皆可讀。**驗收**：以真實快照截圖走查。

### 第 3 波：自動化與整合（選配，依使用回饋決定）

| 任務 | 內容 | 驗收 |
|---|---|---|
| 3.1 週期自動更新 | CronTrigger 每週一自動補抓資料 + 重跑分析（比照 `add_meta_andromeda_weekly_closed_loop_job`） | 週一自動產生新快照，失敗有 log 與 status |
| 3.2 快照對比 | 前端兩快照差異視圖（貢獻變化趨勢） | 可視覺對比任兩次快照 |
| 3.3 Andromeda 資料整合 | 將 MMM 組別貢獻係數提供給 Andromeda 校準層作為 `performance_snapshot` 的去偏參考（單向：Contribution → Andromeda；介面為讀 snapshot 表，不互相 import 業務邏輯） | Andromeda 端 PoC 報告：使用去偏轉換數後校準準確率變化 |
| 3.4 y 變數升級 | 支援 GA4/CRM 訂單數作為 y（設定切換） | 同帳戶雙 y 對比報告 |

---

## 六、風險清單

| 風險 | 影響 | 緩解 |
|---|---|---|
| 花費共線（使用者同步調預算） | 組間分解不準、部分組被判 0% | 一級診斷輸出 + 「錯開預算調整」操作建議；被判 0% 且高共線的組強制標「存疑」 |
| 日轉換量低的帳戶 | 雜訊淹沒訊號 | guardrail 拒絕 + 建議改週粒度（週粒度支援列入 backlog，不在本計劃） |
| 隨機搜尋的不確定性 | 兩次分析數字不同引發困惑 | 固定 seed 集合（config 記錄）；同輸入同 config 結果可重現 |
| 使用者把區間當精確值做預算決策 | 錯誤決策歸咎系統 | UI 呈現原則（第四章）+ 頁面常駐方法說明連結 |
| FB API 欄位/版本變動 | 抓取失敗 | 沿用 fb_ads 的版本常數（v24.0）與錯誤處理；actions 缺欄位時記 warning 不 crash |
| numpy 新依賴 | 部署映像變大（約 +60MB） | 可接受；Dockerfile 無需變更（pip 安裝自 requirements.txt） |

---

## 七、明確不做（Non-goals）

1. **六模型路徑歸因**：無使用者層級路徑資料，不做（未來若接 GA4 BigQuery Export 另立計劃）。
2. **單一活動的精確點估計**：資料不支持，永遠以組別 + 區間呈現。
3. **即時分析**：本質是批次統計，最小更新粒度為日。
4. **自動調整預算**：只給建議排序，不寫回 Meta（涉及寫入權限與責任邊界，需另案評估）。
5. **跨渠道 MMM**（Google/LINE 等）：資料表已預留擴充空間（`account_id` 不綁 Meta 格式），但本計劃只做 Meta。

---

**站略 (Site-tegy) 技術架構小組**
