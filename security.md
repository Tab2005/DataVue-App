# DataVue-App 安全憲法與防禦規範 (security.md)

本文件定義 DataVue-App 的「最高安全憲法」與「系統防禦規範」。當 AI 安全掃描工具
（`claude-code-security-review` GitHub Action、Claude Code 內建 `/security-review`，
或其他等效插件）對本專案進行掃描時，應以本檔案的不變條件為依據，沿著資料流向審查
程式碼，找出違反規則的邏輯與漏洞 —— 特別是「業務邏輯漏洞」（權限繞過、租戶隔離失效
等），而不只是通用的注入型漏洞。

DataVue-App 是一個**多租戶（Team-based）廣告與流量數據分析平台**，整合 Facebook Ads、
Google Search Console（GSC）、Google Analytics 4（GA4），並提供 AI 廣告分析
（Meta Andromeda 評分引擎、OpenRouter/Gemini 摘要）。**本專案沒有金流付款、沒有點數
計費、沒有使用者上傳影音檔案的功能**，套用此文件時請勿誤植其他專案（例如付款防重入、
影音上傳）的規則。

---

## 一、系統最高安全憲法 (Security Invariants)

以下規則在任何狀況下都**絕對不容許被打破**：

1. **團隊強隔離 (Team-Level Isolation)**
   * 任何使用者都絕對不能讀取、修改或刪除不屬於自己所屬 Team 的資料 —— 包含 Facebook
     廣告帳號/報表、GSC 網站資料、GA4 洞察快照、週報、Meta Andromeda 評分紀錄等。
   * 前端透過 `X-Team-Id` header 指定操作對象，**後端在每一次資料存取前，必須查詢
     `TeamMember` 表確認該使用者確實是該 Team 的成員**（見 `dependencies.get_current_team`），
     不能只憑 header 內的 team_id 值就信任存取範圍。
   * Facebook 廣告帳號存取需比對 `Team.visible_ad_account_ids` 白名單，不可讓使用者
     用任意 `account_id` 存取白名單外的廣告帳號資料。

2. **帳號停用必須對「全站所有」受保護端點即時生效**
   * `User.status == SUSPENDED` 的使用者，一旦被停用，必須**立即**無法呼叫任何需要
     登入的 API —— 這必須由 `get_current_user`（所有受保護端點共用的核心依賴注入）
     直接檢查，而不是只掛在少數幾個端點上的 `get_current_active_user`。
   * *歷史教訓*：本專案曾經只有 5 個端點會檢查 `UserStatus`，其餘 100+ 個端點完全不檢查，
     導致「停用帳號」形同虛設（已於 2026-09-01 修復）。掃描時應特別確認：任何新增的
     端點是否繞過 `get_current_user`／直接用 `db.query(User)` 取得使用者物件卻略過
     狀態檢查。

3. **Super Admin 例外邏輯不可被一般使用者觸發**
   * `User.is_super_admin` 只能由後端可信邏輯設定，前端傳入的任何欄位都不可以直接
     或間接改寫這個值（例如透過 `PUT /api/users/{id}` 這類一般更新端點）。
   * `is_super_admin=True` 會在 `dependencies.py` 的多處檢查中（`get_admin_user`、
     `require_permission`、`require_module`）**完全繞過**權限與模組檢查，因此任何能
     設定或洩漏此欄位的路徑，都等同於系統root權限，需視為最高風險。

4. **緊急權限提升端點 (`/api/emergency/fix-super-admin`) 必須維持高強度保護**
   * 此端點透過比對 `X-Emergency-Key` header 與 `ENCRYPTION_KEY` 環境變數的前 32
     字元來授權，成功後會把 `SUPER_ADMIN_EMAIL` 列出的帳號直接設為 Super Admin。
   * **`ENCRYPTION_KEY` 因此具有雙重敏感性**：外洩不只會讓所有加密欄位（見第二節）
     可被解密，其前 32 字元還等於「無需登入即可自我提權為 Super Admin」的密鑰。
   * 掃描時應確認：此端點的比對邏輯使用固定時間比較（或至少不會提早短路造成明顯的
     timing side-channel）、且不會在任何錯誤訊息、log 中洩漏 `expected_key` 或
     `ENCRYPTION_KEY` 本身。

5. **公開分享連結 (Share Link) 只能讀取當下快照的唯讀資料**
   * `GA4 Insights` 分享連結（`share_token` + `revoked_at`）、`Analytics AI` 分析快照
     分享連結（`fb_ads_analytics_ai_snapshots.share_token`）等「免登入即可存取」的
     公開端點，必須：
     1. 一旦 `revoked_at` 被設定（或連結已撤銷），立即回傳 404／無法再讀取。
     2. 回傳內容**不得包含**內部識別欄位，例如 `created_by`、`team_id`、`user_id` 或
        其他能反推出擁有者身分/其他資料的欄位（既有測試
        `test_analytics_ai_snapshot_create_ai_summary_and_share_flow` 已對此把關，
        新增分享類端點時必須維持同等把關）。
     3. 分享連結只能讀「建立當下」寫入的快照內容，不能讓 `share_token` 被用來查詢
        即時、範圍更大的資料（等同於繞過 Team 隔離的後門）。

