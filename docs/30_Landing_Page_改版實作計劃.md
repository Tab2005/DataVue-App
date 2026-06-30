# Landing Page 改版實作計劃

> 建立日期：2026-06-30
> 狀態：規劃中

---

## 一、改版目標

1. 完整呈現 DataVue 所有核心功能（補上 Reports、Meta Andromeda）
2. 拆分新用戶與既有用戶的 CTA 路徑，提升轉換率
3. 建立社會證明與信任感
4. 強化代理商受眾的功能說服力（多帳號、自動排程報告）

---

## 二、現有結構 vs 改版結構對照

| # | 現有 Section | 改版 Section | 異動說明 |
|---|---|---|---|
| 1 | Navbar | Navbar | 微調：拆分 CTA |
| 2 | Hero | Hero | 重寫副標題與浮動卡片 |
| 3 | — | LogoBar（新增） | 整合平台 + 數字佐證 |
| 4 | Features（4 Tab） | Features（5 Tab） | 補上 Reports Tab |
| 5 | PainPoints | PainPoints | 保留，微調文案 |
| 6 | — | MetaAndromeda（新增） | AI 引擎獨立 Section |
| 7 | Audience | Audience | 保留，補上代理商多帳號說明 |
| 8 | — | SocialProof（新增） | 用戶評語 + 使用數字 |
| 9 | HowItWorks（3步） | HowItWorks（4步） | 加上第四步「報表輸出」 |
| 10 | — | FinalCTA（新增） | 全寬召喚 Banner |
| 11 | Footer | Footer | 補上 FAQ 折疊清單 |

---

## 三、各 Section 實作規格

### Section 1 — Navbar（微調）

**檔案**：`frontend/src/components/Landing/Navbar.jsx`

**改動：**
- 現有「立即開始」→ 改為「**免費試用**」，連結改為 `/login?mode=register`
- 「登入」按鈕保留，視覺降低（去除 border 或改為純文字）
- 導航錨點：核心引擎 / 痛點剖析 / 適用場景 / 運作原理 / **AI 引擎**（新增）

---

### Section 2 — Hero（重寫）

**檔案**：`frontend/src/components/Landing/Hero.jsx`

**主標題**：維持「匯聚所有數據 / 洞察一觸即達」

**副標題**（改寫）：
> Facebook Ads、Google Search Console、GA4 — 三大平台數據在同一個宇宙匯聚。DataVue 以 AI 為核心提煉洞察，並自動輸出可分享的週報，讓決策不再等待。

**右側浮動卡片**（從 3 張擴充為 4 張）：
- 原有：FB ROAS 卡、GSC 曝光卡、GA4 轉換率卡
- 新增：**週報卡**「週報已生成 — 自動排程，每週一 09:00 發送」

**主 CTA**：「免費試用 →」（保留 cyan 輝光）
**次 CTA**：「了解核心功能」→ `#features`

---

### Section 3 — LogoBar（新增）

**檔案**：`frontend/src/components/Landing/LogoBar.jsx`（新建）

**設計**：Hero 下方的橫向窄帶（80px 高），深色背景

**內容**：
```
整合平台：[Facebook Ads 圖示]  [Google Search Console 圖示]  [Google Analytics 4 圖示]
數字列：「X 個廣告帳戶已連接  ·  X 份週報自動產出  ·  X 位行銷人使用中」
```

**技術備註**：數字初期可為靜態文案，後續可接後端 API 取得真實數字。

---

### Section 4 — Features（擴充第 5 個 Tab）

**檔案**：`frontend/src/components/Landing/Features.jsx`

**新增 Tab — Reports（橘色主題）**：
- Tab 標籤：「週報自動化 / Reports Automation」
- 標題：「自動排程報告，告別手動整理」
- 說明：「設定一次，自動執行。每日、每週、每月定時生成廣告成效報告，支援 PDF 輸出與一鍵分享連結，讓客戶報告從耗時變成例行事務。」
- 量化成效：「節省 X 小時 / 週的手動整理時間」
- 視覺化：排程設定 UI 截圖風格卡片（顯示「每週一 09:00」、「已發送 12 份」、啟用開關）

