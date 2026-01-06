# Auth Module

認證與 Token 管理模組，提供 Facebook Token 和 AI API Key 的加密儲存功能。

## 功能

- **Facebook Token 管理**
  - 用戶 Token 加密儲存
  - 團隊 Token 管理
  - 短效換長效 Token
  
- **AI API Key 管理**
  - Zeabur/Gemini API Key 加密儲存
  - Provider 切換設定

## 使用方式

### 在本專案中

```python
from modules.auth import TokenManager

# 儲存 Facebook Token
TokenManager.save_user_token(google_id, token, app_id, app_secret, expires_in)

# 取得 Token
token = TokenManager.get_user_token(google_id)

# 儲存 AI 設定
TokenManager.save_ai_settings(google_id, zeabur_api_key="xxx", ai_provider="zeabur")
```

### 複製到其他專案

1. 複製 `modules/auth/` 資料夾
2. 複製 `core/security.py` (加密依賴)
3. 確保 `database.py` 有對應的 User/Team 模型
4. 安裝依賴：`pip install cryptography requests`

## 依賴

- `core.security` - 加密/解密功能
- `database` - 資料庫模型 (User, Team, TeamMember)
