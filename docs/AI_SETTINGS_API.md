# AI Settings API 架構文件

> **版本**: v1.6.7  
> **更新日期**: 2026-01-06  
> **儲存範圍**: Per-User (個人專屬，不共用)

---

## 概覽

AI API Keys 採用 **個人專屬模式**，與 Facebook Ads (團隊共用) 不同。每個使用者獨立設定自己的 API Key，不會與其他團隊成員共用。

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Settings Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   前端 SettingsModal                                             │
│        │                                                        │
│        ├─→ GET /api/ai/settings ─────→ 讀取設定狀態              │
│        │                                                        │
│        ├─→ POST /api/ai/settings ────→ 儲存 (Fernet 加密)        │
│        │                                                        │
│        └─→ DELETE /api/ai/settings/{provider} ──→ 清除 Key      │
│                                                                 │
│   GSCStats (意圖分析)                                            │
│        │                                                        │
│        └─→ POST /api/gsc/page-intents                           │
│                 │                                               │
│                 └─→ TokenManager.get_ai_api_key() ─→ 解密取 Key  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 資料庫結構

### User Table 新增欄位

| 欄位名稱 | 類型 | 加密 | 說明 |
|---------|------|------|------|
| `zeabur_api_key` | String | ✅ Fernet | Zeabur AI Hub API Key |
| `gemini_api_key` | String | ✅ Fernet | Google Gemini API Key |
| `ai_provider` | String | ❌ | 啟用的提供者 (`zeabur` / `gemini`) |
| `ai_model` | String | ❌ | 選擇的 AI 模型 |

### 與 Facebook Ads 的比較

| 設定類型 | 儲存位置 | 共用範圍 |
|----------|---------|---------|
| Facebook Ads Token | `teams` 表 | 🔗 團隊共用 |
| AI API Keys | `users` 表 | 👤 個人專屬 |

---

## API 端點

### `GET /api/ai/settings`

取得目前使用者的 AI 設定狀態。

**Request Headers:**
```
Authorization: Bearer {google_token}
```

**Response:**
```json
{
    "ai_provider": "zeabur",
    "ai_model": "gemini-2.5-flash",
    "has_zeabur_key": true,
    "has_gemini_key": false
}
```

> ⚠️ **安全性**: API 不會回傳 Key 原文，只回傳 `has_*_key` 布林值

---

### `POST /api/ai/settings`

儲存 AI 設定。API Keys 會在儲存前使用 Fernet 加密。

**Request Body:**
```json
{
    "zeabur_api_key": "sk-xxx...",     // 選填，會加密儲存
    "gemini_api_key": "AIza...",       // 選填，會加密儲存
    "ai_provider": "gemini",           // 選填，'zeabur' 或 'gemini'
    "ai_model": "gemini-2.5-flash"     // 選填
}
```

**Response:**
```json
{
    "success": true,
    "message": "AI settings saved successfully",
    "settings": {
        "ai_provider": "gemini",
        "ai_model": "gemini-2.5-flash",
        "has_zeabur_key": true,
        "has_gemini_key": true
    }
}
```

---

### `DELETE /api/ai/settings/{provider}`

清除指定提供者的 API Key。

**Path Parameters:**
- `provider`: `zeabur` 或 `gemini`

**Response:**
```json
{
    "success": true,
    "message": "gemini API key cleared"
}
```

---

### `POST /api/ai/test-gemini`

測試 Google Gemini API 連線狀態。

**Request Headers:**
```
Authorization: Bearer {google_token}
```

**Response (成功):**
```json
{
    "success": true,
    "message": "Connected to Google Gemini API",
    "response": "Connection successful!",
    "model": "gemini-2.5-flash",
    "provider": "gemini"
}
```

**Response (失敗 - 無 API Key):**
```json
{
    "success": false,
    "message": "No Google Gemini API key configured. Please save your API key first.",
    "provider": "gemini"
}
```

---

## Google Gemini Rate Limit 批次處理

### 免費版限制

| 模型 | RPM | TPM | RPD |
|------|-----|-----|-----|
| gemini-2.5-flash | 10 | 250,000 | 500 |
| gemini-2.5-pro | 2 | 50,000 | 25 |

> **RPM** = Requests Per Minute, **TPM** = Tokens Per Minute, **RPD** = Requests Per Day

### 批次處理機制

當使用 Gemini 免費版分析超過 10 個關鍵字時，後端會自動啟用批次處理：

```
┌─────────────────────────────────────────────────────────────────┐
│                   Gemini 批次處理流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   25 個關鍵字 → 分成 3 批次                                       │
│                                                                 │
│   Batch 1 (10 KWs) ─→ 6 秒延遲 ─→                               │
│   Batch 2 (10 KWs) ─→ 6 秒延遲 ─→                               │
│   Batch 3 (5 KWs)                                               │
│                                                                 │
│   總預估時間: 3 × 6 = 18 秒                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 實作程式碼 (`intent_classifier.py`)

```python
BATCH_SIZE = 10  # 每批次關鍵字數量
BATCH_DELAY = 6  # 批次間延遲秒數 (符合 10 RPM)

# 自動判斷是否需要批次處理
use_batching = self.provider == "gemini" and len(queries) > BATCH_SIZE
```

### 前端提示

當使用 Gemini 進行「繼續分析」時，會顯示批次處理提示：

```
⚠️ 繼續分析將分析剩餘 25 個關鍵字

這會消耗 AI API 額度，確定要繼續嗎？

