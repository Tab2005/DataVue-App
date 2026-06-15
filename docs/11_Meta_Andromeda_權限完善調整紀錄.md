# 11 Meta Andromeda 權限完善調整紀錄

## 文件目的

本文件用於記錄 `Meta Andromeda` 模組在 `DataVue-App` 內的權限整合、簡化與驗收結果，並保留舊版細粒度權限設計的歷史背景。

目前 `Meta Andromeda` 已重新定義為 `Prediction / Observation / Learning` 模組。配合此定位，權限模型已從早期的多層功能權限，收斂為與現行系統一致的「模組存取權」模式。

## 現行權限結論

`Meta Andromeda` 現在只保留一個實際生效的入口權限：

- `meta_andromeda` module access

只要使用者在目前工作區具備 `meta_andromeda` 模組存取權，就可使用此模組內全部功能，包括：

- overview
- score lab
- review queue
- monitoring
- release
- drift trigger

現行實作不再區分：

- `meta_andromeda:view`
- `meta_andromeda:feedback`
- `meta_andromeda:operate`
- `meta_andromeda:release`

上述細粒度權限語義已不再作為 `Meta Andromeda` 的實際授權依據。

## 調整原因

`Meta Andromeda` 早期作為獨立 MVP 時，模組內部曾區分 review、feedback、operate、release 等操作層次，因此延伸出細粒度權限設計。

但在接入 `DataVue-App` 並重新定義模組功能後，`Meta Andromeda` 的重點已轉為：

- 無投放數據時，提供素材預估能力
- 有投放數據後，建立 observation 與 learning 閉環

在此階段，模組內部不再需要額外拆分多層角色操作權限。若繼續維持 `feedback / operate / release` 等細粒度 gate，會造成：

- 文件與實作難以維持一致
- 前端按鈕與 API 行為容易出現不一致
- reviewer / operator 的舊命名與新模組職能混淆
- 驗收與後台配置成本不必要增加

因此本次調整決策為：

- 入口層仍使用共用 `module access`
- `Meta Andromeda` 模組內功能暫時不再額外切 feature permission
- 若未來真的需要更細的 release governance，再另行擴充

## 權限模型演進

### 第一階段：細粒度權限方案

早期方案曾規劃下列權限語義：

- `meta_andromeda:view`
- `meta_andromeda:feedback`
- `meta_andromeda:operate`
- `meta_andromeda:release`

同時搭配：

- `team_viewer` 只讀
- `team_member` 可 feedback
- `team_admin` 可 operate / release
- `super_admin` 全域 bypass

此方案曾用於：

- team-aware 授權流程建立
- 前端工作區權限切換驗證
- API 權限覆蓋測試

### 第二階段：模組單權限收斂

配合 `Meta Andromeda` 模組重新定義後，權限架構已收斂為：

- `meta_andromeda` module access = 模組入口與全部功能授權

因此目前真實授權邏輯為：

- 沒有 `meta_andromeda` module access：不可進入或使用模組
- 有 `meta_andromeda` module access：可使用模組全部功能
- `super_admin`：保持全域 bypass

## 本次調整範圍

### 後端

- [backend/modules/auth/dependencies.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\auth\dependencies.py)
- [backend/modules/meta_andromeda/dependencies.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\dependencies.py)
- [backend/modules/meta_andromeda/router.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\router.py)
- [backend/seeds/permission_seeds.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\seeds\permission_seeds.py)
- [backend/tests/test_meta_andromeda_module.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\tests\test_meta_andromeda_module.py)
- [backend/tests/test_permissions.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\tests\test_permissions.py)

### 前端

- [frontend/src/pages/MetaAndromedaScoreLab.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\pages\MetaAndromedaScoreLab.jsx)
- [frontend/src/pages/MetaAndromedaReviewQueue.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\pages\MetaAndromedaReviewQueue.jsx)

### 文件

- [docs/10_Meta_Andromeda_模組說明.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\10_Meta_Andromeda_模組說明.md)
- [docs/12_FB_Ads_導入_Meta_Andromeda_整合規格.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\12_FB_Ads_導入_Meta_Andromeda_整合規格.md)
- [docs/13_FB_Ads_導入_Meta_Andromeda_實作計劃.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\13_FB_Ads_導入_Meta_Andromeda_實作計劃.md)
- 本文件

## 驗收條件

- 沒有 `meta_andromeda` module access 時，不可讀取 `Meta Andromeda` API
- 有 `meta_andromeda` module access 時，可使用模組內全部功能
- 前端頁面不再依 `meta_andromeda:feedback / operate / release` 分別顯示阻擋訊息
- seed、文件與實作中的 `Meta Andromeda` 權限語義一致
- `super_admin` 仍可繞過 module / permission 檢查

## 執行紀錄

### 2026-06-12

- 建立 `Meta Andromeda` 權限完善調整紀錄
- 完成 team-aware 授權流程與前端工作區權限同步
- 完成側欄模組顯示過濾
- 建立細粒度權限模型與對應驗收案例

### 2026-06-15

- `Meta Andromeda` 模組功能重新定義為 `Prediction / Observation / Learning`
- 確認現階段不再需要 `feedback / operate / release` 細粒度授權
- 將 `backend/modules/meta_andromeda/dependencies.py` 收斂為 module-only access
- `Meta Andromeda` 前端頁面移除 `meta_andromeda:operate` 與 `meta_andromeda:feedback` 額外 gate
- `permission_seeds.py` 移除 `Meta Andromeda` feature permission seeds，僅保留 `meta_andromeda` module access
- 測試案例改為驗證「無 module access 拒絕；有 module access 允許全部功能」
- 文件同步改寫，將舊版細粒度權限模型降為歷史背景

## 待辦清單

- [x] 釐清 `Meta Andromeda` 新模組定位對權限模型的影響
- [x] 將 `Meta Andromeda` 收斂為 module-only access
- [x] 對齊前後端與 seed 實作
- [x] 更新模組說明、整合規格與實作計劃文件
- [ ] 跑完整回歸測試並回填結果
