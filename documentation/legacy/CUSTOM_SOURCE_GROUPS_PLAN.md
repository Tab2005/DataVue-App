# 用戶自定義來源分組 - 實作計劃

> 建立時間：2026-01-14
> 狀態：✅ **已完成**

## 一、功能概述

允許用戶新增、編輯、刪除自己的來源分組規則，不再只依賴程式碼中的固定分組。
**分組依據 GA4 Property 儲存**，不同網站可有不同分組設定。

```
來源篩選: [▼ 全部來源]
├── 全部來源
├── 📁 Facebook (集合)     ← 預設分組
├── 📁 Google (集合)       ← 預設分組
├── 🤖 AI 流量 (集合)       ← 預設分組
├── ⭐ 我的客製分組 1       ← 用戶自定義
├── ⭐ 付費廣告 (集合)      ← 用戶自定義
├── [+ 新增分組]            ← 新增按鈕
├── ──────────────
├── facebook.com
└── ...（個別來源）
```

---

## 二、資料儲存方案

### 方案 A：LocalStorage ✅ 已實作
- **儲存 Key**：`source_groups_{propertyId}`（依 GA4 Property 區分）
- **優點**：無需後端、立即可用、依網站區分
- **缺點**：換瀏覽器/裝置會遺失

### 方案 B：資料庫儲存（未來升級）
- **優點**：跨裝置同步、永久保存
- **缺點**：需要後端 API

---

## 三、實作檔案

### 新增檔案

#### ✅ `frontend/src/utils/sourceGroups.js`
- 預設分組常數 (Facebook, Google, Instagram, LINE, Threads, Bing, Yahoo, AI)
- `getAllSourceGroups(propertyId)` - 取得所有分組
- `addCustomGroup(propertyId, name, nameEn, patterns)` - 新增分組
- `updateCustomGroup(propertyId, key, name, nameEn, patterns)` - 更新分組
- `deleteCustomGroup(propertyId, key)` - 刪除分組
- `isDefaultGroup(key)` - 判斷是否為預設分組

#### ✅ `frontend/src/components/SourceGroupModal.jsx`
- 新增/編輯分組的彈出視窗
- 欄位：分組名稱（中/英）、匹配模式
- 預設分組不可編輯/刪除

### 修改檔案

#### ✅ `frontend/src/components/GA4Stats.jsx`
- 移除 `SOURCE_GROUPS` 常數，改用 `sourceGroups.js`
- 使用 `getAllSourceGroups(selectedProperty)` 取得分組
- 加入「+ 新增分組」按鈕
- 加入 ✏️ 編輯按鈕（選擇分組後顯示）
- 支援 `group_` 和 `custom_` 兩種前綴的篩選邏輯

---

## 四、實作進度

- [x] 建立 `sourceGroups.js` 工具函數
- [x] 建立 `SourceGroupModal.jsx` 彈窗組件
- [x] 修改 `GA4Stats.jsx` 使用新的分組系統
- [x] 加入新增分組功能
- [x] 加入編輯/刪除分組功能
- [x] 依 GA4 Property 儲存分組
- [x] 本地測試驗證

---

## 五、未來擴展（方案 B）

```sql
CREATE TABLE source_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    property_id VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    patterns TEXT[] NOT NULL,
    icon VARCHAR(10) DEFAULT '⭐',
    created_at TIMESTAMP DEFAULT NOW()
);
```
