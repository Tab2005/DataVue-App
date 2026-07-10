# 28. Meta Andromeda 素材縮圖跨容器儲存問題與 Worker 集中化方案規劃

- **日期**：2026-07-10
- **性質**：事故記錄 + 架構規劃（暫時修法已實作，完整方案待評估是否動工）
- **狀態**：暫時修法（方案 C）已完成，未 commit；完整方案（方案 D）已完成 D1-D4 程式實作，待部署驗證與後續 commit
- **依據**：
  - docs/24（Andromeda 評分管線拆出 `meta-andromeda-worker` process，Wave 2 把觀測匯入負載一併搬去 worker）
  - docs/25（背景工作負載統一 Worker 架構規劃，本文件延續其「web 永遠不跑重活、worker 集中背景負載」的分工原則）
  - docs/10（Zeabur 部署與持久化儲存設定指南，已提及「Worker 也需要跟 Web 掛同一個 Volume」的風險但未強制檢查）
  - 2026-07-10：使用者回報「用成效分析匯入素材評分，評估紀錄縮圖無法正常呈現」，順藤摸瓜查到的儲存架構缺口

---

## 零、結論摘要

**縮圖壞掉的根因：`backend` 與 `meta-andromeda-worker` 是兩個獨立 Zeabur 服務，各自掛載各自獨立配置的 Volume（兩個不同的 Kubernetes PVC），儘管容器內路徑字串相同（`/app/backend/storage`），實體上是兩顆互不相通的硬碟。**

- 「成效分析匯入」的素材下載/寫檔在 **worker** process 執行（docs/24 Wave 2 的既定設計）
- 縮圖顯示是瀏覽器打 **backend** 的 `/api/meta-andromeda/assets/preview`，backend 只讀自己那顆硬碟
- 兩邊互相看不到對方寫的檔案 → worker 寫的檔案，backend 讀不到 → 404 → 縮圖空白

手動上傳（Score Lab 上傳）目前正常，是因為寫檔跟讀檔剛好都在 backend 同一個 process 內，不是因為這個問題不存在，只是還沒被踩到。

已經先做了一個**零新增基礎設施**的暫時修法（見第二節方案 C），解決眼前的縮圖顯示問題，不影響評分正確性。完整解法（第三節方案 D：把讀寫都集中到 worker）工程量較大、會動到目前穩定的上傳路徑，先寫規劃，不預設現在就要做。

---

## 一、現況盤點

### 1.1 這顆 Volume 是做什麼用的

查證結論：**在目前的實際部署上，這顆 Volume 100% 專門給 Meta Andromeda 素材用，沒有跟其他功能共用**。

- 全 `backend/` 程式碼裡，只有 `META_ANDROMEDA_STORAGE_ROOT`（`core/config.py`）這組設定會寫檔案到這個路徑下；報表、GA4、MMM、日誌等模組都沒有寫東西進去
- `docs/10` 有提到「若用 SQLite，資料庫檔案建議也放同一顆 Volume」，但本專案 `DATABASE_URL` 實際接的是獨立的 PostgreSQL 服務，不適用這個情境
- 硬碟上實際只有一個目錄樹：`meta_andromeda/uploads/<year>/<month>/<day>/asset_*`

### 1.2 兩個服務的角色分工（docs/24 既定設計）

```
backend（web，SERVICE_ROLE=web）
  - 對外 API + 前端縮圖代理（/assets/preview）
  - Score Lab 手動上傳（POST /assets:upload）——只有這裡有掛這條路由
  - 不執行 Andromeda 評分/觀測匯入的重負載（docs/24 的目的就是把這些搬走）

meta-andromeda-worker（worker，SERVICE_ROLE=worker）
  - 只掛 /healthz，完全沒有業務路由（worker_main.py 自己的 docstring 明講）
  - 業務都在 AsyncIOScheduler 排程 job 裡執行：
    - 評分 stream consumer（實際 AI 評分呼叫）
    - 成效分析匯入（下載 Facebook 素材、寫入 storage_adapter）
```

### 1.3 現場證據（2026-07-10 直接查證，唯讀操作）

用 `service exec` 進兩個容器比對：

