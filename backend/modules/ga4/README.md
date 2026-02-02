# GA4 Module

Google Analytics 4 整合模組 - 提供 GA4 認證、屬性列表、分析資料等功能。

## 功能

- **OAuth 認證**: Google OAuth 2.0 授權流程
- **屬性列表**: 取得用戶已驗證的 GA4 屬性
- **分析資料**: 取得工作階段、使用者、瀏覽頁數等指標
- **自訂報表**: 支援多維度、多指標的靈活報表
- **即時資料**: 支援即時分析資料

## 檔案結構

```
modules/ga4/
├── __init__.py          # 模組導出
├── router.py            # API 端點
├── service.py           # GA4 服務
└── README.md            # 本文件
```

## 使用方式

### 在 FastAPI 應用中使用

```python
from fastapi import FastAPI, Depends
from modules.ga4 import router as ga4_router, GA4Service
from modules.auth import get_current_user

app = FastAPI()

# 註冊 GA4 Router
app.include_router(ga4_router)

# 在端點中使用 GA4Service
@app.get("/custom-ga4-data")
async def custom_data(user = Depends(get_current_user)):
    properties, error = GA4Service.list_properties(user)
    return {"properties": properties}
```

### GA4Service 方法

| 方法 | 說明 |
|------|------|
| `exchange_code(user, code, db)` | 交換授權碼取得 Token |
| `get_credentials(user)` | 取得 Google Credentials 物件 |
| `list_properties(user)` | 列出用戶已驗證的屬性 |
| `get_analytics(user, property_id, ...)` | 取得分析資料 |

## API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/ga4/authorize` | 授權連接 |
| GET | `/api/ga4/properties` | 取得屬性列表 |
| GET | `/api/ga4/report` | 取得分析報表 |

## 依賴

- `google-auth`
- `google-api-python-client`
- `google-analytics-data`

## 權限

此模組需要以下權限：
- `ga4:property:connect` - 連接 GA4 屬性
- `ga4:analytics:view` - 查看分析資料

## 設定

在環境變數中設定：
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## 資料結構

### 屬性 (Property)
```python
{
    "name": "properties/123456789",
    "displayName": "My GA4 Property",
    "propertyType": "PROPERTY_TYPE_ORDINARY",
    "createTime": "2023-01-01T00:00:00Z"
}
```

### 報表資料 (Report)
```python
{
    "dimensionHeaders": [...],
    "metricHeaders": [...],
    "rows": [...],
    "rowCount": 100
}
```