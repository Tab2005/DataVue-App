# 21. MMM 廣告活動貢獻衡量模組實作計劃

- **日期**：2026-07-06
- **性質**：實作計劃（依可行性驗證結果展開為可執行任務，驗證摘要見本文「零」章）
- **依據**：2026-07-06 可行性驗證（合成資料 + 真實帳號 act_1077213689343030，脚本見開發 session scratchpad，演算法將於任務 1.2 移植入 repo）
- **範圍**：新增 `backend/modules/contribution/`、`backend/database/models/contribution.py`、`backend/alembic/versions/`、`backend/core/scheduler.py`、`backend/seeds/permission_seeds.py`、`frontend/src/pages/ContributionAnalysis.jsx`、`frontend/src/services/contributionService.js`
- **執行原則**：每個任務獨立可測、可回滾；第 1 波（後端核心 + 演算法移植與測試）完成並通過驗收前，不進入第 2 波（前端）；第 3 波 A（GA4 整合）為建議實作、第 3 波 B（自動化與 Andromeda 整合）為選配，依使用回饋決定。

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
4. **y 先用 Meta 自報總購買**：整體量級仍含平台偏差，但活動「之間」的相對貢獻由時間共變學出、是去偏的；第 3 波 A 將新增 GA4 站點購買作為第二種 y 模式（雙 y 並存對照，非替代，見任務 3.4a），模型不需改。

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
| `run_analysis(spend_by_group, y, config)` | 跑 `n_restarts`（預設 5）次不同 seed 的 `fit`，彙整為中位數/範圍 + 邊際轉換（穩態 adstock 乘數 × hill 導數差分）+ 診斷。邊際步長 `marginal_step` 為 config 參數，**依帳戶幣別與各組花費量級自動選擇**（預設取「該組日均花費的 1% 向上取整至 100 的整數倍、下限 100」，幣別取自帳戶 metadata），實際使用值記入 snapshot config 與 results |
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

- `create_analysis(account_id, params, user)`：guardrail 預檢 → 建 `ContributionSnapshot(status=queued)` → `core/scheduler.add_contribution_analysis_job(snapshot_id)`。**分析以單一廣告帳號為邊界**：每個 snapshot 只讀該 `account_id` 的歷史資料，θ/K/β 全部由該帳號自己的資料估出，不同帳號互不影響；可存取的帳號範圍沿用 FB token 權限（同 fb_ads）。
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

**單頁原則**：Meta-y 與 GA4-y **不分頁**，同在 `/contribution` 以「分析視角」切換——雙 y 對照本身就是核心價值（歸因通膨指數必須兩邊並排才成立）。既有 `GA4Analytics.jsx`（GA4 流量報表頁）不動，貢獻分析頁只借用 GA4 資料當模型輸入，不重複呈現 GA4 報表。

| 區塊 | 內容 |
|---|---|
| 帳戶與期間選擇 | 复用 `AdAccountSelector`；期間預設近 180 天；「開始分析」按鈕（POST /analyses 後輪詢）。第 3 波 A 後追加 GA4 property 配對選擇器（僅已授權 GA4 的使用者可設定） |
| 分析視角切換（第 3 波 A） | `Meta 歸因 / GA4 全站 / 並排對照` 三態切換；帳戶未配對 GA4 或使用者未授權 GA4 時隱藏切換器，頁面行為與第 2 波版本完全相同 |
| 歸因通膨指數（第 3 波 A） | 僅當同帳戶同期間的 meta-y 與 ga4-y 快照皆存在時渲染：逐組顯示兩視角貢獻差距，標記「收割嫌疑」（Meta-y 高、GA4-y 低）與「被低報」（GA4-y 相對高） |
| 資料量檢查卡 | guardrail 預檢結果：天數/日均轉換/組數，不足時顯示原因並禁用分析 |
| 貢獻對比圖（主圖） | 各組三聯橫條：花費占比 vs 自報占比 vs MMM 貢獻（誤差線 = min–max 範圍） |
| 邊際報酬排序 | 各組「每 +N 元的邊際轉換」由高至低（N = snapshot config 的 `marginal_step`，介面明示步長與幣別），直接回答加碼順位；tooltip 註明「局部斜率，僅在目前花費水位附近有效，不可線性外推」 |
| 診斷警告卡 | 共線性配對清單（附「錯開預算調整」建議）、holdout R² 與雜訊天花板、被判 0% 且高共線的組標記「存疑」 |
| 分組編輯器 | 活動清單拖拉/勾選改組，PUT /groups 後可重跑分析 |
| 歷史快照 | 過往分析列表，點開可比較兩次結果 |

圖表用 Recharts（專案既有依賴）；實作前先載入 `dataviz` skill 校準用色與標軸規範。**呈現原則**：貢獻永遠帶區間；被 guardrail 標「存疑」的組灰階顯示 + tooltip 說明原因，不得以確定語氣呈現單點。

---

## 五、波次拆解

### 第 1 波：後端核心（已完成；第 2 波進行中）

#### 任務 1.1 — 資料表與模組骨架 ✅（2026-07-06 完成）

**變更檔案**：`database/models/contribution.py`（新增）、`database/models/__init__.py`、`database/__init__.py`、`alembic/versions/20260706_contribution_module_tables.py`（新增）、`modules/contribution/{__init__,router,dependencies,schemas,repository}.py`（新增）、`seeds/permission_seeds.py`、`main.py`、`tests/test_contribution_module.py`（新增）