| | backend | meta-andromeda-worker |
|---|---|---|
| 儲存路徑檔案數 | 4,544 個 | 59 個 |
| 目錄建立時間 | 2026-06-22 | 2026-07-07（同 worker 服務建立日） |
| `findmnt` 底層 PVC | `pvc-37a89347-...date-service-695f487ce2d178cb4f47605b` | `pvc-008be02c-...date-service-6a4cb7d6721fddff77e831e7` |

兩個 PVC ID 完全不同，且各自的名稱裡都嵌了自己的 `service-<id>`——證實 Zeabur 是「每個服務各自配一顆磁碟」，容器內路徑字串相同不代表底層儲存相同。

### 1.4 為什麼「只把上傳也搬去 worker」不能解決問題

這是最初考慮過、後來排除的做法，記錄排除理由：

若只把「寫入」（Score Lab 上傳）搬去 worker，不動「讀取」（縮圖代理），結果會是：

| 情境 | 現況 | 只搬上傳去 worker 之後 |
|---|---|---|
| 手動上傳 | backend 寫、backend 讀 ✅ 正常 | **worker 寫、backend 讀 ❌ 變壞** |
| 成效分析匯入 | worker 寫、backend 讀 ❌ 壞 | worker 寫、backend 讀 ❌ 還是壞 |

等於把原本穩定的手動上傳也拖下水。**要解決必須寫跟讀同時搬，缺一不可**（見第三節方案 D）。

---

## 二、已實作的暫時修法（方案 C）——零新增基礎設施

### 2.1 做法

「成效分析匯入」流程下載 Facebook 素材時，原始 CDN 網址其實有存下來，只是存在 `MetaAndromedaObservedCreative.media_url` 欄位，從未接到縮圖顯示用的 `MetaAndromedaScoreEvent.preview_url`（一直是 `None` 的死欄位）。

把「評估紀錄」列表 + 明細兩個 API，改成：**本地 `preview_url` 是空的話，退回用 `ObservedCreative.media_url`**。前端 `resolvePreviewUrl()`（`MetaAndromedaReviewQueue.jsx`）本來就支援直接吃 `http` 開頭的網址，不用改前端。

### 2.2 改動檔案

- `backend/modules/meta_andromeda/repository.py`：
  - `list_review_queue()`：批次查詢 `ObservedCreative.media_url`，補進 `preview_url_map`（跟既有的 `ad_name_map`同一套批次查詢模式，避免 N+1）
  - `get_review_queue_detail()`：在既有的 `obs` 查詢（cal_item 路徑 + 直連 `request_context.observed_creative_id` 路徑）後補一行 fallback
- `backend/tests/test_meta_andromeda_module.py`：新增 `test_meta_andromeda_review_queue_falls_back_to_observed_media_url_for_preview`，涵蓋 list + detail 兩個端點

### 2.3 已知限制

- Facebook CDN 網址理論上可能過期失效（通常是廣告下架很久之後），屆時縮圖可能又會壞——但範圍遠小於「現在 100% 都壞」
- **跟評分正確性完全無關**：AI 評分請求一律是 worker 讀自己本地那份副本轉 base64（已查證 `runtime.py::_prepare_asset_context`/`_build_multimodal_user_content` 不會走公開網址這條路），這條修法完全沒有動到評分邏輯

### 2.4 狀態

程式碼已寫完、單元測試已通過（`test_meta_andromeda_module.py` 71 passed，跟既有的 16 個環境問題無關失敗數一致），**尚未 commit**，待使用者確認後自行處理。

---

## 三、完整方案（方案 D）——寫讀都集中到 worker

若未來 Facebook CDN 網址失效的問題浮現、或想徹底移除「本地檔案跟哪個容器有關」這個心智負擔，可以考慮把 Meta Andromeda 的檔案儲存整個收斂到單一 process（worker），backend 完全不再落地寫檔案。

### 3.1 為什麼不能只搬一半（回顧 1.4）

寫跟讀必須同時搬去同一個 process，理由已在 1.4 說明。

### 3.2 推薦收斂方向（本文件建議採用）

方案 D 雖然有兩條可行路徑，但**推薦明確收斂成「backend 保持唯一對外入口，worker 成為唯一檔案持有者，web 只做內部轉發」**，不建議把手動上傳也做成 DB queue。

理由：

