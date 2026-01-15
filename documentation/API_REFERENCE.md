# DataVue-App - API 文件

## 📖 概述

本文件提供 DataVue-App 後端 API 的完整參考，包括端點列表、請求/回應格式、認證方式及錯誤處理。

**Base URL：** `http://localhost:8000` (開發環境) 或您的部署網址

**API 版本：** v2.0.0

---

## 🔐 認證方式

所有需要認證的端點使用 **Bearer Token** 認證。

### 取得 Token

1. 前端透過 Google OAuth 登入取得 `id_token`
2. 將 Token 放入 `Authorization` Header

### 請求範例

```http
GET /api/users/me HTTP/1.1
Host: localhost:8000
Authorization: Bearer <your_google_id_token>
```

### 權限層級

| 層級 | 說明 |
|------|------|
| **Public** | 無需認證 |
| **Authenticated** | 需要有效 Token |
| **Module** | 需要特定模組權限 (fb_ads, gsc, ga4, ai_hub) |
| **Admin** | 需要 Admin 或 Owner 角色 |
| **Super Admin** | 需要超級管理員權限 |

---

## 📡 端點總覽

### 認證與授權

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| POST | `/api/auth/exchange-token` | Authenticated | 交換 Facebook Long-lived Token |
| GET | `/api/auth/token-status` | Authenticated | 檢查 Token 狀態 |
| GET | `/api/auth/me` | Authenticated | 取得當前使用者資訊 |

### 使用者管理

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/users/me` | Authenticated | 取得個人資料 |
| GET | `/api/users/` | Admin | 列出所有使用者 |
| POST | `/api/users/` | Admin | 建立使用者 |
| GET | `/api/users/{user_id}` | Admin | 取得特定使用者 |
| PUT | `/api/users/{user_id}` | Admin | 更新使用者 |
| DELETE | `/api/users/{user_id}` | Admin | 刪除使用者 |

### 團隊管理

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/teams/me` | Authenticated | 取得我的團隊列表 |
| POST | `/api/teams/` | Authenticated | 建立團隊 |
| GET | `/api/teams/{team_id}` | Authenticated | 取得團隊詳情 |
| PUT | `/api/teams/{team_id}` | Admin | 更新團隊 |
| DELETE | `/api/teams/{team_id}` | Admin | 刪除團隊 |
| GET | `/api/teams/{team_id}/members` | Authenticated | 列出成員 |
| POST | `/api/teams/{team_id}/members` | Admin | 新增成員 |
| PUT | `/api/teams/{team_id}/members/{user_id}` | Admin | 更新成員角色 |
| DELETE | `/api/teams/{team_id}/members/{user_id}` | Admin | 移除成員 |

### 邀請系統

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| POST | `/api/invites/` | Admin | 建立邀請連結 |
| GET | `/api/invites/{code}` | Public | 取得邀請詳情 |
| POST | `/api/invites/{code}/accept` | Authenticated | 接受邀請 |

### Facebook Ads

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/ad-accounts` | Module(fb_ads) | 列出廣告帳戶 |
| GET | `/api/dashboard-data` | Module(fb_ads) | 儀表板數據 |
| GET | `/api/analytics` | Module(fb_ads) | 分析數據 |

### Google Search Console

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| POST | `/api/gsc/authorize` | Authenticated | GSC 授權 |
| GET | `/api/gsc/sites` | Module(gsc) | 列出網站 |
| GET | `/api/gsc/analytics` | Module(gsc) | GSC 數據 |
| POST | `/api/gsc/page-titles` | Module(gsc) | 批次抓取頁面標題 |
| POST | `/api/gsc/page-intents` | Module(gsc) | AI 頁面意圖分析 |

### Google Analytics 4

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| POST | `/api/ga4/authorize` | Authenticated | GA4 授權 |
| GET | `/api/ga4/accounts` | Module(ga4) | 列出帳戶 |
| GET | `/api/ga4/properties` | Module(ga4) | 列出資源 |
| GET | `/api/ga4/analytics` | Module(ga4) | GA4 數據 |

### AI 服務

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/ai/providers` | Module(ai_hub) | 列出 AI 供應商 |
| GET | `/api/ai/models` | Module(ai_hub) | 列出可用模型 |
| POST | `/api/ai/test-connection` | Module(ai_hub) | 測試連線 |
| POST | `/api/ai/analyze` | Module(ai_hub) | 分析數據 |
| POST | `/api/ai/analyze-stream` | Module(ai_hub) | 串流分析 |
| GET | `/api/ai/settings` | Authenticated | 取得 AI 設定 |
| POST | `/api/ai/settings` | Authenticated | 儲存 AI 設定 |
| DELETE | `/api/ai/settings/{provider}` | Authenticated | 刪除 API Key |

