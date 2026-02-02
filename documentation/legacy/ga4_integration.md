# GA4 Integration Planning

**建立日期**: 2025-12-30
**狀態**: � 實作中 (階段 1 已完成)

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

## Google Analytics Data API 可用資料

### 主要維度 (Dimensions)

#### 使用者與受眾
- 年齡層 (userAgeBracket)、性別 (userGender)
- 地理位置：城市 (city)、國家 (country)、洲別 (continent)
- 裝置：裝置類別 (deviceCategory)、瀏覽器 (browser)、作業系統 (operatingSystem)、螢幕解析度 (screenResolution)

#### 事件與互動
- 事件名稱 (eventName)、是否為重要事件 (isKeyEvent)
- 頁面：頁面位置 (pageLocation)、頁面標題 (pageTitle)、到達網頁 (landingPage)
- 內容：內容類型 (contentType)、檔案名稱 (fileName)、影片標題 (videoTitle)

#### 行銷與來源
- 來源/媒介 (sourceMedium)、管道群組 (defaultChannelGroup)
- 廣告：廣告格式 (adFormat)、廣告來源 (adSourceName)、廣告單元 (adUnitName)
- 廣告平台：Google Ads、DV360、CM360、SA360 等相關維度

#### 電子商務
- 商品：商品名稱 (itemName)、商品類別 (itemCategory)、商品品牌 (itemBrand)
- 促銷：商品促銷名稱 (itemPromotionName)、促銷版位 (itemPromotionCreativeSlot)

#### 時間
- 日期 (date)、小時 (hour)、星期幾 (dayOfWeek)、月份 (month)、年份 (year)

#### 自訂資料
- 自訂維度 (customEvent:parameter_name)
- 自訂管道群組 (sessionCustomChannelGroup:custom_channel_id)

### 主要指標 (Metrics)

#### 使用者指標
- 活躍使用者：活躍使用者 (activeUsers)、1天活躍 (active1DayUsers)、7天活躍 (active7DayUsers)、28天活躍 (active28DayUsers)
- 新使用者 (newUsers)、總使用者 (totalUsers)

#### 工作階段指標
- 工作階段數 (sessions)、互動工作階段 (engagedSessions)
- 平均工作階段持續時間 (averageSessionDuration)、跳出率 (bounceRate)、參與度 (engagementRate)

#### 事件指標
- 事件計數 (eventCount)、重要事件 (keyEvents)
- 每位使用者事件數 (eventCountPerUser)、每個工作階段事件數 (eventsPerSession)

#### 收益與電子商務
- 總收益 (totalRevenue)、購買收益 (purchaseRevenue)、廣告收益 (totalAdRevenue)
- 購買次數 (ecommercePurchases)、加入購物車 (addToCarts)、結帳次數 (checkouts)
- 平均購買收益 (averagePurchaseRevenue)、每位使用者平均收益 (averageRevenuePerUser)

#### 廣告指標
- 廣告點擊 (advertiserAdClicks)、廣告費用 (advertiserAdCost)、廣告曝光 (advertiserAdImpressions)
- 廣告投資報酬率 (returnOnAdSpend)

#### 內容與頁面
- 觀看次數 (screenPageViews)、每位使用者觀看次數 (screenPageViewsPerUser)
- 捲動使用者 (scrolledUsers)

#### 其他
- 當機相關：遇到當機的使用者 (crashAffectedUsers)、不受當機影響比率 (crashFreeUsersRate)
- 同類群組分析 (cohortActiveUsers, cohortTotalUsers)
- 自訂指標 (customEvent:parameter_name)

### 特別說明
- **自訂資料**：支援事件範圍、使用者範圍的自訂維度和指標
- **整合支援**：涵蓋 Google Ads、Search Console、AdMob 等平台的資料
- **時間範圍**：支援即時資料、歷史資料查詢
- **限制**：API 有配額限制，詳見官方文檔

---

## 驗證步驟

