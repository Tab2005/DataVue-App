# 05_API_參考手冊 (API Reference)

## 📡 基礎資訊
**站略 (Site-tegy)** 的後端 API 是基於 FastAPI 構建，遵循 RESTful 原則。所有的請求均需通過 Google OAuth 2.0 認證，並回傳 JSON 格式數據。

- **Base URL (Local)**: `http://localhost:8000/api`
- **Base URL (Production)**: 由環境變數 `VITE_API_URL` 定義
- **Interactive Docs**: `/docs` (Swagger UI) 或 `/redoc` (ReDoc)

---

## 🔐 認證機制 (Authentication)
系統一律要求在 HTTP Header 中攜帶 Google 簽發的 ID Token：

```http
Authorization: Bearer <GOOGLE_ID_TOKEN>
```

### 1. 使用者資訊與狀態
- `GET /auth/me`：取得當前登入者身分、角色與權限。
- `GET /auth/token-status`：檢查 Facebook Token 的有效期限與剩餘天數。

### 2. 第三方 Token 交換 (OAuth Exchange)
- `POST /auth/exchange-token`：
  - **功能**：將 Facebook 短效 Token 交換為長效 Token（60天）並加密儲存。
  - **參數**：`app_id`, `app_secret`, `short_token`, `team_id` (選填)。

---

## 🤖 AI 分析與串流 (AI & Streaming)
AI 模組支援標準 JSON 回應與 SSE (Server-Sent Events) 串流回應，適合長文本分析。

### 1. 深度數據分析 (SSE)
- **Endpoint**: `POST /ai/analyze-stream`
- **Content-Type**: `text/event-stream`
- **功能**: 即時回傳 AI 對數據的戰略建議。

---

## 📊 核心功能端點 (Core Endpoints)

### 📈 Facebook Ads
- `GET /ad-accounts`：列出該 Token 權限下的所有廣告帳戶。
- `GET /dashboard-data`：取得指定帳戶的關鍵指標 (Spend, Impressions, Clicks)。
- `GET /analytics`：取得細粒度數據，支援自訂時間跨度與指標篩選。

### 🔍 Google Search Console (GSC)
- `POST /gsc/authorize`：提交 GSC 授權碼。
- `GET /gsc/sites`：列出使用者擁有的網站清單。
- `GET /gsc/analytics`：取得點擊、曝光、CTR 與排名數據，`dimensions` 可傳任意 GSC 維度（如 `date`、`query`、`page`、`country`、`device`、`searchAppearance`，可用逗號組合）。
- `GET /gsc/search-appearance-summary`：彙總 `searchAppearance` 維度成效（AMP、Product Snippets、Merchant Listings、Review Snippet 等既有 Rich Result 類型）。
  - **參數**：`site_url`、`start_date`、`end_date`。
  - **回傳**：`has_data`、`total_clicks`、`total_impressions`（以 `date` 維度加總為分母，避免同一結果符合多種外觀類型造成重複計算），以及 `types[]`（每個外觀類型的 clicks/impressions/ctr/position/click_share/impression_share/`is_ai_related_hint`）。
  - **不含 AI Overview / 生成式 AI 數據**：Google 於 2026-06-03 推出的「生成式 AI 效能報表」目前僅能在 GSC 後台查看（成效 > 搜尋結果 > 生成式 AI），尚未透過任何 API 開放。`is_ai_related_hint` 只是對 `search_appearance` 字串做關鍵字比對（`AI`/`OVERVIEW`/`GENERATIVE`/`SGE`）的預留機制，目前保證恆為 `false`，不代表這個網站沒有 AI Overview 曝光。詳見 `docs/35_GSC_AI_Overview_生成式AI搜尋數據擴充實作規劃.md`。
- `POST /gsc/page-intents`：利用 AI 對搜尋頁面進行意圖分類 (Intent Classification)。
- `POST /gsc/keyword-gap`：分析單一頁面「有排名但內文未涵蓋」的關鍵字缺口。
- `POST /gsc/content-gap-suggestions`：針對 `keyword-gap` 找到的缺口關鍵字，用 AI 產生文章方向建議（`expand_existing` 補充現有頁面段落／`new_article` 獨立新文章方向），含建議標題與大綱要點。
  - **參數**：`site_url`、`page_url`、`start_date`、`end_date`、`top_n`（選填）、`missing_keywords`（選填，若已呼叫過 `keyword-gap` 可直接帶入其 `in_content=false` 的項目，避免重複分析）、`provider`（`zeabur`/`gemini`，預設 `zeabur`）、`ai_api_key`（選填）。
  - **回傳**：`suggestions[]`（每項含 `type`、`title`、`outline`、`target_keywords`、`reasoning`）、`model`、`keyword_count`。缺口關鍵字為 0 或 API Key 未設定時回傳空陣列與 `message`，不視為錯誤。
  - 僅生成方向與大綱層級建議，不生成完整文章全文，前端應標示「僅供參考，需人工確認」。詳見 `docs/37_GSC_內容缺口_AI文章方向建議_實作規劃.md`。

### 📊 Google Analytics 4 (GA4)
- `GET /ga4/properties`：取得可用資源清單。
- `GET /ga4/analytics`：取得特定資源的流量與轉化數據。

---

## 👑 團隊與系統管理
- `GET /teams/me`：取得使用者參與的團隊列表。
- `POST /teams/`：建立新團隊（自動指派為 Owner）。
- `POST /invites/`：產生團隊邀請連結代碼。
- `GET /admin/stats`：(超級管理員專用) 全系統使用概況統計。

---

## ⚠️ 錯誤處理 (Error Handling)
系統使用統一的錯誤格式。當發生業務邏輯錯誤時，回傳 `AppException` 格式：

```json
{
  "error_code": "INSUFFICIENT_PERMISSION",
  "detail": "您不具備存取此模組的權限"
}
```

---

**站略 (Site-tegy) API 開發組**  
*穩定的介面，是戰略協作的語言。*
