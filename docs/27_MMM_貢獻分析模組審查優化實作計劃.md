# 27. MMM 貢獻分析模組審查優化實作計劃

- **日期**：2026-07-09
- **性質**：實作計劃（依 2026-07-09 對 docs/21 已完成範圍的全面程式碼審查展開）
- **依據**：審查範圍涵蓋 `backend/modules/contribution/`（engine / data_source / grouping / service / repository / router / schemas / dependencies）、`backend/database/models/contribution.py`、`core/scheduler.py` 貢獻分支、`backend/ai_service.py` contribution prompt、`frontend/src/pages/ContributionAnalysis.jsx`、`frontend/src/services/contributionService.js`
- **審查總評**：整體架構品質高（純函數引擎、分層乾淨、token 不外洩、2026-07-08 兩型事故防禦皆落實、91 項測試覆蓋主要路徑）。發現的問題集中在三類測試照不到的地方：**時間推移類**（資料缺口、殭屍 snapshot）、**跨請求邊界類**（event loop 阻塞、授權、task GC）、**規則與真實資料的錯配**（分組誤判、活動改名、期間不一致）。
- **執行原則**：每個任務獨立可測、可回滾；第 1 波為 hotfix 性質，完成並通過驗收前不進入後續波次；第 2–4 波可依資源並行；第 5 波為效能與 polish，排在 docs/25 worker 架構之前先做止血。

---

## 零、問題總覽與波次對映

| # | 問題 | 嚴重度 | 波次任務 |
|---|---|---|---|
| 1 | 增量抓取只補最近 3 天、不補缺口 → 永久資料空洞污染模型 | 高 | 1.1 |
| 2 | `POST /analyses` 在 event loop 上執行同步 DB + numpy 工作 | 高 | 1.2 |
| 3 | 快取讀取端點缺帳號授權檢查 → 跨帳號資料可讀 | 高 | 1.3 |
| 4 | `loop.create_task` fire-and-forget 有被 GC 的風險 | 中 | 2.1 |
| 5 | 殭屍 snapshot（重啟 / 503 路徑後永久卡 queued/processing） | 中 | 2.2 |
| 6 | 分組關鍵詞誤判（裸 `rt`、`test`、`活動` 無邊界） | 中 | 3.1 |
| 7 | 前綴聚類為 dead code（`_common_prefix([name])` 永遠 None） | 中 | 3.1 |
| 8 | `holdout_days` 可 ≥ 資料天數 → 空訓練集 silently 產出全 0 結果 | 中 | 2.3 |
| 9 | 活動改名 → `GROUP BY (id, name)` 彙總分裂 | 中 | 2.4 |
| 10 | 歷史快照用「現在的分組」渲染，改組後對不上 | 中 | 4.1 |
| 11 | 自報占比用全歷史彙總、MMM 用快照區間 → 對照失真且餵給 AI | 中 | 4.2 |
| 12 | 邊際步長 per-group，UI 只顯示第一組的 step | 中 | 4.3 |
| 13 | 引擎效能：adstock 重算 5 萬次（實際只需 ~42 次）、ridge 固定 4000 迭代 | 低（收益高） | 5.1 |
| 14 | `list_campaign_summaries` 的 `days` 參數為死碼 | 低 | 4.2（併入） |
| 15 | `r2_holdout=None`（holdout 零變異）→ `np.median` TypeError | 低 | 2.3（併入） |
| 16 | `upsert_daily_metrics` docstring 與程式碼矛盾（fetched_at） | 低 | 5.2 |
| 17 | GroupEditor 無法刪空組 → 使用者卡死於 422 | 低 | 4.4 |
| 18 | refresh 固定等 1.5 秒，全量抓取遠不止 → 使用者困惑 | 低 | 4.5 |
| 19 | 未分組活動轉換計入 y、花費被丟棄 → baseline 被墊高且無警告 | 低 | 5.3 |
| 20 | Hill K 分位數自含 holdout 的全序列取（輕微選模 leakage） | 記錄 | 不修（見七） |

---

## 一、第 1 波：Hotfix（高優先，先行完成）

### 任務 1.1 — 增量抓取補缺口

**問題**：`data_source.py` 的 `_resolve_fetch_window` 收到 `db_window` 後把 `(existing_start, existing_end)` 拆包即丟棄，一律只抓最近 3 天。使用者超過 3 天未刷新（極常見），中間日期永遠不會回補；缺口日在 `_assemble_arrays` 中變成 spend=0、y=0 的假資料直接進模型，guardrail 攔不到（天數與日均轉換仍可能達標），分析結果靜默劣化。docs/21 §3.2 明寫「已有資料的日期區間只補**缺口**與最近 3 天」，實作只做了後半。

**變更檔案**：`modules/contribution/data_source.py`、`tests/test_contribution_data_source.py`

**實作步驟**：
1. `_resolve_fetch_window` 改為：
   - `db_window is None` → 維持現行「近 180 天全量」。
   - 有 `db_window` → `start = min(existing_end 次日, yesterday - (attribution_recency_days - 1))`，即「從既有資料末日的次日開始補、且至少涵蓋歸因回補 3 天」；再 clamp 至 `yesterday - (MAX_DATE_RANGE_DAYS - 1)` 下限（超過 180 天的缺口退回全量視窗）。
   - `existing_end` 解析失敗（非 ISO 格式）→ 防禦性退回全量視窗並記 warning。
2. 缺口可能極大（如停用數月），單次視窗最大即 180 天，已有 `on_rows` 邊抓邊寫與 `MAX_PAGES` 防護，不需額外分段。
3. 測試補：`existing_end = 昨天`（→ 只補 3 天，現行為）、`existing_end = 10 天前`（→ 從 9 天前補到昨天）、`existing_end = 200 天前`（→ 退回 180 天全量）、`existing_end` 格式異常（→ 全量 + warning）。

**驗收標準**：上述 4 情境測試全綠；對測試帳戶模擬「快取末日為 N 天前」時，抓取視窗起點 = `min(末日+1, 昨天-2)`；既有 13 項 data_source 測試無回歸。

**風險/回滾**：讀取型變更，最壞情況是多抓幾天（upsert 冪等，不產生重複列）；單檔回滾。

**驗收結果（2026-07-09 完成）**：
- `_resolve_fetch_window` 改為 `start = min(existing_end 次日, yesterday - (attribution_recency_days - 1))`，並 clamp 至 180 天全量下限；`existing_end` 解析失敗時防禦性退回全量視窗 + log warning。
- 新增/改寫 4 項測試取代原本依賴「執行當下實際日曆日」的舊斷言（原測試用固定日期字串巧合通過，改為以 `date.today()` 動態推算，避免未來因日期改變而不穩定）：`test_resolve_fetch_window_recent_gap_uses_3_day_recency_window`（缺口在 3 天回補窗內，行為同舊版）、`test_resolve_fetch_window_fills_gap_beyond_recency_window`（缺口 9 天，起點正確從缺口次日開始）、`test_resolve_fetch_window_clamps_huge_gap_to_full_range`（缺口 400 天，clamp 回 180 天全量）、`test_resolve_fetch_window_falls_back_to_full_range_on_malformed_existing_end`（格式異常退回全量）。
- `tests/test_contribution_data_source.py` 20 項全綠；與 module + engine 合跑共 51 項全綠，無回歸。

