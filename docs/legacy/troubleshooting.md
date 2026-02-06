# 問題排除指南 (Troubleshooting Guide)

本指南記錄了常見的技術問題、原因分析以及解決方案。

---

## 🌐 生產環境問題 (Zeabur / Production)

### 1. "Failed to fetch" (連線失敗)
- **現象**: 點擊按鈕時彈出 "Failed to fetch"。
- **檢查**: 
  - 開啟 F12 開發者工具，查看 Network 標籤。
  - 檢查 Request URL 是否指向 `http://localhost:8000` 而非正式網址。
- **解決**: 
  - 確認前端環境變數 `VITE_API_URL` 已正確設定為後端公開網址。
  - 設定後必須**重新部署 (Redeploy)** 前端服務。

### 2. 500 Internal Server Error (後端崩潰)
- **現象**: 網路請求回傳 500 錯誤。
- **檢查**: 查看 Zeabur 後端服務的 **Logs**。
- **常見原因**:
  - 資料庫欄位不符合 (Schema Drift): 執行 `alembic upgrade head`。
  - `google-auth` 版本過舊: 更新 `requirements.txt` 並重刷。
  - 環境變數缺失: 下載最新代碼並檢查啟動日誌。

### 3. 資料庫結構錯誤 (Schema Drift)
- **案例**: 遇到 `column users.id does not exist`。
- **原因**: 雲端資料庫結構與代碼模型不一致。
- **解決**: 
  - 使用 `alembic upgrade head` 強制更新。
  - 若失效且為測試數據，可手動刪除 Table (`DROP TABLE`) 並透過 `main.py` 的 `init_db()` 安全機制自動重建。

---

## 💻 本地端問題 (Local Development)

### 1. 資料庫鎖定 (Database Locking)
- **案例**: 登入時系統卡住或顯示 502。
- **原因**: SQLite 在多個並行請求同時寫入同一行（如更新 `last_login`）時容易鎖定。
- **解決**: 已關閉 `last_login` 自動更新功能以維持穩定性。

### 2. 邀請連結顯示為 localhost
- **原因**: 後端寫死了回傳網址。
- **解決**: 已更新為動態偵測 Origin 標頭，連結將自動匹配當前使用的網域。

---

## 🛠️ 除錯檢查清單 (Debugging Checklist)
1. **檢查 CORS**: 是否所有紅色的請求都標示跨網域錯誤？
2. **檢查連線**: `DATABASE_URL` 是否能正常連通？
3. **查看日誌**: 永遠優先查看後端的 Traceback 報錯。
4. **驗證結構**: 資料庫欄位是否真的存在？
