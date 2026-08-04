# 25. 背景工作負載統一 Worker 架構規劃

- **日期**：2026-07-08
- **性質**：架構規劃（跨模組：Meta Andromeda、MMM 貢獻分析、GA4 即時轉換洞察）
- **狀態**：規劃中（Wave 1 待核准動工）
- **依據**：
  - docs/24（Andromeda 評分管線拆出 worker process，已完成並上線 `meta-andromeda-worker` 服務）
  - 2026-07-08 生產事故：contribution 全量抓取記憶體暴衝至 2GB 拖垮整台 SiteTegy-01，全站 API 逾時（>30000ms）；根因已修（commit `86e4342`：逐頁串流 + 分批 upsert），但 MMM 分析引擎仍跑在 web process 內
  - docs/21（MMM 貢獻分析模組）、docs/22（GA4 即時轉換洞察模組，未動工）

---

## 零、決策摘要

**所有重負載背景工作先共用同一個 worker 服務（現有 `meta-andromeda-worker`），不預先拆分；拆分只在第四節的觸發條件成立時進行。**

一句話架構：

```
web process（backend 服務）   ＝ API + 輕排程（週報）——永遠不跑重活
worker process（共用 worker）＝ 所有重負載背景 job（Andromeda / MMM / GA4）
```

新增背景負載時的預設答案是「掛進共用 worker」，而不是「開新服務」。

---

## 一、現況盤點

### 1.1 機器與服務

SiteTegy-01（Tencent Cloud 首爾，約 2 vCPU / 3.5GB）上跑 5 個服務：

| 服務 | 角色 | 常態記憶體 |
|---|---|---|
| backend | web process（`SERVICE_ROLE=web`） | ~140-200MB（事故時曾 2GB） |
| meta-andromeda-worker | worker process（`SERVICE_ROLE=worker`，同一 image 以 `worker_main.py` 啟動） | ~200MB |
| postgresql / redis / frontend | 資料層與靜態 | ~125MB / 小 / 小 |

扣掉 k3s 系統層（~0.7-1GB），全機可分配餘裕約 1.5-2GB。**任何單一 process 衝到 GB 級就會拖垮整台機器**（2026-07-08 實證：agent、日誌收集、ingress 全部餓死，連 /health 都無回應）。

### 1.2 三類背景負載的型態

| 負載 | 型態 | 尖峰特徵 | 目前跑在哪 |
|---|---|---|---|
| Andromeda 評分/觀測匯入 | LLM I/O 為主 + ffmpeg/讀檔已 to_thread | 等待多、CPU 低 | worker（docs/24 已拆） |
| MMM 分析（contribution） | **CPU 密集**：800 trials × 5 restarts × 4000 迭代，佔一核 1-5 分鐘 | CPU 突發、記憶體 <10MB | **web process（問題所在）** |
| GA4 洞察 job（docs/22 規劃） | 輕 I/O：每小時 API 查詢 + 小 JSON snapshot + MAD 純函數 | 皆輕 | 未動工（本文件指定落點） |
| 週報排程 | 輕：查資料 + 發送 | 皆輕 | web（維持不動） |

三者型態互補（I/O 等待 / CPU 突發 / 輕量週期），共用一個 worker 時互相干擾的機率低——這是「先共用」成立的技術前提。

### 1.3 既有基礎設施（都不用重建）

- `worker_main.py`：worker 進入點（`SERVICE_ROLE=worker`），只掛 `/healthz`，業務都在 scheduler job 裡。
- `core/scheduler.py::_resolve_scheduler_role_flags`：依 `SERVICE_ROLE`（`all`/`web`/`worker`）決定各 process 註冊哪些 job。
- DB-backed queue 模式：`sweep_meta_andromeda_queue()` 掃 `status='queued'` 的列、`scheduler.get_job()` 防重複註冊、殭屍 processing 回收——**MMM 與未來任何佇列型負載直接仿此模式**。
- 部署：web 與 worker 共用同一個 image，差別只在啟動命令與 `SERVICE_ROLE`。

---

## 二、目標架構與分工原則

### 2.1 job 落點總表（本規劃的核心決策）

| Job | 角色歸屬 | 說明 |
|---|---|---|
| Andromeda：stream consumer / reclaim / db sweeper / 週報閉環 | worker | 現狀，不動 |
| **MMM：contribution queue sweeper（新）** | **worker** | Wave 1 實作 |
| **GA4：intraday 刷新 job + 異常偵測 job（docs/22 §3.1）** | **worker** | docs/22 第 1 波動工時直接掛 worker 角色，不先掛 web 再搬 |
| 週報排程（ReportSchedule） | web | 現狀，不動 |
| HTTP 端點的同步 probe（如 /data/refresh 驗 token） | web | 請求範圍內的輕量驗證，本來就該在 web |

