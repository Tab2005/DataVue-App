# GSC 頁面分析分頁優化實作計畫

> 紀錄日期：2026-01-21

針對頁面分析分頁的關鍵字下拉列表，導入與關鍵字分析分頁相同的優化機制，並新增載入時間顯示功能。

## 現況分析

### 問題
目前 `fetchPageKeywords` 函式（第 656-691 行）一次載入所有 `page,query` 維度的資料，資料量可能非常龐大。

### 已有基礎設施
- **後端分頁**：`gsc_service.py` 的 `get_analytics` 函式已支援 `limit` 和 `offset` 參數
- **Redis 快取**：已啟用，支援分頁資料快取
- **GZip 壓縮**：已全域啟用

---

## 實作方案

### 方案 A：使用現有 API + 優化前端載入策略（建議）

1. **修改 `fetchPageKeywords` 邏輯**：
   - 初次載入時使用 `limit` 參數限制資料量
   - 加入分頁支援（載入更多）
   - 記錄並顯示載入時間

2. **按需載入**：
   - 當用戶展開某個頁面時，若資料不足再發送請求

3. **新增載入時間 UI**：
   - 在下拉關鍵字區塊顯示載入時間（如 `⚡ 125ms`）
   - 顯示資料來源（快取/API）

### 方案 B：新增專用後端 API（可選）

新增 `/api/gsc/page-keywords` 端點，支援按 `page_url` 過濾。

---

## 前端修改細節

### 1. 新增狀態

```javascript
// 載入狀態
const [pageKeywordsLoading, setPageKeywordsLoading] = useState({});  // { pageUrl: boolean }
const [pageKeywordsLoadTime, setPageKeywordsLoadTime] = useState({}); // { pageUrl: number (ms) }
const [pageKeywordsHasMore, setPageKeywordsHasMore] = useState(true);
const [pageKeywordsOffset, setPageKeywordsOffset] = useState(0);
```

### 2. 修改 fetchPageKeywords 函式

添加 `limit`、`offset` 參數，並記錄載入時間：

```javascript
const fetchPageKeywords = async (siteUrl, startDate, endDate, limit = 5000, offset = 0, append = false) => {
    const startTime = performance.now();
    try {
        const resp = await fetch(
            `${API_URL}/api/gsc/analytics?...&dimensions=page,query&limit=${limit}&offset=${offset}`,
            { headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` } }
        );
        const loadTime = Math.round(performance.now() - startTime);
        // ... 處理資料 ...
        setPageKeywordsLoadTime(loadTime);
    } catch (err) { ... }
};
```

### 3. 新增載入時間 UI

```jsx
{/* 在下拉關鍵字區塊標題右側顯示 */}
<span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
    ⚡ {pageKeywordsLoadTime}ms | 共 {totalKeywords} 組關鍵字
</span>
```

---

## 驗證步驟

1. 啟動開發環境
2. 開啟頁面分析分頁
3. 驗證：
   - [ ] 關鍵字列表正常顯示
   - [ ] 載入時間顯示正確
   - [ ] 多次展開/收合同一頁面使用快取

---

## 影響範圍

| 項目 | 影響 |
|------|------|
| 頁面分析分頁 | 主要變更區域 |
| 關鍵字分析分頁 | 不受影響 |
| 後端 API | 不需變更（使用現有分頁功能） |
| GZip / Redis | 自動適用 |