1. 在 Google Cloud Console 啟用 GA4 APIs
2. 測試 OAuth 授權流程
3. 確認 Property 列表正確顯示
4. 驗證報表數據與 GA4 後台一致

---

## 實作計劃

### 📋 階段 1: 資料庫更新 (✅ 已完成)

#### 目標
在 User model 中新增 GA4 整合所需的 token 欄位，與現有的 GSC 欄位保持一致的結構。

#### 具體變更
**修改 `backend/database.py`** - 在 User class 中，於 GSC 欄位區塊之後新增 GA4 欄位：

```python
# Google Search Console (GSC) Integration
gsc_access_token = Column(String, nullable=True)
gsc_refresh_token = Column(String, nullable=True)
gsc_expires_at = Column(DateTime, nullable=True)

# Google Analytics 4 (GA4) Integration
ga4_access_token = Column(String, nullable=True)
ga4_refresh_token = Column(String, nullable=True)
ga4_expires_at = Column(DateTime, nullable=True)
```

#### 資料庫遷移考量
- **SQLite (本地開發)**: 會自動處理 schema 變更
- **PostgreSQL (生產)**: 需要手動執行遷移或使用 Alembic

#### 本地測試計劃
1. **啟動應用程式** - 確認無 import 錯誤 ✅
2. **檢查資料庫連線** - 確認 schema 變更成功 ✅
3. **驗證 User model** - 確保新欄位存在 ✅
4. **測試現有功能** - 確認 GSC/Facebook 功能不受影響 ✅

#### 測試指令
```bash
# 1. 啟動後端 (會自動建立/更新 schema)
cd backend
python -m uvicorn main:app --reload

# 2. 檢查資料庫 (SQLite)
sqlite3 facebook_dashboard.db ".schema users"

# 3. 測試 API 端點
curl http://localhost:8000/api/users/me
```

#### 注意事項
- **安全性**: Token 欄位為 nullable，不影響現有用戶
- **相容性**: 不影響現有 User 記錄，新用戶會有空的 GA4 欄位
- **回滾計劃**: 如有問題，可以直接移除新增的欄位

#### 測試結果
- ✅ Database import successful
- ✅ User model import successful
- ✅ GA4 columns added to database schema
- ✅ Application starts without errors
- ✅ No impact on existing functionality

### 📋 階段 1.5: 模組化架構建立 (✅ 已完成)

#### 目標
建立與 GSC 一致的模組化架構，為 GA4 功能提供完整的模組化支援。

#### 建立的檔案結構
```
backend/modules/ga4/
├── __init__.py          # 模組導出 (router, GA4Service)
├── router.py            # API 端點重新導出
├── service.py           # GA4 服務重新導出
└── README.md            # 模組說明文件
```

#### 權限系統更新
- **啟用 GA4 模組**: 將 `enabled: False` 改為 `enabled: True`
- **權限已定義**: `ga4:property:connect`, `ga4:analytics:view`
- **角色權限**: 已包含在 team_admin 和 team_owner 中

#### 模組化好處
- ✅ 與 GSC 保持一致的架構
- ✅ 支援模組獨立載入和測試
- ✅ 完整的說明文件
- ✅ 可重用於其他專案

---

### 📋 階段 2: Backend Service 實作 (✅ 已完成)

#### 目標
建立 `ga4_service.py`，參考 `gsc_service.py` 的結構，實作 GA4 API 整合。

#### 主要功能
- ✅ OAuth token 交換 (`exchange_code`)
- ✅ Google Analytics Admin API (取得 Properties) (`list_properties`)
- ✅ Google Analytics Data API (取得報表資料) (`get_analytics`)
- ✅ Token 管理與更新 (`get_credentials`)

#### 實作細節
- **OAuth 流程**: 參考 GSC 實作，使用相同的 token 交換邏輯
- **Admin API**: 使用 `google.analytics.admin.AnalyticsAdminServiceClient`
- **Data API**: 使用 `google.analytics.data.BetaAnalyticsDataClient`
- **錯誤處理**: 完整的異常處理和日誌記錄
- **資料格式化**: 將 API 回應轉換為前端友好的格式