GA4 job 掛 worker 的理由：異常偵測的價值恰恰在「web 出事的時候還能發告警」。若掛在 web，web 被拖垮時告警一起死（2026-07-08 就是這種時刻）。

### 2.2 分工鐵律

1. **web process 永遠不執行「分鐘級」以上的工作**：任何預期超過數秒的計算或抓取，一律落 DB 佇列（`status='queued'`）由 worker 撿走，HTTP 回 202 + id 供輪詢。
2. **佇列一律走 DB 表**（snapshot/event 列 + status 欄位），不引入外部佇列系統（見第八節 Non-goals）。
3. **每類佇列必有殭屍回收**：`processing` 超過門檻自動標 `failed`（或重排一次），錯誤訊息可見於前端，不允許永遠轉圈。
4. **記憶體紀律**：背景 job 內禁止把「與資料規模成正比」的集合整份堆在記憶體——逐頁/分批處理是預設寫法（2026-07-08 事故的直接教訓，修法見 commit `86e4342`）。

---

## 三、為什麼「先共用、需要再拆」是對的

1. **資源**：2C/3.5G 的機器塞不下更多常駐 process。每個 FastAPI+SQLAlchemy+numpy process 基礎記憶體 ~150-200MB，再加一個服務等於白吃掉全機 10% 記憶體，換來的隔離在目前負載量下用不到。
2. **負載互補**（見 1.2）：Andromeda 是 I/O 等待、MMM 是短暫 CPU 突發、GA4 是輕量週期——同一 process 內用 asyncio + to_thread 就能並存；MMM 引擎已在 `asyncio.to_thread` 內跑，不會卡 worker 的 event loop。
3. **運維**：一個 worker = 一個部署對象、一份日誌、一個 healthz。拆三個服務的可觀測性成本（誰掛了？哪個要升級？）在單人維運下是純負擔。
4. **拆分成本已預付**：因為 web/worker 共用 image 且 job 註冊由 `SERVICE_ROLE` 分流，未來拆分＝「新增一個 Zeabur 服務 + 一個環境變數」，不需要改業務程式碼（見 4.2）。先共用不會把自己鎖死。

---

## 四、拆分觸發條件與拆分方式

### 4.1 何時拆（任一成立即評估，兩項成立即動手）

| # | 觸發條件 | 觀測方式 |
|---|---|---|
| T1 | worker CPU 持續（非突發）> 70% 超過一週，且 job 有排隊延遲 | Zeabur service metric CPU |
| T2 | MMM 分析從 queued 到開跑的等待常態 > 5 分鐘（被 Andromeda 批次擠壓） | snapshot created_at → processing 時間差 |
| T3 | GA4 告警 job 因 worker 忙碌而錯過整點窗口 ≥ 每週 2 次 | job log 的實際執行時間戳 |
| T4 | worker 記憶體常態 > 800MB（逼近安全上限） | Zeabur service metric MEMORY |
| T5 | 機器升級（如 4C/8G）後仍出現以上任一 | — |

### 4.2 怎麼拆（設計上已鋪好路）

`_resolve_scheduler_role_flags` 泛化為佇列選擇（Wave 2 預留）：worker 增加可選環境變數 `WORKER_QUEUES`（預設 `all`，逗號分隔如 `andromeda,contribution,ga4`）。拆分時：

1. Zeabur 複製一個 worker 服務（同 image、同啟動命令）；
2. 舊 worker 設 `WORKER_QUEUES=andromeda`，新 worker 設 `WORKER_QUEUES=contribution,ga4`（或按瓶頸切）；
3. 不改任何業務程式碼、不改 DB。

---

## 五、實作波次

### Wave 1：MMM 分析移入共用 worker（本規劃的直接行動項）

**變更檔案**：`core/scheduler.py`、`modules/contribution/service.py`、`modules/contribution/router.py`、`tests/test_contribution_service.py`

