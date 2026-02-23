# H-2/H-3：print() 轉換為 logger

> **優先級**：🟠 High  
> **預計工時**：1–2 小時  
> **執行時程**：部署前完成  
> **審查問題編號**：H-2（gsc_service.py）、H-3（zeabur_client.py）

---

## 問題說明

以下兩個檔案在業務邏輯中仍有大量 `print()` 呼叫，在生產環境中：
- 不受日誌等級控制（DEBUG print 永遠輸出）
- 無時間戳、無模組名稱
- 部分包含敏感資訊（clientId 前綴、Token 狀態）

| 檔案 | 問題 print 數 | 類型 |
|------|-------------|------|
| `backend/gsc_service.py` | 18 | 業務邏輯 print（需全部轉換） |
| `backend/services/ai/zeabur_client.py` | ~5 | 業務邏輯 print（`__main__` 區塊內可保留） |

---

## gsc_service.py 修復

### 第一步：確認目前的 print 位置

```powershell
Select-String -Path "backend/gsc_service.py" -Pattern "print\(" | Select-Object LineNumber, Line
```

### 第二步：加入 logger 宣告

在 `gsc_service.py` 頂部（import 區塊之後），確認或新增：

```python
# 若 gsc_service.py 頂部尚未有 logger 宣告，新增以下兩行：
import logging
logger = logging.getLogger(__name__)
```

### 第三步：逐行替換規則

依照 print 內容的語意，對應轉換如下：

| 原始 print 模式 | 替換為 | 備註 |
|---------------|--------|------|
| `print(f"DEBUG: ...")` | `logger.debug(f"...")` | DEBUG 資訊 |
| `print(f"ERROR: ...")` | `logger.error(f"...")` | 錯誤資訊 |
| `print(f"[GSC] ...")` | `logger.info(f"[GSC] ...")` | 一般流程資訊 |
| `print(f"... client_id[:10] ...")` | `logger.debug(f"...")` | 含敏感資訊，改為 debug |
| `print(f"... token ...")` | `logger.debug(f"...")` | 含 Token 相關，改為 debug |

### 第四步：敏感資訊遮蔽

對包含 client ID、Token 狀態的日誌，確保遮蔽：

```python
# ❌ 原始（敏感資訊洩漏）
print(f"DEBUG: Attempting manual token exchange with clientId={client_id[:10]}...")
print(f"DEBUG: Auth Code Length: {len(code)}")

# ✅ 修復後
logger.debug(
    "Attempting manual token exchange",
    extra={"client_id_prefix": client_id[:4] + "****"}  # 只保留前 4 碼
)
logger.debug(f"Auth Code received (length={len(code)})")  # 不輸出實際 code
```

### 具體替換清單（依已知行號）

| 原始行號 | 原始內容摘要 | 替換方式 |
|---------|------------|---------|
| 49 | `print(f"DEBUG: Attempting manual token exchange...")` | `logger.debug(...)` |
| 50 | `print(f"DEBUG: Auth Code Length: ...")` | `logger.debug(...)` |
| 64 | `print(f"DEBUG: ...")` | `logger.debug(...)` |
| 69 | `print(f"DEBUG: ...")` | `logger.debug(...)` |
| 76 | `print(...)` | `logger.info(...)` 或 `logger.debug(...)` |
| 80 | `print(...)` | `logger.info(...)` 或 `logger.debug(...)` |
| 83 | `print(...)` | 對應語意轉換 |
| 86 | `print(...)` | 對應語意轉換 |
| 90 | `print(...)` | 對應語意轉換 |
| 94 | `print(...)` | 對應語意轉換 |
| 104 | `print(...)` | 對應語意轉換 |
| 123 | `print(...)` | 對應語意轉換 |
| 125 | `print(...)` | 對應語意轉換 |
| 168 | `print(...)` | 對應語意轉換 |
| 174 | `print(...)` | 對應語意轉換 |
| 176 | `print(...)` | 對應語意轉換 |
| 240 | `print(...)` | 對應語意轉換 |
| 314 | `print(...)` | 對應語意轉換 |

> ⚠️ 行號在後續修改後可能偏移，以實際 `Select-String` 查詢結果為準。

### 步驟五：執行替換腳本（PowerShell 輔助）

```powershell
# 查看所有 print 行（確認範圍）
Select-String -Path "backend/gsc_service.py" -Pattern "^\s*print\(" | Format-Table LineNumber, Line -Wrap

# 驗證替換結果
Select-String -Path "backend/gsc_service.py" -Pattern "^\s*print\(" | Measure-Object | Select-Object Count
# 預期：Count = 0
```

