# DataVue 文件中心 (Documentation Index)

本目錄包含 DataVue 專案的所有架構設計、模組開發計畫、測試審查報告與部署指南。為了提升文件可讀性與維護效率，文件已按主題模組分類整理如下：

---

## 📁 目錄結構總覽

```text
docs/
├── 01_system/               # 核心系統架構、API 手冊與部署指南
├── 02_ga4/                  # GA4 轉換洞察與分析模組相關規劃與實作紀錄
├── 03_meta_andromeda/       # Meta Andromeda 廣告診斷與素材評分系統
├── 04_mmm/                  # MMM (行銷混合模型) 廣告貢獻衡量模組
├── 05_gsc/                  # Google Search Console 數據與 AI 搜尋擴充
├── 06_features_and_ui/      # 週報、Landing Page 與 UI/UX 改版計畫
├── 07_audits_and_reviews/   # 代碼審查 (Code Review) 與安全性審計報告
├── 08_business/             # 商業模式、定價與推廣策略規劃
├── impl/                    # 歷史修復與單元測試框架實作記錄
├── optimization/            # 歷史性能優化與重構紀錄 (P0 ~ P4)
└── legacy/                  # 舊版規格參考檔案與技術留存
```

---

## 📚 各模組文件目錄索引

### 1. ⚙️ 核心系統與架構 (`docs/01_system/`)
包含專案基本概覽、資料庫設計、權限控制與部署手冊。

- [01_專案概覽.md](01_system/01_專案概覽.md) - 系統核心價值與模組簡介
- [02_系統架構.md](01_system/02_系統架構.md) - 前後端分離架構與技術棧說明
- [03_資料庫設計.md](01_system/03_資料庫設計.md) - PostgreSQL / SQLAlchemy 模型欄位與 ER 設計
- [04_權限管理系統.md](01_system/04_權限管理系統.md) - RBAC 角色與數據存取權限控制
- [05_API_參考手冊.md](01_system/05_API_參考手冊.md) - FastAPI 端點規格說明
- [06_部署指南.md](01_system/06_部署指南.md) & [10_Zeabur_部署與持久化儲存設定指南.md](01_system/10_Zeabur_部署與持久化儲存設定指南.md) - 雲端部署與持久化儲存
- [07_開發與擴充手冊.md](01_system/07_開發與擴充手冊.md) - 開發規範與功能擴充指引
- [25_背景工作負載統一Worker架構規劃.md](01_system/25_背景工作負載統一Worker架構規劃.md) - Worker 佇列架構設計
- [71_專案現況架構與程式碼行數統計.md](01_system/71_專案現況架構與程式碼行數統計.md) - **現況**架構總覽與程式碼行數統計（2026-08-11，首要參考來源）
- [31_專案原始碼架構與關聯分析.md](01_system/31_專案原始碼架構與關聯分析.md) & [36_專案核心原始碼架構與關聯分析.md](01_system/36_專案核心原始碼架構與關聯分析.md) & [38_詳細系統功能與架構手冊.md](01_system/38_詳細系統功能與架構手冊.md) - 歷史拆分記錄與系統功能手冊（行數統計已過時，見上）
- [walkthrough.md](01_system/walkthrough.md) - 系統功能導覽
- [zeabur_deployment_guide.md](01_system/zeabur_deployment_guide.md) - Zeabur 部署操作指南

---

### 2. 📊 GA4 轉換洞察模組 (`docs/02_ga4/`)
包含 GA4 流量管道、到達頁、商品轉換率比對、告警與快照分享功能。

