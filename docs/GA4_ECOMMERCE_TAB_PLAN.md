# GA4 電子商務分頁實作計劃

> 狀態：✅ **已完成**

## 目標

在 GA4 儀表板新增「電子商務」分頁，支援：
- 雙維度選擇（商品維度 + 流量維度）
- 6 個電商專用 KPI 卡片和表格欄位
- 與 GA4 後台一致的交叉分析體驗

---

## 一、商品維度選擇器（主要）

| 選項 | API 維度名稱 | 說明 |
|------|-------------|------|
| 項目名稱 | `itemName` | 商品名稱 |
| 商品類別 | `itemCategory` | 商品分類 |
| 商品品牌 | `itemBrand` | 品牌名稱 |

---

## 二、流量維度選擇器（次要，選填）

| 選項 | API 維度名稱 | 說明 |
|------|-------------|------|
| 無 | (不加入) | 僅顯示商品維度 |
| 管道分組 | `sessionDefaultChannelGrouping` | Organic, Paid, Direct 等 |
| 來源 | `sessionSource` | google, facebook 等 |
| 媒介 | `sessionMedium` | organic, cpc, referral 等 |
| 來源/媒介 | `sessionSourceMedium` | google / organic 等 |

---

## 三、動態篩選器

根據選擇的維度顯示對應篩選器：

| 維度類型 | 篩選器標籤 |
|---------|-----------|
| 商品維度 | 商品篩選（從 API 數據產生選項）|
| 流量維度 | 來源篩選（當選擇流量維度時顯示）|

---

## 四、KPI 卡片（6 個指標）

| 指標 | API 名稱 | 格式 |
|------|---------|------|
| 總人數 | `totalUsers` | 數字 |
| 已看過的商品數 | `itemsViewed` | 數字 |
| 加入購物車的商品數 | `itemsAddedToCart` | 數字 |
| 已購買的商品數 | `itemsPurchased` | 數字 |
| 商品收益 | `itemRevenue` | 貨幣 |
| 轉換率 | (計算) `itemsPurchased / itemsViewed * 100` | 百分比 |

---

## 五、UI 佈局

```
┌────────────────────────────────────────────────────────────────┐
│  📦 商品維度                     🌐 流量維度（選填）             │
│  [▼ 項目名稱]                    [▼ 無]                        │
├────────────────────────────────────────────────────────────────┤
│  🎯 商品篩選                     🎯 來源篩選（流量維度時顯示）    │
│  [▼ 全部商品]                    [▼ 全部來源] ← 僅當有流量維度   │
└────────────────────────────────────────────────────────────────┘
```

當選擇流量維度時：
- API 請求帶兩個 dimensions：`dimensions: ['itemName', 'sessionSourceMedium']`
- 表格第一欄顯示商品名稱，第二欄顯示來源/媒介
- KPI 可同時根據商品篩選 + 來源篩選計算

---

## 六、實作變更

### [MODIFY] GA4Stats.jsx

1. **新增常數**
```javascript
const ECOMMERCE_DIMENSIONS = [
    { key: 'itemName', label_zh: '項目名稱', label_en: 'Item Name' },
    { key: 'itemCategory', label_zh: '商品類別', label_en: 'Item Category' },
    { key: 'itemBrand', label_zh: '商品品牌', label_en: 'Item Brand' }
];

const TRAFFIC_SECONDARY_DIMENSIONS = [
    { key: 'none', label_zh: '無', label_en: 'None' },
    { key: 'sessionDefaultChannelGrouping', label_zh: '管道分組', label_en: 'Channel' },
    { key: 'sessionSource', label_zh: '來源', label_en: 'Source' },
    { key: 'sessionMedium', label_zh: '媒介', label_en: 'Medium' },
    { key: 'sessionSourceMedium', label_zh: '來源/媒介', label_en: 'Source/Medium' }
];

const ECOMMERCE_METRICS = [
    'totalUsers', 'itemsViewed', 'itemsAddedToCart', 
    'itemsPurchased', 'itemRevenue'
    // conversionRate 計算: itemsPurchased / itemsViewed * 100
];
```

2. **新增 State**
```javascript
const [ecommerceDimension, setEcommerceDimension] = useState('itemName');
const [ecommerceSecondaryDimension, setEcommerceSecondaryDimension] = useState('none');
const [ecommerceFilter, setEcommerceFilter] = useState('all');
const [ecommerceSecondaryFilter, setEcommerceSecondaryFilter] = useState('all');
```

3. **更新 TABS 配置**
```javascript
{ 
    key: 'ecommerce', 
    label_zh: '🛒 電子商務', 
    label_en: '🛒 Ecommerce', 
    metrics: ECOMMERCE_METRICS, 
    dimensions: ['itemName'] 
}
```

4. **修改 fetchAnalytics**
- 支援多維度請求（當有次要維度時）
- `dimensions: ecommerceSecondaryDimension !== 'none' ? [ecommerceDimension, ecommerceSecondaryDimension] : [ecommerceDimension]`

5. **新增 getEcommerceKPIData 函數**
- 根據商品篩選 + 來源篩選計算 KPI

6. **新增電子商務 UI 控制區**
- 商品維度選擇器
- 流量維度選擇器（次要）
- 動態篩選器

7. **更新表格渲染**
- 支援雙欄維度顯示

---

## 七、實作進度

- [x] 儲存實作計劃
- [x] 新增 TABS 配置（ecommerce tab）
- [x] 新增電子商務維度常數 (ECOMMERCE_DIMENSIONS)
- [x] 新增次要維度常數（流量）(TRAFFIC_SECONDARY_DIMENSIONS)
- [x] 新增電子商務 State
- [x] 新增 getEcommerceColumnOrder 與 getEcommerceColumnLabel 函數
- [x] 修改 fetchAnalytics 支援多維度
- [x] 修改 fetchCompareData 支援多維度
- [x] 實作 getEcommerceKPIData 函數
- [x] 渲染電子商務 UI（雙維度選擇器）
- [x] 更新表格支援雙維度欄位
- [x] 整合來源分組功能至來源篩選
- [x] 本地測試驗證

---

## 八、注意事項

> [!IMPORTANT]
> **GA4 API 維度限制**
> - 單次請求最多 9 個維度
> - 電商維度 + 流量維度 = 2 個維度，在限制內

> [!WARNING]
> **電商指標可用性**
> - `itemsViewed`、`itemsAddedToCart`、`itemsPurchased`、`itemRevenue` 需要網站有實作 GA4 電商事件
> - 若網站無電商事件，這些指標會是 0
