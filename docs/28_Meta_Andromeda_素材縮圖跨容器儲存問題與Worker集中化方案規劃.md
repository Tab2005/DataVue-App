# 28. Meta Andromeda 素材縮圖跨容器儲存問題與 Worker 集中化方案規劃

- **日期**：2026-07-10
- **性質**：事故記錄 + 架構規劃（暫時修法已實作，完整方案待評估是否動工）
- **狀態**：暫時修法（方案 C）已完成，未 commit；完整方案（方案 D）僅規劃，未核准動工
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

### 3.2 具體要動的兩塊

**(a) 寫入面：手動上傳也要落到 worker 的硬碟**

`POST /assets:upload` 目前是 backend 收到 HTTP 請求、在同一個 process 內直接寫檔。要讓檔案落在 worker，backend 收到上傳請求後不能自己寫，需要把檔案內容轉發給 worker——可以仿照現有「成效分析匯入」已經在用的 DB-backed queue 模式（docs/25 §1.3 提到的既有基礎設施），或直接開一個 worker 內部專用的寫入端點，由 backend 用 Zeabur 內部網路呼叫。

**(b) 讀取面：縮圖/下載端點要能拿到 worker 硬碟上的檔案**

`worker_main.py` 目前刻意不掛業務路由（docs/24 的設計原則）。要滿足讀取需求，兩個做法擇一：

1. 在 worker 上新增一個**範圍很小的內部專用讀檔端點**（例如 `GET /internal/assets/raw?key=...`），backend 的 `/assets/preview`、`/assets/download` 改成：本地找不到檔案時，透過 Zeabur 內部網路（`*.zeabur.internal`，跟現在 DB/Redis 連線用的機制一樣）轉發請求給 worker，取回內容再回傳給瀏覽器。
2. 或者乾脆全部檔案讀寫都固定由 worker 處理，backend 的兩個端點永遠內部轉發給 worker，不再自己碰本地硬碟。

做法 1 影響面較小（backend 仍是唯一對外服務，worker 新增的端點只服務內部流量），是比較保守、建議優先評估的做法。

### 3.3 影響範圍與風險

- 會動到目前穩定運作的手動上傳路徑（Score Lab 上傳），需要完整迴歸測試
- worker 新增業務端點，跟 docs/24「worker 不掛業務路由」的原始設計原則有出入，需要明確記錄例外理由（僅限內部流量、範圍極小）
- 兩個 process 之間多一次網路呼叫，縮圖載入延遲會略增（本地檔案系統讀取 vs. 內部網路 + 檔案系統讀取）

### 3.4 觸發條件（比照 docs/25 §四的風格，先不做，除非）

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
