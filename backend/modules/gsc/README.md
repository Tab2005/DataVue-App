# GSC Module

Google Search Console 整合模組 - 提供 GSC 認證、網站列表、分析資料等功能。

## 功能

- **OAuth 認證**: Google OAuth 2.0 授權流程
- **網站列表**: 取得用戶已驗證的 GSC 網站
- **分析資料**: 取得點擊數、曝光數、CTR、排名等指標
- **頁面標題抓取**: 批次抓取頁面標題（含資料庫快取）
- **AI 意圖分析**: 基於 AI 的搜尋意圖分類

## 檔案結構

```
modules/gsc/
├── __init__.py          # 模組導出
├── router.py            # API 端點
├── service.py           # GSC 服務
└── README.md            # 本文件
```

## 使用方式

### 在 FastAPI 應用中使用

```python
from fastapi import FastAPI, Depends
from modules.gsc import router as gsc_router, GSCService
from modules.auth import get_current_user

app = FastAPI()

# 註冊 GSC Router
app.include_router(gsc_router)

# 在端點中使用 GSCService
@app.get("/custom-gsc-data")
async def custom_data(user = Depends(get_current_user)):
    sites, error = GSCService.list_sites(user)
    return {"sites": sites}
```

### GSCService 方法

| 方法 | 說明 |
|------|------|
| `exchange_code(user, code, db)` | 交換授權碼取得 Token |
| `get_credentials(user)` | 取得 Google Credentials 物件 |
| `list_sites(user)` | 列出用戶已驗證的網站 |
| `get_analytics(user, site_url, start_date, end_date, dimensions)` | 取得分析資料 |

## API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/gsc/authorize` | POST | 交換授權碼 |
| `/api/gsc/sites` | GET | 列出網站 |
| `/api/gsc/analytics` | GET | 取得分析資料 |
| `/api/gsc/page-titles` | POST | 抓取頁面標題 |
| `/api/gsc/page-intents` | POST | AI 意圖分析 |

## 依賴

- `google-auth`: Google OAuth 認證
- `google-api-python-client`: Google API 客戶端
- `httpx`: HTTP 客戶端（頁面標題抓取）
- `modules.ai_hub`: AI 意圖分類（可選）

## 複用到其他專案

1. 複製以下資料夾/檔案:
   - `modules/gsc/`
   - `gsc_service.py`
   - `database.py`（User 模型需包含 GSC Token 欄位）
   
2. 安裝依賴:
   ```bash
   pip install google-auth google-api-python-client httpx
   ```

3. 設定環境變數:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

4. 在 User 模型中添加:
   ```python
   gsc_access_token = Column(String)
   gsc_refresh_token = Column(String)
   gsc_expires_at = Column(DateTime)
   ```