---

## 二、受保護的貴重資產清單 (Assets to Protect)

AI 掃描應特別監控並確保以下資產不被洩露、篡改或非法存取：

* **`ENCRYPTION_KEY`（Fernet 對稱金鑰）**：用於加解密下列所有欄位（`core/security.py`）。
  嚴禁出現在前端程式碼、Git 版本控制、log、錯誤訊息、或任何回傳給使用者的 API response
  中。外洩等同於資料庫內所有第三方憑證全部裸奔，且其前 32 字元同時是 Super Admin
  緊急提權密鑰（見憲法第 4 條）。
* **第三方 OAuth / API 憑證（加密儲存於 `User` / `Team` / `UserIntegration` 表）**：
  * Facebook：`fb_access_token`、`fb_app_secret`（個人與 Team 層級皆有）
  * GSC：`gsc_access_token`、`gsc_refresh_token`
  * GA4：`ga4_access_token`、`ga4_refresh_token`
  * AI：`gemini_api_key`、`openrouter_api_key`
  * 上述欄位落地前必須經過 `core/security.py` 的 `encrypt_value()`，讀取時才
    `decrypt_value()`；**新增任何第三方憑證欄位時，一律比照此加密作法，禁止明文落地**。
* **Google ID Token 驗證邏輯 (`core/security.verify_google_token`)**：必須持續檢查
  `email_verified`、`aud`（`GOOGLE_CLIENT_ID`）與簽名，不可弱化或跳過任一項檢查。
  本系統無自建密碼系統，帳號安全完全依賴此驗證鏈是否正確。
* **`TeamInvite.code`（團隊邀請連結）**：具有 `expires_at` 過期時間，過期後不可再用於
  加入團隊；被使用次數 (`used_count`) 應正確累計，避免無限次數重複使用邀請碼。
* **Meta Andromeda 素材檔案 (assets)**：使用者上傳的廣告素材縮圖/影片截圖，儲存於
  內部 Worker（`META_ANDROMEDA_INTERNAL_WORKER_TOKEN` 保護），存取需通過
  `META_ANDROMEDA_ALLOWED_MEDIA_HOSTS` 白名單與大小限制
  (`META_ANDROMEDA_UPLOAD_MAX_BYTES`)。
* **資料庫連線字串 (`DATABASE_URL`)**：必須存放於環境變數，不可寫死於程式碼或
  commit 進版本控制。

---

## 三、身分驗證與授權原則 (Authentication & Authorization)

DataVue-App **沒有帳號密碼系統**，所有登入皆透過 Google OAuth ID Token，因此：

1. **雙重防線要求**
   * **身分驗證 (Authentication)**：`get_current_user` 驗證 Google ID Token 並確保
     `email_verified=true`，取得/建立對應的 `User` 記錄。
   * **授權檢查 (Authorization)**：確認該使用者對「這一筆資料」有資格存取 —— 不能只
     檢查「有沒有登入」就放行。**每一個涉及 Team 資料的查詢，都必須用當前使用者的
     `user.id` 反查 `TeamMember`／`UserModuleAccess`／`UserPermission`，確認其確實
     隸屬於資料所屬的 Team、且擁有對應模組與權限**，不能只信任前端傳來的 `team_id`
     或 `account_id`。

2. **角色與權限矩陣 (RBAC)**
   * 系統層級：`UserRole`（`ADMIN` / `MEMBER` / `VIEWER`）+ `is_super_admin` 旗標。
   * 團隊層級：`Role`（`team_owner` / `team_admin` / `team_member` / `team_viewer`），
     透過 `RolePermission` 對應到細粒度 `Permission`（格式 `模組:功能:動作`，例如
     `fb_ads:analytics:view`）。
   * 模組存取：`UserModuleAccess`（`team_id` 為 `NULL` 代表個人工作區權限，否則為
     該 Team 專屬的模組開關）。
   * 個別授予/撤銷：`UserPermission.granted`（`True`=額外授予、`False`=明確撤銷），
     掃描時應確認撤銷邏輯（`granted=False`）確實會蓋過角色預設權限，而非被忽略。
   * `require_permission()` / `require_module()` / `require_super_admin()`
     （`dependencies.py`）是唯一應該被用來保護端點的方式；新端點若手動重寫類似邏輯
     而非重用這些 dependency，應視為高風險，需仔細檢查是否有遺漏。

3. **帳號狀態檢查**：見憲法第 2 條。

---

## 四、信任邊界與資料流向規則 (Trust Boundaries)

* **信任邊界定義**：瀏覽器前端與其送出的所有欄位（含 `X-Team-Id` header、
  `team_id`／`account_id`／`user_id` 等 body 欄位）皆為「外部不可控危險區」；
  後端伺服器與資料庫為「內部安全區」。
