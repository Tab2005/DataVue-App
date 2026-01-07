# AI Hub Module

AI 整合模組 - 提供 AI 客戶端、意圖分類器、以及相關 API。

## 功能

- **多提供者支援**: Zeabur AI Hub、Google Gemini
- **意圖分類**: 基於 AI 的搜尋意圖分析（informational, commercial, navigational, transactional）
- **串流回應**: 支援 Server-Sent Events 串流 AI 回應
- **加密儲存**: AI API Key 使用 Fernet 加密儲存

## 檔案結構

```
modules/ai_hub/
├── __init__.py              # 模組導出
├── clients/                  # AI 客戶端
│   ├── __init__.py
│   ├── gemini.py            # Google Gemini 客戶端
│   └── zeabur.py            # Zeabur AI Hub 客戶端
├── intent_classifier.py     # 意圖分類器
├── router.py                # API 端點
├── service.py               # 主要 AI 服務
└── README.md                # 本文件
```

## 使用方式

### 在 FastAPI 應用中使用

```python
from fastapi import FastAPI
from modules.ai_hub import router as ai_router, AIService

app = FastAPI()

# 註冊 AI Router
app.include_router(ai_router, prefix="/api/ai")

# 測試 AI 連線
success = AIService.test_connection(
    api_key="your_api_key",
    provider="zeabur",  # or "gemini"
    model="gemini-2.5-flash"
)
```

### 使用意圖分類器

```python
from modules.ai_hub import AIIntentClassifier

classifier = AIIntentClassifier(api_key="key", provider="gemini")
result = classifier.classify_queries([
    "如何減肥",           # informational
    "Nike 跑鞋價格",      # commercial
    "Facebook 登入",      # navigational
    "線上購買 iPhone"     # transactional
])

print(result)
# {
#     "success": True,
#     "results": [
#         {"query": "如何減肥", "intent": "informational", "confidence": 0.95},
#         ...
#     ]
# }
```

### 直接使用客戶端

```python
from modules.ai_hub import ZeaburAIClient, GoogleGeminiClient

# Zeabur (OpenAI 相容)
zeabur = ZeaburAIClient(api_key="key")
response = zeabur.chat("Explain AI in 50 words")

# Gemini
gemini = GoogleGeminiClient(api_key="key")
result = gemini.classify_intents(["query1", "query2"])
```

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/ai/providers` | GET | 取得可用 AI 提供者 |
| `/api/ai/models` | GET | 取得可用模型列表 |
| `/api/ai/test-connection` | POST | 測試 AI 連線 |
| `/api/ai/analyze` | POST | 分析資料（串流回應） |
| `/api/ai/settings` | GET | 取得 AI 設定 |
| `/api/ai/settings` | POST | 儲存 AI 設定 |
| `/api/ai/test-gemini` | POST | 測試 Gemini 連線 |

## 依賴

- `openai`: Zeabur AI Hub (OpenAI 相容 API)
- `google-genai`: Google Gemini API（可選）
- `core.security`: 加密金鑰管理
- `modules.auth`: Token 管理（AI Key 儲存）

## 複用到其他專案

1. 複製以下資料夾/檔案:
   - `modules/ai_hub/`
   - `services/ai/`
   - `ai_service.py`
   - `core/security.py`
   
2. 安裝依賴:
   ```bash
   pip install openai google-genai cryptography
   ```

3. 設定環境變數:
   ```bash
   ZEABUR_AI_HUB_API_KEY=your_zeabur_key  # 可選
   GOOGLE_AI_API_KEY=your_gemini_key       # 可選
   ENCRYPTION_KEY=your_fernet_key
   ```
