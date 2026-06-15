# 11 Meta Andromeda 權限完善調整紀錄

## 文件目的

本文件用於記錄 `Meta Andromeda` 模組在 `DataVue-App` 內的權限完善工作，作為後續實作、驗收、回歸測試與部署追蹤的單一依據。

本次調整不只處理「後台已顯示模組與角色」的整合狀態，而是要把模組可見性、操作權限、團隊工作區隔離與測試覆蓋補到可驗收狀態。

## 背景

目前後台權限設定頁已能列出：

- 模組 `meta_andromeda`
- 權限 `meta_andromeda:view`
- 權限 `meta_andromeda:feedback`
- 權限 `meta_andromeda:operate`
- 權限 `meta_andromeda:release`

但依目前程式實作，這代表的是「權限資料已接入」，不代表：

- 前端側欄會依實際模組權限隱藏或顯示
- 路由保護會依目前選取的 team 正確切換
- API 端點會依 `X-Team-ID` 做角色權限判定
- reviewer / member / viewer / admin 的隔離已被測試驗證

## 現況判讀

### 已完成

- `Meta Andromeda` 已加入模組 seed
- 對應權限 seed 已存在
- 模組 API 已接上權限 dependency
- 前端頁面已對部分操作按鈕使用 `usePermission`
- 後台權限管理頁已顯示此模組與角色矩陣

### 未完成

- 共用授權 dependency 尚未正確吃到 team context
- 前端路由與 permission hook 尚未完整使用目前工作區 team
- 側欄尚未依模組存取權做顯示過濾
- 文件中的權限命名與 seed/實作不一致
- 權限隔離測試尚未覆蓋真實 allow / deny 情境

## 問題摘要

### 1. 權限命名不一致

文件 [10_Meta_Andromeda_模組說明.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\10_Meta_Andromeda_模組說明.md) 目前寫的是：

- `meta_andromeda:module`
- `meta_andromeda:operate`
- `meta_andromeda:feedback`
- `meta_andromeda:release`

但權限 seed 實際建立的是：

- `meta_andromeda:view`
- `meta_andromeda:feedback`
- `meta_andromeda:operate`
- `meta_andromeda:release`

而模組入口保護又另外依賴 `user_module_access` 的 `meta_andromeda` 模組可見性，不是單靠 `meta_andromeda:view`。

### 2. 後端權限檢查未帶入 team context

目前共用的 `require_permission()` 與 `require_module()` 依賴在呼叫 `PermissionService` 時，`team_id` 寫死為 `None`。

這表示：

- API 端點即使在團隊工作區下操作
- 前端即使帶了 `team_id` query string
- 後端實際授權仍以個人工作區模式判斷

### 3. 前端模組保護未真正跟隨工作區切換

目前 `ProtectedModule` 與 `usePermission()` 雖支援 `teamId`，但 Meta Andromeda 的路由保護與頁面使用沒有完整傳入目前工作區的 team id。

這表示：

- 切換團隊後，頁面權限可能不會跟著切換
- 使用者可能看到不該看到的選單
- 或被錯誤擋下本來應可操作的功能

### 4. 側欄目前是靜態顯示

`Meta Andromeda` 子選單目前直接寫死在側欄資料結構內，尚未依 `useUserModules()` 或等價權限來源動態過濾。

### 5. 測試尚未驗證真實權限隔離

目前 Meta Andromeda 測試大多透過 dependency override 直接略過權限檢查，這能驗證功能流程，但不能證明權限模型正確。

## 本次調整目標

本次調整要完成以下目標：

1. 統一 Meta Andromeda 權限命名與文件說明
2. 讓後端模組/權限檢查支援 team-aware 判定
3. 讓前端路由與操作權限跟隨目前選取工作區
4. 讓側欄依模組權限正確顯示或隱藏
5. 補齊 reviewer / member / viewer / admin / super admin 的權限測試
6. 更新模組文件與本調整紀錄，保留驗收結果

## 實作範圍

### 後端

- [backend/modules/auth/dependencies.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\auth\dependencies.py)
- [backend/services/permission_service.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\services\permission_service.py)
- [backend/modules/meta_andromeda/dependencies.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\dependencies.py)
- [backend/modules/meta_andromeda/router.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\modules\meta_andromeda\router.py)
- [backend/tests/test_meta_andromeda_module.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\tests\test_meta_andromeda_module.py)
- [backend/tests/test_permissions.py](C:\Users\BWM2\Documents\python\DataVue-App\backend\tests\test_permissions.py)

### 前端

- [frontend/src/App.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\App.jsx)
- [frontend/src/components/Sidebar.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\components\Sidebar.jsx)
- [frontend/src/hooks/usePermission.jsx](C:\Users\BWM2\Documents\python\DataVue-App\frontend\src\hooks\usePermission.jsx)
- Meta Andromeda 相關頁面

### 文件

- [docs/10_Meta_Andromeda_模組說明.md](C:\Users\BWM2\Documents\python\DataVue-App\docs\10_Meta_Andromeda_模組說明.md)
- 本文件

## 調整策略

