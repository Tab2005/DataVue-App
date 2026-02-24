# 實作記錄：H-2/H-3 — print() 轉換為 logger

> **對應計畫**：`03_緊急修復_print轉logger.md`  
> **執行日期**：2026-02-24  
> **審查問題**：H-2（gsc_service.py）、H-3（zeabur_client.py）  
> **狀態**：✅ 完成

---

## 摘要

將兩個業務邏輯檔案中的 `print()` 呼叫全面替換為標準 `logging` 模組，消除生產環境中不受控制的文字輸出，並對含敏感資訊的輸出進行遮蔽處理。

---

## 修改檔案

| 檔案 | 替換前 print 數 | 替換後 print 數（業務邏輯） | 變動 |
|------|----------------|--------------------------|------|
| `backend/gsc_service.py` | 18 | **0** | ✅ 全部替換 |
| `backend/services/ai/zeabur_client.py` | 11 | **0**（5 個業務邏輯）| ✅ 業務邏輯全部替換，`test_client()` 保留 6 個 |

---

## gsc_service.py 修改詳情

### 新增 import

```python
import logging
logger = logging.getLogger(__name__)
```

### 替換清單

| 原始行號 | 原始內容摘要 | 替換後 | 日誌等級 | 備註 |
|---------|------------|--------|---------|------|
| 49 | `print(f"DEBUG: Attempting manual token exchange with clientId={client_id[:10]}...")` | `logger.debug("Attempting manual token exchange (client_id: %s****, secret_prefix: %s)", ...)` | DEBUG | 敏感資訊遮蔽：client_id 只保留前 4 碼 |
| 50 | `print(f"DEBUG: Auth Code Length: {len(code)}")` | `logger.debug("Auth Code received, length=%d", len(code))` | DEBUG | 不輸出實際 code 內容 |
| 64 | `print(f"DEBUG: Trying URI='{uri}' WITH SECRET")` | `logger.debug("Trying URI='%s' WITH SECRET", uri)` | DEBUG | — |
| 69 | `print(f"DEBUG: Status: {response.status_code}")` | `logger.debug("Status: %s", response.status_code)` | DEBUG | — |
| 76 | `print(f"DEBUG: Error: {err}")` | `logger.debug("Error: %s", err)` | DEBUG | — |
| 80 | `print("DEBUG: Trying attempts WITHOUT SECRET")` | `logger.debug("Trying attempts WITHOUT SECRET")` | DEBUG | — |
| 83 | `print(f"DEBUG: Trying URI='{uri}' NO SECRET")` | `logger.debug("Trying URI='%s' NO SECRET", uri)` | DEBUG | — |
| 86 | `print(f"DEBUG: Status: {response.status_code}")` | `logger.debug("Status: %s", response.status_code)` | DEBUG | — |
| 90 | `print(f"DEBUG: Error: {response.json().get('error')}")` | `logger.debug("Error: %s", response.json().get('error'))` | DEBUG | — |
| 94 | `print(f"ERROR BODY: {error_detail}")` | `logger.error("Token exchange failed, error body: %s", error_detail)` | ERROR | — |
| 104 | `print(f"ERROR BODY: {error_detail}")` | `logger.error("Token exchange failed, error body: %s", error_detail)` | ERROR | — |
| 123 | `print("=== GSC AUTH ERROR START ===")` 、`traceback.print_exc()`、`print("=== GSC AUTH ERROR END ===")` | `logger.exception("GSC authentication error")` | ERROR | 合併為單一 exception 呼叫（自動包含 traceback） |
| 168 | `print("[GSC] Token refreshed successfully")` | `logger.info("[GSC] Token refreshed successfully")` | INFO | — |
| 174 | `print("[GSC] New token saved to database")` | `logger.info("[GSC] New token saved to database")` | INFO | — |
| 176 | `print(f"[GSC] Token refresh failed: {e}")` | `logger.warning("[GSC] Token refresh failed: %s", e)` | WARNING | 可恢復錯誤改為 WARNING |
| 240 | `print(f"[GSC REDIS HIT] Returning {len(cached_data)} rows.")` | `logger.debug("[GSC REDIS HIT] Returning %d rows.", len(cached_data))` | DEBUG | — |
| 314 | `print(f"[GSC Pagination] Loaded {len(all_rows)} rows so far...")` | `logger.debug("[GSC Pagination] Loaded %d rows so far...", len(all_rows))` | DEBUG | — |