### 權限管理

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/permissions/modules` | Admin | 列出所有模組 |
| GET | `/api/permissions/user/{user_id}/modules` | Admin | 取得使用者模組權限 |
| POST | `/api/permissions/user/{user_id}/modules` | Admin | 授予模組權限 |
| DELETE | `/api/permissions/user/{user_id}/modules/{module_name}` | Admin | 撤銷模組權限 |

### 系統管理

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/admin/stats` | Super Admin | 系統統計 |
| GET | `/api/admin/users` | Super Admin | 所有使用者 |
| GET | `/api/admin/teams` | Super Admin | 所有團隊 |
| DELETE | `/api/admin/users/{user_id}` | Super Admin | 強制刪除使用者 |

### 其他

| 方法 | 端點 | 權限 | 說明 |
|------|------|------|------|
| GET | `/api/health` | Public | 健康檢查 |
| GET | `/api/saved-views` | Authenticated | 儲存的視圖 |
| POST | `/api/saved-views` | Authenticated | 新增視圖 |
| DELETE | `/api/saved-views/{view_id}` | Authenticated | 刪除視圖 |

---

## 📝 端點詳細說明

### 1. 認證與授權

#### POST /api/auth/exchange-token

**說明：** 交換 Facebook Short-lived Token 為 Long-lived Token

**權限：** Authenticated

**請求體：**
```json
{
  "app_id": "123456789",
  "app_secret": "abc123def456",
  "short_token": "EAABwzLixnjYBO...",
  "team_id": "team_uuid" // 選用，若為團隊層級
}
```

**回應：**
```json
{
  "message": "Token exchanged successfully"
}
```

**錯誤回應：**
```json
{
  "detail": "Token exchange failed: Invalid credentials"
}
```

---

#### GET /api/auth/token-status

**說明：** 檢查 Facebook Token 的過期狀態

**權限：** Authenticated

**查詢參數：**
- `team_id` (選用): 團隊 ID，若提供則檢查團隊 Token

**回應：**
```json
{
  "expires_at": "2026-03-15T10:30:00Z",
  "days_remaining": 45,
  "is_expired": false,
  "token_exists": true
}
```

---

#### GET /api/auth/me

**說明：** 取得當前使用者資訊

**權限：** Authenticated