- `Score Lab` 手動上傳是互動式流程；前端目前預期 `POST /assets:upload` 立即回傳 `asset_uri`，接著才能直接送出評分
- 若改成 DB queue，上傳就會從同步流程變成「accepted -> 輪詢等待 asset 建立完成 -> 才能送評分」，不只動到 backend，前端流程也要重寫
- 觀測匯入本來就是背景工作，適合 queue；手動上傳不是背景工作，硬套 queue 只會提高不必要的複雜度
- 因此在方案 D 下，**寫入面與讀取面都走 backend -> worker 內部 HTTP 轉發**，是影響面最小、最符合現有互動模型的做法

### 3.3 具體要動的兩塊

**(a) 寫入面：手動上傳也要落到 worker 的硬碟**

`POST /assets:upload` 目前是 backend 收到 HTTP 請求、在同一個 process 內直接寫檔。方案 D 下，backend 仍保留這條對外 API，但職責改成：

1. 收檔、做基本 request 驗證與權限檢查
2. 把檔案內容轉發給 worker 內部端點
3. 由 worker 實際呼叫 `MetaAndromedaService.upload_asset()` / `storage_adapter.store_asset()` 寫入自己的 Volume
4. worker 回傳既有 `AssetUploadResponse` payload，backend 原樣回給前端

這樣 `Score Lab` 前端完全不用改互動模型，仍然是同步拿到 `asset_uri` 後立刻可送評分。

**(b) 讀取面：縮圖/下載端點要能拿到 worker 硬碟上的檔案**

`worker_main.py` 目前刻意不掛業務路由（docs/24 的設計原則）。要滿足讀取需求，理論上有兩種做法：

1. 在 worker 上新增一個**範圍很小的內部專用讀檔端點**（例如 `GET /internal/assets/raw?key=...`），backend 的 `/assets/preview`、`/assets/download` 改成：本地找不到檔案時，透過 Zeabur 內部網路（`*.zeabur.internal`，跟現在 DB/Redis 連線用的機制一樣）轉發請求給 worker，取回內容再回傳給瀏覽器。
2. 或者乾脆全部檔案讀寫都固定由 worker 處理，backend 的兩個端點永遠內部轉發給 worker，不再自己碰本地硬碟。

若目標是**徹底移除「backend 本地硬碟是否有檔」這個心智負擔**，則方案 D 應進一步採用做法 2 的精神：

- backend 的 `/assets/preview` 對外路由保留
- 但在 `filesystem` backend 下，實際檔案內容一律由 worker 端點提供
- backend 不再自己直讀本地 `META_ANDROMEDA_STORAGE_ROOT`

換句話說，對外介面還是 backend；真正持有檔案的一律只有 worker。

### 3.4 內部 API 合約草案

為避免後續實作時又回頭討論路由長相，先把建議合約固定下來。

**(a) Worker 內部寫入端點**

- `POST /internal/meta-andromeda/assets`
- 用途：供 backend 轉發手動上傳檔案，由 worker 實際寫檔與建立 asset DB record
- request：
  - `multipart/form-data`
  - 欄位：
    - `asset_type`
    - `source_filename`
    - `file`
    - `uploaded_by`（可選；backend 解析完當前使用者後往內傳）
    - `content_type`（可選；若 multipart 本身已有檔案 MIME，可不另傳）
- response：
  - 與現行 `AssetUploadResponse` 一致，避免 backend 還要做 payload 轉換

**(b) Worker 內部讀檔端點**

- `GET /internal/meta-andromeda/assets/raw?uri=...`
- 用途：供 backend 讀取 worker Volume 上的原始素材內容，再回傳給瀏覽器
- request：
  - query string 至少帶 `uri`
  - 不建議直接接受任意絕對路徑；以 `asset_uri` 或 `storage_key` 為查找主鍵較安全
- response：
  - 成功：直接回原始檔案 stream
  - header 至少包含：
    - `Content-Type`
    - `Content-Length`（若可得）
    - `X-Meta-Andromeda-Storage-Key`（可選，利於 debug）
  - 失敗：
    - `404`：asset record 不存在或 worker 本地實體檔案不存在
    - `403`：path traversal / 非法 key
    - `401`：內部認證失敗

**(c) Backend 對外端點維持不變**

- `POST /api/meta-andromeda/assets:upload`
- `GET /api/meta-andromeda/assets/preview?uri=...`

前端與外部呼叫端不需要因方案 D 改任何 API。

### 3.5 驗證與安全模型

worker 新增內部端點不代表可以放棄驗證；只是驗證邊界從「公開使用者」變成「內網 caller（backend）」。

建議：