---

## zeabur_client.py 修改詳情

### 新增 import

```python
import logging
logger = logging.getLogger(__name__)
```

### 業務邏輯替換清單

| 原始行號 | 原始內容摘要 | 替換後 | 日誌等級 |
|---------|------------|--------|---------|
| 124 | `print(f"[INFO] Zeabur AI Client initialized with endpoint: {self.base_url}")` | `logger.info("Zeabur AI Client initialized with endpoint: %s", self.base_url)` | INFO |
| 173 | `print(f"[INFO] Generating content with {model} (provider: ...)")` | `logger.debug("Generating content with %s (provider: %s)", model, ...)` | DEBUG |
| 174 | `print(f"[INFO] Temperature: {temperature}, Max tokens: {max_output}")` | `logger.debug("Temperature: %s, Max tokens: %s", temperature, max_output)` | DEBUG |
| 205 | `print(f"[ERROR] AI generation failed: {e}")` | `logger.error("AI generation failed: %s", e, exc_info=True)` | ERROR |
| 251 | `print(f"[ERROR] Connection test failed: {e}")` | `logger.error("Connection test failed: %s", e, exc_info=True)` | ERROR |

### 保留的 print（__main__ 測試區塊）

`test_client()` 函式（第 259 行起）及 `if __name__ == "__main__":` 區塊內的 print 全部保留，這些僅在手動執行腳本時使用，不影響生產環境。

---

## 設計決策

### 格式化方式：`%s` 而非 f-string

所有替換採用 `%s`/`%d` 格式化，而非 f-string。理由：
- 當日誌等級被過濾（例如 `LOG_LEVEL=INFO`）時，`%s` 格式化可跳過字串拼接，效能較好。
- 例：`logger.debug("Status: %s", response.status_code)` — `status_code` 不會被求值與拼接。

### 敏感資訊遮蔽

| 敏感欄位 | 遮蔽方式 |
|---------|---------|
| `client_id` | 只保留前 4 碼，後接 `****` |
| `client_secret` | 只保留前 3 碼 prefix |
| Auth Code 內容 | 僅輸出長度（`len(code)`），不輸出實際值 |

### exception vs error

在 OAuth 錯誤捕獲區塊，原有 `print("=== ... ===") + traceback.print_exc()` 三行合併為：

```python
logger.exception("GSC authentication error")
```

`logger.exception()` 等同於 `logger.error(..., exc_info=True)`，自動附加完整的 traceback，輸出更精簡。

---

## 驗收結果

| 項目 | 預期 | 實際 | 狀態 |
|------|------|------|------|
| `gsc_service.py` 業務邏輯 print 數 | 0 | 0 | ✅ |
| `zeabur_client.py` 業務邏輯 print 數 | 0 | 0 | ✅ |
| `zeabur_client.py` `__main__` 區塊 print 保留 | 全部保留 | 保留（第 264–294 行） | ✅ |
| logger 宣告正確加入 | 兩檔案均有 | ✅ | ✅ |
| 敏感資訊（client_id）遮蔽 | 只保留前 4 碼 | `client_id[:4] + "****"` | ✅ |

---

## 驗證指令

```powershell
# 確認 gsc_service.py 無殘留業務邏輯 print（應返回 Count=0）
Select-String -Path "backend/gsc_service.py" -Pattern "^\s*print\(" | Measure-Object | Select-Object Count

# 確認 zeabur_client.py 剩餘 print 均在測試函式內（行號 > 259）
Select-String -Path "backend/services/ai/zeabur_client.py" -Pattern "^\s*print\(" | Format-Table LineNumber, Line
```