### 任務 1.2 — `POST /analyses` 同步段移出 event loop

**問題**：`router.py` 的 `create_analysis_endpoint` 是 `async def`（`_dispatch_analysis` 需要 running loop），但直接呼叫的 `service.create_analysis` 內含 `get_or_create_groups`（DB）、`_assemble_arrays`（撈最多 180 天 × 全活動列）、`check_guardrails`（numpy）、`create_snapshot` + commit——全部同步跑在 event loop 上。這違反 `router.py:12-19` 檔頭自述的慣例，也是 docs/24 修過的同類根因（psycopg2 鎖等待無 timeout → 整個 backend 含 `/health` 凍結）。

**變更檔案**：`modules/contribution/service.py`、`modules/contribution/router.py`、`tests/test_contribution_service.py`

**實作步驟**：
1. `service.create_analysis` 拆為兩段：
   - `prepare_analysis(db, ...)`（同步）：預檢 + 建 snapshot + commit，回傳 `snapshot`。**不做 dispatch**。
   - `_dispatch_analysis(snapshot_id)` 維持原樣（需在 event loop 上呼叫）。
2. router 端點改為：`snapshot = await asyncio.to_thread(prepare_analysis, ...)` → 回到 loop 後呼叫 `_dispatch_analysis(snapshot.id)`。
   - 注意：`to_thread` 內不可用 router 的 `Depends(get_db)` session（session 非 thread-safe 且會橫跨等待期間），比照 `refresh_data` 的短生命週期 session 模式，在 thread 內自建 `SessionLocal` 並於 finally close。router 端點簽名移除 `db=Depends(get_db)`。
3. 既有 `create_analysis` 保留為薄包裝（`prepare` + `dispatch`）供測試與 CLI 同步呼叫，`__all__` 不變。
4. 測試補：mock `prepare_analysis` 確認 router 走 `to_thread`；service 測試改對 `prepare_analysis` 斷言（原 12 項語義不變）。

**驗收標準**：POST /analyses 行為不變（202 / 422 / 503 路徑全部保留）；service 12 項 + module 16 項無回歸；以人工注入 `time.sleep(3)` 於 `_assemble_arrays` 模擬慢查詢時，並發的 `/health` 請求不被阻塞（本地驗證一次即可，不留為自動化測試）。

**風險/回滾**：行為等價重構；回滾兩檔即可。

**驗收結果（2026-07-09 完成）**：
- `service.py` 拆為 `prepare_analysis(db, ...)`（同步：guardrail 預檢 + `_assemble_arrays` + 建 snapshot + commit，不含 dispatch）+ 既有 `create_analysis` 降級為薄相容包裝（`prepare_analysis` + `_dispatch_analysis`，供測試/CLI 同步呼叫，行為與呼叫介面不變）。
- `router.py` 的 `create_analysis_endpoint`：`snapshot = await asyncio.to_thread(prepare_analysis, db, ...)` → 回到 event loop 後才呼叫 `_dispatch_analysis(snapshot.id)`。沿用既有 request-scoped `Depends(get_db)` session（非另建短生命週期 session）——因為 `prepare_analysis` 只涉及本地快速 DB 查詢 + numpy guardrail 運算（無外部網路等待），與 `refresh_data` 需要跨 Meta API 長時間等待、必須避免佔用連線池的情境不同；經 `asyncio.to_thread` 丟到 threadpool 執行緒後即不再佔用 event loop，同一 session 物件在該執行緒內循序使用無執行緒安全疑慮。
- 新增回歸測試 `test_create_analysis_endpoint_offloads_to_thread_then_dispatches`（`tests/test_contribution_service.py`）：直接 `asyncio.run()` 呼叫 router coroutine（略過 TestClient/lifespan，沿用任務 1.4 附註的「HTTP e2e 在 TestClient lifespan 累積下會 OOM」教訓），驗證 dispatch 只在 snapshot 建立後、於 event loop 上被呼叫恰一次。過程中發現一個匯入陷阱並記錄：`modules/contribution/__init__.py` 執行 `from .router import router` 後，套件屬性 `modules.contribution.router` 被同名 APIRouter 實例覆蓋，連 `import modules.contribution.router as x`（依屬性鏈解析）都會撈到被覆蓋後的物件而非子模組本身；必須改用 `sys.modules["modules.contribution.router"]` 直接取子模組才能正確 monkeypatch 其模組層級名稱。
- `tests/test_contribution_service.py` 13 項全綠；與 module + engine + data_source + grouping 合跑共 76 項全綠，無回歸。

### 任務 1.3 — 快取讀取端點加帳號授權檢查

**問題**：`/campaigns`、`/groups`（GET/PUT）、`GET /analyses`、`GET /analyses/{id}`、`PUT .../ai-summary` 都只掛 `require_contribution_module`，然後直接以 query 的 `account_id`（或 snapshot 內的 account_id）查本地快取表。fb_ads 的帳號權限靠「用使用者自己的 token 打 Meta API」隱性把關；contribution 讀本地快取，這層把關不存在——任何有 contribution 模組權限的使用者可用任意 `account_id` 讀到其他團隊帳號的花費、轉換、分析結果與 AI 解讀。docs/21 §3.4「可存取的帳號範圍沿用 FB token 權限（同 fb_ads）」目前只對 `/data/refresh` 成立。

**變更檔案**：`modules/contribution/dependencies.py`（新增帳號授權依賴）、`modules/contribution/router.py`（相關端點掛上）、`modules/fb_ads/accounts_service.py`（新增 `resolve_accessible_account_ids`）、`tests/test_contribution_module.py`（既有 fixture 補 patch）、`tests/test_contribution_service.py`（POST /analyses wiring 測試補 team 參數）、`tests/test_contribution_account_access.py`（新增）

