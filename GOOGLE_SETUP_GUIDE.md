# Google OAuth Client ID 設定教學 (Step-by-Step Guide)

本教學將引導您如何在 Google Cloud Console 申請 Client ID，這是讓 Google 登入功能運作的必要金鑰。

## 步驟 1：建立專案 (Create Project)

1.  前往 [Google Cloud Console](https://console.cloud.google.com/)。
2.  點選左上角的專案選單 (Select a project)。
3.  點選右上角的 **"NEW PROJECT" (新增專案)**。
4.  輸入專案名稱 (例如：`Facebook Dashboard`)，點選 **"CREATE" (建立)**。
5.  等待幾秒鐘，確認右上角通知顯示建立成功，並切換到該專案。

## 步驟 2：設定 OAuth 同意畫面 (Configure OAuth Consent Screen)

1.  點選左側選單的 **"APIs & Services" (API 和服務)** > **"OAuth consent screen" (OAuth 同意畫面)**。
2.  **User Type (使用者類型)**：
    - 選擇 **"External" (外部)**。
    - 點選 **"CREATE" (建立)**。
3.  **App Information (應用程式資訊)**：
    - **App name**: 輸入您的網站名稱 (例如：`FB Dashboard`)。
    - **User support email**: 選擇您的 Email。
    - **Developer contact information**: 輸入您的 Email。
    - 點選 **"SAVE AND CONTINUE"**。
4.  **Scopes (範圍)**：
    - 直接點選 **"SAVE AND CONTINUE"** (預設會包含 email, profile, openid，這樣就夠了)。
5.  **Test Users (測試使用者)**：
    - **重要**：在您的應用程式發布 (Publish) 之前，只有被加入名單的人才能登入。
    - 點選 **"ADD USERS"**。
    - 輸入您自己的 Google Email。
    - 點選 **"SAVE AND CONTINUE"**。
6.  最後確認頁面，點選 **"BACK TO DASHBOARD"**。

## 步驟 3：建立憑證 (Create Credentials)

1.  點選左側選單的 **"Credentials" (憑證)**。
2.  點選上方 **"CREATE CREDENTIALS" (建立憑證)** > **"OAuth client ID"**。
3.  **Application type (應用程式類型)**：
    - 選擇 **"Web application" (網頁應用程式)**。
4.  **Name**：可以使用預設值或自行命名。
5.  **Authorized JavaScript origins (已授權的 JavaScript 來源)**：
    - 這是最重要的一步！這裡要填入您的網站網址，Google 才會允許登入。
    - 點選 **"ADD URI"**，填入本地開發網址：
      `http://localhost:5173`
    - 再點選 **"ADD URI"**，填入您的 Zeabur 正式網址 (請將下方網址換成您真正的網址)：
      `https://your-app.zeabur.app`
    - **注意**：網址結尾**不要**加斜線 `/`。
6.  **Authorized redirect URIs (已授權的重新導向 URI)**：
    - 如果您使用彈出視窗登入 (Popup)，這裡通常不需要填，或是填入與 Origin 相同的網址。
    - 建議填入：`http://localhost:5173` 和 `https://your-app.zeabur.app`。
7.  點選 **"CREATE" (建立)**。

## 步驟 4：取得 Client ID

1.  建立成功後，會彈出一個視窗顯示 "Your Client ID" 和 "Client Secret"。
2.  我們只需要 **Client ID** (通常是一長串字串，結尾是 `.apps.googleusercontent.com`)。
3.  複製這個 Client ID。

## 步驟 5：填入環境變數

回到您的專案：

1.  **本地開發**：
    - 在 `frontend` 資料夾下建立或是修改 `.env.development` 檔案。
    - 加入一行：`VITE_GOOGLE_CLIENT_ID=您的Client_ID`

2.  **Zeabur 部署**：
    - **Frontend 服務**：
        - 進入 Frontend 服務 > **Variables** (環境變數)。
        - 新增 Key: `VITE_GOOGLE_CLIENT_ID`
        - Value: `您的Client_ID`
    - **Backend 服務** (新增)：
        - 進入 Backend 服務 > **Variables** (環境變數)。
        - 新增 Key: `GOOGLE_CLIENT_ID`
        - Value: `您的Client_ID` (與前端相同)
    - **重新部署**：
        - 設定完成後，請記得對兩個服務都按 **Redeploy** (重新部署) 才會生效。

完成！現在您可以重新啟動專案 (`npm run dev`) 來測試登入功能了。
