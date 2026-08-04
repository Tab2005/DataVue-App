# 16 Zeabur 部署與持久化儲存設定指南

## 目的

本指南詳細說明如何將 **DataVue Analytics** 系統部署至 [Zeabur](https://zeabur.com/) 雲端平台，並重點介紹新增的 **Meta Andromeda 儲存持久化掛載 (Volume Mount)** 機制之設定方式。

本系統已針對 Zeabur 的容器化與多服務架構進行優化，支援自動化部署、PostgreSQL/SQLite 持久化、以及獨立的背景排程 Worker 運作。

---

## 🏗️ 系統服務架構

在 Zeabur 上，建議將系統拆分為以下服務：
1. **PostgreSQL** 或 **SQLite** (持久化 Volume 掛載)：資料庫。
2. **Backend (API Server)**：處理前端請求與核心邏輯。
3. **Scheduler Worker**：專門負責週報自動化生成的背景程序（確保服務重啟時不漏掉任務）。
4. **Frontend**：靜態網站託管 (Static Hosting)。

---

## 🛠️ 第一階段：資料庫與儲存持久化設定

### 方案 A：Zeabur 持久化磁碟掛載 (本地儲存，推薦)
適用於不需要額外付費購買 S3 雲端儲存的場景。本方案將廣告圖片/影片快照與 SQLite 資料庫一同存放在 Zeabur 的持久化磁碟中。

#### 1. 建立 Volume
1. 若採 **`SERVICE_ROLE=worker` + `SERVICE_ROLE=web` 拆分部署**，請進入 Zeabur 控制台的 **Meta Andromeda Worker 服務**（不是 Web API 服務）。
2. 前往 **「儲存 (Volumes)」** 分頁，點擊 **「新增儲存區 (Add Volume)」**。
3. 將掛載路徑 (Mount Path) 設定為：`/app/backend/storage`。
4. **只有在 `SERVICE_ROLE=all` 的單機/未拆分模式下，這顆 Volume 才需要掛在同一個 API 服務上。** 若已拆成 web + worker，Meta Andromeda 素材檔案的唯一持有者應是 worker，不應再要求 web service 也掛同一顆素材 Volume。

#### 2. 設定環境變數
切換到 **「變數 (Variables)」** 分頁，配置以下持久化變數：
```bash
# 指定使用本地 filesystem
META_ANDROMEDA_STORAGE_BACKEND=filesystem
# 將素材落檔根目錄指向掛載點
META_ANDROMEDA_STORAGE_ROOT=/app/backend/storage/meta_andromeda
# 若使用 SQLite，需將資料庫檔案一併指向掛載點（極度重要，防止重新部署後資料被清空）
DATABASE_URL=sqlite:////app/backend/storage/facebook_dashboard.db
```

---

### 方案 B：S3 相容物件儲存 (雲端儲存)
適用於多後端節點水平擴充，或希望靜態檔案透過獨立 CDN 加速的生產場景。

#### 1. 儲存桶準備
* 在 AWS S3、Cloudflare R2 等平台建立 BUCKET（如 `datavue-assets`）。
* 設定 CORS 政策，允許您的前端網域（如 `https://datavue-dev-saas.sitetegy.com`）跨域存取。

#### 2. Zeabur 環境變數設定
在後端服務的 **「變數 (Variables)」** 分頁配置：
```bash
META_ANDROMEDA_STORAGE_BACKEND=s3_compatible
META_ANDROMEDA_STORAGE_S3_BUCKET=datavue-assets
META_ANDROMEDA_STORAGE_S3_REGION=ap-northeast-1
META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID=YOUR_S3_ACCESS_KEY
META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY=YOUR_S3_SECRET_ACCESS_KEY
# 非 AWS S3（如 Cloudflare R2 / MinIO）需指定自訂 Endpoint URL
META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
# 設定公開 CDN 或 Base URL 供前端讀取素材圖片
META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL=https://assets.sitetegy.com/meta-andromeda
```

---

## 🐍 第二階段：後端與排程服務部署

### 2.1 基礎設定
1. 選擇 Git 儲存庫，並將 **Root Directory** 設為 `backend`。
2. **API Server (Web 服務)**:
   * Port 改為 `8000`。
   * 環境變數 `ENABLE_REPORT_SCHEDULER` 設為 `false`。
3. **Scheduler Worker (排程背景服務)**:
   * 新增另一個服務，Root Directory 同樣是 `backend`。
   * **Start Command** 改為 `python scheduler_worker.py`。
   * 環境變數 `ENABLE_REPORT_SCHEDULER` 設為 `true`。

### 2.2 核心環境變數對照表
請在 Zeabur 後端與 Worker 的 Variables 頁面配置以下項目：

| 變數名稱 | 說明 | 範例/來源 |
| :--- | :--- | :--- |
| `DATABASE_URL` | 資料庫連線字串 | PostgreSQL 內網地址 或 方案 A 的本地掛載路徑 |
| `ENCRYPTION_KEY` | Fernet 安全加密金鑰 | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GOOGLE_CLIENT_ID` | Google OAuth ID | Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | Google Client Secret | Google Cloud Console (GSC 整合必填) |
| `SUPER_ADMIN_EMAIL` | 最高管理員帳號 | `admin@example.com` (多個以逗號分隔) |
| `GOOGLE_AI_API_KEY` | Gemini API Key | Google AI Studio (用於週報 AI 摘要) |
| `ALLOWED_ORIGINS` | 允許的前端來源 | `https://datavue-dev-saas.sitetegy.com` |
| `ENV` | 執行環境 | `production` |

### 2.3 Meta Andromeda 模組專屬環境變數對照表
為使 Meta Andromeda 廣告評估與漂移診斷模組正常運作，請在後端及背景服務中配置以下環境變數：

| 變數名稱 | 說明 | 預設值 / 範例 |
| :--- | :--- | :--- |
| `META_ANDROMEDA_STORAGE_BACKEND` | 素材儲存後端，可選 `filesystem` 或 `s3_compatible` | `filesystem` |
| `META_ANDROMEDA_STORAGE_ROOT` | 本地素材落檔根目錄，必須指向持久化磁碟掛載路徑 | `/app/backend/storage/meta_andromeda` |
| `META_ANDROMEDA_INTERNAL_WORKER_BASE_URL` | Web 服務呼叫 worker 內部素材 API 的 Zeabur 內網位址；**`SERVICE_ROLE=web` 且 `filesystem` 時必填** | `http://meta-andromeda-worker.zeabur.internal` |
| `META_ANDROMEDA_INTERNAL_WORKER_TIMEOUT_SECONDS` | Web 服務轉發素材讀寫到 worker 的 timeout | `10` |
| `META_ANDROMEDA_INTERNAL_WORKER_SHARED_SECRET` | 內部素材 API 的 HMAC 驗證 secret；與 token 二選一，建議優先使用 | `replace-me` |
| `META_ANDROMEDA_INTERNAL_WORKER_TOKEN` | 內部素材 API 的固定 token；與 shared secret 二選一 | `replace-me` |
| `META_ANDROMEDA_SCORING_PROVIDER` | 評分模組運行者。**生產環境必須設為 `openrouter`**，否則強制走啟發式備用，AI 評分永遠不執行。`auto` 模式需同時設定 `META_ANDROMEDA_SCORING_MODEL` 才會走 AI。本地開發可設 `heuristic` 避免消耗 API 額度。 | `openrouter` |
| `META_ANDROMEDA_SCORING_MODEL` | 評分使用的 OpenRouter 模型 ID | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` |
| `META_ANDROMEDA_SCORING_ALLOW_FALLBACK` | AI 呼叫失敗時是否自動降級為啟發式備用 | `true` |
| `META_ANDROMEDA_QUEUE_HOST` | 自動評分事件佇列。**若採用 2.4 節的獨立 Meta Andromeda Worker，Web 與 Worker 服務都必須明確設為 `redis_stream`**（見 2.4 節說明），否則預設 `auto` 在未拆分 Worker 時才適用 | `auto` / 拆分後建議 `redis_stream` |
| `META_ANDROMEDA_STORAGE_S3_BUCKET` | S3 儲存桶名稱 (方案 B) | `datavue-assets` |
| `META_ANDROMEDA_STORAGE_S3_ACCESS_KEY_ID` | S3 連線 Key ID (方案 B) | `YOUR_S3_ACCESS_KEY` |
| `META_ANDROMEDA_STORAGE_S3_SECRET_ACCESS_KEY` | S3 連線 Secret (方案 B) | `YOUR_S3_SECRET_ACCESS_KEY` |
| `META_ANDROMEDA_STORAGE_S3_ENDPOINT_URL` | 非 AWS S3 (如 Cloudflare R2) 需指定自訂端點 (方案 B) | `https://<account_id>.r2.cloudflarestorage.com` |
| `META_ANDROMEDA_STORAGE_PUBLIC_BASE_URL` | 靜態資源公開讀取 Base URL (方案 B) | `https://assets.sitetegy.com/meta-andromeda` |

---

### 2.4 Meta Andromeda 獨立 Worker（docs/24 Wave 2，選配但生產環境強烈建議）

**背景**：Meta Andromeda 的素材評分與觀測匯入若跟 API 服務同一個 process，評分期間的 DB/檔案/ffmpeg 等阻塞工作會佔用 event loop，導致整站 API（含權限檢查）在批次評分時全部卡住無回應（根因與修復過程見 [docs/24](file:///C:/Users/BWM2/Documents/python/DataVue-App/docs/24_Meta_Andromeda_評分管線Event_Loop阻塞修復與模組優化實作計劃.md)）。Wave 1 已用 `asyncio.to_thread` 止血，讓同 process 運行也不會卡死；本節的獨立 Worker 是進一步的架構隔離，讓評分負載完全離開 API 服務。

> [!IMPORTANT]
> 這個「Meta Andromeda Worker」跟 2.1 節既有的「Scheduler Worker」（`scheduler_worker.py`）是**兩個不同的東西**，靠兩個獨立的環境變數切換，彼此不互斥：
> - `ENABLE_REPORT_SCHEDULER`：控制**週報**排程要不要在這個服務跑。
> - `SERVICE_ROLE`：控制**Meta Andromeda 評分/匯入**排程要不要在這個服務跑。
>
> 兩者同時存在時完全獨立生效——例如 Meta Andromeda Worker 服務可以同時設定 `SERVICE_ROLE=worker` 且 `ENABLE_REPORT_SCHEDULER=false`（不跑週報，只跑評分），也可以視資源需求合併到既有的 Scheduler Worker 服務上（`ENABLE_REPORT_SCHEDULER=true` + `SERVICE_ROLE=worker`）。**唯一不能做的是把 Meta Andromeda Worker 服務的 `ENABLE_REPORT_SCHEDULER` 設為 `false` 又不知道這個變數其實是「整個 APScheduler 排程器」的總開關**——若設為 `false`，週報跑不動也就算了，但 Meta Andromeda 的 stream consumer/reclaim/db queue sweeper 全部一起停擺，評分事件會卡在 queued 狀態永遠不會被處理。這個服務至少要有一項排程需求（週報或 Meta Andromeda）時，`ENABLE_REPORT_SCHEDULER` 就必須是 `true`。

#### 2.4.1 新增服務

1. 新增一個服務，Root Directory 同樣是 `backend`，與 API 服務共用同一個 repo/image。
2. **Start Command** 改為 `python worker_main.py`。
3. 若 Meta Andromeda 素材走 `filesystem` 方案，**這個 Worker 服務必須掛載素材 Volume**；若走 `s3_compatible` 方案則不需要。方案 D 完成後，素材上傳與預覽都經由 worker 內部代理，worker 是唯一需要碰實體素材檔案的服務。
4. Port 設定與健康檢查路徑改為 `/healthz`（不是 `/health`——這支程式沒有掛業務 router，僅有這一個端點）。

#### 2.4.2 環境變數對照表

| 變數名稱 | Web (API) 服務 | Meta Andromeda Worker 服務 | 說明 |
| :--- | :--- | :--- | :--- |
| `SERVICE_ROLE` | `web` | `worker` | 未設定時預設 `all`（單機開發行為，不拆分） |
| `META_ANDROMEDA_INTERNAL_WORKER_BASE_URL` | **必填**（若 Web 採 `filesystem`） | 可不填 | Web 用來呼叫 Worker 的 `/internal/meta-andromeda/assets*`；建議填 Zeabur 內網 URL |
| `META_ANDROMEDA_INTERNAL_WORKER_SHARED_SECRET` 或 `META_ANDROMEDA_INTERNAL_WORKER_TOKEN` | **必填其一** | **必填其一** | Web/Worker 兩邊必須一致，否則素材 upload / preview 會全部失敗 |
| `META_ANDROMEDA_QUEUE_HOST` | `redis_stream` | `redis_stream` | 兩邊都要設定；Web 端 `get_active_host()` 在 `SERVICE_ROLE=web` 下即使沒設也會自動收斂成 `redis_stream`/`database_queue`，但明確設定可避免混淆 |
| `ENABLE_REPORT_SCHEDULER` | 依 2.1 節既有規劃 | **必須為 `true`**（見上方 IMPORTANT 提示） | 全域排程器總開關，不是週報專屬開關 |
| `REDIS_URL` | 必填 | 必填 | Zeabur 可直接加 Redis 服務並注入內網連線字串；兩邊必須連到同一個 Redis |
| 其餘 `DATABASE_URL`/`ENCRYPTION_KEY`/AI 金鑰等 | 依現有設定 | 與 Web 服務**完全相同** | Worker 需要能查詢/寫入同一個資料庫、解密同一批使用者 API 金鑰 |

#### 2.4.3 部署後驗證

1. 呼叫 Worker 服務的 `/healthz`，確認 `status: "ok"`、`scheduler.running: true`。
2. 在 Web 服務批次匯入素材，觀察 Web 服務的 CPU/記憶體用量應無評分負載痕跡（評分工作應只出現在 Worker 服務的資源圖表上）。
3. 批次匯入期間持續呼叫 Web 的 `/api/permissions/me/module/meta_andromeda`，回應時間應維持正常（不應卡住）。
4. 手動重啟或暫停 Worker 服務，確認 Web 服務仍可正常接受匯入/評分請求（事件會堆積在 Redis stream 或 DB，Worker 恢復後自動繼續消化，不會遺失）。
5. 呼叫 Web 服務的 `/api/meta-andromeda/runtime-health`，確認：
   - `checks.storage.mode == "worker_remote"`（`SERVICE_ROLE=web` + `filesystem`）
   - `checks.internal_asset_worker.base_url` 已填入 Zeabur 內網 URL
   - `checks.internal_asset_worker.auth_configured == true`
6. 呼叫 Worker 服務的 `/healthz`，確認 `internal_asset_worker.auth_configured == true`；若為 `filesystem`，`storage_root` 應指向實際掛載路徑。

#### 2.4.4 降級路徑

若暫時不想拆 Worker（例如流量小、先求簡單），不設定 `SERVICE_ROLE`（維持預設 `all`）即可，行為與拆分前完全一致——Wave 1 的 `asyncio.to_thread` 止血已確保這種單 process 模式不會卡住 event loop，只是評分負載仍會佔用 Web 服務的資源。

---

## 🌐 第三階段：前端部署

1. 建立服務，選擇您的 Git 儲存庫。
2. **Root Directory**: 設定為 `frontend`。
3. **Build Command**: `npm install && npm run build`。
4. **Output Directory**: `dist` (Vite 預設輸出)。
5. **環境變數 (Variables)**：
   - `VITE_API_URL`: 後端 API 的**公網網址** (不含末尾的 `/api`)。
   - `VITE_GOOGLE_CLIENT_ID`: 必須與後端一致。

---

## 🔄 第四階段：資料庫遷移 (Migrations)

部署完成後，請透過 Zeabur 的 **Console (控制台)** 連線至 API 後端服務，並執行：
```bash
alembic upgrade head
```
此步驟會在您的 PostgreSQL/SQLite 資料庫中，建立最新的 Meta Andromeda 評估表與 Lineage 表格。

---

## 🛡️ 常見問題與除錯 (Troubleshooting)

> [!TIP]
> **排程沒跑？**
> 可呼叫 `/health` 檢查 `checks.scheduler.running` 是否為 `true`。請確保 Web 服務與 Scheduler Worker 服務的 `ENABLE_REPORT_SCHEDULER` 變數互斥（一為 `false`，另一為 `true`），避免重複觸發。

> [!TIP]
> **拆分 Meta Andromeda Worker（2.4 節）後，評分事件一直卡在 `queued`？**
> 1. 確認 Worker 服務的 `SERVICE_ROLE=worker` 且 `ENABLE_REPORT_SCHEDULER=true`（兩者缺一都會導致 Meta Andromeda 排程完全沒註冊）。
> 2. 呼叫 Worker 服務的 `/healthz`，確認 `scheduler.running: true` 且 `redis: "ok"`。
2.5. 若素材上傳或縮圖同時失敗，優先檢查 Web 的 `/api/meta-andromeda/runtime-health`：`checks.internal_asset_worker.base_url` 是否存在、`auth_configured` 是否為 `true`。
> 3. 確認 Web 與 Worker 兩邊的 `REDIS_URL` 指向同一個 Redis 實例，且 `META_ANDROMEDA_QUEUE_HOST=redis_stream` 兩邊一致。
> 4. Redis 若暫時不可用，事件會落在 `database_queue` 模式（DB 裡 `status="queued"`），等 Worker 恢復連線後由 `sweep_meta_andromeda_queue`（預設每 5 秒掃一次）自動補派工，不需要手動介入。

> [!WARNING]
> **CORS 跨網域政策攔截？**
> * **檢查後端設定**：確保後端的 `ALLOWED_ORIGINS` 包含前端的完整網址，且不帶結尾斜線（如 `https://datavue-dev-saas.sitetegy.com`）。
> * **例外 CORS 保險**：後端已在 [main.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/main.py) 的 Exception Handlers 中實作 CORS 保修機制。如果後端拋出 500、403 等未捕獲錯誤，回傳回應仍會被加上正確的 CORS 標頭，以便於前端在 Console 印出正確的錯誤 JSON，而不是被 CORS 政策訊息遮蔽。

> [!IMPORTANT]
> **觀察事實素材下載與儲存失敗？**
> * **S3 權限或 Volume 權限**：檢查後端日誌是否有 `[Observation Import] Failed to download or store asset` 警告。
> * **容錯保護**：後端已在 [service.py](file:///C:/Users/BWM2/Documents/python/DataVue-App/backend/modules/meta_andromeda/service.py) 實作下載與 S3 寫入的 try-except 容錯。就算 S3 金鑰失效或本地儲存寫入失敗，廣告績效與文字數據依然能正常匯入，僅實體圖片會回退讀取 FB 的原始網址。

> [!CAUTION]
> **Meta Andromeda 批次評分全部走啟發式備用（AI 未執行）？**
>
> **最常見原因：`META_ANDROMEDA_SCORING_PROVIDER` 未在 Zeabur 設定，或設成 `heuristic`。**
>
> 本地 `.env` 預設為 `heuristic`（節省開發成本），但 Zeabur 若未覆寫此變數，部署後所有評分均會強制使用備用模式，與 OpenRouter API Key 是否設定無關。
>
> **第一步排查（環境設定）：**
> 1. Zeabur 後端服務 → Variables → 確認 `META_ANDROMEDA_SCORING_PROVIDER=openrouter`
> 2. 後台設定頁 → 輸入 OpenRouter API Key → 儲存 → 確認 Response 中 `has_openrouter_key: true`
> 3. 部署後可查看 Zeabur 日誌，搜尋 `generate_score_result` 行，確認 `DB Key present: True` 且 `provider_override: openrouter`
>
> **若環境設定正確但 OpenRouter 後台仍看不到任何 API 請求（代表錯誤發生在送出請求之前）：**
>
> 啟用完整 traceback 日誌：確認 `runtime.py` 的 `except Exception as exc:` 有加 `exc_info=True`，部署後日誌會顯示精確的錯誤行號。以下是三個已確認過的隱藏陷阱：
>
> **陷阱 1：`few_shot_examples` 型別錯誤**
>
> Alembic migration 若使用 `json.dumps([])` 將 `few_shot_examples` 寫入 JSON 欄位，SQLAlchemy 讀回時可能返回字串 `'[]'` 而非 list。`_load_scoring_profile` 未做型別檢查時，字串會直接傳入 `_format_few_shot_block()`，導致函數對字元迭代（`'['.get(...)`）而非 dict 元素，拋出 `AttributeError: 'str' object has no attribute 'get'`，在 API 請求送出前即觸發 fallback。
>
> 修正方式：migration 中 `few_shot_examples` 欄位直接使用 `[]`（Python list），不使用 `json.dumps([])`；`_load_scoring_profile` 中讀取後加型別檢查：
> ```python
> few_shot_raw = row.few_shot_examples
> if isinstance(few_shot_raw, str):
>     try:
>         few_shot_raw = json.loads(few_shot_raw)
>     except Exception:
>         few_shot_raw = []
> if not isinstance(few_shot_raw, list):
>     few_shot_raw = []
> ```
>
> **陷阱 2：`request_context` 未包含在 score payload 中**
>
> `repository.py` 的 `_score_to_detail()` 若缺少 `"request_context"` 欄位，AI Prompt 中的 `Headline`、`Primary text`、`CTA` 全為空字串。模型仍會回傳 JSON，但評分依據不完整，品質偏低。修正方式：確認 `_score_to_detail` 包含 `"request_context": _safe_json_dict(score.request_context)`。`_safe_json_dict` 需能處理 JSON 欄位返回字串的情形（`isinstance(value, str)` → `json.loads`）。
>
> **陷阱 3：推理模型 `max_tokens` 不足導致 JSON 截斷**
>
> 使用 `nvidia/nemotron-*-reasoning` 等推理模型時，模型的 chain-of-thought 思考過程與實際輸出共享同一個 `max_tokens` 預算。當 prompt 包含真實廣告文案時，思考鏈會變長，剩餘給 JSON 輸出的 token 不足，導致回應中途截斷，`_extract_json_payload` 解析失敗並觸發 fallback（錯誤訊息："AI response JSON structure is broken. Extracted: { "overall_score": ..."）。
>
> 修正方式：`runtime.py` 中 `generate_content` 呼叫的 `max_tokens` 設為 `4096`（而非 `2048`）。
>
> **AI 評分的 Key 查找優先順序：**
>
> 批次匯入觀察廣告時，系統依下列順序取得 OpenRouter API Key：
> 1. **後台個人設定**（後台 → AI 設定 → OpenRouter Key）→ 加密存在 PostgreSQL users 表
> 2. **環境變數** `OPENROUTER_API_KEY`（Zeabur Variables）
> 3. **環境變數** `ZEABUR_AI_HUB_API_KEY`（備用）
>
> 若使用後台個人設定，不需要設定 `OPENROUTER_API_KEY` 環境變數。但 `META_ANDROMEDA_SCORING_PROVIDER=openrouter` **無論如何都必須設定**。
>
> **後台設定頁連線測試失敗（400）？**
>
> 連線測試 `POST /api/ai/test-connection` 當欄位顯示 `'********'` 時，前端送出 `api_key: null`。後端會自動從 DB 讀取已儲存的個人 Key 來測試，不需要另外設定環境變數。若測試仍失敗，代表 DB 中沒有有效的 Key，需重新在後台設定頁儲存。

> [!WARNING]
> **後台設定頁儲存 API Key 後，重開頁面 Key 消失？**
>
> 若儲存時回傳 `{"success": true}` 但 `settings.has_openrouter_key: false`，代表加密失敗（Key 存成 NULL）。
> 檢查 Zeabur Variables 中 `ENCRYPTION_KEY` 是否存在且格式正確（44 字元的 Fernet Base64 Key）。
> 可用以下指令產生新金鑰：
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```
> ⚠️ 若更換新的 `ENCRYPTION_KEY`，所有使用者先前儲存的加密 Key（FB Token、AI Key）將全部失效，需重新設定。