**既有 Tab 微調：**
- GSC Tab：亮點說明補上「含內容缺口（Keyword Gap）分析」
- FB Ads Tab：補上「支援多廣告帳號切換，適合代理商跨客戶管理」

---

### Section 5 — PainPoints（保留，微調）

**檔案**：`frontend/src/components/Landing/PainPoints.jsx`

**微調**：
- 痛點三「架構僵化」的 DataVue 方案說明中，補上「自訂內容分組」與「報表自動排程」作為靈活擴展的具體佐證

---

### Section 6 — MetaAndromeda（新增）

**檔案**：`frontend/src/components/Landing/MetaAndromeda.jsx`（新建）

**定位**：「即將全面開放的 AI 廣告評分引擎」

**設計風格**：深色仿終端機風格，與 Features Tab 4（AI 智庫）一致的視覺語言

**區塊結構**：
```
[章節標籤] AI 廣告引擎  ·  Coming Soon
[主標題] Meta Andromeda
           AI 廣告素材評分系統
[副標題] 每一支廣告在投放前，都經過 AI 的嚴格審核。
         廣告素材評分、自動審核佇列、偏差校準 — 為代理商設計的智能廣告管理系統。

[四個能力卡片]
├── 廣告素材評分  — 自動對創意進行多維度評分，預測投放潛力
├── 審核佇列管理  — 管理所有待審素材，支援批次操作
├── 偏差自動校準  — 當評分出現系統性偏差時，自動生成修正版模型
└── 版本控制      — 管理不同版本的評分模型，精確掌控上線時機

[狀態說明]「目前開放早期測試，歡迎代理商夥伴申請加入」
[CTA] 申請優先體驗 →（導向 /login 或聯繫表單）
```

---

### Section 7 — Audience（保留，補強）

**檔案**：`frontend/src/components/Landing/Audience.jsx`

**改動**：
- 「數位代理商」卡片描述中，補上「多帳號切換 · 團隊協作 · 自動排程報告」三個 feature badge

---

### Section 8 — SocialProof（新增）

**檔案**：`frontend/src/components/Landing/SocialProof.jsx`（新建）

**設計**：三欄用戶評語卡片，深色磨砂卡片風格

**初期內容結構**（先用佔位文案，後續替換真實評語）：
```
卡片 1：
"使用 DataVue 之後，每週的廣告報告從 3 小時縮短到 20 分鐘。"
— 行銷經理 / 電商品牌

卡片 2：
"GSC 的關鍵字缺口分析幫助我們找到了競品沒有覆蓋的長尾詞，流量提升了 40%。"
— SEO 策略師 / 數位代理商

卡片 3：
"多帳號管理功能對我們這種同時服務 10+ 客戶的代理商來說是剛需。"
— 業務總監 / 整合行銷公司
```

---

### Section 9 — HowItWorks（3步 → 4步）

**檔案**：`frontend/src/components/Landing/HowItWorks.jsx`

**新增 Step 04（青綠色主題）**：
- 副標題：「自動輸出，隨時分享」
- 說明：「設定排程後，報表自動生成並支援一鍵分享連結。客戶、主管、團隊成員，隨時查看最新成效。」

**視覺調整**：桌機版連接線從 3 段擴充為 4 段（blue → purple → cyan → teal）

---

### Section 10 — FinalCTA（新增）

**檔案**：`frontend/src/components/Landing/FinalCTA.jsx`（新建）

**設計**：全寬區塊，漸層背景（cyan → purple），居中排版