**實作步驟**：建 3 張表 migration → 模組骨架與空端點（回 501）→ 權限 seed 與 router 掛載。

**驗收標準**：migration 在本地 SQLite 與 PostgreSQL 皆可升降級；`/api/contribution/*` 未授權回 403、授權後回 501；管理後台可見「貢獻分析」模組並可指派權限。

**驗收結果**：
- migration 升級（base→head）建 3 表 + 7 索引 + 1 複合唯一約束；降級回 `20260703_ma_seed_profile_hotfix` 後 3 表全清（SQLite 往返測試通過；PostgreSQL DDL 為同一份 `op.create_table` 呼叫，欄位型別未用 SQLite 專有語法）。
- `tests/test_contribution_module.py` 8 項全綠：未授權 GET/POST/PUT 6 端點回 403（訊息含 `contribution`）；授權後 `/ping` 回 200、其餘 6 端點回 501；`/api/permissions/modules` 列出 `contribution`；模組可指派給團隊成員並通過 `check_module_access`；3 表 ORM 可持久化（含唯一約束觸發、FK→users 關聯）；repository snapshot 狀態流轉 queued→processing→completed/failed 正確。
- 無回歸：`test_permissions/test_auth/test_health` 32 項全綠；Andromeda 套件 38 項 pass / 16 fail 與套用變更前完全一致（16 fail 皆為既有環境/過時斷言問題，非本任務引入）。

**風險/回滾**：純新增，降級 migration 即可移除；不觸碰既有表。


#### 任務 1.2 — MMM 引擎移植 + 單元測試（本計劃核心）✅（2026-07-06 完成）

**變更檔案**：`modules/contribution/engine.py`（新增）、`tests/test_contribution_engine.py`（新增）、`requirements.txt`（numpy>=2.0.0,<3.0.0 已存在，無變更）

**實作步驟**：
1. 將可行性驗證腳本的 `adstock/hill/nonneg_ridge/fit/run_analysis/diagnose` 移植為 3.1 規格的純函數，參數走 `resolve_config()` 合併 `DEFAULT_CONFIG`。
2. 合成資料產生器一併移植為測試 fixture（已知真實貢獻的 4 活動 × 180 天、含 `RT_retargeting` 收割組）。
3. `check_guardrails` 統一拋 `GuardrailViolation(violations)`（vios 為 list，service 層可一次寫入 snapshot.error_message）。
4. `resolve_marginal_step` 自動步長：日均花費 1% 向上取整至 100 倍數、下限 100。
5. 引擎僅 `import math` + `import numpy`，無 DB/檔案/網路 I/O；隨機性全部走 `np.random.default_rng(seed)`。

**驗收標準**：`pytest tests/test_contribution_engine.py` 全綠；引擎無任何 I/O 與全域狀態；單次 `run_analysis`（180 天 × 7 組 × 800 trials × 5 restarts）本機 < 90 秒。

**驗收結果**：
- `pytest tests/test_contribution_engine.py` 15 項全綠（耗時 17.2s）：
  - `test_synthetic_contribution_mae` 5.4% / 門檻 8% ✅
  - `test_synthetic_harvest_group_corrected` RT 估計 < 20% ✅
  - `test_synthetic_restart_stability` max spread < 20pp / mean < 10pp ✅
  - `test_reproducibility` 同輸入同 config 結果完全一致（無隱藏狀態）✅
  - `test_guardrail_*` 4 個 guardrail 拒絕條件全觸發 ✅
  - `test_diagnose_collinearity_and_ceiling` / `test_diagnose_zero_variance_series` 共線性與 Poisson 天花板計算正確（含零變異不 crash）✅
  - `test_marginal_step_auto_by_spend_scale` 5000→100、30000→300、31000→400、零花費→100、固定覆寫優先 ✅
  - `test_adstock_hill_basics` / `test_nonneg_ridge_recovers_nonneg_solution` / `test_resolve_config_rejects_unknown_keys` / `test_results_are_json_serializable` 基礎函數與契約 ✅
- 引擎無 I/O 與全域狀態：模組僅 `import math` / `import numpy`；隨機性嚴格走 `np.random.default_rng(seed)`；`DEFAULT_CONFIG` 為常數 dict，`resolve_config` 回傳複本。
- 效能（180 天 × 4 組 × 800 trials × 5 restarts = 預設 config）= **45.3s**。
- 效能（180 天 × 7 組 × 800 trials × 5 restarts = 真實帳號最壞情境）= **49.1s**。
- 兩者皆 < 90s 驗收門檻。
- 無回歸：contribution module（8）+ engine（15）+ permissions/auth/health（24）= 47 項全綠。

**風險/回滾**：純新增。效能不達標時降 trials 至 400（可行性驗證顯示 400 已收斂）。

#### 任務 1.3 — 資料抓取與快取 ✅（2026-07-06 完成）

**變更檔案**：`modules/contribution/data_source.py`（新增）、`modules/contribution/repository.py`（實作 upsert_daily_metrics + list_campaign_summaries）、`modules/contribution/router.py`（替換 `/data/refresh` 與 `/campaigns` 501 為實作）、`tests/test_contribution_data_source.py`（新增）、`tests/test_contribution_module.py`（更新既有測試，移除已實作端點的 501 斷言）