* **資料流安全防護**：
  1. **權限與歸屬判斷嚴禁只靠前端傳入的 ID**：`team_id`、`account_id`、
     `site_url`（GSC）、`property_id`（GA4）等識別碼，後端必須重新查詢資料庫，
     確認其與目前登入使用者的所屬關係一致，才能讀取或寫入對應資料。
  2. **AI 分析/摘要功能的 API Key 解析順序固定**：`TokenManager.get_ai_api_key()`
     只依「使用者自己儲存的加密金鑰」解析，不可讓前端直接指定要用「別人」的 Key；
     若請求帶入 `api_key`（BYOK 模式），僅能視為**當前使用者自己**臨時提供的金鑰，
     不落地儲存除非使用者明確呼叫 `/api/ai/settings` 儲存。
  3. **匯出/分享類端點回傳前，需人工白名單欄位**（`response_model` 或手動組裝
     dict），而不是把 ORM object 直接序列化整包回傳 —— 避免不小心夾帶
     `fb_access_token`、`*_refresh_token`、`*_api_key` 等加密欄位（即使是密文）
     外流。

---

## 五、攻擊面與邊界防禦規範 (Attack Surface Defenses)

1. **登入入口**
   * 完全委託 Google OAuth，沒有自建密碼登入表單，因此**不涉及**密碼爆破/憑證填充
     風險；但需確保 `GOOGLE_CLIENT_ID` 設定正確，避免接受來自其他 OAuth Client 簽發
     的 Token（`aud` 檢查不可被移除）。
   * `verify_google_token` 結果有 5 分鐘 TTL 快取（`core/security.py`），若使用者在
     Google 端被停權/撤銷授權，最多會有 5 分鐘的延遲才會反映到本系統 —— 屬已知、
     可接受的風險窗口，掃描時不需視為新漏洞，但**不應該被進一步放大**（例如快取時間
     被誤改成數小時）。

2. **公開/匿名端點（無需登入）**
   * `/api/emergency/fix-super-admin`：見憲法第 4 條。
   * `/api/analytics-ai/share/{token}`、GA4 洞察分享端點：見憲法第 5 條。
   * `/health`：僅能回傳存活狀態，**不得**包含任何 API 金鑰長度、使用者統計等內部
     除錯資訊（這類資訊只能出現在 `/health/admin` 這種要求 Super Admin 的端點裡，
     本專案已依此原則收斂過一次，新增欄位時需維持相同分級）。
   * 團隊邀請連結 `/api/teams/invites/{code}`：需檢查 `expires_at` 是否過期，且加入
     成功後應正確地把使用者與正確的 Team/Role 建立關聯，不可被竄改成其他 Team。

3. **速率限制 (Rate Limiting)**
   * 全站預設 `200/minute`（依來源 IP，`limiter.py`，可選 Redis 儲存於多實例間共享）。
   * 涉及外部收費 API 呼叫的端點（Facebook Graph API、GSC/GA4 API、OpenRouter/Gemini
     AI 分析）應額外評估是否需要比預設值更嚴格的獨立限流，避免單一使用者或惡意腳本
     短時間內刷爆團隊/系統共用的第三方 API 配額。

4. **CORS**
   * 生產環境只允許 `tabisme.com`、`zeabur.app`、`sitetegy.com` 及其子網域，且強制
     HTTPS（`main.py` 的 `allow_origin_regex`）；本地開發才允許 `http://localhost`
     與 `http://127.0.0.1`。新增網域時務必只加進這條 regex，不可整條放寬成 `.*`。

5. **檔案上傳（Meta Andromeda 素材）**
   * 僅接受白名單內的 MIME type（`modules/meta_andromeda/service/assets.py`），並有
     `META_ANDROMEDA_UPLOAD_MAX_BYTES` 大小上限、圖片會被縮放壓縮（最大邊長
     1200px）。掃描時應確認新的上傳路徑是否同樣套用這兩層檢查，避免被繞過去直接
     寫入未經檢查的原始檔案。

6. **管理端強制刪除端點 (`DELETE /api/admin/users/{id}`、`DELETE /api/users/{id}`)**
   * 這兩個端點會對資料庫做**實體刪除 (hard delete)**，會撞上十幾張表的外鍵約束
     （權限指派、週報、GA4 洞察快照、團隊共用規則等），且**故意保留**供「完全無關聯
     資料」的帳號使用 —— 一般後台操作流程應優先使用「停用帳號」
     （`PUT /api/users/{id}` 設定 `status=SUSPENDED`），而不是強制刪除。
   * `PUT /api/users/{id}` 已內建防呆：不能停用自己、不能停用 Super Admin —— 掃描時
     應確認這兩條防呆邏輯沒有被繞過或移除。

---

## 六、明確排除範圍 (Out of Scope for This Project)

以下這類規則**不適用**於 DataVue-App，掃描或審查時請勿誤套用其他專案的規則：

* 金流/付款防重入（Stripe / 綠界等 webhook idempotency）——本專案無金流功能。
* 使用者點數/算力餘額扣款機制、Race Condition 預扣邏輯 —— 本專案無點數計費系統。
* 使用者自建帳密登入、密碼雜湊儲存 —— 本專案完全採用 Google OAuth，無自建密碼。
* 大型使用者影音檔案上傳（僅 Meta Andromeda 的廣告素材縮圖屬小型圖片，見第五節第 5 點）。