- **只接受 Zeabur 內網 URL 呼叫**：例如 `http://meta-andromeda-worker.zeabur.internal:<port>`
- backend 呼叫 worker 時，附帶固定的 internal auth header
- 認證機制直接復用現有 Meta Andromeda external worker callback 那套概念，避免平行長出第二套安全模型：
  - 優先用 shared secret 簽章
  - 次選固定 bearer token
- worker 端點收到請求後，先驗簽 / 驗 token，再做任何讀寫動作
- 讀檔端點一律禁止 caller 直接指定絕對檔案路徑；必須先查 DB asset record，再把 `storage_key` 拼回 worker 本地 storage root，並做 `resolve()` + `relative_to()` 檢查

這樣可最大限度重用現有設定概念與程式碼，避免把「內部素材代理」再做成另一套難維護的安全分支。

### 3.6 設定項規劃

方案 D 不需要新增基礎設施，但需要補幾個環境變數來描述 worker 內網位址與驗證資訊。

建議新增：

- `META_ANDROMEDA_INTERNAL_WORKER_BASE_URL`
  - 例如 `http://meta-andromeda-worker.zeabur.internal`
  - backend 用來呼叫 worker 內部素材 API
- `META_ANDROMEDA_INTERNAL_WORKER_TIMEOUT_SECONDS`
  - backend 轉發 worker 時的 timeout
- `META_ANDROMEDA_INTERNAL_WORKER_SHARED_SECRET`
  - 若採 HMAC 驗證
- `META_ANDROMEDA_INTERNAL_WORKER_TOKEN`
  - 若採固定 token 驗證

命名上刻意沿用現有 `EXTERNAL_WORKER_*` / `EXTERNAL_QUEUE_*` 風格，避免未來看設定時一眼分不出用途。

### 3.7 程式分工藍圖

建議不要把全部邏輯直接塞進現有 router；實作時至少分成下面幾塊：

**(a) backend 端**

- 保留現有對外路由：
  - `/assets:upload`
  - `/assets/preview`
- 新增一個「worker 內部素材 gateway」小模組，專責：
  - 發送 upload 轉發請求
  - 發送 raw file 讀取請求
  - 產生 internal auth header
  - 把 worker 失敗轉成適合對外 API 的錯誤

**(b) worker 端**

- 在 `worker_main.py` 額外掛一個極小的 internal router
- 這個 router 只處理：
  - 素材寫入
  - 素材讀取
- 不承接 review queue、score、release、monitoring 等任何對外業務 API

**(c) 共用邏輯**

- `MetaAndromedaService.upload_asset()` 仍作為唯一的寫入業務實作
- 讀檔時若目前 router 內有 MIME 推斷 / `FileResponse` 組裝邏輯，應抽到共用 helper，避免 backend / worker 各寫一份不一致版本

### 3.8 建議 rollout 順序

方案 D 會碰到目前穩定的手動上傳路徑，因此不應一次全改；建議分階段推進。

| Phase | 內容 | 目的 |
|---|---|---|
| D1 | 先補 worker internal read endpoint，backend preview 改成可轉發 | 先驗證 web -> worker 內網讀檔穩定 |
| D2 | 再補 worker internal upload endpoint，backend upload 改成同步轉發 | 切掉 web 本地寫檔 |
| D3 | 清掉 backend 直接讀 `META_ANDROMEDA_STORAGE_ROOT` 的 filesystem 分支 | 讓 worker 成為唯一檔案持有者 |
| D4 | 補文件、監控、部署檢查 | 防止日後配置 drift |

若要更保守，D1 可以先做成 feature flag，確認 Zeabur 內網轉發穩定後再切到 D2。

### 3.9 測試計畫

這個方案最怕「功能看起來沒壞，但其實只在單機開發模式能跑」，因此測試要覆蓋角色分流與內部轉發。

至少需要：

- backend router 測試
  - `/assets:upload` 會正確把 multipart 轉發給 worker
  - `/assets/preview` 會正確代理 worker stream
  - worker 回 `404/401/500` 時，backend 對外行為符合預期
- worker internal router 測試
  - 未帶 token / 簽章時拒絕
  - 非法 `uri` / 非法 `storage_key` 時拒絕
  - 合法素材可正確回傳 MIME 與檔案內容