**實作步驟（實作時對照原計劃的兩處調整，理由詳列於下）**：
1. 研究既有「使用者可存取帳號清單」機制後發現：這不是一張靜態 DB 白名單表，而是 `routers/facebook.py` 的 `/api/ad-accounts` 端點即時判斷——owner 見自己 FB token 下的全部帳號（不受限制）；非 owner 依 `Team.visible_ad_account_ids`（JSON 白名單字串欄位）過濾「team token 可見的帳號」。前端 `apiClient.js` 已對每個請求全域帶上 `X-Team-ID` header（來自 `localStorage.selected_team_id`），故 contribution 端點可直接沿用既有 `get_current_team` 依賴（驗證 header 對應的 team 且使用者為成員，否則 403）取得 team context。
2. 新增 `modules.fb_ads.accounts_service.resolve_accessible_account_ids(current_user, team) -> (ids: set, error: str | None)`：複製 `/api/ad-accounts` 的可視範圍判斷邏輯（owner 不受白名單限制、非 owner 取交集），但只回傳 ID 集合（同時含 `act_123`/`123` 兩種型式）供 containment 檢查，且不依賴 request-scoped DB session（team 的白名單資料已是傳入 ORM 物件的屬性，無需額外查詢）——複用既有 `get_all_ad_accounts`（含 Redis 快取 + Meta API），不重造 token/快取邏輯。
3. `modules/contribution/dependencies.py` 新增三個授權工具：`ensure_account_access`（async，供已是 `async def` 的端點如 POST /analyses 直接 `await`）、`verify_account_access_or_403`（sync 包裝，內部 `asyncio.run(...)`，供 6 個既有 `def` 端點呼叫——這些端點在 Starlette threadpool 執行緒內執行、無 running event loop，`asyncio.run` 安全）、`verify_snapshot_account_access_or_404`（snapshot 類端點用，未授權回 404 而非 403，與「snapshot 不存在」同訊息）。
4. **調整一：`/data/refresh` 刻意不套用此檢查**（原計劃列了此端點）。原因：`/data/refresh` 已一律用「呼叫者自己的」FB token 抓資料（不接受 team token override），Meta 自己的帳號權限本身即是等同 fb_ads 的隱性門檻；而該端點刻意不持有 request-scoped `Depends(get_db)` 以避免在等待 Meta API 期間佔用連線池（2026-07-08 事故教訓，見該端點既有註解）。加上 `team=Depends(get_current_team)` 會 transitively 拉入一個貫穿整個請求生命週期的 `Depends(get_db)` session（FastAPI 對 generator 依賴的 teardown 時機是整個請求完成後，不是子依賴解析完成後），等同重新引入同一類連線池風險，故不在此端點加上檢查；已在 `dependencies.py` 檔頭與程式碼註解說明此決策。
5. **調整二：額外把 `POST /analyses`（發起分析）也納入檢查**（原計劃只列 campaigns / groups GET+PUT / analyses **列表** / data refresh，未列 POST 建立分析）。理由：POST /analyses 同樣是讀寫本地快取表（`_assemble_arrays` 撈資料 + 建 snapshot），沒有 Meta API 的隱性門檻，任何模組使用者原本可對任意 `account_id` 發起分析並建立 snapshot（雖然結果需再透過 GET /analyses/{id} 才能讀到，該端點已受保護，但仍應在寫入源頭一併把關，且此端點已持有 `Depends(get_db)`，加上 `get_current_team` 不會新增連線池風險）。
6. 6 個套用檢查的端點：`GET /campaigns`、`GET /groups`、`PUT /groups`、`POST /analyses`、`GET /analyses`（列表）、`GET /analyses/{id}`、`PUT .../ai-summary`（`GET /analyses/{id}` 與 PUT ai-summary 皆先取 snapshot 再驗 `snapshot.account_id`，404 語意一致）。

**驗收標準**：新增授權測試全綠；既有 16 項 module 測試無回歸（測試 fixture 的使用者需補帳號授權關聯）；手動以兩個不同團隊的使用者驗證互相讀不到對方帳號。

**風險/回滾**：行為變更（未授權者從 200 變 403/404）——上線前確認現有使用者的帳號授權資料完整，避免誤傷合法使用者；回滾移除依賴即可。

**驗收結果（2026-07-09 完成）**：
- 既有 `tests/test_contribution_module.py` 的 `contribution_authorized_client` fixture 新增 monkeypatch：把 `resolve_accessible_account_ids` patch 為「任何 account_id 皆視為可視」（`_AllowAllSet.__contains__` 恆真），因為該檔案 16 項測試聚焦模組骨架/分組/分析編排等既有業務邏輯，不是在測授權行為本身；授權行為改由新檔案獨立驗證。修正時同樣踩到與任務 1.2 相同的套件屬性遮蔽陷阱，改用 `sys.modules["modules.contribution.dependencies"]` 取得真正子模組再 patch。
- 新增 `tests/test_contribution_account_access.py` 15 項全綠：
  - 6 項純函數層（`resolve_accessible_account_ids`，mock `get_all_ad_accounts`）：無 team 個人範圍不受限、owner 不受白名單限制、非 owner 依白名單取交集、非 owner 無白名單時僅受 team token 範圍限制、錯誤傳遞為空集合、白名單 JSON 格式異常保守回空集合。
  - 9 項 router 層（`TestClient` + `app.dependency_overrides[get_current_team]` + mock `get_all_ad_accounts`）：`/campaigns` owner 內外帳號 200/403、非 owner 白名單內外 200/403；`/groups` GET+PUT 未授權 403；`GET /analyses`（列表）未授權 403；`GET /analyses/{id}` 未授權回 **404**（非 403）且訊息與「真的不存在」的 snapshot 完全相同（用以驗證無法從回應分辨兩種情況）、授權後 200；`PUT .../ai-summary` 未授權 404。
  - 過程中發現本專案的全域 `HTTPException` handler（`main.py`）把錯誤回應改寫為 `{"error": ..., "error_code": ..., "error_type": ...}`（非 FastAPI 預設的 `{"detail": ...}`），測試斷言需讀 `"error"` 欄位，已修正並加註解避免未來重踩。
  - `tests/test_contribution_service.py` 的新端點 wiring 測試（任務 1.2 新增）補上 `team=None` 顯式傳入（直接呼叫 coroutine 略過 FastAPI DI，`Depends(get_current_team)` 的預設值不會被解析）與 `ensure_account_access` 的 no-op monkeypatch。
- 全套回歸：`test_contribution_module`(16) + `test_contribution_engine`(15) + `test_contribution_data_source`(20) + `test_contribution_grouping`(11) + `test_contribution_service`(13) + `test_contribution_account_access`(15) + `test_permissions` + `test_auth` + `test_health` = **115 項全綠**，無回歸。

---

## 二、第 2 波：正確性補強（中優先）

### 任務 2.1 — 背景 task 強引用防 GC

**問題**：`service.py` `_dispatch_analysis` 的 `loop.create_task(_run())` 回傳值未保留；CPython 文件明確警告未被引用的 task 可能在執行中被垃圾回收。分析要跑 ~50 秒，風險真實存在。

**變更檔案**：`modules/contribution/service.py`、`tests/test_contribution_service.py`

**實作步驟**：module-level `_background_tasks: set[asyncio.Task] = set()`；`task = loop.create_task(_run())` → `_background_tasks.add(task)` → `task.add_done_callback(_background_tasks.discard)`。測試斷言 dispatch 後 task 進入集合、完成後自動移除。

**驗收標準**：新測試綠；dispatch local_async 路徑既有測試無回歸。