---

## zeabur_client.py 修復

### 確認業務邏輯 vs 測試腳本的 print

```
services/ai/zeabur_client.py 的 print 分布：
  業務邏輯（需轉換）：第 124、173、174、205、251、261、268-291 行
  __main__ 測試區塊（可保留 print）：if __name__ == "__main__": 以下
```

### 加入 logger 宣告

```python
# 在 zeabur_client.py 頂部加入（若未存在）：
import logging
logger = logging.getLogger(__name__)
```

### 業務邏輯 print 替換規則

```python
# ❌ 業務邏輯中的 print（這些在 class 方法或模組級別函式中）
print(f"[Zeabur] Sending request to ...")
print(f"[Zeabur] Response status: ...")
print(f"Error: ...")

# ✅ 修復後
logger.debug(f"Sending request to ...")
logger.debug(f"Response status: {response.status_code}")
logger.error(f"Request failed: ...")
```

### `__main__` 區塊的處理

```python
# ✅ 這些 print 可以保留，因為是手動測試腳本
if __name__ == "__main__":
    print("Testing Zeabur client...")  # 保留
    result = client.some_method()
    print(f"Result: {result}")         # 保留
```

---

## 驗證步驟

### 1. 確認 gsc_service.py 無殘留 print

```powershell
# 業務邏輯 print 數量應為 0
Select-String -Path "backend/gsc_service.py" -Pattern "^\s*print\(" | Measure-Object | Select-Object Count
```

### 2. 確認 zeabur_client.py 業務邏輯 print 已清除

```powershell
# 查看所有 print 位置，確認只剩 __main__ 區塊下方的 print
Select-String -Path "backend/services/ai/zeabur_client.py" -Pattern "^\s*print\(" | Format-Table LineNumber, Line
```

### 3. 測試日誌輸出格式

```powershell
cd backend
$env:LOG_LEVEL = "DEBUG"
python -c "
import gsc_service
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
# 呼叫任一觸發 logger 的函式
"
```

**預期輸出格式**：
```
2026-02-24 10:00:00,123 [gsc_service] DEBUG: Attempting manual token exchange
2026-02-24 10:00:00,124 [gsc_service] DEBUG: Auth Code received (length=...）
```

---

## 驗收標準

- [ ] `gsc_service.py` 中業務邏輯 `print()` 數量為 **0**
- [ ] `zeabur_client.py` 中業務邏輯 `print()` 數量為 **0**（`__main__` 區塊不計）
- [ ] 所有替換後的 `logger.xxx()` 呼叫格式正確（有 f-string 或 % 格式化）
- [ ] 應用程式啟動後無因 logger 設定錯誤導致的 AttributeError
- [ ] 設定 `LOG_LEVEL=DEBUG` 後，原 print 訊息改以結構化日誌格式輸出

---

## 注意事項

### 日誌等級選擇準則

| 情境 | 等級 | 範例 |
|------|------|------|
| 正常流程記錄（高頻） | `DEBUG` | Token 交換開始、API 呼叫參數 |
| 重要流程節點 | `INFO` | Token 刷新成功、連線建立 |
| 可恢復的異常 | `WARNING` | 快取 miss、重試 |
| 操作失敗 | `ERROR` | API 呼叫失敗、Token 無效 |
| 系統級致命錯誤 | `CRITICAL` | 資料庫連線失敗（通常由 startup 層處理） |

### 轉換前後對照範例

```python
# gsc_service.py 典型情況

# Before（不佳）：
print(f"DEBUG: Attempting manual token exchange with clientId={client_id[:10]}...")
print(f"DEBUG: Auth Code Length: {len(code)}")
print(f"[GSC] Successfully refreshed token for user {user_id}")
print(f"ERROR: Failed to fetch GSC data: {e}")
print(f"GSC property list fetched: {len(properties)} items")

# After（推薦）：
logger.debug("Attempting manual token exchange (client_id prefix: %s****)", client_id[:4])
logger.debug("Auth Code received, length=%d", len(code))
logger.info("Successfully refreshed token for user %s", user_id)
logger.error("Failed to fetch GSC data: %s", e, exc_info=True)
logger.debug("GSC property list fetched: %d items", len(properties))
```

> 💡 使用 `%s` 格式化（而非 f-string）在日誌等級被過濾時可以跳過字串拼接，效能較好。但 f-string 可讀性較高，兩種方式在功能上均正確。
