# Phase 1: Google 登入整合計畫 (Google Login Integration Plan)

## 目標 (Goal)
實作 Google OAuth 登入機制，保護應用程式。使用者必須使用 Google 帳號登入後，才能進入儀表板 (Dashboard) 查看數據。

## 需要使用者審閱 (User Review Required)
> [!IMPORTANT]
> **您需要取得 Google Client ID**
> 您需要前往 Google Cloud Console 申請一組 **Client ID**。
> 我會提供詳細步驟教您如何申請。目前我會先用佔位符號 (Placeholder) 進行開發。

## 預計變更 (Proposed Changes)

### 前端 (Frontend)
#### [NEW] [frontend/src/pages/Login.jsx](file:///c:/Users/netgm/OneDrive/%E6%96%87%E4%BB%B6/Python/Facebook-Dashboard-Web-App/frontend/src/pages/Login.jsx)
- **新增登入頁面**：包含 "Sign in with Google" 按鈕。

#### [NEW] [frontend/src/components/ProtectedRoute.jsx](file:///c:/Users/netgm/OneDrive/%E6%96%87%E4%BB%B6/Python/Facebook-Dashboard-Web-App/frontend/src/components/ProtectedRoute.jsx)
- **新增保護路由元件**：這是一個檢查機制。如果使用者沒有有效的 Google Token，就會被強制導回登入頁 (`/login`)。

#### [MODIFY] [frontend/src/App.jsx](file:///c:/Users/netgm/OneDrive/%E6%96%87%E4%BB%B6/Python/Facebook-Dashboard-Web-App/frontend/src/App.jsx)
- **修改路由架構**：
    - 將現有的儀表板頁面用 `ProtectedRoute` 包起來。
    - 引入 `react-router-dom` 來管理頁面跳轉 (Login <-> Dashboard)。
    - *注意*：因為 `package.json` 裡面還沒有 `react-router-dom`，我會一併安裝。

#### [MODIFY] [frontend/.env.production](file:///c:/Users/netgm/OneDrive/%E6%96%87%E4%BB%B6/Python/Facebook-Dashboard-Web-App/frontend/.env.production)
- **新增環境變數**：加入 `VITE_GOOGLE_CLIENT_ID`。

### 後端 (Backend)
#### [MODIFY] [backend/main.py](file:///c:/Users/netgm/OneDrive/%E6%96%87%E4%BB%B6/Python/Facebook-Dashboard-Web-App/backend/main.py)
- **新增驗證機制 (Middleware)**：
    - 檢查 API 請求的 Header 是否包含 `Authorization: Bearer <token>`。
    - 驗證該 Token 是否為 Google 簽發的有效憑證。

## 驗證計畫 (Verification Plan)
### 手動驗證 (Manual Verification)
1.  啟動應用程式。
2.  確認網頁是否自動跳轉到「登入頁面」。
3.  使用 Google 帳號進行登入。
4.  登入成功後，確認是否能進入「儀表板」。
5.  檢查後端 Log，確認 Token 有被正確驗證。