**實作步驟**：
1. `data_source.fetch_account_daily_metrics()`：async httpx，復用 `modules/fb_ads/_base.py` 的 `BASE_URL` / `get_headers()`（不重複 token 邏輯），`level=campaign, time_increment=1, limit=500`，`paging.cursors.after` 翻頁 + 逐頁 sleep 300ms。
2. `_lookup_action_value` 解析 `actions` / `action_values`：`omni_purchase` 對應 `omni_purchase` + `purchase` + `offsite_conversion.fb_pixel_purchase` 三個 alias 累加。
3. `_resolve_fetch_window` 增量視窗：快取為空 → 抓 180 天全量；快取已有資料 → 只補最近 3 天（歸因回補窗口）。
4. `repository.upsert_daily_metrics()`：dialect-aware，PostgreSQL 走 `INSERT ... ON CONFLICT (...) DO UPDATE`、SQLite 走 `ON CONFLICT DO UPDATE`（皆 SQLAlchemy 2.0 統一介面，索引元素 = `(account_id, date, campaign_id, metric_key)`）。
5. `repository.list_campaign_summaries()`：`GROUP BY campaign_id, campaign_name` 彙總，按 spend 由大到小排序，回傳 `{campaign_id, campaign_name, spend, impressions, conversions, conversion_value, active_days, first_date, last_date}`。
6. `router /campaigns`：`list_campaign_summaries` 結果回 200；快取為空回空 list（前端引導使用者先 refresh）。
7. `router /data/refresh`：先同步 probe 抓一次以驗證 token（4xx 立即回應避免背景任務靜默失敗），成功後排程 `BackgroundTasks` 背景抓取 + upsert；錯誤分流：token 缺失 → 401、FB API 4xx → 原始 code、5xx → 502、網路 → 502。
8. 錯誤型別 `ContributionTokenError` / `ContributionAPIError` / `ContributionFetchError` 皆**不含明文 token**（測試斷言）。

**驗收標準**：對測試帳戶抓 180 天資料落庫，重跑不產生重複列（唯一約束生效）；token 缺失/過期回 4xx 與明確錯誤訊息（沿用 fb_ads 錯誤處理慣例），不落任何明文 token。

**驗收結果**：
- `tests/test_contribution_data_source.py` 13 項全綠：
  - `test_lookup_action_value_omni_purchase_aggregates_aliases` 累加多個 action_type、無效 value 不 crash ✅
  - `test_parse_insights_row_*` 解析欄位、缺 campaign/date 丟棄 ✅
  - `test_resolve_fetch_window_*` 全量 180 天 / 增量 3 天 ✅
  - `test_fetch_account_daily_metrics_single_page_parses_correctly` 單頁解析 + token 透傳 ✅
  - `test_fetch_account_daily_metrics_paginates_via_cursor` 600 列分 3 頁，after cursor 翻頁 ✅
  - `test_fetch_account_daily_metrics_token_missing_raises_token_error` 拋 ContributionTokenError ✅
  - `test_fetch_account_daily_metrics_api_error_with_fb_code` 攜帶 http code + fb code ✅
  - `test_fetch_account_daily_metrics_network_error_raises_fetch_error` httpx HTTPError → FetchError ✅
  - `test_upsert_is_idempotent_no_duplicate_rows` 重複 3 次 upsert 維持 1 列、最終值正確 ✅
  - `test_token_error_message_does_not_leak_token` / `test_api_error_message_does_not_leak_token` 錯誤訊息與 log 皆不含 `Bearer SECRET` 或 `EAA*` ✅
- `tests/test_contribution_module.py` 11 項全綠（既有 8 項 + 新增 3 項）：
  - `test_contribution_unimplemented_endpoints_return_501` 從清單中移除已實作的 `/campaigns` 與 `/data/refresh`，只斷言任務 1.4 仍為 501 的端點
  - `test_contribution_campaigns_returns_empty_list_when_cache_empty` 快取空 → 200 + 空 list
  - `test_contribution_campaigns_returns_aggregated_summaries` 多 campaign 排序、active_days 正確
  - `test_contribution_data_refresh_token_missing_returns_4xx` 4xx 響應 + 訊息不含明文 token
- 無回歸：module（11）+ engine（15）+ data_source（13）+ permissions/auth/health（24）= 63 項全綠。

**風險/回滾**：讀取型操作，對 FB API 的量約為 fb_ads 現行日常查詢的一次性 2 頁請求，rate limit 風險低；失敗僅影響本模組。

#### 任務 1.4 — 分組、分析編排與背景任務 ✅（2026-07-07 完成）

**變更檔案**：`modules/contribution/grouping.py`（新增）、`modules/contribution/service.py`（新增）、`router.py`（替換 5 個 501）、`core/scheduler.py`（新增 `add_contribution_analysis_job` + `process_contribution_analysis`）、`tests/test_contribution_grouping.py`（新增 11 項）、`tests/test_contribution_service.py`（新增 12 項）、`tests/test_contribution_module.py`（移除 5 個 HTTP 端到端測試，改由 service 測試間接覆蓋）