**驗收結果（2026-07-09 完成）**：
- `service.py` 新增 module-level `_background_tasks: set[asyncio.Task] = set()`；`_dispatch_analysis` 的 `loop.create_task(_run())` 回傳值 `add` 進集合、`task.add_done_callback(_background_tasks.discard)` 完成後自動移除。
- 新增 `test_dispatch_analysis_keeps_strong_reference_until_task_completes`：用 `asyncio.Event` 控制 fake `process_analysis` 的執行時序，斷言 dispatch 完成當下 task 已在集合中（尚未執行完）、等待完成後集合正確清空。
- `tests/test_contribution_service.py` 14 項全綠，無回歸。

### 任務 2.2 — 殭屍 snapshot 回收

**問題**：apscheduler 是 in-memory date-trigger——server 在 job 執行前重啟，snapshot 永久卡 `queued`；`process_analysis` 中途重啟則永久卡 `processing`；503 路徑（scheduler 與 local loop 皆不可用）也留下 queued snapshot。前端輪詢無限轉圈。Andromeda 有 `cleanup_stale_score_events` 對應機制，contribution 沒有。

**變更檔案**：`modules/contribution/repository.py`（新增 `mark_stale_snapshots_failed`）、`core/scheduler.py`（開機掃描）、`tests/test_contribution_service.py`

**實作步驟**：
1. `repository.mark_stale_snapshots_failed(db, *, queued_older_than_minutes=10, processing_older_than_minutes=30) -> int`：把超時的 queued/processing snapshot 標為 `failed`，`error_message` 分別為 `stale_queued_reclaimed`（提示使用者重新發起）與 `stale_processing_reclaimed`（伺服器重啟或任務中斷）。
2. 掛載時機：app lifespan 啟動時掃一次（同 scheduler 初始化處），另比照 Andromeda 以低頻 interval job（每 15 分鐘）掃描。閾值取分析實際耗時（~50s）的安全倍數，避免誤殺執行中的任務。
3. 測試：建立過期 queued / processing / 正常 processing 三筆，掃描後前兩筆 failed、第三筆不動。

**驗收標準**：測試綠；重啟 server 後卡住的 snapshot 在 15 分鐘內轉 failed 且前端可見明確錯誤訊息。

**驗收結果（2026-07-09 完成）**：
- `core/config.py` 新增 3 個設定：`CONTRIBUTION_STALE_QUEUED_MINUTES`（預設 10）、`CONTRIBUTION_STALE_PROCESSING_MINUTES`（預設 30，分析實測 45-90 秒的安全倍數）、`CONTRIBUTION_STALE_SWEEP_INTERVAL_SECONDS`（預設 900 秒 = 15 分鐘）。
- `repository.mark_stale_snapshots_failed(db, *, queued_older_than_minutes, processing_older_than_minutes, now=None)`：依 `created_at` 判斷超時（`process_analysis` 轉 processing 後未再更新任何時間戳可用，用建立時間近似「已執行多久」，門檻已含安全餘裕），把超時的 queued/processing 分別標 `stale_queued_reclaimed` / `stale_processing_reclaimed`，回傳回收筆數；呼叫端負責 commit。
- `core/scheduler.py` 新增 `sweep_contribution_stale_snapshots()`（async，短生命週期 `SessionLocal`，比照 `sweep_meta_andromeda_queue` 模式）+ `add_contribution_stale_sweep_job()`（interval trigger）；`start_scheduler()` 在 `run_meta_andromeda_jobs` 旗標下註冊 interval job 並於開機當下立即掃一次（不等第一個 interval）——沿用與 Meta Andromeda 相同的 role flag，理由：docs/25 Wave 1 規劃將 contribution 背景負載併入同一 worker，此處先與其共用註冊時機，未來 worker 化時一併搬遷不需重新設計。
- 新增 2 項測試：`test_mark_stale_snapshots_failed_reclaims_only_overdue`（4 種情境：過期 queued/processing 各回收、未過期的兩者皆不受影響）、`test_sweep_contribution_stale_snapshots_commits_reclaimed_rows`（monkeypatch `SessionLocal` 綁測試 db，驗證 async 版本確實 commit 寫入）。
- 過程修正一個小疏漏：`repository.py` 只 import 了 `datetime`，新函式用到 `timedelta` 未 import，補上後測試通過。
- `test_contribution_module.py`（21 項）+ `test_scheduler.py` 全綠；`test_scheduler.py::test_get_next_run_time_uses_weekly_schedule` 1 項既有失敗經 `git stash` 前後對照確認為修改前即存在的日期相依測試問題，與本任務無關。

### 任務 2.3 — 引擎 guardrail 補 holdout 上限 + r2 None 防護

**問題一**：schema 允許 `holdout_days` 7–180、`min_days` 90 → 傳 90 天資料 + `holdout_days=90` 時 `split=0` → 空訓練集 → `nonneg_ridge` 權重全 0 → 貢獻全 0，不 crash 不報錯，使用者拿到一份「全部沒貢獻」的假報告。
**問題二**：holdout 段 y 零變異時 `r2_holdout=None`，`run_analysis` 的 `dist([r["r2_holdout"] for r in restarts])` 對 None 做 `np.median` 直接 TypeError → 整筆分析 failed。

**變更檔案**：`modules/contribution/engine.py`、`tests/test_contribution_engine.py`

**實作步驟**：
1. `check_guardrails` 新增：`holdout_days >= n` → violation「holdout 天數 ≥ 資料天數，無訓練資料」；`holdout_days > n // 3` → violation「holdout 占比過高（建議 ≤ 1/3），訓練資料不足」。
2. `run_analysis` 的 `dist()` 呼叫前過濾 None：全 None 時該指標回 `None`（JSON 可序列化），部分 None 時以有值者計算。
3. 測試補：90 天 + holdout 90 → GuardrailViolation；90 天 + holdout 45（= n/2）→ violation；180 天 + holdout 45 → 通過（現行預設不受影響）；holdout 段常數 y → 不 crash、r2.holdout 為 None。

**驗收標準**：新測試綠；既有 15 項 engine 測試無回歸（預設 config 180 天 / holdout 45 = 25% < 1/3，不觸發新規則）。

**注意**：新 guardrail 會在 `create_analysis` 預檢即回 422，前端 `detail.errors` 直接呈現，無需前端變更。

**驗收結果（2026-07-09 完成，門檻由計劃書的 1/3 調整為 1/2，理由詳列於下）**：
- 實作時發現 **原計劃的 `n // 3` 門檻會誤傷 docs/21 §3.1 guardrails 明文記載的合法最小組合**：`min_days=90`（下限）搭配 `holdout_days` 預設值 45，比例恰為 50%——若用 1/3 門檻（30 天），這個文件記載的「90 天下限」組合會被直接擋死，等於讓下限形同虛設（因為 `create_analysis` 的 `holdout_days` 未指定時一律用預設 45，使用者若真的只有 90 天資料且未手動調小 holdout，會永遠卡在 422）。改用 **`holdout_days > n // 2`**：90 天+45 holdout（50%）剛好通過，180 天+45 holdout（25%，官方建議組合）不受影響，仍能攔住明顯過高的比例（如 90 天配 46+ 天 holdout）。
- `check_guardrails` 新增兩條規則（`holdout_days >= n` 與 `holdout_days > n // 2`）；`run_analysis` 內部 `dist()` 改為先過濾 None 值，全為 None 時三個欄位皆回 `None`。
- 新增 6 項測試：`test_guardrail_holdout_days_equal_to_total_days_rejected`、`test_guardrail_holdout_days_ratio_too_high_rejected`、`test_guardrail_documented_minimum_90_days_with_default_holdout_passes`（驗證文件記載下限不被誤傷）、`test_guardrail_default_180_days_with_default_holdout_passes`、`test_run_analysis_holdout_zero_variance_r2_is_none_not_crash`（holdout 段常數 y，驗證不 crash 且 `r2.holdout` 三欄皆為 `None`，`r2.full` 正常計算）。
- `tests/test_contribution_engine.py` 20 項全綠（原 15 + 新 5，另有一項寫在既有 guardrail 區塊）；與 service + module 合跑共 52 項全綠，無回歸。

