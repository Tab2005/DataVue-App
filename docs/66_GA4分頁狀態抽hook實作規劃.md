# GA4 分頁狀態抽 hook 實作規劃（docs/59 P2-1）

- 立案日期：2026-08-04
- 對應審查項目：docs/59 §P2-1「前端狀態管理已達單一元件規模上限」（建議處理順序 8）

---

## 1. 問題

`pages/GA4Insights.jsx` 是 1,206 行、94 個 `useState` 的單一元件。實測 props 數與
docs/59 的統計一致：

| 分頁 | props 數 |
|---|---|
| `ItemsTab` | 53 |
| `LandingPagesTab` | 51 |
| `AlertsTab` | 23 |
| 其餘 4 個 | 11–12 |

後果就是 docs/59 講的：加一個小欄位要在父層 state、傳遞、子層解構三處同步改；
任何 state 變動 re-render 整個檔案；已經出現過漏傳。

## 2. 做法：一個分頁一個 hook

新增：

```
frontend/src/hooks/useGA4LandingPagesTab.js
frontend/src/hooks/useGA4ItemsTab.js
```

每個 hook 收攏該分頁的**全部** state、loader 與 handler，回傳一個物件；分頁元件
改成只收一個 prop：

```jsx
<LandingPagesTab language={language} t={t} isMobile={isMobile}
                 propertyId={propertyId} canManageRules={canManageGa4InsightsRules}
                 landing={landing} />
```

51 / 53 props → 各 5 個。加欄位從「三處同步改」變成「hook 內部一處」。

### 為什麼 hook 在**父層**呼叫，而不是分頁元件自己呼叫

docs/59 的建議寫的是「讓分頁元件自己持有狀態」。實作前確認過現況後改成父層持有，
理由是一個 docs/59 沒有列到的既有行為：

```jsx
{propertyId && activeTab === 'landing' && (<LandingPagesTab ... />)}
```

分頁是**條件渲染**的——切走就 unmount。狀態現在放在父層，所以切到別的分頁再切回來
時，快照、分類篩選、渠道選擇、比較開關、表格頁碼全都還在，也不會重打一次 GA4
查詢（父層的懶載入條件是 `!landingSnapshot`）。

如果照字面把狀態移進分頁元件，切走 unmount 就全部丟掉，切回來會重抓一次 GA4 並把
使用者選的篩選條件重設。那是使用者看得到的退步，不接受。

hook 在父層呼叫則兩者兼得：狀態的生命週期不變，而「這個分頁的所有狀態與行為」仍然
收在單一個檔案裡——後者才是 docs/59 真正要解決的維護成本。

至於 re-render：狀態仍在父層，所以「任何 state 變動 re-render 全部分頁」這點沒有靠
抽 hook 解決。但實際上非 active 的分頁根本沒有被渲染（條件渲染），re-render 的範圍
本來就只有目前這一個分頁，這一項的實際影響比 docs/59 描述的小。真要處理要改成
`memo` + 穩定的 callback 參考，屬於另一個層次的優化，本次不做。

## 3. 順帶處理：`DaySelector`

`DaySelector` 目前定義在 `GA4Insights.jsx` 的元件**函式內部**，再當 prop 傳給 5 個
分頁。每次父層 render 都會產生一個新的函式identity，React 因此把它當成不同的元件
型別 → 整棵子樹 unmount 再 mount，內部的 `customText` state 跟著重置。

搬到 `GA4InsightsShared.jsx` 當模組層級元件，分頁直接 import：一次同時解掉這個潛在
的重掛載問題，並從 5 個分頁各拔掉一個 prop。

## 4. 邊界條件

抽 hook 時要保住的既有行為：

1. **懶載入**：父層 `useEffect` 依 `activeTab`/`propertyId` 判斷「沒抓過才抓」。
   改由 hook 提供 `ensureLoaded(propertyId)`，把 `!snapshot` / `!rules` 的判斷收進去
2. **切換屬性時的重設**：`handlePropertyChange` 現在會清掉各分頁的快照與篩選。
   hook 提供 `reset()`，由 `handlePropertyChange` 明確呼叫——刻意不用「watch
   propertyId 自己重設」的寫法，避免 effect 觸發順序跟 `load(next)` 交錯
3. **loader 的預設參數**：`loadLandingPages(pid, days, keyEvent = landingKeyEvent, ...)`
   這種「沒傳就用目前 state」的預設值語意要原樣保留，呼叫端（分頁元件）傳位置參數
   的寫法一個字都不用改
4. 渠道分組規則的 CRUD 會連動重載規則列表與分組下拉，順序不變

## 5. 測試

新增 `frontend/src/pages/__tests__/GA4Insights.test.jsx`：

1. 切到到達頁會載入一次；切走再切回來**不重載**、篩選條件仍在（第 2 節那個行為的鎖）
2. 切換 GA4 屬性會清掉兩個分頁的快照與篩選
3. 到達頁分類規則新增/刪除後會連動重載規則列表與到達頁資料
4. 商品分頁排序點擊會切換欄位與方向（`sortedItemsRows` / `renderItemsSortHeader`）
5. `DaySelector` 自訂天數：有效值才生效、無效值還原顯示

## 6. 不做的事

- 不動 `AlertsTab`（23 props）與其餘 4 個分頁（11–12 props）：docs/59 明講重點是
  到達頁與商品這兩個 50+ 的，其餘規模還在可讀範圍
- 不引入狀態管理函式庫
- 不做 `memo` / callback 穩定化（理由見第 2 節末）