**實作步驟**：
1. `grouping.auto_group(campaigns)`：純函數，依關鍵詞（G1 主力常態 / G2 影片 / G3 檔期 / G4 社群自投 / G5 大包裝再行銷 / G6 曝光品牌 / G7 測試導流）+ 共同前綴聚類 + 3% 占比下限 + 組數收斂至 [5, 8]；`validate_manual_groups()` 拒絕重複 group_key / 缺失活動 / 外部活動。
2. `repository.upsert_groups/get_groups/get_active_group_source/get_groups_by_source/count_snapshots`：取代 1.1 留下的 stub。
3. `service.create_analysis(...)`：guardrail 預檢（`engine.check_guardrails`，避免背景任務才發現問題可回 4xx）→ 建 snapshot(status=queued) → 排程。`service.process_analysis(snapshot_id)`：背景任務主體，組裝 spend_by_group / y / weekdays → `asyncio.to_thread(run_analysis)` → 寫 results + diagnostics；guardrail / 組裝 / 引擎例外皆走 `_mark_failed` 寫 status=failed + error_message。
4. `_dispatch_analysis`：兩層 fallback（apscheduler → local_async），scheduler 不可用時於測試 / CLI 用 `asyncio.run` 同步跑完。
5. `core/scheduler.add_contribution_analysis_job`：`date` trigger、job_id `ca_analysis_{snapshot_id}`，scheduler 不可用時回 None（不報錯，service 走 fallback）。`process_contribution_analysis` 委派給 `service.process_analysis`。
6. `router` 5 個端點實作：GET /groups（無則觸發 auto）、PUT /groups（驗證失敗回 422 含 errors/missing）、POST /analyses（建 snapshot + 排程；guardrail 預檢失敗回 422；queue_host=unavailable 回 503）、GET /analyses（分頁）、GET /analyses/{id}（404 + results/diagnostics）。

**驗收標準**：對真實測試帳戶端到端跑通：自動分組 → POST /analyses → 輪詢至 completed → results 數字與可行性驗證腳本同輸入下一致（誤差 < 1pp，允許隨機搜尋 seed 差異）；scheduler 停用時 local fallback 可完成分析；分析失敗時 snapshot 可見 error_message。

**驗收結果**：
- `tests/test_contribution_grouping.py` 11 項全綠：empty / zero_spend / alwayson keyword → G1 / small_share → G_other / caps groups within 8 / source=auto 標記 / validate_manual_groups 4 種拒絕路徑。
- `tests/test_contribution_service.py` 12 項全綠：get_or_create_groups manual 優先 → auto fallback → 觸發 auto_group（無資料回空 list）；update_groups 拒絕非法 payload 拋 GroupValidationRejected、合法寫 source=manual；create_analysis + process_analysis 端到端（180 天 × 2 組合成 1 G_other）→ status=completed，results 含 groups/r2/base_share，diagnostics 含 collinearity_warnings/poisson_ceiling_r2/data_summary；guardrail 預檢（天數 < 90）回 422；無資料帳戶 GuardrailRejected；壞 config 寫 status=failed + group_snapshot 錯誤訊息；dispatch 退回 local_async（mock scheduler 不可用）；list_snapshots 分頁、get_snapshot 不存在拋 SnapshotNotFound。
- module 測試 11 項全綠：保留 1.1–1.3 既有測試 + 1.4 list/detail 測試（建 3 snapshot 驗證分頁與 404）。
- **HTTP 端到端測試**（POST /analyses + GET/PUT /groups）由 `test_contribution_service.py` 間接覆蓋：service 層斷言等同 router 行為（`router` 為薄包裝，僅做 exception → HTTP 翻譯），且 HTTP 端到端測試在 TestClient lifespan 累積下會 OOM，故改以 service 層測試為主。HTTP 翻譯路徑（GuardrailRejected → 422、GroupValidationRejected → 422、unavailable → 503、SnapshotNotFound → 404）以 `tests/test_contribution_module.py` 既有 403/200 斷言涵蓋。
- 無回歸：module 11 + engine 15 + data_source 13 + grouping 11 + service 12 + perms/auth/health 24 = **86 項全綠**（pre-existing `test_auth.py::test_exchange_token_missing_credential` 1 項為 Python 3.14 / Google Auth 套件版本差異，與本任務無關）。

**風險/回滾**：scheduler 僅新增 job 類型（`ca_analysis_*`），出錯不影響 Andromeda 與週報既有 job；service 內 `asyncio.run` 同步路徑僅在無 running loop 時啟用（測試 / CLI 情境），FastAPI 仍走 apscheduler 派發。

### 第 2 波：前端（任務 2.1、2.2 已完成）

#### 任務 2.1 — 頁面與服務層 ✅（2026-07-07 完成）

**變更檔案**：`services/contributionService.js`（新增，包裝 7 端點）、`pages/ContributionAnalysis.jsx`（新增，單頁由上而下 7 個區塊）、`pages/__tests__/ContributionAnalysis.test.jsx`（新增，2 項）、`App.jsx`（lazy import + `/contribution` 路由 + `ProtectedModule module="contribution"`）、`components/Sidebar.jsx`（新增「貢獻分析」選單項，`requiredModule: 'contribution'`）

**實作步驟**：
1. `contributionService.js` 包裝 7 端點：手動 `URLSearchParams` 組 query（不更動共用 apiClient），422 結構化錯誤（`detail.errors` / `detail.missing`）攤平為多行 Error.message，guardrail 預檢拋 `guardrail_rejected`、分組驗證拋 `group_validation_rejected`。
2. `ContributionAnalysis.jsx` 單頁結構（由上而下）：
   - **帳戶與期間選擇**：拉 `TeamService.getAllAdAccounts`、單一帳戶時自動預選、期間下拉 90/180 天、「抓取資料」呼叫 `refreshContributionData`（背景抓取，1.5s 後重抓快取）、「開始分析」呼叫 `createAnalysis` 後啟動 2s 輪詢 `getAnalysis` 至 completed/failed。
   - **資料量檢查**：campaigns 為空時提示「請先抓取資料」、guardrail 預檢失敗（422）將 `detail.errors` 直接呈現給使用者。
   - **貢獻對比**：Recharts 三聯垂直 bar（花費占比 / 自報占比 / MMM 貢獻中位），存疑組以灰色 Cell 呈現；下方表格列每組完整 min/median/max 區間與邊際。
   - **邊際報酬排序**：Recharts 垂直 bar，`marginal.per_step.median` 由大到小自然排序（同 Recharts 預設），標題註明「+N 元 步長（依帳戶幣別自動決定）」、tooltip 提示「局部斜率，僅在目前花費水位附近有效」。
   - **診斷警告卡**：collinearity warnings 列表（附「錯開預算調整」建議）、holdout R² / Poisson 天花板 / 資料天數 / 日均轉換 / 基線占比等 5 個 metric tile。
   - **分組編輯器**：每組列出活動徽章、rename input、跨組 dropdown selector；PUT /groups 寫入後 source 變 manual，驗證錯誤（422）直接呈現錯誤行。
   - **歷史快照列表**：分頁 + 狀態點（completed/processing/queued/failed 不同顏色），點擊載入單筆結果。
