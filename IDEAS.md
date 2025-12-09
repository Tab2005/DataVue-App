# 開發構想紀錄 (Development Ideas & Brainstorming)

此檔案用於記錄與 AI 助理討論的開發構想、可行性分析以及未來的規劃。

## 1. Google 帳號登入整合 (Google OAuth Integration)

**日期**: 2025-12-08
**狀態**: 評估中 (Under Assessment)

### 需求描述
目前前端畫面無需登入即可訪問。目標是實作透過 Google 帳號登入後，才能看到儀表板畫面，以增加安全性。

### 可行性分析 (Feasibility Analysis)
**結論**: **完全可行 (High Feasibility)**。
目前的技術架構 (React + FastAPI) 非常適合整合 Google OAuth。

### 實作架構規劃

#### 1. Google Cloud Platform (GCP) 設定
- 需要在 Google Cloud Console 建立專案。
- 設定 OAuth 同意畫面 (OAuth Consent Screen)。
- 取得 **Client ID** (前端用) 和 **Client Secret** (後端驗證用，視架構而定)。

#### 2. 前端 (React)
- **套件**: 使用 `@react-oauth/google` (官方推薦的現代化套件)。
- **流程**:
  1. 新增一個「登入頁面」 (Login Page) 作為預設首頁。
  2. 放置 "Sign in with Google" 按鈕。
  3. 使用者登入成功後，Google 會回傳一個 `Credential` (JWT)。
  4. 前端將此 Credential 存入 LocalStorage 或 Context。
  5. 實作 `ProtectedRoute` 元件，檢查是否有 Token，若無則導回登入頁。

#### 3. 後端 (FastAPI) - 選用但推薦
雖然純前端驗證也可以擋住一般使用者，但為了安全性，後端 API 也應該要驗證 Token。
- **套件**: `google-auth` 或 `pyjwt`。
- **流程**:
  1. 前端呼叫 API 時，將 Google Token 放在 Header (`Authorization: Bearer <token>`)。
  2. 後端 Middleware 攔截請求，驗證該 Token 是否為 Google 簽發且有效。
  3. 驗證通過才回傳數據。

### 預計變動檔案
- `frontend/package.json`: 新增 OAuth 套件。
- `frontend/src/App.jsx`: 新增路由 (Router) 與保護機制。
- `frontend/src/pages/Login.jsx`: 新增登入頁面。
- `backend/main.py`: 新增 Token 驗證邏輯 (Middleware)。

### 待確認事項
- 是否只需要前端擋住畫面就好？還是後端 API 也要做嚴格驗證？(建議兩者都做)

### 常見問題釐清 (Q&A)
**Q: Google 登入跟 Facebook API 設定有關聯嗎？**
**A: 完全沒有關聯，兩者是獨立的。**
- **Google 登入 (Authentication)**: 就像是「大門鑰匙」，決定誰可以進入這個網站看到畫面。
- **Facebook API (Data Source)**: 就像是「電視訊號」，決定畫面裡面有沒有數據可以看。
- **結論**: 即使設定了 Google 登入，如果沒有在設定頁面輸入正確的 Facebook App ID/Secret，進去後也只會看到空的儀表板，無法抓取數據。

**Q: 這樣還有需要驗證後端 API 嗎？**
**A: 強烈建議要驗證 (Security Best Practice)。**
- **如果只做前端驗證**: 只是把「門」關起來，但「窗戶」是開的。駭客或懂技術的人如果知道您的 API 網址 (例如 `https://.../api/dashboard-data`)，可以直接繞過登入頁面，發送請求把資料抓走。
- **如果加上後端驗證**: 就像是窗戶也加了鐵窗。後端會檢查每一個請求：「你有 Google 的通行證嗎？」如果沒有，就算知道網址也拿不到任何資料。
- **建議**: 如果您的數據很敏感，**後端驗證是必須的**。如果只是防君子不防小人，前端驗證勉強夠用。

## 2. 多人使用與資料庫規劃 (Multi-User Support & Database)

**日期**: 2025-12-08
**狀態**: 規劃中 (Planning)

### 問題描述
目前系統使用單一檔案 `tokens.json` 儲存 Facebook Token。這意味著**所有使用者共享同一個 Token**。
如果使用者 A 設定了他的 Facebook 帳號，使用者 B 進來也會看到 A 的數據；如果 B 修改了設定，A 的數據就會被覆蓋。