#### 新增依賴
- `google-analytics-admin` - Admin API 客戶端
- `google-analytics-data` - Data API 客戶端

#### 測試結果
- ✅ GA4Service import successful
- ✅ No syntax errors
- ✅ Dependencies installed successfully
- ✅ Ready for router implementation

### 📋 階段 3: Backend Router 實作 (✅ 已完成)

#### 目標
建立 `routers/ga4.py`，參考 `routers/gsc.py`，實作三個 API 端點。

#### API 端點
- ✅ `POST /api/ga4/authorize` - 授權連接
- ✅ `GET /api/ga4/properties` - 取得 Property 列表
- ✅ `GET /api/ga4/report` - 取得分析報表

#### 實作細節
- **權限檢查**: 使用 `require_module("ga4")` 進行模組存取控制
- **錯誤處理**: 完整的異常處理和 HTTP 狀態碼
- **參數驗證**: 使用 Pydantic models 和 Query 參數驗證
- **資料格式化**: 將服務層資料轉換為 API 回應格式

#### 模組整合
- ✅ 更新 `modules/ga4/__init__.py` 導出 router 和 GA4Service
- ✅ 模組導入測試通過
- ✅ 與現有架構完全相容

#### 測試結果
- ✅ Router import successful
- ✅ Module exports working correctly
- ✅ No syntax errors
- ✅ Ready for frontend implementation

### 📋 階段 4: Frontend 實作 (✅ 已完成)

#### 目標
實作前端 GA4 整合介面。

#### 主要組件
- ✅ 更新 `Sidebar.jsx` - 新增「流量分析」選單
- ✅ 建立 `GA4Connect.jsx` - 連接畫面 (參考 GSCConnect)
- ✅ 建立 `GA4Stats.jsx` - Property 選擇器、KPI 卡片、報表
- ✅ 建立 `GA4Analytics.jsx` - 主頁面組件
- ✅ 更新 `App.jsx` - 新增路由配置

#### 實作細節
- **側邊欄整合**: 新增 FiTrendingUp 圖標的「流量分析」選單項目
- **連接畫面**: 參考 GSCConnect 的玻璃擬態設計，適配 GA4 品牌色彩
- **統計組件**: 支援多個分析維度 (總覽、流量來源、用戶行為、內容分析)
- **日期範圍**: 支援預設日期範圍 (7天、28天、3個月、自訂)
- **KPI 卡片**: 顯示主要指標與變化趨勢
- **資料表格**: 顯示詳細的分析數據

#### 路由配置
- **路徑**: `/ga4`
- **權限檢查**: 使用 `ProtectedModule` 檢查 `ga4` 模組權限
- **錯誤處理**: 完整的錯誤邊界和載入狀態

#### 前端功能
- **屬性選擇**: 下拉選單選擇 GA4 屬性
- **即時載入**: 切換屬性或日期時自動重新載入資料
- **響應式設計**: 支援手機和桌面版面配置
- **多語言支援**: 中英文介面切換

#### 測試結果
- ✅ Frontend build successful
- ✅ GA4Analytics component compiled
- ✅ No syntax errors in new components
- ✅ Routing configuration working
- ✅ Sidebar integration complete
- ✅ **權限修復**: 超級管理員現在有完整 GA4 模組存取權

### 📋 階段 5: 整合測試 (進行中)

#### 目標
完整測試 GA4 整合功能。

#### 權限系統修復
**問題發現**: 超級管理員權限不見了
- **根本原因**: 權限 seeding 只建立了基本權限結構，但沒有為超級管理員自動授予所有模組存取權
- **修復方案**: 為超級管理員 (is_super_admin=True) 手動添加所有模組的 UserModuleAccess 記錄
- **修復結果**: 超級管理員現在有 FB Ads、GSC、GA4 全部 3 個模組的存取權

#### 測試項目
- ✅ 權限系統修復
- OAuth 授權流程
- Property 列表顯示
- 報表資料正確性
- 與 GA4 後台數據一致性

---