**回應：**
```json
{
  "id": "user_uuid",
  "google_id": "123456789",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "member",
  "is_super_admin": false,
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

### 2. 團隊管理

#### GET /api/teams/me

**說明：** 取得當前使用者所屬的所有團隊

**權限：** Authenticated

**回應：**
```json
[
  {
    "id": "team_uuid_1",
    "name": "Marketing Team",
    "owner_id": "user_uuid",
    "created_at": "2025-01-01T00:00:00Z",
    "member_role": "owner"
  },
  {
    "id": "team_uuid_2",
    "name": "Sales Team",
    "owner_id": "another_user_uuid",
    "created_at": "2025-02-01T00:00:00Z",
    "member_role": "member"
  }
]
```

---

#### POST /api/teams/

**說明：** 建立新團隊

**權限：** Authenticated

**請求體：**
```json
{
  "name": "New Team"
}
```

**回應：**
```json
{
  "id": "new_team_uuid",
  "name": "New Team",
  "owner_id": "current_user_uuid",
  "created_at": "2026-01-15T10:30:00Z"
}
```

---

#### GET /api/teams/{team_id}/members

**說明：** 列出團隊成員

**權限：** Authenticated (需為團隊成員)

**回應：**
```json
[
  {
    "user_id": "user_uuid_1",
    "email": "owner@example.com",
    "name": "Owner Name",
    "role": "owner",
    "joined_at": "2025-01-01T00:00:00Z"
  },
  {
    "user_id": "user_uuid_2",
    "email": "member@example.com",
    "name": "Member Name",
    "role": "member",
    "joined_at": "2025-01-15T00:00:00Z"
  }
]
```

---

### 3. Facebook Ads

#### GET /api/ad-accounts

**說明：** 列出可存取的 Facebook 廣告帳戶

**權限：** Module(fb_ads)

**查詢參數：**
- `team_id` (選用): 團隊 ID，使用團隊 Token

**回應：**
```json
{
  "accounts": [
    {
      "id": "act_123456789",
      "name": "My Ad Account",
      "account_status": 1,
      "currency": "USD"
    }
  ]
}
```

**錯誤回應：**
```json
{
  "detail": "No Facebook token available"
}
```

---

#### GET /api/dashboard-data

**說明：** 取得儀表板數據（花費、觸及、點擊、互動）

**權限：** Module(fb_ads)

**查詢參數：**
- `account_id`: 廣告帳戶 ID (必填)
- `start_date`: 開始日期 YYYY-MM-DD (必填)
- `end_date`: 結束日期 YYYY-MM-DD (必填)
- `team_id` (選用): 團隊 ID

**回應：**
```json
{
  "summary": {
    "spend": 1250.50,
    "reach": 50000,
    "clicks": 2500,
    "impressions": 100000
  },
  "daily_data": [
    {
      "date": "2026-01-01",
      "spend": 100.00,
      "reach": 4000,
      "clicks": 200
    },
    {
      "date": "2026-01-02",
      "spend": 110.50,
      "reach": 4200,
      "clicks": 210
    }
  ]
}
```

---

### 4. Google Search Console

#### POST /api/gsc/authorize

**說明：** 授權 GSC 並儲存 Refresh Token

**權限：** Authenticated

**請求體：**
```json
{
  "code": "4/0AfJoh...",
  "team_id": "team_uuid" // 選用
}
```

**回應：**
```json
{
  "message": "GSC authorized successfully"
}
```

---

#### GET /api/gsc/sites

**說明：** 列出已驗證的 GSC 網站

**權限：** Module(gsc)

**查詢參數：**
- `team_id` (選用): 團隊 ID

**回應：**
```json
{
  "sites": [
    {
      "siteUrl": "https://example.com/",
      "permissionLevel": "siteOwner"
    },
    {
      "siteUrl": "sc-domain:example.com",
      "permissionLevel": "siteOwner"
    }
  ]
}
```

---

#### GET /api/gsc/analytics

**說明：** 查詢 GSC 數據

**權限：** Module(gsc)

**查詢參數：**
- `site_url`: 網站 URL (必填)
- `start_date`: 開始日期 YYYY-MM-DD (必填)
- `end_date`: 結束日期 YYYY-MM-DD (必填)
- `dimensions`: 維度，逗號分隔 (預設: "date")
  - 可選: date, page, query, country, device
- `team_id` (選用): 團隊 ID

**回應：**
```json
{
  "rows": [
    {
      "keys": ["2026-01-01"],
      "clicks": 150,
      "impressions": 5000,
      "ctr": 0.03,
      "position": 15.2
    },
    {
      "keys": ["2026-01-02"],
      "clicks": 160,
      "impressions": 5200,
      "ctr": 0.031,
      "position": 14.8
    }
  ]
}
```

---

#### POST /api/gsc/page-titles

**說明：** 批次抓取頁面標題（帶快取）

**權限：** Module(gsc)

**請求體：**
```json
{
  "urls": [
    "https://example.com/page1",
    "https://example.com/page2"
  ],
  "team_id": "team_uuid" // 選用
}
```

**回應：**
```json
{
  "titles": {
    "https://example.com/page1": "Page 1 Title",
    "https://example.com/page2": "Page 2 Title"
  }
}
```

---

#### POST /api/gsc/page-intents

**說明：** AI 分析頁面意圖

**權限：** Module(gsc)

**請求體：**
```json
{
  "urls": [
    "https://example.com/buy-product",
    "https://example.com/how-to-guide"
  ]
}
```

**回應：**
```json
{
  "intents": {
    "https://example.com/buy-product": {
      "intent": "transactional",
      "confidence": 0.95
    },
    "https://example.com/how-to-guide": {
      "intent": "informational",
      "confidence": 0.88
    }
  }
}
```

---

### 5. Google Analytics 4

#### POST /api/ga4/authorize

**說明：** 授權 GA4 並儲存 Refresh Token

**權限：** Authenticated

**請求體：**
```json
{
  "code": "4/0AfJoh...",
  "team_id": "team_uuid" // 選用
}
```

**回應：**
```json
{
  "message": "GA4 authorized successfully"
}
```

---

#### GET /api/ga4/accounts

**說明：** 列出 GA4 帳戶

**權限：** Module(ga4)

**查詢參數：**
- `team_id` (選用): 團隊 ID

**回應：**
```json
{
  "accounts": [
    {
      "name": "accounts/123456789",
      "displayName": "My GA4 Account"
    }
  ]
}
```

---

#### GET /api/ga4/properties

**說明：** 列出 GA4 資源

**權限：** Module(ga4)

**查詢參數：**
- `account_name`: 帳戶名稱，例如 "accounts/123456789" (必填)
- `team_id` (選用): 團隊 ID

**回應：**
```json
{
  "properties": [
    {
      "name": "properties/987654321",
      "displayName": "My Website"
    }
  ]
}
```

---

#### GET /api/ga4/analytics

**說明：** 查詢 GA4 數據

**權限：** Module(ga4)

**查詢參數：**
- `property_id`: 資源 ID (必填)
- `start_date`: 開始日期 YYYY-MM-DD (必填)
- `end_date`: 結束日期 YYYY-MM-DD (必填)
- `metrics`: 指標，逗號分隔 (預設: "activeUsers,sessions")
  - 可選: activeUsers, sessions, screenPageViews, eventCount, totalRevenue 等
- `dimensions`: 維度，逗號分隔 (預設: "date")
  - 可選: date, pagePath, country, deviceCategory 等
- `team_id` (選用): 團隊 ID

**回應：**
```json
{
  "rows": [
    {
      "dimensionValues": [{"value": "2026-01-01"}],
      "metricValues": [
        {"value": "1200"},  // activeUsers
        {"value": "1500"}   // sessions
      ]
    }
  ],
  "dimensionHeaders": [{"name": "date"}],
  "metricHeaders": [
    {"name": "activeUsers", "type": "TYPE_INTEGER"},
    {"name": "sessions", "type": "TYPE_INTEGER"}
  ]
}
```

---

### 6. AI 服務

#### GET /api/ai/providers

**說明：** 列出可用的 AI 供應商

**權限：** Module(ai_hub)

**回應：**
```json
{
  "providers": ["gemini", "zeabur"]
}
```

---

#### GET /api/ai/models

**說明：** 列出指定供應商的可用模型

**權限：** Module(ai_hub)

**查詢參數：**
- `provider`: AI 供應商 (預設: "zeabur")

**回應：**
```json
{
  "models": [
    "gemini-2.0-flash-exp",
    "gemini-2.5-flash",
    "gemini-1.5-pro"
  ]
}
```

---

#### POST /api/ai/test-connection

**說明：** 測試 AI 服務連線

**權限：** Module(ai_hub)

**請求體：**
```json
{
  "api_key": "your_api_key", // 選用，若未提供則使用已儲存的 Key
  "provider": "gemini",
  "model": "gemini-2.0-flash-exp"
}
```

**回應：**
```json
{
  "success": true,
  "message": "Connection successful",
  "provider": "gemini",
  "model": "gemini-2.0-flash-exp"
}
```

---

#### POST /api/ai/analyze

**說明：** 分析數據（同步回應）

**權限：** Module(ai_hub)

**請求體：**
```json
{
  "data": {
    "metrics": {
      "spend": 1250.50,
      "reach": 50000,
      "clicks": 2500
    }
  },
  "context": "分析這些廣告數據的趨勢和建議",
  "provider": "gemini",
  "model": "gemini-2.0-flash-exp"
}
```

**回應：**
```json
{
  "analysis": "根據數據分析，您的廣告表現...",
  "provider": "gemini",
  "model": "gemini-2.0-flash-exp"
}
```

---

#### POST /api/ai/analyze-stream

**說明：** 串流分析數據（SSE 回應）

**權限：** Module(ai_hub)

**請求體：** 同 `/api/ai/analyze`

**回應：** Server-Sent Events (SSE)
```
data: {"chunk": "根據數據"}
data: {"chunk": "分析..."}
data: {"done": true}
```

---

#### POST /api/ai/settings

**說明：** 儲存 AI 設定（API Keys 加密儲存）

**權限：** Authenticated

**請求體：**
```json
{
  "provider": "gemini",
  "api_key": "your_api_key",
  "model": "gemini-2.0-flash-exp" // 選用
}
```

**回應：**
```json
{
  "message": "AI settings saved successfully"
}
```

---

#### GET /api/ai/settings

**說明：** 取得 AI 設定（API Keys 已解密）

**權限：** Authenticated

**回應：**
```json
{
  "gemini": {
    "api_key": "decrypted_key",
    "model": "gemini-2.0-flash-exp"
  },
  "zeabur": {
    "api_key": "decrypted_key",
    "model": "gemini-2.5-flash"
  }
}
```

---

### 7. 權限管理

#### GET /api/permissions/modules

**說明：** 列出所有可用模組

**權限：** Admin

**回應：**
```json
{
  "modules": [
    {
      "id": "fb_ads",
      "name": "Facebook Ads",
      "description": "Facebook 廣告分析"
    },
    {
      "id": "gsc",
      "name": "Google Search Console",
      "description": "搜尋引擎最佳化分析"
    },
    {
      "id": "ga4",
      "name": "Google Analytics 4",
      "description": "網站流量分析"
    },
    {
      "id": "ai_hub",
      "name": "AI Hub",
      "description": "AI 智慧分析"
    }
  ]
}
```

---

#### GET /api/permissions/user/{user_id}/modules

**說明：** 取得使用者的模組權限

**權限：** Admin

**回應：**
```json
{
  "user_id": "user_uuid",
  "modules": ["fb_ads", "gsc"]
}
```

---

#### POST /api/permissions/user/{user_id}/modules

**說明：** 授予使用者模組權限

**權限：** Admin

**請求體：**
```json
{
  "module_name": "ga4"
}
```

**回應：**
```json
{
  "message": "Module access granted successfully"
}
```

---

#### DELETE /api/permissions/user/{user_id}/modules/{module_name}

**說明：** 撤銷使用者模組權限

**權限：** Admin

**回應：**
```json
{
  "message": "Module access revoked successfully"
}
```

---

### 8. 系統管理

#### GET /api/admin/stats

**說明：** 取得系統統計資訊

**權限：** Super Admin

**回應：**
```json
{
  "total_users": 150,
  "total_teams": 25,
  "active_users_today": 80,
  "total_api_calls_today": 5000
}
```

---

#### GET /api/health

**說明：** 健康檢查端點

**權限：** Public

**回應：**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "timestamp": "2026-01-15T10:30:00Z",
  "database": {
    "type": "PostgreSQL",
    "connected": true
  },
  "environment": {
    "all_configured": true,
    "details": {
      "GOOGLE_CLIENT_ID": true,
      "GOOGLE_CLIENT_SECRET": true,
      "DATABASE_URL": true
    }
  },
  "system": {
    "python_version": "3.11.0",
    "platform": "Windows"
  },
  "message": "Backend is running (Modular Version)"
}
```