💎 您正在使用 Google Gemini，因免費版有請求限制，
分析將分 3 批次進行，預計需要 18 秒。
```

---

## 後端實作

### TokenManager 新增方法 (`auth.py`)

```python
class TokenManager:
    @staticmethod
    def save_ai_settings(google_id, zeabur_api_key=None, gemini_api_key=None, 
                         ai_provider=None, ai_model=None):
        """儲存 AI 設定 (Keys 會 Fernet 加密)"""
        
    @staticmethod
    def get_ai_settings(google_id):
        """讀取 AI 設定狀態 (不含 Key 原文)"""
        
    @staticmethod
    def get_ai_api_key(google_id, provider=None):
        """取得解密後的 API Key (供後端使用)"""
```

### 加密機制

- **演算法**: Fernet (對稱加密)
- **金鑰來源**: 環境變數 `ENCRYPTION_KEY`
- **相同金鑰用於**: Facebook Token, AI API Keys

---

## 前端實作

### SettingsModal.jsx

```javascript
// 新增 API 函數
const fetchAiSettings = async () => { /* GET /api/ai/settings */ }
const saveAiSettingsToServer = async (settings) => { /* POST /api/ai/settings */ }

// useEffect: 開啟 Modal 時從後端載入設定
useEffect(() => {
    if (isOpen) {
        fetchAiSettings().then(settings => {
            setActiveAiProvider(settings.ai_provider);
            localStorage.setItem('ai_provider', settings.ai_provider); // Sync for GSCStats
        });
    }
}, [isOpen]);
```

### GSCStats.jsx

```javascript
// 只傳送 provider，不傳送 API Key
const requestBody = {
    provider: localStorage.getItem('ai_provider') || 'zeabur',
    // ai_api_key 不再由前端傳送，後端會從 DB 讀取
};
```

---

## 安全性設計

| 層級 | 機制 |
|------|------|
| **傳輸層** | HTTPS |
| **儲存層** | Fernet 加密 |
| **API 層** | 不回傳 Key 原文 |
| **前端層** | 不儲存 Key 在 localStorage |

### API Key Fallback 機制

當後端需要 API Key 時，會依以下優先順序尋找：

```
┌─────────────────────────────────────────────────────────────────┐
│                   API Key 優先順序 (由高到低)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1️⃣ 使用者資料庫設定 (個人加密儲存)                              │
│         ↓ 如果沒有                                               │
│   2️⃣ Request 參數 (向後相容)                                     │
│         ↓ 如果沒有                                               │
│   3️⃣ 環境變數 (全域共用 / Fallback)                              │
│         ↓ 如果沒有                                               │
│   ❌ 回傳錯誤訊息                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 環境變數設定

| 環境變數 | Provider | 用途 |
|---------|----------|------|
| `ZEABUR_AI_HUB_API_KEY` | `zeabur` | Zeabur AI Hub 全域金鑰 |
| `GOOGLE_AI_API_KEY` | `gemini` | Google Gemini 全域金鑰 |

> 💡 **提示**: 環境變數作為 Fallback，當使用者沒有設定個人 API Key 時會自動使用。

### 實際程式碼邏輯

```python
# backend/routers/gsc.py

# Step 1: 從資料庫取得加密的 API Key
api_key = TokenManager.get_ai_api_key(user.google_id, provider=provider)

# Step 2: Fallback 到環境變數
if not api_key:
    if provider == "gemini":
        api_key = request.ai_api_key or os.getenv("GOOGLE_AI_API_KEY")
    else:
        api_key = request.ai_api_key or os.getenv("ZEABUR_AI_HUB_API_KEY")
```

### 使用情境範例

| 情境 | Zeabur 選擇時 | Gemini 選擇時 |
|------|--------------|--------------|
| 使用者有設定個人 Key | ✅ 用個人 Key | ✅ 用個人 Key |
| 使用者沒設定，有環境變數 | ✅ 用環境變數 | ✅ 用環境變數 |
| 都沒設定 | ❌ 回傳錯誤 | ❌ 回傳錯誤 |

### 典型部署配置

```bash
# .env (後端環境變數)

# 必要 - 用於加密所有敏感資料
ENCRYPTION_KEY=your-fernet-key-here

# 選填 - 全域 Fallback (所有使用者共用)
ZEABUR_AI_HUB_API_KEY=sk-zeabur-xxx...

# 選填 - Google Gemini 全域 Fallback
GOOGLE_AI_API_KEY=AIza...
```

---

## 支援的 AI 模型

### Zeabur AI Hub

| 模型 | 說明 |
|------|------|
| `gemini-2.5-flash` | ✅ 推薦，快速 |
| `gemini-2.5-pro` | 高品質 |
| `claude-sonnet-4-5` | Claude 4.5 |
| `gpt-4o` | OpenAI GPT-4o |

### Google Gemini Direct

| 模型 | 說明 |
|------|------|
| `gemini-2.5-flash` | ✅ 推薦 |
| `gemini-2.5-pro` | 高品質 |
| `gemini-2.0-flash` | 上一代 |
| `gemini-1.5-flash` | 穩定版 |

---

## 相關檔案

| 檔案 | 用途 |
|------|------|
| `backend/database.py` | User 表欄位定義 |
| `backend/auth.py` | TokenManager 加密/解密方法 |
| `backend/routers/ai.py` | AI Settings API 端點 |
| `backend/routers/gsc.py` | GSC API (使用 AI Key) |
| `backend/services/ai/gemini_client.py` | Google Gemini 直連客戶端 |
| `frontend/src/components/SettingsModal.jsx` | 設定 UI |
| `frontend/src/components/GSCStats.jsx` | 意圖分析 UI |