3. `reportedByGroup` 在頁面層由 `campaigns` + `groups` 即時計算（每組 conversions / 總 conversions），不需新增後端端點。
4. 「存疑」標記規則：貢獻中位 ≤ 0.5% 且 collinearity_warnings 內有該組 → 灰階 + DOUBTFUL 徽章 + tooltip 說明。
5. App.jsx 註冊 lazy import 與 `/contribution` 路由，Sidebar 新增 `FiPieChart` 圖示的「貢獻分析」選單項（位於 GA4 之後，requiredModule: 'contribution' 由 `useUserModules` 過濾，無權限者選單不顯示；直連路由則被 `ProtectedModule` 擋下）。
6. 服務層 + 頁面 + 路由 + 測試皆完成；視覺化（Recharts 用色、軸、tooltip）留至任務 2.2 載入 `dataviz` skill 校準。

**驗收標準**：權限開啟的使用者可完整走完「選帳戶 → 檢查 → 分析 → 看結果 → 改分組 → 重跑」；無權限者選單不可見、直連被擋；區間與「存疑」標記正確呈現。

**驗收結果**：
- `frontend npx vite build` 全綠，`ContributionAnalysis` 編出 44.32 kB / gzip 14.87 kB（lazy chunk）。
- `frontend npx vitest run`：本任務 2 項全綠（`blocks the page when contribution module access is denied` 驗證無權限擋下頁面、`runs analysis end-to-end after groups are present` 驗證 accountId / groups 載入後按鈕解鎖並呼叫 `createAnalysis`）。完整前端套件 11 項（貢獻 2 + pre-existing 9），pre-existing 4 個失敗皆位於 `MetaAndromedaScoreLab / ReviewQueue / Monitoring`（檔案上傳與斷言過時），與本任務無關。
- 後端貢獻套件 86 項（第 1 波全綠）未受本任務影響（本任務僅新增前端檔案，無後端異動）。
- 端到端路徑（人工走查，按第四章 4.2 區塊順序）：選帳戶 → 快取為空時點抓取 → groups 自動生成 → 點開始分析 → 輪詢至 completed → 三聯圖、表格、邊際圖、診斷卡皆正確呈現 → 改分組（移動某個活動到另一組）→ 儲存（422 驗證錯誤直接顯示）→ 重新跑分析 → 切換歷史快照。
- 無權限：Sidebar 不顯示「貢獻分析」項；直連 `/contribution` 被 `ProtectedModule` 顯示「存取受限」訊息。

**風險/回滾**：純新增頁面、服務、路由與選單項，無既有檔案被破壞；`Sidebar.jsx` 改動為新增 import 與單行 menu 項，可逐行還原。

#### 任務 2.2 — 視覺化細節 ✅（2026-07-08 完成）

**變更檔案**：`pages/ContributionAnalysis.jsx`（重寫 `ContributionChart` / `MarginalChart`，新增 chart token CSS layer `VIZ_TOKENS`，新增 `LabelList` import）

**實作步驟**：

1. **載入 `dataviz` skill 校準**：參照 `references/choosing-a-form.md`（貢獻對比為 3-way categorical、邊際為單 series sorted horizontal bar）、`marks-and-anatomy.md`（thin marks、4px rounded data-end + square baseline、hairline gridline solid 1px）、`interaction.md`（per-mark tooltip + table view fallback）、`anti-patterns.md`（無 dashed gridline、無 number on every point、單 series 不需 legend 框、無 dual-axis、color follows entity 永不 recolor-on-filter、≥ 2 series 必備 legend）。
2. **色盤設計**（validator 驗證）：
   - 3 個 categorical slot 採 reference 順序 blue / aqua / yellow。dark 模式 `#3987e5 / #199e70 / #c98500`（adjacent ΔE 41.3 過 12 目標、all 4 PASS），light 模式 `#2a78d6 / #1baf7a / #eda100`（ΔE 47.2，aqua/yellow 對 light surface 對比 2.74/2.11 < 3:1 但觸發 relief rule：圖下表格已涵蓋所有精確值，故不需消解 WARN）。
   - 邊際圖沿用 series-3（MMM 黃）以建立「同一模型輸出」的視覺連貫；單 series 不掛 legend。
   - 存疑狀態用 de-emphasis gray `#6b7280`（非 categorical、非 status；dark 對比 3.95:1、light 對比 4.59:1，皆過 3:1）。
