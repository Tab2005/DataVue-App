# 專案程式碼檢視報告（2026-01-16）

範圍：backend 主要入口與核心模組、部分關鍵路由與服務。此文件僅列出問題/可優化點，未做任何改動。

## 摘要
- 高風險：3
- 中風險：6
- 低風險：3

## 詳細發現

### 1) CORS 全開設定（高）
- 現況：多個入口檔案使用 `allow_origins=["*"]`。在含有使用者身分/Token 的 API 服務上，建議改為白名單，避免跨站資源濫用風險。
- 位置：
  - [backend/main.py](backend/main.py#L61-L67)
  - [backend/main_v2.py](backend/main_v2.py#L59-L65)
  - [backend/main_legacy.py](backend/main_legacy.py#L554-L563)

### 2) Debug/診斷端點可能在正式環境暴露（高）
- 現況：`/api/debug/*` 提供資料庫修復、權限/超管檢查等能力，其中部分端點接受 `token` query 參數，若未嚴格限制或關閉，存在敏感資訊曝光/誤用風險。
- 位置：
  - [backend/routers/debug.py](backend/routers/debug.py#L1-L151)
  - [backend/main_legacy.py](backend/main_legacy.py#L565-L640)

### 3) 金鑰與機密資訊在日誌中外洩風險（高）
- 現況：
  - `ENCRYPTION_KEY` 缺失時會產生臨時金鑰並輸出到 stderr（可能導致機密曝露與資料不可解密）。
  - DB 連線字串完整輸出到日誌（可能包含帳密）。
  - Token 前綴、Email 直接輸出到日誌。
- 位置：
  - [backend/core/security.py](backend/core/security.py#L17-L41)
  - [backend/database.py](backend/database.py#L43-L88)
  - [backend/dependencies.py](backend/dependencies.py#L18-L33)

### 4) 缺失 `ENCRYPTION_KEY` 時使用 volatile key（中）
- 現況：未設定 `ENCRYPTION_KEY` 時會生成一次性金鑰，導致已存資料在重啟後無法解密。
- 建議：在正式環境改為 fail-fast 或啟動檢查強制設定。
- 位置：
  - [backend/core/security.py](backend/core/security.py#L17-L41)

### 5) `requests.get` 未設定 timeout（中）
- 現況：交換 long-lived token 的請求未設 timeout，可能造成服務阻塞。
- 位置：
  - [backend/auth.py](backend/auth.py#L217-L235)
  - [backend/modules/auth/service.py](backend/modules/auth/service.py#L207-L226)

### 6) 認證流程與 Token 管理邏輯重複（中）
- 現況：`backend/auth.py` 與 `backend/modules/auth/service.py` 皆包含 `TokenManager`，容易造成行為分歧與維護成本上升。
- 位置：
  - [backend/auth.py](backend/auth.py#L1-L120)
  - [backend/modules/auth/service.py](backend/modules/auth/service.py#L1-L120)

### 7) Token 驗證邏輯分散且重複（中）
- 現況：`verify_google_token` 在多處重複實作，缺乏統一快取/錯誤處理策略。
- 位置：
  - [backend/dependencies.py](backend/dependencies.py#L18-L33)
  - [backend/routers/facebook.py](backend/routers/facebook.py#L31-L41)
  - [backend/routers/debug.py](backend/routers/debug.py#L28-L37)

### 8) 大量 `print` 直接輸出（中）
- 現況：多處使用 `print`（含 DEBUG 與錯誤訊息），缺乏結構化日誌與等級控管，難以在正式環境觀測與稽核。
- 位置：
  - [backend/dependencies.py](backend/dependencies.py#L18-L33)
  - [backend/routers/facebook.py](backend/routers/facebook.py#L79-L112)
  - [backend/auth.py](backend/auth.py#L1-L40)

### 9) 每次請求寫入 `debug_fields.log`（低）
- 現況：每次呼叫 `get_custom_report` 都嘗試寫入檔案，可能影響效能並增加 I/O。
- 位置：
  - [backend/async_services.py](backend/async_services.py#L385-L389)

### 10) 例外處理中寫入 `debug_auth.log`（低）
- 現況：`get_current_user` 發生例外時直接寫入檔案，可能在併發場景造成 I/O 競爭與檔案膨脹。
- 位置：
  - [backend/dependencies.py](backend/dependencies.py#L164-L173)

---

如需我針對上述任一項提出具體修正方案或實作，請指示優先順序。