### 解決方案：導入資料庫 (Database Integration)
為了讓不同使用者擁有各自的 Facebook 設定，我們需要將「Google 帳號」與「Facebook Token」綁定。

#### 架構變更
1.  **廢除 `tokens.json`**: 改用資料庫儲存。
2.  **資料表設計 (Schema)**:
    - `users` table:
        - `id`: Primary Key
        - `google_id`: Google 唯一使用者 ID (來自 Google Login)
        - `email`: 使用者 Email
        - `fb_access_token`: 該使用者的 Facebook Long-Lived Token
        - `fb_app_id`: (選填) 該使用者的 App ID
        - `fb_app_secret`: (選填) 該使用者的 App Secret (需加密儲存)

#### 流程
1.  使用者透過 Google 登入 -> 後端取得 `google_id`。
2.  使用者設定 Facebook API -> 後端將 Token 存入資料庫，並關聯到該 `google_id`。
3.  使用者查看儀表板 -> 後端根據目前的 `google_id` 去資料庫撈出對應的 Token -> 呼叫 Facebook API。

#### 技術選擇
- **開發階段**: SQLite (輕量、無需額外安裝伺服器，Python 內建支援)。
- **正式階段**: PostgreSQL (Zeabur 有提供插件，適合多人同時連線)。

## 3. 開發路線圖 (Development Roadmap)

**建議順序**: 先完成登入 (Phase 1)，再導入資料庫 (Phase 2)。
**原因**: 資料庫需要 `google_id` 作為 Key 來區分使用者。如果沒有先完成登入功能，我們就拿不到 `google_id`，資料庫也無法設計。

### Phase 1: Google 登入整合 (Google Login)
- [x] 前端：新增登入頁面，實作 Google Sign-In。
- [x] 前端：實作路由保護 (未登入導回首頁)。
- [x] 後端：(選用) 實作 Token 驗證 Middleware。
- **目標**: 確保只有登入的使用者能看到畫面，並取得使用者的 `google_id`。

### Phase 2: 資料庫導入 (Database Integration)
- [x] 後端：設計 `User` 資料表 (SQLite)。
- [x] 後端：修改 API，將 Token 存入資料庫 (綁定 `google_id`)。
- [x] 後端：修改 API，從資料庫讀取 Token。
- **目標**: 實現多使用者支援，每個人的設定互不干擾。

## 4. 安全性強化 (Security Hardening)

**日期**: 2025-12-09
**狀態**: 建議實作 (Recommended)

### 風險評估
目前 Token 以明文 (Plain Text) 儲存在 SQLite 資料庫中。若駭客取得 `facebook_dashboard.db` 檔案，即可直接竊取所有使用者的 Token。

### 解決方案：資料加密 (Data Encryption)
使用 `cryptography` 套件對敏感欄位進行加密。

- **技術**: 對稱式加密 (Symmetric Encryption)，例如 Fernet。
- **金鑰管理**: 產生一把 `ENCRYPTION_KEY`，存放在 `.env` 檔案中 (不入庫)。
- **流程**:
    [x] 寫入資料庫前：`encrypt(token, key)`
    [x] 從資料庫讀取後：`decrypt(encrypted_token, key)`

### 實作細節紀錄 (Implementation Details)
> 此區塊紀錄已執行的實作計畫與技術細節。

#### 後端依賴 (Backend Dependencies)
- 新增 `cryptography` 套件。

#### 設定檔 (Configuration)
- `.env` 檔案新增 `ENCRYPTION_KEY` (自動生成，不可公開)。

#### 驗證邏輯 (Authentication Logic)
- **Lazy Migration (無痛轉移)**: 
  - 讀取 Token 時若解密失敗 (代表是舊的明文資料)，會自動回傳原始值，確保舊使用者不受影響。
  - 寫入 Token 時一律進行加密。
- **TokenManager 改動**:
  - `save_user_token`: 加密 `long_lived_token` 與 `app_secret` 後存入資料庫。
  - `get_user_token`: 從資料庫讀取 `fb_access_token` 後解密回傳。

#### 驗證測試 (Verification)
- 已建立並執行 `test_phase4.py`。
- 確認舊的明文 Token 可正常讀取。
- 確認新寫入的 Token 在資料庫中呈現亂碼 (`gAAAA...`)，且讀取時可正確還原。