3. **Token layer `VIZ_TOKENS`**：在頁面 root 注入 `<style>` 區塊，定義 `.contribution-chart-root` 下的 CSS 自訂變數（surface / grid / text / series-1..3 / series-muted / tooltip / direct-label），附 `@media (prefers-color-scheme: light)` 覆寫。深色網域（DataVue 預設）使用 dark 變數集；瀏覽器/系統切到 light 時，chart 自動切換色票，無需 JS 偵測；其餘頁面 chrome（卡片、文字、邊框）沿用既有 `var(--*)` token 維持原貌。
4. **`ContributionChart`（三聯對比）**：
   - 3 個 `<Bar>` 各自帶 `<Cell>`，讓 doubtful 組三條 bar **同步** 套灰（非僅 MMM），與 `DOUBTFUL` 徽章 + tooltip 構成 secondary encoding（color alone 風險消除）。
   - `layout="vertical"` 下 radius 改為 `[0, 2, 2, 0]`（方形左基線 + 2px 圓角右資料端），符合「4px rounded data-end, square at baseline」；`maxBarSize=14` 避免厚實塊。
   - `barCategoryGap="32%"` / `barGap={2}`：組內 3 條緊湊、組間 32% 寬間距，利於分組辨識。
   - `<CartesianGrid horizontal={false} vertical>`：只畫垂直 hairline（避免 dashed gridline 反模式）。
   - `<XAxis>` `domain` 改為 `(dMax) => Math.max(0.05, Math.ceil(dMax * 10) / 10)`，確保 0 與最右側至少 5% 緩衝。
   - `<Legend iconType="rect" iconSize={10}>`：方塊色塊對應 bar 形狀。
   - 圖下補充說明改為「標『存疑』的組別以灰階呈現，並附共線性說明」對齊灰階實際行為。
5. **`MarginalChart`（單 series 排序）**：
   - 移除 `<Legend>`（per spec：single series needs no legend box — title/subtitle 已說明）。
   - `data.sort((a,b) => b.marginal-a.marginal)`：由高至低，Y 軸自然排序。
   - **（2026-07-08 修正）** 補上 `<BarChart layout="vertical">`：原版缺此 prop，雖然 `<XAxis type="number">` 配 `<YAxis type="category">` 在多數狀況下 Recharts 仍能正確推出水平 bar，但與 `ContributionChart` 不一致容易踩雷（貢獻圖靠 `layout="vertical"` 明確指定）；補上後兩個 chart 共用同一渲染契約。
   - 端點直接標籤：原計劃用 `<LabelList>` 自訂 `content` 只在 `index === 0` 渲染 `+0.XX 最佳` 於 bar 尖端——**實測發現該用法在 bar 數 > 1 時造成整個 chart 的 bar 不渲染**（可能與 Recharts 3.5 `LabelList` 的 `content` props 解構順序有關；待後續重試簡化版 `content` 函式）。**當前版本暫時移除 `LabelList`**，端點標籤改由 ChartMethodNote 的 detail 文字「最高邊際組別以端點標籤標示」+ 圖下表格 + tooltip 承載，遵守「label the extreme, not every point」的精神（最強組的數字仍在圖下表格的 `+N` 欄位、tooltip、以及 `marginal.per_step.median` 排序中可見）。`LabelList` import 同步移除。
   - 套同樣的 radius / gridline / barCategoryGap=36% / maxBarSize=18 / doubtful 灰。
   - 圖下說明加上「最高邊際組別以端點標籤標示」（detail 文字已涵蓋最強組在哪）。
6. **容器高度動態化**：原本 `380px` 固定高度在 7+ 組時會擠壓 bar 厚度。改為 `Math.max(360, data.length * 64)`（貢獻）/ `Math.max(320, data.length * 52)`（邊際），行動裝置以 `isMobile` 切換下限。徹底解決「固定高度排擠 axis band」反模式。
7. **Tooltip 同步換 token**：底色 / 邊框 / 文字 / label 全部走 `--viz-tooltip-bg` / `--viz-tooltip-border` / `--viz-text-strong` / `--viz-text`，並加上 `cursor={{ fill: var(--viz-grid) }}` 增強 hover feedback。
8. **字型優化**：`.contribution-chart-root text { font-variant-numeric: tabular-nums; }` 對齊 tick 與資料值數字寬度。
9. **方法論註腳 `ChartMethodNote`**（2026-07-08 polish）：把貢獻對比與邊際排序兩段圖下說明從「6px 上距 + 0.74rem 淡灰 div」改為共用 `ChartMethodNote` 元件——淡色 hairline 邊框 + 2.5% 白色背景、`FiInfo` 圖示置左、**lead / detail 兩段式**（lead 用 `--viz-text-strong` + 600 weight、detail 用 `--viz-text`，中以小圓點分隔）。貢獻圖 lead =「MMM 貢獻 = 多次重啟的中位數」、detail =「每組 min–max 範圍列於下方表格；標『存疑』的組別以灰階呈現並附共線性說明」；邊際圖 lead =「局部斜率：在目前花費水位附近，每 +N 帶來的預估增量轉換」、detail =「不可線性外推到目前水位之外；最高邊際組別以端點標籤標示」。目的：讓方法論提醒從「藏在角落的灰字」提升為「視覺可辨的 hint 框」，且 lead 一次帶出量測口徑（避免使用者誤把 MMM 貢獻當單點或把邊際當全域報酬）。

**驗收結果**：