- [09_GA4週報功能實作計畫.md](02_ga4/09_GA4週報功能實作計畫.md) - GA4 週報功能規劃
- [22_GA4_即時轉換洞察模組實作計劃.md](02_ga4/22_GA4_即時轉換洞察模組實作計劃.md) - 核心洞察模組設計
- [34_GA4_轉換洞察渠道標籤精準化實作計劃.md](02_ga4/34_GA4_轉換洞察渠道標籤精準化實作計劃.md) - 渠道分類邏輯
- [39_GA4_轉換洞察快照分享連結實作計劃.md](02_ga4/39_GA4_轉換洞察快照分享連結實作計劃.md) & [61_GA4分享連結凍結副本實作規劃.md](02_ga4/61_GA4分享連結凍結副本實作規劃.md) - 洞察分享與凍結快照
- [40_GA4_商品頁面與商品轉換率交叉對照擴充構想.md](02_ga4/40_GA4_商品頁面與商品轉換率交叉對照擴充構想.md) ~ [57_GA4_商品頁面比對成長方向篩選實作規劃.md](02_ga4/57_GA4_商品頁面比對成長方向篩選實作規劃.md) - 到達頁與商品頁面交叉分析、成長方向與自訂天數篩選
- [59_GA4轉換洞察模組架構審查報告.md](02_ga4/59_GA4轉換洞察模組架構審查報告.md) ~ [67_GA4低風險清理實作紀錄.md](02_ga4/67_GA4低風險清理實作紀錄.md) - 查詢並行化、權限補強與 Code Clean

---

### 3. 🎯 Meta Andromeda 廣告診斷模組 (`docs/03_meta_andromeda/`)
包含 Meta 投放環境診斷、Prompt 自適應校準、素材評分閉環與 Worker 集中化方案。

- [12_Meta_Andromeda_技術完整參考手冊.md](03_meta_andromeda/12_Meta_Andromeda_技術完整參考手冊.md) - 技術總覽與演算法架構
- [13_Meta_Andromeda_模組操作與核對流程指南.md](03_meta_andromeda/13_Meta_Andromeda_模組操作與核對流程指南.md) - 數據核對與操作 SOP
- [14_Meta_Andromeda_投放環境診斷系統實作計劃.md](03_meta_andromeda/14_Meta_Andromeda_投放環境診斷系統實作計劃.md) ~ [16_Meta_Andromeda_廣告目標分類與指標路由計畫.md](03_meta_andromeda/16_Meta_Andromeda_廣告目標分類與指標路由計畫.md) - 診斷系統與 Prompt 自適應校準
- [17_Meta_Andromeda_Phase3_學習閉環與診斷校準工作台實作成果報告.md](03_meta_andromeda/17_Meta_Andromeda_Phase3_學習閉環與診斷校準工作台實作成果報告.md) & [18_Meta_Andromeda_模組功能審查與優化報告.md](03_meta_andromeda/18_Meta_Andromeda_模組功能審查與優化報告.md) - 學習閉環成果與模組審查
- [19_Meta_Andromeda_素材評分閉環優化建議報告.md](03_meta_andromeda/19_Meta_Andromeda_素材評分閉環優化建議報告.md) & [20_Meta_Andromeda_素材評分閉環優化實作計劃.md](03_meta_andromeda/20_Meta_Andromeda_素材評分閉環優化實作計劃.md) - 素材評分與診斷校準
- [23_Meta_Andromeda_非轉換素材預測對照補完計劃.md](03_meta_andromeda/23_Meta_Andromeda_非轉換素材預測對照補完計劃.md) - 非轉換素材預測對照
- [24_Meta_Andromeda_評分管線Event_Loop阻塞修復與模組優化實作計劃.md](03_meta_andromeda/24_Meta_Andromeda_評分管線Event_Loop阻塞修復與模組優化實作計劃.md) & [28_Meta_Andromeda_素材縮圖跨容器儲存問題與Worker集中化方案規劃.md](03_meta_andromeda/28_Meta_Andromeda_素材縮圖跨容器儲存問題與Worker集中化方案規劃.md) - 異步效能與儲存優化
- [30_Meta_Andromeda_評分模型真實準確率分析與改善建議.md](03_meta_andromeda/30_Meta_Andromeda_評分模型真實準確率分析與改善建議.md) & [32_Meta_Andromeda_評分模型準確率改善實作計劃.md](03_meta_andromeda/32_Meta_Andromeda_評分模型準確率改善實作計劃.md) - AI 模型準確率反饋與迭代
- [68_Meta_Andromeda_模組與成效分析匯入優化審查報告.md](03_meta_andromeda/68_Meta_Andromeda_模組與成效分析匯入優化審查報告.md) - 模組整體與觀測匯入路徑優化審查（2026-08-07）
- [facebook-ads-metrics-guide.md](03_meta_andromeda/facebook-ads-metrics-guide.md) - Facebook 廣告指標參考指南

---

