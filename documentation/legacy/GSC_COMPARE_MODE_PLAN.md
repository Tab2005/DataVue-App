# GSC 比較模式實作計劃

## 目標

為 GSC 頁面新增比較模式功能，讓用戶可以將當前日期範圍的數據與前一時段或去年同期進行比較。

## 參考實作

GA4 compare mode (`GA4Stats.jsx`)

---

## 提議變更

### GSCStats.jsx 修改

1. **新增常數與狀態**
   - `COMPARE_OPTIONS` 常數
   - `compareMode`, `compareData`, `compareLoading` 狀態

2. **新增函數**
   - `getCompareDateRange()` - 計算比較日期範圍
   - `fetchCompareData()` - 取得比較期間數據
   - `calculateChange()` - 計算變化百分比
   - `getCompareTotals()` - 計算比較期間總計

3. **UI 修改**
   - 設定面板新增比較模式選擇器
   - KPI 卡片顯示變化百分比 (▲/▼)

---

## 實作順序

1. [x] 新增常數和狀態定義
2. [x] 實作 `getCompareDateRange` 函數
3. [x] 實作 `fetchCompareData` 函數  
4. [x] 新增 useEffect 觸發比較載入
5. [x] 修改設定面板 UI
6. [x] 修改 KPI 卡片顯示邏輯
7. [ ] 測試驗證