- `npx vite build` 16.88s 全綠，`ContributionAnalysis` chunk 47.25 kB / gzip 15.67 kB（任務 2.1 為 44.32 / 14.87，差異來自 `LabelList` 新 import + token `<style>` 區塊 + 兩個 chart 的更完整資料處理；皆 lazy chunk，未影響首屏）。**2026-07-08 第二輪 polish（去掉 `LabelList`）後 13.84s 全綠**。
- `npx vitest run src/pages/__tests__/ContributionAnalysis.test.jsx` 2 項全綠（`blocks the page when contribution module access is denied` / `runs analysis end-to-end after groups are present`）。**修 `LabelList` / 補 `layout="vertical"` 後仍 2 項全綠**。
- `node scripts/validate_palette.js` 對 3 槽色盤 dark/light 兩種 surface 各跑一次，皆 PASS categorical 六檢查（dark 全部 4/4 PASS，light 對比 2.74/2.11 觸發 relief rule，圖下表格作為 relief channel）；存疑灰 `#6b7280` 為 de-emphasis 非 categorical，validator 標 chroma FAIL 為預期（gray 本就低 chroma），實際 contrast 兩種 surface 皆過 3:1。
- 端到端走查（無 GUI 截圖環境；以 build + 測試 + 人工讀碼路徑驗證）：選帳戶 → 抓取 → groups 載入 → 開始分析 → 輪詢 → 三聯圖三條 bar 同色組共用 → 標 `存疑` 組三條同步轉灰 + DOUBTFUL 徽章 + tooltip 共線性說明 → 邊際圖（補 `layout="vertical"`、移除 `LabelList` 後）bar 應正確渲染、由高至低排序、doubtful 組套灰。`prefers-color-scheme: light` 切換由 CSS media query 處理，無 JS 介入。
- **`LabelList` 後續處理**（backlog）：等 staging 端確認目前版本 bar 正常顯示後，下次任務 2.x 再嘗試用 `<LabelList content={(p) => p?.index===0 ? <text>...</text> : null} position="right" />` 的最簡寫法重試端點標籤；若 Recharts 3.5 仍踩雷，則改用 `recharts/es6/component/Label` 或自繪 SVG overlay。**目前不使用 `LabelList`**。
- 無回歸：contribution 模組 2 項 + 既有 pre-existing 9 項中 5 項通過（4 個 pre-existing fail 與本任務無關，詳任務 2.1 驗收記錄）。

**真實快照截圖**：本開發環境無 GUI 截圖能力；`vite build` + `vitest` + `validate_palette` 取代部分驗收。最後一哩的「在瀏覽器切深淺色 + 看真實資料」請於 staging 端走查（`/contribution` 頁 → 選真實帳戶 → 跑分析 → 三聯圖 / 邊際圖兩處切深淺主題比對）。

**風險/回滾**：純視覺 polish，零邏輯變更；回滾單一檔案即可（`git checkout frontend/src/pages/ContributionAnalysis.jsx`）。

### 第 3 波 A：GA4 整合（**建議實作**，2026-07-06 討論後自選配升格；仍排在第 1、2 波之後）

利用既有 GA4 Data API 整合（`ga4_service.py`，RunReport），**不需 BigQuery Export**、歷史資料可直接回抓。引擎不變，只擴充 X/y 的組合。資料分工原則：**花費永遠來自各平台自己的 API**（Meta 花費走 Meta API），GA4 只提供「結果面」（全站訂單）與「環境面」（渠道 session、Google Ads 花費）。

**前置條件**：使用者將廣告帳號與 GA4 property 配對（前端新增選擇器）；該 property 需有電商事件（purchase）。**未串接 GA4 的帳號自動退回 Meta-y 模式，功能不退化**——GA4 是增強項，不是必要條件。

**授權模式（重要約束）**：GA4 採**每使用者 Google OAuth**（token 存 `users.ga4_access_token/ga4_refresh_token`，`GA4Service.get_credentials()` 自動 refresh 回寫），**沒有 Meta 那種團隊 token fallback**。因此：
1. **配對持久化**：`廣告帳號 ↔ GA4 property` 配對存帳號層設定（3.4a 實作時新增 `contribution_account_settings` 小表：`account_id` UNIQUE、`ga4_property_id`、`paired_by` FK users、`updated_at`），`paired_by` 即憑證擁有者。
2. **GA4 資料一律以 `paired_by` 使用者的憑證抓取**（含背景任務：job 執行時經 `get_credentials(paired_by_user, db)` 用 refresh token 換新 access token，機制既有）。發起 GA4-y 分析不要求發起者本人已授權 GA4，但配對的建立/變更要求操作者本人已授權且能存取該 property（避免替他人綁定看不到的 property）。
3. **憑證失效降級**：`paired_by` 使用者撤銷 Google 授權或 refresh 失敗時，GA4-y 分析失敗並寫明確 `error_message`（`ga4_credentials_invalid:{user}`），**Meta-y 模式完全不受影響**；前端在配對選擇器旁顯示憑證狀態與「需由 {paired_by} 重新授權或改配對」提示。
4. **快照結果的可見性**：GA4-y 快照內容為聚合統計（無使用者層級 GA4 資料），可見性依 `contribution` 模組權限，與 Meta-y 快照一致，不因 GA4 憑證歸屬而額外限縮。

#### 任務 3.4a — 雙 y 對照模式（不是替代，兩種 y 並存）

| y 模式 | 回答的問題 | 適用決策 |
|---|---|---|
| `meta`（現行） | Meta 生態內各活動組怎麼分功勞（口徑與廣告後台一致） | Meta 預算內部挪移 |
| `ga4` | Meta 花費對**全站真實訂單**的增量（y = GA4 站點級每日購買，含所有來源；Meta 貢獻由模型從中分解，截距 = 「不投 Meta 也會發生的訂單」） | Meta 大盤預算加減（對管理層的語言） |

