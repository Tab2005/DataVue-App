# 用戶自定義來源分組 - 實作計劃

> 建立時間：2026-01-14
> 狀態：進行中

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

### 方案 A：LocalStorage（先實作）✅
- **儲存 Key**：`source_groups_{propertyId}`（依 GA4 Property 區分）
- **優點**：無需後端、立即可用、依網站區分
- **缺點**：換瀏覽器/裝置會遺失

### 方案 B：資料庫儲存（未來升級）
- **優點**：跨裝置同步、永久保存
- **缺點**：需要後端 API

---

## 三、實作計劃 - 方案 A

### 3.1 新增檔案

#### [NEW] `frontend/src/utils/sourceGroups.js`
- 預設分組常數
- `getAllSourceGroups(propertyId)` - 取得所有分組
- `addCustomGroup(propertyId, group)` - 新增分組
- `updateCustomGroup(propertyId, key, group)` - 更新分組
- `deleteCustomGroup(propertyId, key)` - 刪除分組

#### [NEW] `frontend/src/components/SourceGroupModal.jsx`
- 新增/編輯分組的彈出視窗
- 欄位：分組名稱、匹配模式

### 3.2 修改檔案

#### [MODIFY] `frontend/src/components/GA4Stats.jsx`
- 移除 `SOURCE_GROUPS` 常數
- 使用 `getAllSourceGroups(selectedProperty)` 取得分組
- 加入新增/編輯/刪除分組 UI

---

## 四、實作順序

- [ ] 建立 `sourceGroups.js` 工具函數
- [ ] 建立 `SourceGroupModal.jsx` 彈窗組件
- [ ] 修改 `GA4Stats.jsx` 使用新的分組系統
- [ ] 加入新增/編輯/刪除分組功能
- [ ] 本地測試

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
