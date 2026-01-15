# GA4 內容分析分頁實作計劃

> 狀態：🔄 **進行中** - 第二階段（內容類型分組管理）

---

## 階段一：基礎內容分析 ✅ 已完成

- [x] 維度選擇器（網頁標題、網頁路徑、網頁 URL）
- [x] 基礎內容類型篩選（固定商品頁、文章頁）
- [x] 6 個 KPI 卡片
- [x] 表格數據顯示

---

## 階段二：內容類型分組管理（進行中）

### 目標
讓用戶可以自訂內容類型分組，類似流量來源的 Source Groups 功能。

### 規則類型設計

```javascript
const CONTENT_RULE_TYPES = [
    { key: 'contains', label_zh: '包含關鍵字', label_en: 'Contains' },
    { key: 'startsWith', label_zh: '路徑開頭', label_en: 'Starts With' },
    { key: 'endsWith', label_zh: '路徑結尾', label_en: 'Ends With' },
    { key: 'equals', label_zh: '完全符合', label_en: 'Equals' }
];
```

### 分組資料結構

```javascript
{
    key: 'custom_product_pages',
    label_zh: '商品頁',
    label_en: 'Product Pages',
    isDefault: false,  // true = 預設分組，false = 自訂分組
    rules: [
        { type: 'contains', value: 'product' },
        { type: 'startsWith', value: '/products/' },
        { type: 'startsWith', value: '/shop/' }
    ]
}
```

### 預設分組（可編輯）

| 分組 | 預設規則 | 說明 |
|------|---------|------|
| 商品頁 | `/products/`, `/shop/`, `product`, `item` | 電商商品頁面 |
| 文章頁 | `/blog/`, `/article/`, `post`, `news` | 部落格/新聞頁面 |

### 儲存機制

- LocalStorage key: `ga4_content_groups_${propertyId}`
- 格式: JSON array of group objects
- 預設分組可編輯但不可刪除

---

## 實作變更

### [NEW] ContentGroupModal.jsx
建立內容類型分組編輯 Modal，參考 SourceGroupModal.jsx

**功能：**
- 新增/編輯/刪除內容類型分組
- 支援多種規則類型（包含、路徑開頭、路徑結尾、完全符合）
- 動態新增/移除規則
- 預覽符合規則的頁面數量

### [NEW] utils/contentGroups.js
內容分組管理工具函數

```javascript
// 預設分組定義
export const DEFAULT_CONTENT_GROUPS = [...];

// 取得所有分組（預設 + 自訂）
export function getAllContentGroups(propertyId) {...}

// 儲存自訂分組
export function saveCustomContentGroup(propertyId, group) {...}

// 刪除自訂分組
export function deleteCustomContentGroup(propertyId, groupKey) {...}

// 檢查是否為預設分組
export function isDefaultContentGroup(groupKey) {...}

// 根據規則過濾數據
export function filterByContentGroup(rows, group, dimension) {...}
```

### [MODIFY] GA4Stats.jsx

1. **移除固定 CONTENT_TYPE_GROUPS 常數**
2. **新增狀態**
   ```javascript
   const [contentGroups, setContentGroups] = useState([]);
   const [showContentGroupModal, setShowContentGroupModal] = useState(false);
   const [editingContentGroup, setEditingContentGroup] = useState(null);
   ```

3. **載入分組**
   ```javascript
   useEffect(() => {
       if (selectedProperty) {
           setContentGroups(getAllContentGroups(selectedProperty));
       }
   }, [selectedProperty]);
   ```

4. **更新 UI**
   - 下拉選單添加「➕ 新增分組」選項
   - 選擇分組時顯示「編輯」按鈕
   - 預設分組顯示編輯按鈕但不顯示刪除

5. **更新 getContentKPIData**
   - 使用 `filterByContentGroup()` 替代固定 patterns

---

## 實作進度

- [x] 基礎內容分析功能
- [ ] 建立 contentGroups.js 工具函數
- [ ] 建立 ContentGroupModal.jsx 組件
- [ ] 更新 GA4Stats.jsx 整合分組管理
- [ ] 本地測試驗證

---

## UI 設計

### 內容類型下拉選單
```
🏷️ 內容類型
┌─────────────────────────────┐
│ 全部頁面                     │
│ ── 預設分組 ──              │
│ 📦 商品頁          [✏️]     │
│ 📄 文章頁          [✏️]     │
│ ── 自訂分組 ──              │
│ 🏠 首頁            [✏️][🗑️] │
│ ─────────────────           │
│ ➕ 新增分組...               │
└─────────────────────────────┘
```

### Modal 編輯介面
```
┌─────────────────────────────────────┐
│ 編輯內容類型分組                      │
├─────────────────────────────────────┤
│ 分組名稱: [商品頁                  ] │
│                                     │
│ 規則:                               │
│ ┌─────────────┬──────────────┬───┐ │
│ │ 路徑開頭 ▼  │ /products/   │ 🗑 │ │
│ │ 路徑開頭 ▼  │ /shop/       │ 🗑 │ │
│ │ 包含關鍵字▼ │ product      │ 🗑 │ │
│ └─────────────┴──────────────┴───┘ │
│ [➕ 新增規則]                        │
│                                     │
│ 預覽: 符合 156 個頁面                │
│                                     │
│           [取消]  [儲存]             │
└─────────────────────────────────────┘
```