- integration 測試
  - 手動上傳 -> 送分 -> review queue 可預覽
  - 成效分析匯入 -> review queue 可預覽
  - `SERVICE_ROLE=web` 與 `SERVICE_ROLE=worker` 分工下都不會意外回退到 web 本地寫檔

### 3.10 影響範圍與風險

- 會動到目前穩定運作的手動上傳路徑（Score Lab 上傳），需要完整迴歸測試
- worker 新增業務端點，跟 docs/24「worker 不掛業務路由」的原始設計原則有出入，需要明確記錄例外理由（僅限內部流量、範圍極小）
- 兩個 process 之間多一次網路呼叫，縮圖載入延遲會略增（本地檔案系統讀取 vs. 內部網路 + 檔案系統讀取）
- backend 若只做「本地找不到才 fallback worker」，會留下雙路徑行為，後續排查困難；**方案 D 應避免半套切換**
- 內部 worker URL / token 若配置漂移，會直接讓手動上傳與縮圖同時失效，因此部署檢查與 health 訊息要一併補上

### 3.11 非推薦分支（記錄為何不採用）

避免之後重複回頭討論，先把幾條不推薦路徑寫死：

- **不把手動上傳改成 DB queue 主流程**：
  - 會破壞 `Score Lab` 目前同步拿 `asset_uri` 的互動模型
  - 需要前端額外輪詢或狀態機，複雜度高於收益
- **不採 backend 本地先讀、找不到再轉發的長期架構**：
  - 這只適合作為短期過渡，不適合作為方案 D 最終形態
  - 最終形態應明確只有 worker 碰 filesystem
- **不把 worker 擴成第二個對外 API 面**：
  - worker 的素材端點只服務內部流量
  - 對外公開入口仍應維持 backend 單一邊界

### 3.12 D4 實際補齊項目（2026-07-10）

方案 D 的最後一階段不是再加功能，而是把「沒配好環境時要能被看見」這件事補齊，避免上線後只剩 404/502 現象卻沒有明確檢查面。

已補齊：

- Web `runtime-health` 現在會在 `filesystem + SERVICE_ROLE=web` 時明確回報：
  - `checks.storage.mode == "worker_remote"`
  - `checks.internal_asset_worker.base_url`
  - `checks.internal_asset_worker.auth_configured`
- Worker `/healthz` 現在會回報 `internal_asset_worker.auth_configured`、`storage_backend`、`storage_root`
- `SERVICE_ROLE=all`（單機 / 本地未拆分）保留相容路徑：
  - upload 仍可直接本地寫檔
  - preview 仍可直接本地讀檔
  - 不要求一定要配置 internal worker base URL
- Zeabur 部署文件已更新為：
  - `filesystem` 拆分模式下，素材 Volume 掛在 worker，不再要求 web 也掛同一顆素材 Volume
  - Web/Worker 兩邊都必須配置同一組 internal worker auth
  - 部署後要檢查 Web `runtime-health` 與 Worker `/healthz`

這代表方案 D 到 D4 為止，已經不只是「功能能跑」，而是「配置錯了也能被健康檢查直接指出來」。

### 3.13 觸發條件（比照 docs/25 §四的風格，先不做，除非）

| # | 觸發條件 |
|---|---|
| T1 | 方案 C 的 Facebook CDN 網址在實務上真的開始出現大量過期失效（縮圖重新變空白） |
| T2 | 有其他需求也需要「backend 讀 worker 寫的檔案」（例如週報要嵌入素材縮圖），方案 C 的個案修法無法覆蓋 |
| T3 | 決定要把 filesystem 儲存後端整個換掉（例如評估改用 S3 相容物件儲存），屆時方案 D 可以直接被物件儲存取代，不需要额外做 worker 內部代理

任一成立才評估動工；目前（2026-07-10）三項皆未成立，方案 C 已足夠覆蓋回報的問題。

---

## 四、Non-goals（本次不做的事，避免之後重複討論）

- **不引入 S3 相容物件儲存**：使用者明確希望先留在 Zeabur 原生方案內解決，方案 D 若未來真的要做，物件儲存仍是備案而非本次規劃範圍
- **不嘗試讓兩個服務掛同一顆 Volume**：Zeabur 底層 Kubernetes 的 Volume 預設是 ReadWriteOnce，同一時間只能被一個運行中的 Pod 掛載，backend 與 worker 是兩個同時在跑的獨立 Pod，這條路風險高、且不確定目前方案是否支援，已排除