---

## ⚠️ 錯誤回應

### 錯誤格式

所有錯誤回應遵循統一格式：

```json
{
  "detail": "錯誤描述",
  "error_code": "ERROR_CODE" // 選用
}
```

### 常見錯誤碼

| HTTP 狀態碼 | 錯誤碼 | 說明 |
|-------------|--------|------|
| 400 | `BAD_REQUEST` | 請求參數錯誤 |
| 401 | `UNAUTHORIZED` | 未提供有效 Token |
| 403 | `FORBIDDEN` | 無權限存取 |
| 404 | `NOT_FOUND` | 資源不存在 |
| 422 | `VALIDATION_ERROR` | 資料驗證失敗 |
| 500 | `INTERNAL_ERROR` | 伺服器內部錯誤 |
| 502 | `EXTERNAL_API_ERROR` | 外部 API 呼叫失敗 |

### 錯誤範例

**401 Unauthorized**
```json
{
  "detail": "Token verification failed: Invalid token"
}
```

**403 Forbidden**
```json
{
  "detail": "No access to gsc module",
  "error_code": "MODULE_ACCESS_DENIED"
}
```

**422 Validation Error**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## 🧪 測試 API

### 使用 Swagger UI

訪問 `http://localhost:8000/docs` 使用互動式 API 文件。

### 使用 cURL

```bash
# 健康檢查
curl http://localhost:8000/api/health

# 認證請求
curl -H "Authorization: Bearer <your_token>" \
     http://localhost:8000/api/users/me

# POST 請求
curl -X POST \
     -H "Authorization: Bearer <your_token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "New Team"}' \
     http://localhost:8000/api/teams/
```

### 使用 Postman

1. 建立新請求
2. 在 Headers 加入：
   - `Authorization`: `Bearer <your_token>`
   - `Content-Type`: `application/json`
3. 填入請求體（若需要）
4. 發送請求

---

## 📚 參考資源

- [FastAPI 文件](https://fastapi.tiangolo.com/)
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

---

**文件版本：** 2.0  
**最後更新：** 2026-01-15
