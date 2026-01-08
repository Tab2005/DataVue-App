# GSC Performance Optimization

> 建立日期：2026-01-08  
> 狀態：✅ 已完成  
> 最後更新：2026-01-08

提升 GSC 資料載入效能，改善大量資料（25000 筆）的用戶體驗。

---

## 優化項目

### 1. ✅ 後端：並行 API 請求
- **檔案**：`backend/gsc_service.py`
- **內容**：將串列 API 請求改為並行（每 3 批次同時發送）
- **技術**：使用 `ThreadPoolExecutor` 實作並行請求，每個執行緒使用獨立的 Google API 連線
- **效果**：25 次請求 → 9 組並行（約 **3x 加速**）
- **實測**：25000 筆資料約 60 秒載入

### 2. ✅ 後端：快取機制
- **檔案**：`backend/gsc_service.py`
- **內容**：新增記憶體快取（`_gsc_cache` dict），5 分鐘內相同查詢直接返回
- **快取鍵**：`{site_url}:{start_date}:{end_date}:{dimensions}`
- **效果**：重複查詢 **0 秒**
- **日誌**：`[GSC Cache] HIT` 表示快取命中

### 3. ✅ 前端：漸進式載入
- **檔案**：`frontend/src/components/GSCStats.jsx`
- **內容**：
  - 新增 `displayLimit` 狀態（初始 100 筆）
  - 修改 `getSortedFilteredData()` 返回 `{ displayData, totalCount, hasMore }`
  - 新增「載入更多」(+100) 和「載入全部」按鈕
- **效果**：前端快速渲染首批資料，避免 DOM 卡頓

### 4. ✅ 前端：大資料量警告
- **檔案**：`frontend/src/components/GSCStats.jsx`
- **內容**：
  - >1000 筆：「載入全部」按鈕顯示 ⚠️ 圖示
  - >5000 筆：顯示警告文字「大量資料載入可能較慢」
  - 滑鼠懸停顯示提示
- **效果**：提醒用戶大量資料可能影響瀏覽器效能

---

## 驗證結果

| 測試項目 | 結果 |
|----------|------|
| 並行 API 載入 25000 筆 | ✅ 約 60 秒 |
| 快取命中 | ✅ 日誌顯示 `[GSC Cache] HIT` |
| 漸進式載入首批 | ✅ 顯示 100/25000 筆 |
| 載入更多按鈕 | ✅ 每次增加 100 筆 |
| 大資料量警告 | ✅ 顯示 ⚠️ 和警告文字 |

---

## Git 提交記錄

- `288ba40` - feat(gsc): auto-paginate analytics data in 1000-row batches (max 25000)
- `416602c` - perf(gsc): add parallel API, caching, and progressive rendering optimizations