**內容**：
```
[主標題] 現在就開始，讓數據替你工作
[副標題] 免費連接您的第一個數據源，三分鐘內看到洞察
[主 CTA]  免費試用 →
[次 CTA]  查看功能示範（anchor to #features）
[說明文字] 無需信用卡 · OAuth 安全授權 · 隨時取消
```

---

### Section 11 — Footer（補上 FAQ）

**檔案**：`frontend/src/components/Landing/Footer.jsx`

**新增 FAQ 折疊清單（5 題）**：

| 問題 | 回答摘要 |
|---|---|
| 需要信用卡才能試用嗎？ | 不需要，免費連接第一個數據源 |
| 支援哪些廣告帳戶類型？ | Facebook Ads、Google 生態系（GSC、GA4） |
| 我的數據安全嗎？ | 使用 OAuth 2.0，不儲存密碼，資料加密傳輸 |
| 是否支援多人協作？ | 支援團隊功能，可邀請成員並設定權限 |
| Meta Andromeda 什麼時候開放？ | 目前開放早期測試，可申請優先體驗 |

---

## 四、新元件檔案清單

| 狀態 | 檔案路徑 | 說明 |
|------|---------|------|
| 新建 | `frontend/src/components/Landing/LogoBar.jsx` | 整合平台 Badge + 數字帶 |
| 新建 | `frontend/src/components/Landing/MetaAndromeda.jsx` | AI 引擎獨立 Section |
| 新建 | `frontend/src/components/Landing/SocialProof.jsx` | 用戶評語卡片 |
| 新建 | `frontend/src/components/Landing/FinalCTA.jsx` | 全寬召喚 Banner |
| 修改 | `frontend/src/components/Landing/Navbar.jsx` | CTA 拆分 |
| 修改 | `frontend/src/components/Landing/Hero.jsx` | 副標題 + 第四張浮動卡 |
| 修改 | `frontend/src/components/Landing/Features.jsx` | 新增 Reports Tab |
| 修改 | `frontend/src/components/Landing/PainPoints.jsx` | 文案微調 |
| 修改 | `frontend/src/components/Landing/Audience.jsx` | 代理商卡補強 |
| 修改 | `frontend/src/components/Landing/HowItWorks.jsx` | 增加第四步 |
| 修改 | `frontend/src/components/Landing/Footer.jsx` | 新增 FAQ |
| 修改 | `frontend/src/pages/Landing.jsx` | 引入所有新 Section |

---

## 五、實作優先順序

### Phase 1（高優先，直接影響轉換）
- [ ] Navbar CTA 拆分（免費試用 vs 登入）
- [ ] Features 新增 Reports Tab
- [ ] FinalCTA Section 新增

### Phase 2（中優先，差異化說服）
- [ ] Hero 副標題重寫 + 第四張浮動卡
- [ ] MetaAndromeda Section 新增
- [ ] HowItWorks 增加第四步

### Phase 3（補強信任感）
- [ ] LogoBar 新增
- [ ] SocialProof 新增
- [ ] Audience 代理商卡補強
- [ ] Footer FAQ 新增
- [ ] PainPoints 文案微調

---

## 六、設計規範（沿用現有風格）

- **色系**：保留現有 cyan / purple / blue / green 主題分色
- **背景**：深色（`bg-black` / `bg-gray-900`）為基底
- **卡片**：毛玻璃效果（`backdrop-blur`、`bg-white/5`）
- **動畫**：Framer Motion 或 CSS transition，hover 上浮 `-8px`
- **字體**：主標題 `font-bold text-4xl`，區塊標籤用 cyan badge
- **間距**：各 Section `py-24`，保持寬鬆呼吸感

---

## 七、後續追蹤

- SocialProof 的真實用戶評語需與業務端確認是否有真實案例可用
- LogoBar 的動態數字（帳號數、報表數）是否接後端 API，需確認有無對應端點
- Meta Andromeda「申請優先體驗」CTA 的導向目標（/login 還是另建申請表單）需確認