1. **`core/scheduler.py` 新增 `sweep_contribution_queue()`**（仿 `sweep_meta_andromeda_queue`）：
   - 每 20 秒掃 `ContributionSnapshot` 中 `status='queued'`（`order_by created_at asc`、`limit 10`），對每筆呼叫既有 `add_contribution_analysis_job()`；`scheduler.get_job(job_id)` 防重複。
   - 殭屍回收：`status='processing'` 且超過 30 分鐘（`CONTRIBUTION_STALE_PROCESSING_MINUTES`，預設 30）→ 標 `failed`，`error_message='分析逾時中斷（worker 重啟或超時），請重新發起'`。
   - 註冊位置：`start_scheduler()` 的 `run_meta_andromeda_jobs` 分支（worker 與 dev `all` 跑、web 不跑）。
2. **`service.py::_dispatch_analysis` 角色感知**：
   - `SERVICE_ROLE == 'web'` → 不做任何 in-process 執行，直接回 `('db_queue', 'worker_sweeper')`，snapshot 留在 queued；
   - `SERVICE_ROLE in ('all', 'worker')` → 維持現行（scheduler → local_async fallback），單機開發行為不變。
3. **`router.py`**：202 訊息表加 `'db_queue': '已排入佇列，背景 worker 將於一分鐘內開始分析'`。
4. **測試**（沿用 SessionLocal monkeypatch 模式）：
   - sweeper 撿起 queued snapshot 並完成；
   - processing 超時被標 failed 且 error_message 明確;
   - `SERVICE_ROLE=web` 時 `create_analysis` 不觸發 in-process 執行、回 db_queue；
   - 既有 64 項 contribution 測試零回歸。

**驗收標準**：正式環境發起分析後，backend（web）CPU 無尖峰、worker CPU 出現對應尖峰；分析期間連打 `/api/contribution/campaigns` 等端點回應 < 2s；snapshot 狀態流 queued → processing → completed 可由前端輪詢觀察。

**回滾**：revert 單一 commit；web 端 fallback 邏輯保留，回滾後行為即回到現狀。

### Wave 2：角色旗標泛化 + GA4 落點預留（與 docs/22 第 1 波合併執行）

1. `_resolve_scheduler_role_flags` 的第二旗標由「meta_andromeda jobs」語意改名為「background worker jobs」（純改名 + 註解，行為不變）；預留 `WORKER_QUEUES` 解析（預設 all，本波不啟用分流）。
2. docs/22 的 `ga4_insights_intraday_job` 與 `ga4_insights_daily_job` 實作時直接註冊在 worker 分支——docs/22 §3.1 的排程規格不變，只是落點按本文件 2.1 表。

### Wave 3（選配，低優先）：運維加固

1. Zeabur 上為 backend 與 worker 設定記憶體上限（backend ~1GB、worker ~1.2GB）：爆掉時被 OOM-kill 自行重啟，不再拖垮整台機器——這是 2026-07-08 事故「損害控制」層的防線，與程式碼修復互補。
2. 服務更名 `meta-andromeda-worker` → `datavue-worker`（純識別，反映其已非單一模組專屬；改名不影響部署）。
3. `/healthz` 回應內加各佇列積壓數（queued 計數），供外部監控。

---

## 六、風險清單

| 風險 | 影響 | 緩解 |
|---|---|---|
| MMM CPU 突發擠壓 Andromeda 評分 | 評分延遲數分鐘 | 兩者皆背景任務可容忍；持續發生即觸發 T2 拆分 |
| worker 單點：重啟時所有背景工作暫停 | job 延遲 1-2 分鐘 | DB 佇列不丟資料；sweeper 重啟後自動續跑；殭屍回收兜底 |
| sweeper 與 dev `all` 角色 in-process 執行重複處理 | 同一 snapshot 跑兩次 | `scheduler.get_job()` 防重；processing 狀態互斥（撿起即轉 processing） |
| web 先上、worker 後上的部署窗口 | 分析短暫滯留 queued | 順序無關：snapshot 落庫不丟，worker 上線即撿走 |
| 共用 worker 記憶體逐步墊高 | 逼近機器上限 | Wave 3 記憶體上限 + T4 觸發條件 |

---

## 七、明確不做（Non-goals）

1. **不引入 Celery / RQ / 外部佇列系統**：DB 表 + APScheduler sweeper 已在 Andromeda 驗證夠用；多一套 broker 是多一個故障點與運維對象，目前規模無此需求。
2. **不預先拆多個 worker**：見第三、四節，拆分由觸發條件驅動。
3. **不做自動水平擴充（HPA）**：單機 k3s 上無意義；先垂直（機器升級）後水平。
4. **不動 docs/24 已完成的 Andromeda worker 內部架構**：本規劃只是把更多負載掛進同一模式。

---

**站略 (Site-tegy) 技術架構小組**