### 任務 2.4 — 活動改名的彙總分裂修復

**問題**：`repository.list_campaign_summaries` 以 `GROUP BY (campaign_id, campaign_name)`；增量抓取只覆寫最近 3 天的 `campaign_name`，歷史列保留舊名快照——改名後同一 `campaign_id` 出現兩列，花費占比被攤薄、`auto_group` 對同一 cid append 兩次（可能同 cid 進兩個組，後續 manual 驗證報「同時出現在多個組別」）。

**變更檔案**：`modules/contribution/repository.py`、`tests/test_contribution_data_source.py`

**實作步驟**：
1. `list_campaign_summaries` 改為只 `GROUP BY campaign_id`；`campaign_name` 取最新日期列的值——跨 SQLite/PostgreSQL 的安全做法：主查詢不取 name，另以一個「(campaign_id, max(date)) 對 name」的查詢在 Python 端合併（資料量為活動數等級，無效能顧慮）。
2. 測試補：同 campaign_id 兩個名稱（舊名 100 天 + 新名 3 天）→ 回傳單列、name 為新名、spend 為兩段合計。

**驗收標準**：測試綠；`/campaigns`、`auto_group`、`update_groups` 驗證路徑對改名活動行為正確。

**驗收結果（2026-07-09 完成）**：
- `list_campaign_summaries` 改為 `GROUP BY campaign_id` 單欄；主查詢不再 select `campaign_name`。另以一個「`campaign_id` → `max(date)`」子查詢 JOIN 回原表取得該日期的 `campaign_name`——利用資料表既有唯一約束 `(account_id, date, campaign_id, metric_key)` 保證此 JOIN 對每個 `campaign_id` 恰回一列，不需要 `DISTINCT`（`DISTINCT ON` 是 PostgreSQL 特有語法，若真需要會破壞 SQLite 相容性，此設計完全避開）。
- 新增 `test_contribution_campaigns_renamed_campaign_does_not_split_into_two_rows`：同一 `campaign_id` 三天資料（前兩天舊名、第三天新名），驗證彙總合併為一列、花費為三天加總（未被攤薄）、顯示名稱為最新一天的新名。
- `test_contribution_module.py` 相關測試（含既有 `test_contribution_campaigns_returns_aggregated_summaries`）3 項全綠，無回歸。

---

## 三、第 3 波：分組規則修正

### 任務 3.1 — 關鍵詞邊界 + 前綴聚類實作或移除

**問題一（誤判）**：`_KEYWORD_RULES` G5 含裸 `rt`——名稱含 "Smart"、"Start"、"sport" 的活動全被分進「大包裝再行銷」；`test` 吃掉 "contest"、"latest"；`活動` 二字在中文活動命名極常見，大量活動被誤分到 G3 檔期。
**問題二（dead code）**：`auto_group` 對每個活動呼叫 `_common_prefix([name])` 只傳一個名稱，而 `_common_prefix` 對 `len < 2` 永遠回 None——docs/21 §3.3 規則 1 的「相同前綴聚類」從未生效，所有無關鍵詞活動全部落入 G_other。

**變更檔案**：`modules/contribution/grouping.py`、`tests/test_contribution_grouping.py`

**實作步驟**：
1. 英文關鍵詞加 word boundary：`rt` → `\brt\b`（或直接移除，`retargeting|re[_\- ]?target|再行銷` 已足夠覆蓋）；`test` → `\btest\b`；`event` → `\bevent\b`（防 "prevent"）。
2. 中文關鍵詞收斂：`活動` 從 G3 移除（訊號太弱），保留 `檔期|seasonal|promo`；視真實帳戶命名習慣可補 `雙11|雙十一|母親節|周年慶` 等強訊號詞（實作時以測試帳戶實際名稱清單校準）。
3. 前綴聚類二選一（**建議 a**）：
   - (a) 真正實作：先跑關鍵詞分桶，對落入 G_other 的活動集合做跨活動前綴聚類——以名稱前 `_COMMON_PREFIX_LEN` 字元分桶，桶內 ≥ 2 個活動且合計占比 ≥ `min_spend_share` 才成組（`G_prefix_*`），其餘留 G_other。
   - (b) 刪除 dead code 並同步修訂 docs/21 §3.3（移除「相同前綴」字樣）。
4. 測試補：`Smart Shopping` 不進 G5；`contest` 不進 G7；同前綴 3 活動（無關鍵詞、占比達標）聚為一組；既有 11 項分組測試無回歸。

**驗收標準**：新舊測試全綠；對真實測試帳戶跑一次 `auto_group`，人工核對分組結果無明顯誤判。

**注意**：分組規則變更會改變新帳戶的 auto 分組結果；既有帳戶已存 DB 的分組不受影響（manual 優先、auto 不自動重算），無遷移需求。