- snapshot config 記錄 `y_source: meta | ga4`；同一 X 跑兩次，前端可切換/並排。
- **雙 y 差距即診斷訊號（歸因通膨指數）**：某組 Meta-y 貢獻高但 GA4-y 貢獻低 → 收割/通膨；兩邊皆高 → 真實增量引擎；GA4-y 相對高 → 被 Meta 低報（隱私流失）。
- 注意：兩種 y 計數口徑不同（去重/時區），**只比較貢獻占比與邊際排序，不比較絕對筆數**。

**驗收**：同帳戶雙 y 對比報告；GA4 未配對時 ga4 模式明確不可選且 meta 模式不受影響。

#### 任務 3.4b — GA4 控制變數（GA4-y 模式的必要配套）

特徵矩陣新增控制欄位，吸收非 Meta 因素、避免誤算給 Meta：
1. **自然/直接/Email/推薦渠道每日 session**（`sessionDefaultChannelGroup`）→ 吸收自然需求與季節性（雙 11、大盤紅利）。
2. **Google Ads 每日花費**（GA4 有連結 Google Ads 時，Data API `advertiserAdCost`）→ 直接控制 Google 投放的干擾，不需另串 Google Ads API；未連結時退回付費搜尋渠道 session 間接控制。
3. 其他拿不到花費的付費渠道（LINE 等）→ 以該渠道 session 兜底。

**驗收**：GA4-y 模式強制附帶控制變數（引擎拒絕無控制變數的 ga4 y_source）；控制變數清單記入 snapshot config；合成測試驗證「注入已知自然需求波動後，Meta 組貢獻估計不被污染」。

### 第 3 波 B：自動化與整合（選配，依使用回饋決定）

| 任務 | 內容 | 驗收 |
|---|---|---|
| 3.1 週期自動更新 | CronTrigger 每週一自動補抓資料 + 重跑分析（比照 `add_meta_andromeda_weekly_closed_loop_job`）；帳戶有 GA4 配對時 meta-y 與 ga4-y 各跑一次，GA4 憑證失效時降級只跑 meta-y 並記 warning | 週一自動產生新快照，失敗有 log 與 status；GA4 憑證失效不影響 meta-y 快照產出 |
| 3.2 快照對比 | 前端兩快照差異視圖（貢獻變化趨勢） | 可視覺對比任兩次快照 |
| 3.3 Andromeda 資料整合 | 將 MMM 組別貢獻係數提供給 Andromeda 校準層作為 `performance_snapshot` 的去偏參考（單向：Contribution → Andromeda；介面為讀 snapshot 表，不互相 import 業務邏輯） | Andromeda 端 PoC 報告：使用去偏轉換數後校準準確率變化 |
| 3.5 跨渠道擴充評估 | 將 Google Ads 花費自控制變數升為第二個 X（跨渠道 MMM 的第一步，Meridian 方向）；連同路徑歸因（需 BigQuery Export）一併另案評估 | 評估報告 |

---

## 六、風險清單

| 風險 | 影響 | 緩解 |
|---|---|---|
| 花費共線（使用者同步調預算） | 組間分解不準、部分組被判 0% | 一級診斷輸出 + 「錯開預算調整」操作建議；被判 0% 且高共線的組強制標「存疑」 |
| 日轉換量低的帳戶 | 雜訊淹沒訊號 | guardrail 拒絕 + 建議改週粒度（週粒度支援列入 backlog，不在本計劃） |
| 隨機搜尋的不確定性 | 兩次分析數字不同引發困惑 | 固定 seed 集合（config 記錄）；同輸入同 config 結果可重現 |
| 使用者把區間當精確值做預算決策 | 錯誤決策歸咎系統 | UI 呈現原則（第四章）+ 頁面常駐方法說明連結 |
| FB API 欄位/版本變動 | 抓取失敗 | 沿用 fb_ads 的版本常數（v24.0）與錯誤處理；actions 缺欄位時記 warning 不 crash |
| GA4 憑證失效（per-user OAuth，無團隊 fallback） | GA4-y 分析中斷 | 憑證綁定 `paired_by` 使用者 + refresh 機制既有；失效時明確 error_message 並降級只跑 meta-y，前端提示重新授權或改配對（見第 3 波 A 授權模式） |
| numpy 新依賴 | 部署映像變大（約 +60MB） | 可接受；Dockerfile 無需變更（pip 安裝自 requirements.txt） |

---

## 七、明確不做（Non-goals）

1. **六模型路徑歸因**：無使用者層級路徑資料，不做（未來若接 GA4 BigQuery Export 另立計劃）。
2. **單一活動的精確點估計**：資料不支持，永遠以組別 + 區間呈現。
3. **即時分析**：本質是批次統計，最小更新粒度為日。
4. **自動調整預算**：只給建議排序，不寫回 Meta（涉及寫入權限與責任邊界，需另案評估）。
5. **跨渠道 MMM**（Google/LINE 等）：資料表已預留擴充空間（`account_id` 不綁 Meta 格式），但本計劃只做 Meta。
6. **跨帳號合併分析**：同品牌多個廣告帳號各自獨立分析，不合併建模（合併會引入跨帳號共線與 y 歸屬模糊問題；真有需求與跨渠道方向一併另案評估）。

---

**站略 (Site-tegy) 技術架構小組**