### Phase 1. 權限語義統一

- 明確區分「模組可進入」與「模組內功能操作」
- 保留 `meta_andromeda` 作為 module access key
- 保留 `meta_andromeda:view` 作為唯讀檢視語義，不作為 module access 的別名
- 修正文檔中 `meta_andromeda:module` 的描述，避免與實作不一致

### Phase 2. 後端 team-aware 權限檢查

- 從 request header 取得目前工作區 `X-Team-ID`
- `require_module()` 與 `require_permission()` 必須使用實際 team context
- Meta Andromeda API 的所有權限保護改為依工作區判斷

### Phase 3. 前端工作區權限同步

- 前端 permission hooks 要統一使用目前工作區 team id
- 路由保護與頁面操作權限都要一致
- 側欄依使用者可見模組列表過濾

### Phase 4. 測試與驗收

- 新增 allow / deny 測試
- 驗證 team viewer 僅能看
- 驗證 team member 可 feedback 但不可 operate / release
- 驗證 team admin 可 operate / release
- 驗證 super admin 仍可 bypass

## 驗收條件

- 非授權使用者不可進入 `/meta-andromeda*` 路由
- 沒有 module access 時側欄不顯示 `Meta Andromeda`
- `team_viewer` 只能讀取 overview / review queue / monitoring / release overview / feedback list
- `team_member` 可提交 feedback，但不可 upload asset、submit score、trigger drift、approve/reject/rollback release
- `team_admin` 與 `team_owner` 可執行 operate / release
- `super_admin` 保持全域 bypass
- 文件與 seed / 程式實作中的權限命名一致
- 自動測試可覆蓋主要權限路徑

## 風險與注意事項

- 若前端與後端各自使用不同的 team 來源，會出現畫面可見但 API 403 的不一致
- 若沿用目前 override 型測試，容易誤判權限已完成
- 若文件不先修正，UAT 與後台操作會繼續混淆 `module access` 和 `view permission`

## 執行紀錄

### 2026-06-12

- 建立本調整紀錄文件
- 完成現況盤點
- 確認本次優先處理範圍為權限模型、team-aware 授權、前端顯示與測試覆蓋
- 完成 Phase 1 決策：
  - `meta_andromeda` = module access key，負責模組可見性與主入口存取
  - `meta_andromeda:view` = 唯讀檢視語義，保留給角色矩陣與 finer-grained read permission
  - `meta_andromeda:feedback / operate / release` = 模組內操作權限
- 已同步更新 Meta Andromeda 模組說明與模組 README
- 已將 seed 中 `meta_andromeda:view` 的顯示名稱改為「唯讀檢視」
- 完成 Phase 2 後端 team-aware 授權：
  - `backend/modules/auth/dependencies.py` 的 `require_module()` / `require_permission()` 已改為讀取 `X-Team-ID`
  - 舊版 `backend/dependencies.py` 同步對齊，避免新舊授權邏輯分叉
  - 已新增測試驗證 team-scoped module access 與 team role permission 會隨 `X-Team-ID` 生效
- 完成 Phase 3 前端工作區權限同步：
  - `frontend/src/hooks/usePermission.jsx` 新增 `useSelectedTeamId()`，集中追蹤目前工作區
  - 未顯式傳入 `teamId` 的 `ProtectedModule` / `useModuleAccess` / `usePermission` / `useUserModules` / `useUserPermissions`，會自動使用目前選取工作區
  - `frontend/src/components/Layout.jsx` 在工作區切換時會派發前端事件，確保同頁面內 hook 立即同步
  - Meta Andromeda 的 Monitoring / Release / ReviewQueue / ScoreLab 頁面已顯式使用 `selectedTeamId`
  - 已執行 `frontend` build 驗證通過
- 完成側欄模組顯示過濾：
  - `frontend/src/components/Sidebar.jsx` 已改為使用 `useUserModules()` 動態過濾 module-backed 選單
  - 目前 `fb_ads` / `gsc` / `ga4` / `meta_andromeda` 相關入口都會依目前工作區的 module access 顯示或隱藏
  - 已再次執行 `frontend` build 驗證通過

## 待辦清單

- [x] 統一 Meta Andromeda 權限命名與文件
- [x] 修正後端 `require_module()` / `require_permission()` 的 team-aware 行為
- [x] 修正前端 route guard 與 page-level permission hook 的 team 同步
- [x] 修正側欄模組顯示過濾
- [x] 補齊後端權限測試
- [ ] 更新模組說明文件與驗收結果

### 2026-06-15

- 補齊 Meta Andromeda API 層權限測試，覆蓋下列情境：
  - 無 `module access` 時不得讀取 `overview`
  - `team_viewer` 可讀取唯讀入口
  - `team_member` 可提交 feedback，但不可執行 `operate` 與 `release`
  - `team_admin` 可執行 `drift:trigger` 與 `release:approve`
- 補齊共用授權 dependency 測試，確認 `super_admin` 可繞過 module / permission 檢查
- 已使用 `backend\\.venv311\\Scripts\\python.exe -m pytest` 驗證新增案例通過