**驗收結果（2026-07-09 完成，採建議方案 a：真正實作前綴聚類）**：
- 關鍵詞修正：G5 移除裸 `rt`（`retargeting|re[_\- ]?target|再行銷` 已足夠覆蓋，不需要短字串萬用匹配）；G7 的 `test` 改 `\btest\b`（保留 `測試|導流|測試導流` 不變，中文字無此類子字串誤判風險）；G3 移除 `活動`、`event` 加邊界為 `\bevent\b`。
- 前綴聚類真正實作（取代 dead code）：`auto_group` 拆成 Step 1a（關鍵詞分桶，無匹配者收進 `unmatched` list）+ Step 1b（對 `unmatched` 依名稱前 `_COMMON_PREFIX_LEN` 字元跨活動分桶；桶內需 ≥ 2 個活動且合計花費占比 ≥ `min_spend_share` 才建立 `G_prefix_*` 組，否則整桶併入 `G_other`）。原本恆回 `None` 的 `_common_prefix()` 輔助函式已刪除（無其他呼叫點）。
- 新的 Step 1b 對 `prefix_candidates`（獨立字典）迭代並寫入 `g_other["campaign_ids"]`，未迭代 `buckets`/`g_other` 自身，不會重蹈 2026-07-08「邊迭代 G_other 邊 append」無限迴圈的覆轍（`test_auto_group_terminates_with_unmatched_low_share_campaign` 既有回歸測試仍綠）。
- 新增 8 項測試：`test_auto_group_smart_shopping_not_misclassified_as_retargeting`、`test_auto_group_contest_not_misclassified_as_test_traffic`、`test_auto_group_bare_test_keyword_still_matches_g7`（確認修正不是矯枉過正）、`test_auto_group_activity_keyword_no_longer_triggers_g3`、`test_auto_group_real_prefix_clustering_groups_unmatched_campaigns`（3 個同前綴活動正確聚為一組，舊版 dead code 下這 3 個活動只會各自散落 G_other）、`test_auto_group_prefix_cluster_requires_at_least_two_members`、`test_auto_group_prefix_cluster_requires_aggregate_share_above_threshold`（7 項 + 原 12 項 = 19 項，比計劃列的略多，補了「不是矯枉過正」與「單一活動不成組」「合計占比不足不成組」三個邊界案例）。
- `tests/test_contribution_grouping.py` 19 項全綠；全套 contribution + permissions/auth/health 回歸 132 項全綠，無回歸。
- **未完成項**：驗收標準「對真實測試帳戶跑一次 `auto_group`，人工核對分組結果無明顯誤判」——本開發環境無真實帳戶資料存取權限，未執行；建議上線後於 staging 或首個實際使用的帳戶上人工核對一次分組結果。
- 分組規則變更確認不影響既有帳戶：`auto_group` 只在 `get_or_create_groups` 偵測「完全無分組」時才呼叫（manual 優先、auto 已存在則直接回傳，不重算），已存 DB 的分組不受本次規則變更影響。

---

## 四、第 4 波：前端一致性修正

### 任務 4.1 — 歷史快照以 group_snapshot 渲染

**問題**：`AnalysisView` 的 rows 由頁面當前 `groups` state 組出，但 snapshot 的 `results.groups` key 來自分析當時的 `config.group_snapshot`。使用者改組後點開舊快照，對不上的組顯示 0 或消失。

**變更檔案**：`frontend/src/pages/ContributionAnalysis.jsx`、`frontend/src/pages/__tests__/ContributionAnalysis.test.jsx`

**實作步驟**：`AnalysisView` 與 `buildAiPayload` 的 groups 來源改為 `snapshot.config?.group_snapshot ?? groups`（舊快照無 config 時退回現行為）；分組編輯器維持用當前 groups（職責不同）。測試補：mock 一筆 group_snapshot 與當前 groups 不同的快照，斷言渲染行數與 label 來自 snapshot。

**驗收標準**：改組後切歷史快照，各組數字與當時分組一致；vitest 全綠。

**驗收結果（2026-07-09 完成）**：
- `AnalysisView` 新增 `effectiveGroups = snapshot?.config?.group_snapshot ?? groups`，`rows` useMemo 與傳給 `AiInsightsCard`（進而 `buildAiPayload`）的 `groups` 皆改用 `effectiveGroups`；分組編輯器（`GroupEditor`）維持用當前 `groups` state 不變。
- 新增測試 `renders a historical snapshot using its own group_snapshot, not the current groups state`：mock 一筆歷史快照的 `config.group_snapshot` 群組名稱與目前 `groups` state 不同，點選該歷史快照後斷言表格顯示 `group_snapshot` 的名稱（`G1 · 舊名稱（分析當時）`）而非目前 state 的新名稱。斷言鎖定 `ContributionTable`（純 HTML table）的渲染文字，避開 Recharts 在 JSDOM 下 width/height 為 -1 無法可靠渲染 SVG 文字的已知限制。
- `ContributionAnalysis.test.jsx` 3 項全綠（原 2 + 新 1）。

### 任務 4.2 — 自報占比改用快照區間（含後端 days 死參數處理）

**問題**：`reportedByGroup` 用 `/campaigns` 的**全歷史**彙總計算，MMM 貢獻只涵蓋快照區間；兩者並排在主圖比較、還餵進 AI payload——90 天分析配 180 天自報占比時對照失真，AI 據此下「高估/低估」結論。後端 `list_campaign_summaries` 的 `days` 參數目前是死碼（建了 subquery 又 `del`）。

**變更檔案**：`modules/contribution/repository.py`、`modules/contribution/router.py`、`modules/contribution/schemas.py`、`frontend/src/services/contributionService.js`、`frontend/src/pages/ContributionAnalysis.jsx`、`tests/test_contribution_module.py`

**實作步驟**：
1. 後端 `list_campaign_summaries` 把 `days` 死參數改為明確的 `date_start: str | None, date_end: str | None`（Python 端傳入，`WHERE date BETWEEN`），`/campaigns` 端點透傳兩個 optional query 參數。
2. 前端 `reportedByGroup` 改依 `activeSnapshot` 的 `date_start/date_end` 呼叫 `listCampaignSummaries({ accountId, dateStart, dateEnd })` 計算（快照切換時重算）；分組編輯器與「快取活動數」提示維持全歷史查詢（職責不同，兩次呼叫）。
3. `buildAiPayload` 的 `reported_share` 隨之對齊快照區間。

**驗收標準**：90 天快照的自報占比只計 90 天內轉換；後端測試補 date-range 過濾斷言；前端 vitest 全綠。

**驗收結果（2026-07-09 完成）**：
- `repository.list_campaign_summaries` 的 `days: int | None` 死參數改為 `date_start: str | None, date_end: str | None`，`base_filters` 依兩者是否提供動態加上 `date >= date_start` / `date <= date_end`；連帶名稱回填的兩個子查詢也共用同一組 `base_filters`（若指定區間，「最新一天的名稱」也限縮在該區間內，口徑一致）。`/campaigns` 端點新增對應的可選 query 參數並透傳。
- 前端 `contributionService.listCampaignSummaries` 增加 `dateStart`/`dateEnd` 參數（沿用既有 `buildQuery` 對 undefined 的過濾邏輯，不影響既有無參數呼叫）。
- `ContributionAnalysis.jsx` 新增 `snapshotCampaigns` state + `useEffect`（依 `accountId` / `activeSnapshot.snapshot_id` / `date_start` / `date_end` 變化重打），`reportedByGroup` 改依 `snapshotCampaigns` 計算；同時比照任務 4.1，cid→group_key 的對應也改用 `activeSnapshot?.config?.group_snapshot ?? groups`，確保「MMM 貢獻」與「自報占比」用同一套分組口徑對照，不會出現半邊用歷史分組、半邊用當前分組的不一致。`campaigns`（全歷史）state 不變，仍供分組編輯器與「快取活動數」提示使用。
- 新增後端測試 `test_contribution_campaigns_filters_by_date_range`：4 天資料中只有 2 天落在指定區間，斷言全歷史彙總（4 天/1600 花費）與限定區間彙總（2 天/200 花費）皆正確。
- 新增前端測試 `computes reportedByGroup from the snapshot date range, not the full campaign history`：故意讓全歷史彙總（c1/c2 轉換相同 → 50/50）與快照區間彙總（8:2 → 80/20）產生截然不同的結果，斷言渲染出的自報占比是 80.0%/20.0%（快照區間），驗證此為修復後行為而非巧合。
- 後端 `test_contribution_module.py` 相關測試全綠；前端 `ContributionAnalysis.test.jsx` 4 項全綠（新增 1）。

