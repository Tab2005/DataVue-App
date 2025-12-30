# GA4 Integration Planning

**建立日期**: 2025-12-30
**狀態**: 📋 規劃中

---

## 概述

整合 Google Analytics 4，採用與 GSC 相同的 OAuth 授權流程。用戶連接 GA4 後，系統自動列出有權限的 Properties，選擇後即可查看分析報表。

---

## 前置需求

### Google Cloud Console 設定

需要啟用以下 API：

| API | 用途 |
|-----|------|
| **Google Analytics Admin API** | 列出用戶的 GA4 Properties |
| **Google Analytics Data API** | 取得報表數據 |

### OAuth Scope

```python
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly'
]
```

---

## 實作項目

### Backend

| 檔案 | 說明 |
|------|------|
| `ga4_service.py` | OAuth token 交換、Admin API、Data API 整合 |
| `routers/ga4.py` | API 端點：authorize, properties, report |
| `database.py` | User model 新增 `ga4_access_token`, `ga4_refresh_token` |

### Frontend

| 檔案 | 說明 |
|------|------|
| `GA4Connect.jsx` | 連接畫面 (與 GSCConnect 相同風格) |
| `GA4Stats.jsx` | Property 選擇器、KPI 卡片、報表 |
| `Sidebar.jsx` | 新增「流量分析」選單項目 |

---

## API 端點設計

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/api/ga4/authorize` | 授權連接 |
| GET | `/api/ga4/properties` | 取得 Property 列表 |
| GET | `/api/ga4/report` | 取得分析報表 |

---

## GA4 指標規劃

| 指標 | API 名稱 | 用途 |
|------|----------|------|
| 工作階段 | `sessions` | 流量概覽 |
| 使用者 | `totalUsers` | 訪客分析 |
| 瀏覽頁數 | `screenPageViews` | 內容表現 |
| 跳出率 | `bounceRate` | 品質評估 |
| 平均互動時間 | `averageSessionDuration` | 參與度 |

---

## 驗證步驟

1. 在 Google Cloud Console 啟用 GA4 APIs
2. 測試 OAuth 授權流程
3. 確認 Property 列表正確顯示
4. 驗證報表數據與 GA4 後台一致