### 4. 📈 MMM 行銷混合模型 (`docs/04_mmm/`)
行銷活動成效歸因與媒體貢獻衡量。

- [21_MMM_廣告活動貢獻衡量模組實作計劃.md](04_mmm/21_MMM_廣告活動貢獻衡量模組實作計劃.md) - 模組實作計畫
- [26_MMM_貢獻分析結果判讀指南.md](04_mmm/26_MMM_貢獻分析結果判讀指南.md) - 結果分析與維運指南
- [27_MMM_貢獻分析模組審查優化實作計劃.md](04_mmm/27_MMM_貢獻分析模組審查優化實作計劃.md) - 審查與演算法微調

---

### 5. 🔍 GSC 搜尋引擎數據 (`docs/05_gsc/`)
包含 Google Search Console 數據分析、AI Overview 與內容缺口建議。

- [29_GSC_API_資料呈現擴充實作規劃.md](05_gsc/29_GSC_API_資料呈現擴充實作規劃.md) - GSC 數據擴充規劃
- [35_GSC_AI_Overview_生成式AI搜尋數據擴充實作規劃.md](05_gsc/35_GSC_AI_Overview_生成式AI搜尋數據擴充實作規劃.md) - AI Overview 生成式搜尋解析
- [36_GSC_Phase1_搜尋類型與裝置國家交叉分析實作規劃.md](05_gsc/36_GSC_Phase1_搜尋類型與裝置國家交叉分析實作規劃.md) - 多維度搜尋交叉分析
- [37_GSC_內容缺口_AI文章方向建議_實作規劃.md](05_gsc/37_GSC_內容缺口_AI文章方向建議_實作規劃.md) - 內容缺口與 SEO 建議生成

---

### 6. 🎨 介面與功能規劃 (`docs/06_features_and_ui/`)
- [08_週報功能實作方案.md](06_features_and_ui/08_週報功能實作方案.md) - 定時與自動化週報系統
- [11_Landing_Page_改版實作計劃.md](06_features_and_ui/11_Landing_Page_改版實作計劃.md) - 首頁視覺與說明改版
- [58_成效分析頁AI廣告分析改版實作規劃.md](06_features_and_ui/58_成效分析頁AI廣告分析改版實作規劃.md) - 成效頁 UI/UX 重構

---

### 7. 🔍 代碼審查與重構歷史 (`docs/07_audits_and_reviews/`)
- [33_大型檔案拆分重構實作計劃.md](07_audits_and_reviews/33_大型檔案拆分重構實作計劃.md) - 代碼模組化拆分
- [69_全專案未完成規劃與缺口盤點.md](07_audits_and_reviews/69_全專案未完成規劃與缺口盤點.md) - 全 docs 目錄未完成項目盤點清單（2026-08-07）
- [archive/](07_audits_and_reviews/archive/) - 過時歷史快照（`CODE_AUDIT_*.md`、`CODE_REVIEW_*.md`、`OPTIMIZATION_REPORT.md`）：內容提到的架構（如單檔 `backend/database.py`）已不存在，僅供追溯歷史脈絡，非現行待辦

---

### 8. 💼 商業模式與推廣 (`docs/08_business/`)
產品定位、定價架構、商業化阻斷點與獲客策略（非技術文件）。

- [72_商業模式與推廣策略規劃.md](08_business/72_商業模式與推廣策略規劃.md) - 現況商業盤點、三大商業化阻斷點（Meta App Review／Google OAuth 驗證／計費分級）、代理商垂直 SaaS 定價提案與分階段推廣策略（2026-08-12，**待審閱**）

---

## 💡 貢獻與開發規範

新增或更新文件時，請遵守以下原則：
1. **目錄歸類**：請將新的計畫或手冊置於對應的子目錄（如 `02_ga4/` 或 `03_meta_andromeda/`）。
2. **更新索引**：在新增文件後，同步更新本 [README.md](README.md) 的文件清單。
3. **繁體中文**：開發規範與文件預設使用**繁體中文**撰寫，詳情請參考專案根目錄 [GEMINI.md](../GEMINI.md)。
4. **相對路徑**：索引與文件間的連結一律使用相對路徑，勿使用 `file:///` 絕對路徑，以確保在 GitHub 或其他機器上可正常開啟。