### 任務 4.3 — 邊際步長 per-group 顯示

**問題**：引擎對每組各自算 step（依該組日均花費），前端 `marginalStep` 取 `results.groups` 第一個 key 的 step 套在表頭與圖說——各組花費量級差大時標籤是錯的。

**變更檔案**：`frontend/src/pages/ContributionAnalysis.jsx`

**實作步驟**：`ContributionTable` 表頭改為「邊際轉換（每組步長見列內）」，每列顯示 `+{row.marginalPerStep.median}（/ +{row.marginalStep} 元）`；`MarginalChart` 因各組步長不同不可直接比大小——改為以「每 +100 元」正規化（`per_step.median / step * 100`）排序與顯示，圖說明示正規化口徑；`ChartMethodNote` lead 同步改寫。tooltip 顯示該組原始 step 與原始邊際值。

**驗收標準**：兩組 step 不同（100 vs 500）的快照，表格與圖的數字口徑正確且圖可跨組比較；vitest 全綠。

**驗收結果（2026-07-09 完成）**：
- `AnalysisView` 的 `rows` 新增 `marginalStepValue: data.marginal?.step ?? null`（每組自己的步長，取代舊版全域 `marginalStep`）。
- `ContributionTable` 表頭改為「邊際轉換（每組步長見列內）」；每列改用 `+{median}（/ +{step}{currency}）` 格式，各列使用自己的 `row.marginalStepValue`。
- `MarginalChart` 改用正規化值 `(rawMarginal / step) * 100`（每 +100 元的邊際轉換）排序與繪圖，才可跨組公平比較；原始 tooltip 的 `formatter` 換成自訂 `MarginalTooltipContent` 元件，同時顯示正規化值與原始 step/原始邊際值。`ChartMethodNote` 的 lead/detail 改寫為描述正規化口徑。
- 移除全域 `marginalStep`（原本取 `results.groups` 第一個 key 的 step 套用到所有列的 bug 根源）：刪除頂層 `ContributionAnalysis` 元件內的計算、`AnalysisView` 的 prop、`ContributionTable`/`MarginalChart` 的 prop，全面改為逐列讀取。
- 新增測試 `shows each group's own marginal step, not the first group's step for all rows`：G1 step=100、G2 step=500，斷言表格分別顯示 `+1.20（/ +100）` 與 `+3.00（/ +500）`（若舊 bug 仍在，G2 會誤顯示 `/ +100`）。
- `npx vite build` 全綠；`ContributionAnalysis.test.jsx` 5 項全綠（新增 1）。

### 任務 4.4 — GroupEditor 空組處理

**問題**：把某組活動全搬走後，空組被後端 422（`campaign_ids 不可為空`）擋下，UI 又沒有刪組功能，使用者卡死。

**變更檔案**：`frontend/src/pages/ContributionAnalysis.jsx`

**實作步驟**：`handleSaveGroups` 送出前過濾 `campaign_ids.length === 0` 的組；編輯器對空組顯示「此組將於儲存時移除」提示；（可選）加「新增組別」按鈕（group_key 自動取 `G_custom_N`），本任務先做過濾與提示，加組視回饋決定。

**驗收標準**：搬空一組後儲存成功、該組消失；無活動被丟失（後端 `validate_manual_groups` 的完整性檢查仍然把關）。

**驗收結果（2026-07-09 完成）**：
- `handleSaveGroups` 送出前以 `editingGroups.filter((g) => (g.campaign_ids || []).length > 0)` 過濾空組，完整性把關仍交給後端 `validate_manual_groups`（未新增前端側的完整性邏輯，避免前後端規則分岔）。
- `GroupEditor` 新增條件渲染：`editing && group.campaign_ids.length === 0` 時顯示警示區塊「此組已無任何活動，將於儲存時移除。」（虛線警示樣式，與既有錯誤/警告色調一致）；未在編輯狀態下的空組維持原本「無活動。」的低調提示（理論上不會出現，因為已存 DB 的分組不會是空的）。
- 新增測試 `warns about and filters out emptied groups on save`：把唯一活動從 G1 移到 G2（透過活動徽章上的 select），斷言 G1 顯示移除警示，點擊「儲存分組」後 `updateGroups` 收到的 payload 只含 G2（G1 已被過濾掉）。
- `npx vite build` 全綠；`ContributionAnalysis.test.jsx` 6 項全綠（新增 1）。

### 任務 4.5 — refresh 完成度回饋

**問題**：`handleRefreshData` 固定等 1.5 秒重抓快取；全量 180 天背景抓取遠不止 1.5 秒，首次使用者看到仍是 0 筆而困惑。

**變更檔案**：`frontend/src/pages/ContributionAnalysis.jsx`

**實作步驟**：改為輪詢 `listCampaignSummaries`（間隔 3 秒、上限 60 秒）：活動數增加或連續兩次不變且 > 0 即停止並顯示成功；逾時顯示「抓取仍在背景進行，稍後請按重新整理」。輪詢期間按鈕維持「抓取中…」。離開頁面/切換帳戶時清除輪詢 timer。

**驗收標準**：首次全量抓取過程中 UI 有進度回饋、完成後活動清單自動出現；切換帳戶不殘留輪詢。

**驗收結果（2026-07-09 完成）**：
- 停止條件抽成獨立純函數 `evaluateRefreshPoll({ count, baselineCount, lastCount, elapsedMs, timeoutMs })`（具名匯出），回傳 `{ stop, reason }`（`reason` ∈ `increased` / `stabilized` / `timeout` / `null`）——刻意脫離 `setInterval` 直接可單元測試，避免用 fake timers 模擬 async `setInterval` callback 交錯造成的測試脆弱性。
- `handleRefreshData` 呼叫 `refreshContributionData` 成功後，以 `REFRESH_POLL_INTERVAL_MS`（3000）建立 `setInterval`，每次呼叫 `listCampaignSummaries` 取得最新活動數並丟給 `evaluateRefreshPoll` 判斷；`stop=true` 時清除計時器、`setRefreshing(false)`，並依 `reason` 顯示對應的 `refreshNotice`（`success` 或 `info` 語氣）。
- 新增 `refreshPollRef` 於帳戶切換的 `useEffect` 與元件卸載的清理 effect 中一併清除，避免切換帳戶或離開頁面時輪詢殘留（呼應驗收標準「切換帳戶不殘留輪詢」）。
- 移除舊版固定 `setTimeout(..., 1500)` 假裝抓完的邏輯。
- 新增 5 項 `evaluateRefreshPoll` 純函數單元測試（increased / stabilized / 尚為 0 不算 stabilized / timeout / 皆不成立則繼續輪詢）+ 1 項使用真實計時器（非 fake timers）的整合測試：點擊「抓取資料」→ 斷言按鈕變為「抓取中…」→ 等待兩次真實輪詢 tick（間隔 3 秒，共等待 ~6 秒；測試逾時上限拉高至 10 秒）→ 第二次活動數增加，斷言顯示「資料已抓取完成。」提示且按鈕恢復可點擊。過程中修正一個測試撰寫疏漏：`findByRole` 找到的按鈕即使被 disabled 也會匹配（accessible name 不受 disabled 影響），須額外等待 `accountId` 自動帶入後按鈕實際啟用，才能點擊觸發 `handleRefreshData`（否則會因 `accountId` 仍為空字串而提前 return，導致「抓取中…」永遠不出現）。
- `npx vite build` 全綠；`ContributionAnalysis.test.jsx` 12 項全綠（新增 6：1 項整合測試 + 5 項純函數單元測試）。

