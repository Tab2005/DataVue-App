# Auth Module

認證模組 - 提供認證依賴、Token 管理、以及用戶相關 API。

## 功能

- **Google OAuth 認證**: 驗證 Google Token 並自動註冊用戶
- **Token 管理**: Facebook Token 和 AI API Key 的加密儲存
- **權限檢查**: 模組存取和細粒度權限控制
- **用戶狀態**: Super Admin、Admin、Active User 等角色驗證

## 檔案結構

```
modules/auth/
├── __init__.py          # 模組導出
├── dependencies.py      # FastAPI 依賴 (get_current_user 等)
├── router.py            # API 端點 (/api/auth/*)
├── service.py           # TokenManager 服務
└── README.md            # 本文件
```

## 使用方式

### 在 FastAPI 應用中使用

```python
from fastapi import FastAPI, Depends
from modules.auth import router as auth_router, get_current_user, require_module

app = FastAPI()

# 註冊 Auth Router
app.include_router(auth_router)

# 在端點中使用認證依賴
@app.get("/api/protected")
async def protected_endpoint(user = Depends(get_current_user)):
    return {"email": user.email}

# 檢查模組存取權限
@app.get("/api/gsc/data")
async def gsc_data(_: bool = Depends(require_module("gsc"))):
    return {"data": "..."}
```

### 導出的依賴

| 依賴名稱 | 說明 |
|----------|------|
| `get_current_user` | 取得當前認證用戶 |
| `get_current_active_user` | 確保用戶狀態為 ACTIVE |
| `get_admin_user` | 確保用戶為 Admin 或 Super Admin |
| `get_super_admin` | 確保用戶為 Super Admin |
| `get_current_team` | 驗證團隊成員身份 |
| `require_permission(key)` | 檢查特定權限 |
| `require_module(key)` | 檢查模組存取權 |
| `require_super_admin()` | 要求 Super Admin |

### API 端點

| 端點 | 方法 | 說明 |
|------|------|------|
| `/api/auth/me` | GET | 取得當前用戶資訊 |
| `/api/auth/token-status` | GET | 取得 Token 狀態 |
| `/api/auth/ai-settings` | GET | 取得 AI 設定 |

## 依賴

- `cryptography`: Fernet 加密
- `google-auth`: Google OAuth Token 驗證
- `core.security`: 加密金鑰管理

## 複用到其他專案

1. 複製 `modules/auth/` 資料夾
2. 複製 `core/security.py`（加密依賴）
3. 安裝依賴:
   ```bash
   pip install cryptography google-auth
   ```
4. 設定環境變數:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   ENCRYPTION_KEY=your_fernet_key
   ```
