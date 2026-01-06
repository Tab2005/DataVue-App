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

### Fallback 順序

當後端需要 API Key 時，依以下順序尋找：

1. 使用者資料庫設定 (已加密)
2. Request 參數 (向後相容)
3. 環境變數 (`ZEABUR_AI_HUB_API_KEY` / `GOOGLE_AI_API_KEY`)

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