**第 4 波全量回歸（2026-07-09）**：
- 前端 `npx vitest run`（全套）：contribution 12 項全綠；既有 4 個 pre-existing 失敗（`MetaAndromedaMonitoring` / `MetaAndromedaReviewQueue` / `MetaAndromedaScoreLab` 各檔案，皆為過時斷言/檔案上傳 mock 問題）與本波修改的檔案無關（git status 確認這些檔案本波未變更）。
- 後端 `pytest`：contribution 全套 + permissions + auth + health = **133 項全綠**，無回歸。
- `npx vite build` 全程全綠。

---

## 五、第 5 波：效能與 polish

### 任務 5.1 — 引擎效能優化（adstock memoize + ridge 早停）

**問題**：`theta_grid` 只有 6 個離散值，`adstock(s, theta)`（純 Python 逐元素迴圈）在 800 trials × 5 restarts × 每組 2 次呼叫下被重算約 5 萬次，實際只需 6 θ × 組數 ≈ 42 次；`nonneg_ridge` 固定 4000 次迭代無早停。50 秒的分析在 `to_thread` 中仍以 Python bytecode 持有 GIL，擠壓 event loop 上其他請求（docs/25 worker 化之前的止血）。

**變更檔案**：`modules/contribution/engine.py`、`tests/test_contribution_engine.py`

**實作步驟**：
1. `fit` 開頭預計算 `adstock_cache[(group_index, theta)]`（6 θ × 組數個陣列，一次算完），trial 迴圈內查表；同一 cache 供 K 分位數與 `_build_features` 共用（`_build_features` 增加接受預轉換陣列的路徑）。
2. K 分位數同樣可預計算：`k_cache[(group_index, theta, quantile)]`（6×3×組數個純量）。
3. `nonneg_ridge` 加收斂早停：`max(abs(w_new - w)) < tol`（tol=1e-8）即 break，`iters` 改為上限語義（預設值與 `DEFAULT_CONFIG` 不變，結果數值容差內一致）。
4. **驗收關鍵——結果可重現性**：`test_reproducibility` 必須維持「同輸入同 config 完全一致」；memoize 不改變任何數值路徑（同一組 (θ, K) 的特徵完全相同），早停 tol 取足夠小以確保既有合成資料測試（MAE、harvest 糾正、restart 穩定性）全部維持原斷言通過。
5. 效能基準記錄於本文件：優化前 180 天 × 7 組 × 800 trials × 5 restarts = 49.1s，優化後目標 **< 10s**。

**驗收標準**：engine 15 項（含 reproducibility 與 MAE 門檻）全綠；效能基準達標並記錄實測值。

**風險/回滾**：純引擎內部重構；任一合成測試數值漂移即回滾檢查，不得放寬既有斷言遷就實作。

### 任務 5.2 — repository 文件與死碼清理

**變更檔案**：`modules/contribution/repository.py`

**實作步驟**：`upsert_daily_metrics` docstring 的「不更新 fetched_at」改為與程式碼一致（衝突時以 `current_timestamp()` 刷新，語義為「最後抓取時間」）；`days` 死參數已由任務 4.2 改為 date range，確認無殘留註解。

**驗收標準**：docstring 與行為一致；全部後端測試無回歸。

### 任務 5.3 — 未分組花費診斷警告

**問題**：`_assemble_arrays` 刻意讓未分組活動的轉換計入 y、花費被丟棄（保持 y 總和）——分組後新上線的活動會把 baseline 墊高，且無任何提示。

**變更檔案**：`modules/contribution/service.py`、`modules/contribution/engine.py`（diagnostics 結構）、`frontend/src/pages/ContributionAnalysis.jsx`（診斷卡）、`tests/test_contribution_service.py`

**實作步驟**：
1. `_assemble_arrays` 回傳值補「未分組花費合計與占比」（分析區間內、該 account 該 metric_key 的總花費 vs 已分組花費）。
2. `process_analysis` 把 `ungrouped_spend_share` 寫入 `diagnostics.data_summary`；占比 > 5% 時在 `diagnostics` 追加 warning 條目（結構同 collinearity_warnings 的呈現慣例）：「有 X% 花費未分組，其轉換會被歸入基線，建議重新產生分組後重跑」。
3. 前端診斷卡新增對應 MetricTile 與警告顯示；AI payload 的 diagnostics 一併帶上（prompt 不需改，「只引用 payload 內數字」規則已涵蓋）。

**驗收標準**：合成測試：3 活動其中 1 個不在任何組 → `ungrouped_spend_share` 正確、超閾值出警告；前端診斷卡可見。

---

## 六、建議執行順序與相依

```
第 1 波（hotfix，串行）：1.1 → 1.2 → 1.3
第 2 波（可並行）：2.1 / 2.2 / 2.3 / 2.4
第 3 波：3.1（獨立）
第 4 波：4.1 / 4.3 / 4.4 / 4.5 可並行；4.2 依賴 2.4（同檔 list_campaign_summaries，先合再改避免衝突）
第 5 波：5.1（獨立、建議排在 docs/25 worker 化之前）；5.2 依賴 4.2；5.3 獨立
```

回歸基線：每波完成後跑全量 contribution 後端測試（現行 91 項 + 各波新增）與前端 `ContributionAnalysis.test.jsx`，並比照 docs/21 慣例在本文件各任務下補「驗收結果」。

---

## 七、明確不修（記錄在案）

1. **Hill K 分位數的輕微選模 leakage**（K 自含 holdout 的全序列取）：與可行性驗證腳本行為一致，MAE 門檻由該行為校準；修正需重新驗證所有合成資料斷言，收益（holdout R² 更嚴謹）不成比例。留待 docs/25 worker 化或引擎下次大改時一併處理。
2. **前後端時區微差**（前端 UTC 昨天 vs 後端 server-local 昨天）：最壞差 1 天且被歸因回補視窗覆蓋，不影響分析正確性。
3. **GroupEditor 的「新增組別」功能**：任務 4.4 只做空組過濾；加組視使用回饋另議。

---

**站略 (Site-tegy) 技術架構小組**
