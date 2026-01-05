# Facebook Dashboard SaaS - 專案路線圖與創意筆記

**最後更新**: 2025-12-30
**專案狀態**: v1.6.1 (Stable Phase - 穩定版)
**品牌名稱**: **DataVue**

本文檔用於追蹤 Facebook Dashboard SaaS 平台的開發路線圖、已完成的里程碑以及未來的架構計畫。

---

## 🏗️ 多數據源整合架構規劃 (Multi-Source Integration)

### 背景
系統正從「單一 FB Ads 儀表板」擴展為「多數據源整合平台」(FB Ads + GSC + GA4)。
需要重新思考導航結構、總覽頁面定位、以及 Header 選擇器的設計。

### 問題 1: 總覽頁面定位

**現況**: 總覽 (Dashboard) 只顯示 FB Ads 數據
**問題**: GSC / GA4 加入後，用戶需要一個「全景視圖」

**建議方案: 統一總覽儀表板**
```
┌─────────────────────────────────────────────────────────────┐
│  📊 總覽 (Unified Dashboard)                                 │
├───────────────────┬───────────────────┬─────────────────────┤
│  💰 FB Ads        │  🔍 GSC           │  📈 GA4             │
│  ─────────────    │  ─────────────    │  ─────────────      │
│  本月花費 $12,345 │  本月點擊 8,432   │  本月工作階段 15K   │
│  ROAS 2.8x        │  平均排名 #4.2    │  轉換率 3.2%        │
│  購買 156         │  曝光 298K        │  跳出率 42%         │
└───────────────────┴───────────────────┴─────────────────────┘
```
- 一眼看到所有渠道的 KPI
- 卡片式設計，每個渠道獨立一塊
- 點擊卡片可直接跳轉到對應詳細頁面

### 問題 2: 頂部廣告帳號選擇器

**現況**: Header 固定顯示 FB 廣告帳號下拉選單
**問題**: GSC 是以「網站」為單位，GA4 是以「Property」為單位，三者選擇邏輯不同

**方案 A: 情境式選擇器**

| 目前所在頁面 | Header 顯示 |
|-------------|-------------|
| FB Ads 成效分析 | 廣告帳號選擇器 |
| GSC 搜尋管理 | 網站選擇器 |
| GA4 流量分析 | Property 選擇器 |
| 總覽 (統一) | 不顯示 / 顯示已連結資產 |

**方案 B: 側邊欄資產管理**
```
┌─────────────────────┐
│ 🏢 福來朗內部       │ ← 團隊名稱
├─────────────────────┤
│ 📊 已連結資產        │
│  ├ 🔵 FB: act_123   │
│  ├ 🟢 GSC: example  │
│  └ 🟠 GA4: 12345    │
├─────────────────────┤
│ 📈 總覽             │
│ 💰 Facebook Ads     │ → 進入後再選帳號
│ 🔍 搜尋管理 (GSC)   │ → 進入後再選網站
│ 📊 流量分析 (GA4)   │
└─────────────────────┘
```

### 問題 3: 導航結構調整

**現況**: 側邊欄按「功能」分類 (總覽、成效分析、指標管理...)
**建議**: 改為按「數據源 → 功能」兩層結構

```
📊 總覽 (跨渠道)
─────────────────
💰 Facebook Ads
   ├ 成效分析
   ├ 指標管理
   └ AI 診斷
─────────────────
🔍 Google Search Console
   ├ 搜尋成效
   ├ 頁面分析
   └ 關鍵字群組
─────────────────
📈 Google Analytics (未來)
   ├ 流量概覽
   └ 轉換漏斗
─────────────────
⚙️ 設定
```

### 實作優先級

| 優先級 | 項目 | 工作量 |
|:------:|------|--------|
| 🔴 P1 | Header 選擇器改為情境式 | 2-3 小時 |
| 🔴 P1 | 側邊欄導航重構 (按數據源分組) | 2-3 小時 |
| 🟡 P2 | 統一總覽儀表板設計 | 4-6 小時 |
| 🟢 P3 | 資產管理面板 (查看所有已連結帳號) | 2-3 小時 |

---

## 🎨 品牌定位 (Brand Identity)

### DataVue
**整合 FB Ads、Google Search Console、GA4 的全方位行銷數據儀表板**

- **名稱由來**: Data (數據) + Vue (法語「視野」)
- **品牌口號**:
  - 英文: *"See the complete picture."*
  - 中文: *「數據全景，一目了然」*
- **目標用戶**: 行銷團隊、數位廣告代理商、電商企業
- **核心價值**: 多數據源整合、即時洞察、團隊協作

### 配色方案
- **主色**: 深藍 (#1E3A8A) - 專業、信賴
- **輔色**: 青綠 (#10B981) - 成長、洞察
- **強調色**: 橙色 (#F59E0B) - 行動、活力

---

## 🏁 Completed Features (已完成功能)

### 3. 使用者與權限管理 (Phase 3: Access Control) - ✅ v1.6.0 完成
**目標**: 建立完整的權限控制與付費訂閱基礎。
- **🔐 權限管理系統 (RBAC)**:
  - 模組化權限架構 (FB Ads, GSC, GA4)
  - 角色定義 (Owner, Admin, Member, Viewer)
  - PermissionService 核心邏輯
- **👤 超級管理員後台**:
  - 模組/權限/角色可視化列表
  - 使用者模組授權管理介面 (User Module Access)
- **⚡ 前端權限整合**:
  - `usePermission` & `useModuleAccess` Hooks
  - 路由保護與 UI 條件渲染
- **🛡️ API 安全防護**:
  - `require_module` 裝飾器 (已應用於 GSC 模組)
  - 新使用者自動授權流程

---

## 🚧 Active Development (開發進行中)

目前正在構建或即將進行的功能。

### 1. AI 智慧分析引擎 (Phase 1: 分析師)
**目標**: 將儀表板從被動的報表工具轉變為「主動的 AI 顧問」。
*   **✅ 後端服務**: 已實作透過 Google Gemini 整合的 `AIService`。
*   **✅ 前端介面**: 完成 "AI Analyst" 側邊滑出面板與連線測試按鈕。
*   **✅ 診斷模式**: 自動分析目前畫面數據 (Campaign/AdSet)，找出關鍵問題與機會點。
*   **🚧 分層金鑰管理 (Scope Key Management)**:
    *   **個人金鑰 (User Level)**: 存於 `users` 資料表，僅限個人工作區使用。
    *   **團隊金鑰 (Team Level)**: 存於 `teams` 資料表，供團隊成員協作使用。
    *   **分享邏輯**: 明確的「複製到團隊 (Copy to Team)」按鈕 (不採用隱式共享)。
*   **🚧 AI 自訂指令系統 (Custom AI Instructions)**:
    *   **概念**: 允許用戶/團隊定義 System Prompts，客製化 AI 的分析風格 (Persona)。
    *   **儲存**: 資料庫 (`ai_system_prompt` 欄位)。
    *   **優先級**: 團隊指令 (Team Prompt) > 個人指令 (User Prompt) > 系統預設 (System Default)。

---

### 2. AI 模組升級計劃 (Zeabur AI Hub Multi-Model) 🆕

**目標**: 將 AI 模組從單一 Gemini 模型升級為支援多種 AI 模型 (GPT, Claude, Gemini 等)，透過 Zeabur AI Hub 統一介面。

#### 背景

| 項目 | 現況 | 升級後 |
|------|------|--------|
| SDK | Google GenAI SDK | ✅ OpenAI SDK (更通用) |
| 支援模型 | 僅 Gemini | ✅ 15+ 種模型 |
| API 端點 | 寫死 Zeabur Gemini | ✅ 可選 東京/舊金山 |
| 用戶選擇 | 無 | ✅ 前端可切換模型 |

#### 技術架構

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Zeabur AI Hub                                       │
│                    (統一 API Gateway - OpenAI 相容)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│   │  Gemini   │   │  Claude   │   │   GPT     │   │ DeepSeek  │            │
│   │ 2.5/3.0   │   │ 4.5/Haiku │   │ 4o/5/mini │   │ v3.2      │            │
│   └───────────┘   └───────────┘   └───────────┘   └───────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↑
                                    │ OpenAI SDK
                                    │ base_url = "https://hnd1.aihub.zeabur.ai/v1"
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ZeaburAIClient (新模組)                                  │
│                     backend/services/ai/zeabur_client.py                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↑
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                     前端 AI 面板                                             │
│                     - 廣告診斷                                               │
│                     - 週報生成                                               │
│                     - 搜尋意圖分類 (未來)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 支援模型清單

| Provider | 模型 ID | 說明 | 推薦場景 |
|----------|---------|------|----------|
| **Gemini** | `gemini-2.5-flash` | 快速、免費額度高 | ✅ 日常分析 (推薦) |
| **Gemini** | `gemini-2.5-pro` | 高品質、長文本 | 深度報告 |
| **Gemini** | `gemini-3-flash-preview` | 最新預覽版 | 測試新功能 |
| **Claude** | `claude-sonnet-4-5` | Anthropic 高品質 | 複雜推理 |
| **Claude** | `claude-haiku-4-5` | 快速、經濟 | 批量處理 |
| **GPT** | `gpt-4o` | OpenAI 多模態 | 圖文分析 |
| **GPT** | `gpt-4o-mini` | 經濟實惠 | 一般任務 |
| **GPT** | `gpt-5` | 最新旗艦 | 最高品質 |
| **DeepSeek** | `deepseek-v3.2` | 開源高品質 | 程式碼生成 |
| **Qwen** | `qwen-3-32` | 通義千問 | 中文優化 |
| **Llama** | `llama-3.3-70b` | Meta 開源 | 通用任務 |

#### 核心程式碼 (參考 automatic-affiliates-king)

```python
# backend/services/ai/zeabur_client.py

from openai import OpenAI
from typing import Optional, Dict, Iterator
import os


class ZeaburAIClient:
    """Zeabur AI Hub 客戶端 - 透過 OpenAI 相容 API 統一調用多種 AI 模型"""
    
    MODELS = {
        "gemini-2.5-flash": {"provider": "gemini", "max_tokens": 8192, "description": "快速、免費額度高 ✅ 推薦"},
        "gemini-2.5-pro": {"provider": "gemini", "max_tokens": 32000, "description": "高品質、長文本"},
        "claude-sonnet-4-5": {"provider": "anthropic", "max_tokens": 8192, "description": "Anthropic 高品質"},
        "claude-haiku-4-5": {"provider": "anthropic", "max_tokens": 8192, "description": "快速、經濟"},
        "gpt-4o": {"provider": "openai", "max_tokens": 16000, "description": "多模態"},
        "gpt-4o-mini": {"provider": "openai", "max_tokens": 16000, "description": "經濟實惠"},
        "deepseek-v3.2": {"provider": "deepseek", "max_tokens": 8192, "description": "開源高品質"},
    }
    
    ENDPOINTS = {
        "tokyo": "https://hnd1.aihub.zeabur.ai/v1",
        "sanfrancisco": "https://sfo1.aihub.zeabur.ai/v1"
    }
    
    def __init__(self, api_key: Optional[str] = None, endpoint: str = "tokyo"):
        self.api_key = api_key or os.getenv("ZEABUR_AI_HUB_API_KEY")
        if not self.api_key:
            raise RuntimeError("ZEABUR_AI_HUB_API_KEY is required.")
        
        self.base_url = self.ENDPOINTS.get(endpoint, endpoint)
        
        # 使用 OpenAI SDK 連接 Zeabur AI Hub
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def generate_content(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        system_prompt: Optional[str] = None
    ) -> str | Iterator[str]:
        """生成 AI 內容，支援串流輸出"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        model_config = self.MODELS.get(model, {"max_tokens": 8192})
        max_output = max_tokens or model_config["max_tokens"]
        
        if stream:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output,
                stream=True
            )
            
            def stream_generator():
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            return stream_generator()
        else:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_output
            )
            return response.choices[0].message.content
    
    def get_available_models(self) -> Dict[str, Dict]:
        """獲取可用模型列表"""
        return self.MODELS.copy()
```

#### 檔案變更清單

| 操作 | 檔案路徑 | 說明 |
|------|----------|------|
| 🆕 新增 | `backend/services/ai/__init__.py` | AI 模組初始化 |
| 🆕 新增 | `backend/services/ai/zeabur_client.py` | Zeabur AI Hub 客戶端 |
| ✏️ 修改 | `backend/ai_service.py` | 改為呼叫 ZeaburAIClient |
| ✏️ 修改 | `backend/routers/ai.py` | 新增模型選擇參數 |
| ✏️ 修改 | `frontend/.../AIAnalyst.jsx` | 新增模型選擇下拉選單 |
| 📦 新增 | `requirements.txt` | 添加 `openai` 套件 |

#### 環境變數

```bash
# .env (Zeabur AI Hub)
ZEABUR_AI_HUB_API_KEY=sk-xxxxxxxxxxxxxxxx
ZEABUR_AI_HUB_ENDPOINT=https://hnd1.aihub.zeabur.ai  # 東京 (預設)
# 或 https://sfo1.aihub.zeabur.ai (舊金山)
```

#### 前端設定 UI (整合中心)

模型選擇整合到現有的「整合中心 (Integration Center)」設定頁面：

```
┌──────────────────────────────────────────────────────────────────┐
│ 整合中心 (Integration Center)                              ✕    │
├──────────────────────────────────────────────────────────────────┤
│ [Facebook Ads]  [AI Intelligence]                                │
│                                                                   │
│ 🟢 已連線 (用戶自訂 Key)                                          │
│ 請輸入您的 API Key                                                │
│                                                                   │
│ Provider                                                          │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ▼ Zeabur AI Hub (多模型支援) ✅ 推薦                         │ │
│ │   ─────────────────────────────────────                      │ │
│ │   Google Gemini (原有)                                       │ │
│ │   Zeabur AI Hub (多模型支援) ✅ 推薦                         │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ AI 模型 (Zeabur AI Hub 專用)                                     │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ▼ gemini-2.5-flash (快速、免費額度高) ✅ 推薦               │ │
│ │   ─────────────────────────────────────                      │ │
│ │   gemini-2.5-pro (高品質、長文本)                           │ │
│ │   claude-sonnet-4-5 (Anthropic 高品質)                      │ │
│ │   gpt-4o (OpenAI 多模態)                                    │ │
│ │   deepseek-v3.2 (開源高品質)                                │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ API Key                                                           │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ sk-•••••••••••••••••••••••                                   │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│                                       [清除]    [測試連線]        │
└──────────────────────────────────────────────────────────────────┘
```

**設定儲存策略**：
- `ai_provider`: 儲存於 `users` 表 (`google_gemini` | `zeabur`)
- `ai_model`: 儲存於 `users` 表 (`gemini-2.5-flash` | `claude-sonnet-4-5` | ...)
- 當 provider 為 `google_gemini` 時，model 選擇器隱藏

**其他 UI 顯示**：
- AI 分析面板標題顯示：「🤖 AI 廣告診斷 (gemini-2.5-flash)」
- 週報生成同理


#### 實作優先級

| 優先級 | 項目 | 說明 | 工作量 |
|--------|------|------|--------|
| 🔴 P1 | 建立 `zeabur_client.py` | 核心 AI 客戶端 | 1 小時 |
| 🔴 P1 | 整合到 `ai_service.py` | 替換現有實現 | 30 分鐘 |
| 🔴 P1 | 更新 `routers/ai.py` | 添加模型選擇 API | 30 分鐘 |
| 🟡 P2 | 前端模型選擇器 | 下拉選單 UI | 1 小時 |
| 🟡 P2 | 模型偏好儲存 | 記住用戶選擇 | 30 分鐘 |
| 🟢 P3 | 搜尋意圖分類整合 | 應用到 GSC 功能 | 2 小時 |

#### 向下相容性

| 現有功能 | 影響 | 處理方式 |
|----------|------|----------|
| 廣告診斷 | ✅ 無影響 | 預設使用 gemini-2.5-flash |
| 週報生成 | ✅ 無影響 | 預設使用 gemini-2.5-flash |
| 連線測試 | ✅ 無影響 | 自動偵測可用模型 |

> **回滾計劃**: 若新模組有問題，保留 `ai_service.py` 原始版本，透過環境變數切換：
> `USE_LEGACY_AI_SERVICE=true`

---


## ✅ Completed Features (已完成功能)

### 1. 核心架構與安全性 (Core Architecture)
*   **✅ Google OAuth 登入**: 採用 JWT 的安全驗證流程。
*   **✅ 角色權限控制 (RBAC)**: 支援 超級管理員、團隊擁有者、管理員、一般成員 等角色。
*   **✅ 資料庫整合**: 從 SQLite/JSON 遷移至 PostgreSQL (Zeabur Ready)。
*   **✅ 安全性強化**: FB Access Tokens 儲存採用 Fernet 加密。
*   **✅ Token 隔離**: 嚴格區分「個人工作區」與「團隊工作區」的數據權限。
*   **✅ Strict Token Mode**: 強制個人工作區使用個人 Token，防止 Fallback 導致資料洩漏。
*   **✅ 團隊 Token 管理**: 支援儲存與顯示 Token 到期時間，並提供即將過期通知。

### 2. 儀表板與數據分析 (Dashboard & Analytics)
*   **✅ 多層級分析**: 支援 Campaign / Ad Set / Ad 層級切換與動態日期範圍。
*   **✅ 比較模式 (Comparison)**: 支援「年增率 (YoY)」與「上期比較」邏輯。
*   **✅ 進階指標**:
    *   **漏斗 (Funnel)**: 轉換率 (CVR)、流失率 (Drop-off)、購物車價值實現率。
    *   **電商 (E-commerce)**: ROAS, CPA, 客單價 (ATV)。
    *   **互動 (Engagement)**: 貼文分享、留言、收藏數。
*   **✅ 視覺化圖表**: 支援雙軸趨勢圖 (Dual-Axis)，例如 Spend vs ROAS。
*   **✅ UI 優化**: 凍結表頭 (Sticky Headers)、緊湊型表格、穩健的錯誤處理。
*   **✅ 快篩功能 (Active Only Filter)**: 一鍵篩選正在投放的廣告，排除已暫停/結束的項目。

#### 快篩功能說明 (Active Only Filter)

**位置**: Analytics 頁面 → 過濾工具列 → ⚡ 只看快篩 (Active)

**功能作用**: 當開啟此開關時，系統只會顯示狀態為 `ACTIVE`（進行中）的廣告活動、廣告群組或廣告。

| 開啟 | 關閉 |
|:----:|:----:|
| 只顯示正在投放的廣告 | 顯示所有廣告（包含已暫停、已完成的） |

**使用場景**:
- 快速排除已暫停或結束的廣告，專注分析當前投放中的成效
- 讓 KPI 計算更準確（只加總正在投放的項目）
- 表格更簡潔，只看活躍項目

### 3. 團隊協作 (SaaS Features)
*   **✅ 團隊工作區**: 建立、管理與切換多個團隊。
*   **✅ 邀請系統**: 產生 24小時有效期的邀請連結。
*   **✅ 廣告帳號白名單**: 精細控制團隊成員可見的廣告帳號列表 (含 Robust Filtering 修復)。
*   **✅ 視角共享**: 支援資料庫層級的「個人視角」與「團隊視角」儲存策略。
*   **✅ 超級管理員後台**: 全域的使用者與團隊管理介面。

#### 團隊角色權限設計 (Team RBAC)

| 角色 | 說明 | 取得方式 |
|------|------|----------|
| **Owner** | 團隊創建者，最高權限 | 建立團隊時自動成為 `team.owner_id` |
| **Admin** | 可管理團隊設定與成員 | 創建者預設為 Admin，手動指派 |
| **Member** | 可查看數據，無管理權限 | 透過邀請連結加入時的預設角色 |
| **Viewer** | 僅能查看數據 | 手動指派 |

| 功能 | Owner | Admin | Member | Viewer |
|------|:-----:|:-----:|:------:|:------:|
| 查看數據 | ✅ | ✅ | ✅ | ✅ |
| 產生邀請連結 | ✅ | ✅ | ❌ | ❌ |
| 修改團隊 API 設定 | ✅ | ✅ | ❌ | ❌ |
| 設定廣告帳號白名單 | ✅ | ✅ | ❌ | ❌ |
| 更改成員角色 | ✅ | ✅ | ❌ | ❌ |
| 踢除成員 | ✅ | ✅ | ❌ | ❌ |
| 解散團隊 | ✅ | ❌ | ❌ | ❌ |

> **已知設計問題**: Member 和 Viewer 目前功能相同（都只能查看數據），未來可考慮區分：
> - **Member**: 可儲存視角、設定個人偏好
> - **Viewer**: 純粹只讀

### 4. 使用者體驗與手機版 (UX & Mobile)
*   **✅ 響應式設計**: 手機版完全優化 (智慧側邊欄、卡片式列表)。
*   **✅ 語系支援**: 繁體中文 / English 切換。
*   **✅ 智慧導覽**: 側邊欄自動收合、快速情境切換。

### 5. Google Search Console 整合 (GSC Integration) 🆕

#### 已完成功能 (v1.5.6 ~ v1.5.8)

| 功能 | 說明 | 版本 |
|------|------|------|
| **GSC OAuth 授權** | 連接使用者的 Search Console 帳號 | v1.5.5 |
| **站點列表** | 顯示使用者擁有的所有網站 | v1.5.5 |
| **每日成效 Tab** | 按日期分群的點擊/曝光數據 | v1.5.6 |
| **關鍵字分析 Tab** | 熱門關鍵字排行 + 搜尋篩選 + 排序 | v1.5.6 |
| **關鍵字群組** | 相似關鍵字自動分群 (Jaccard Index 相似度) | v1.5.6 |
| **頁面分析 Tab** | 頁面效能排行 + 可點擊連結 | v1.5.6 |
| **頁面趨勢 Tab** 📊 | 頂層 / 走勢向上 / 走勢向下（本期 vs 前期比較） | v1.5.7 |
| **真實頁面標題** | 後端抓取 `<title>` 標籤顯示（上限 50 篇） | v1.5.7 |
| **Top/Bottom 標示** | Top 5 🏆 綠色 / Bottom 5 ⚠️ 紅色 | v1.5.7 |
| **頁面核心關鍵字** | 每頁顯示 Top 5 關聯關鍵字 + 點擊/曝光 | v1.5.7 |
| **日期範圍選擇器** | 預設選項 + 自訂日期範圍 | v1.5.6 |
| **URL 解碼** | 中文 URL 路徑正確顯示 | v1.5.7 |
| **🌍 地區分佈 Tab** ✨ | `country` 維度 - 各國家流量排行 + 80+國家中文翻譯 | v1.5.8 |
| **📱 裝置分佈 Tab** ✨ | `device` 維度 - 卡片式視覺化（手機/桌機/平板） | v1.5.8 |

#### 待優化項目 (Optimization Backlog)

| 優先級 | 功能 | 說明 |
|:------:|------|------|
| 🟡 中 | **頁面標題資料庫快取** | 抓過的標題存入 DB，避免重複爬取 |
| 🟡 中 | **頁面標題分批載入** | 滾動時 Lazy Loading 更多標題 |
| 🟢 低 | **智慧語言分群** | 見下方詳細說明 |
| 🟢 低 | **可調整分群閾值** | 讓用戶控制關鍵字分群的敏感度 |
| 🟢 低 | **資料匯出 CSV/Excel** | 表格資料匯出功能 |
| 🟢 低 | **GSC Token 團隊共享** | 將 GSC Token 綁定至團隊層級 |

##### 智慧語言分群 (Hybrid Language Grouping)

**問題**：目前使用「詞分割」(word split) 對英文有效，但中文無空格會失敗。

| 語系 | 詞分割 (目前) | N-gram | 最佳方案 |
|------|:------------:|:------:|:--------:|
| 英文 | ✅ 好 | ❌ 差 | 詞分割 |
| 中文 | ❌ 差 | ✅ 好 | N-gram |
| 混合 | 🟡 普通 | 🟡 普通 | 混合策略 |

**建議實作**：語言自動偵測 + 混合策略
```javascript
const getSimilarity = (str1, str2) => {
  const hasChinese = (s) => /[\u4e00-\u9fa5]/.test(s);
  
  if (hasChinese(str1) || hasChinese(str2)) {
    return ngramSimilarity(str1, str2); // 中文用 N-gram
  } else {
    return wordSimilarity(str1, str2);  // 英文用詞分割
  }
};
```

---

### 🔮 搜尋意圖分類 (Search Intent Classification) - ✅ 後端已實作

**目標**：自動分析 GSC 頁面/關鍵字的搜尋意圖，幫助用戶了解內容與搜尋需求的匹配程度。

#### ✅ 已完成項目 (2025-12-31)

| 項目 | 說明 | 檔案 |
|------|------|------|
| **AI 意圖分類器** | 使用 Zeabur AI Hub 分析關鍵字搜尋意圖 | `backend/services/ai/intent_classifier.py` |
| **批量分類 API** | 支援一次分析多個關鍵字 | `AIIntentClassifier.classify_queries()` |
| **頁面意圖計算** | 根據關鍵字點擊數加權計算頁面主要意圖 | `AIIntentClassifier.classify_page_queries()` |

> **技術選擇**：最終採用 AI 模型 (Zeabur AI Hub) 而非規則式分類，以獲得更高準確度 (95%+) 與更好的中英文支援。

#### 概念說明

| 意圖類型 | 英文 | 說明 | 典型關鍵字 |
|----------|------|------|------------|
| 🔵 資訊型 | Informational | 用戶想了解某事 | 如何、是什麼、教學、how, what, guide |
| 🟠 商業型 | Commercial | 用戶在評估選項 | 推薦、評價、比較、best, review, vs |
| 🟢 導航型 | Navigational | 用戶想到達特定網站 | 品牌名、網站名 |
| 🔴 交易型 | Transactional | 用戶準備購買/行動 | 購買、價格、下載、buy, price, discount |

#### 功能規劃

**第一階段：頁面意圖分類**

| 位置 | 顯示內容 | 說明 |
|------|----------|------|
| 頁面列表 | 意圖標籤 (pill) | 顯示該頁面的**主要意圖類型** (如 `🔵 資訊型`) |
| 頁面詳情 | 雷達圖 | 顯示 4 種意圖的**分布比例** (如 資訊 42% / 商業 37% / 導航 11% / 交易 11%) |

**第二階段：關鍵字意圖分類** (未來)

| 功能 | 說明 |
|------|------|
| 關鍵字標籤 | 每個關鍵字旁顯示意圖標籤 |
| 意圖篩選 | 只看特定意圖類型的關鍵字 |

---

#### 後端 API 設計

##### 新增端點

```python
# routers/gsc.py

@router.get("/api/gsc/{site_url}/pages/intents")
async def get_page_intents(
    site_url: str,
    since: str,
    until: str,
    user: User = Depends(get_current_user)
):
    """
    取得頁面的搜尋意圖分類
    
    Returns:
    {
        "pages": [
            {
                "page": "/blog/facebook-ads-tutorial",
                "title": "Facebook 廣告教學 - 新手指南",
                "primary_intent": "informational",
                "intent_distribution": {
                    "informational": 0.65,
                    "commercial": 0.25,
                    "navigational": 0.05,
                    "transactional": 0.05
                },
                "top_queries": [
                    {"query": "facebook 廣告教學", "intent": "informational", "clicks": 120},
                    {"query": "fb 廣告設定", "intent": "informational", "clicks": 85}
                ]
            }
        ]
    }
    """
```

##### 意圖分類服務

```python
# service_modules/intent_classifier.py

class IntentClassifier:
    """搜尋意圖分類器 (規則式)"""
    
    # 中英文規則庫
    INTENT_RULES = {
        "informational": {
            "zh": ["如何", "是什麼", "為什麼", "教學", "方法", "步驟", "技巧", "入門", "指南", "完整"],
            "en": ["how", "what", "why", "guide", "tutorial", "tips", "learn", "example", "definition"]
        },
        "commercial": {
            "zh": ["推薦", "評價", "比較", "最佳", "排名", "優缺點", "選擇", "vs", "差異", "評測"],
            "en": ["best", "review", "vs", "compare", "top", "alternative", "recommendation", "pros", "cons"]
        },
        "navigational": {
            "zh": ["官網", "登入", "網站"],  # + 動態品牌名稱
            "en": ["login", "sign in", "official", "website"]  # + 動態品牌名稱
        },
        "transactional": {
            "zh": ["購買", "價格", "費用", "下載", "報名", "訂閱", "折扣", "優惠", "免費", "試用"],
            "en": ["buy", "price", "discount", "download", "order", "subscribe", "free", "trial", "coupon"]
        }
    }
    
    @classmethod
    def classify_query(cls, query: str) -> dict:
        """
        分類單一查詢
        
        Returns:
            {
                "intent": "informational",  # primary intent
                "scores": {
                    "informational": 0.7,
                    "commercial": 0.2,
                    "navigational": 0.05,
                    "transactional": 0.05
                }
            }
        """
        query_lower = query.lower()
        scores = {intent: 0.0 for intent in cls.INTENT_RULES}
        
        for intent, rules in cls.INTENT_RULES.items():
            for keyword in rules["zh"] + rules["en"]:
                if keyword in query_lower:
                    scores[intent] += 1
        
        # Normalize scores
        total = sum(scores.values()) or 1
        scores = {k: v / total for k, v in scores.items()}
        
        # Determine primary intent
        primary = max(scores, key=scores.get)
        
        # Default to informational if no match
        if all(v == 0.25 for v in scores.values()):
            primary = "informational"
            scores["informational"] = 0.5
            scores["commercial"] = 0.2
            scores["navigational"] = 0.15
            scores["transactional"] = 0.15
        
        return {"intent": primary, "scores": scores}
    
    @classmethod
    def classify_page(cls, queries: list[dict]) -> dict:
        """
        根據頁面的所有關鍵字分類頁面意圖
        
        Args:
            queries: [{"query": "...", "clicks": 50}, ...]
        
        Returns:
            {
                "primary_intent": "informational",
                "intent_distribution": {...}
            }
        """
        total_clicks = sum(q.get("clicks", 1) for q in queries)
        weighted_scores = {
            "informational": 0,
            "commercial": 0,
            "navigational": 0,
            "transactional": 0
        }
        
        for q in queries:
            result = cls.classify_query(q["query"])
            weight = q.get("clicks", 1) / total_clicks
            for intent, score in result["scores"].items():
                weighted_scores[intent] += score * weight
        
        primary = max(weighted_scores, key=weighted_scores.get)
        
        return {
            "primary_intent": primary,
            "intent_distribution": weighted_scores
        }
```

---

#### 前端 UI 設計

##### 1. 頁面列表 - 意圖標籤

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📄 頁面分析                                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 頁面                                    │ 意圖  │ 點擊 │ 曝光  │ CTR   │ 排名 │
├─────────────────────────────────────────┼───────┼──────┼───────┼───────┼──────┤
│ Facebook 廣告教學 - 新手指南            │🔵 資訊│ 1,234│ 45,678│ 2.70% │ 3.2  │
│ 2024 最佳 Facebook 廣告工具推薦         │🟠 商業│ 856  │ 32,100│ 2.67% │ 4.5  │
│ Facebook 廣告費用一次看懂               │🔴 交易│ 543  │ 21,456│ 2.53% │ 5.1  │
│ DataVue 官方網站                        │🟢 導航│ 321  │ 8,765 │ 3.66% │ 1.2  │
└─────────────────────────────────────────┴───────┴──────┴───────┴───────┴──────┘
```

**標籤樣式 (CSS)**:

```css
.intent-pill {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

.intent-informational { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.intent-commercial    { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.intent-navigational  { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.intent-transactional { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
```

##### 2. 頁面詳情 - 雷達圖

當用戶**點擊某頁面**時，展開/彈出詳情面板，顯示：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 📄 Facebook 廣告教學 - 新手指南                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────┐     ┌─────────────────────────────────────────┐   │
│   │                     │     │ 📊 搜尋意圖分布                          │   │
│   │   [雷達圖區域]       │     │                                         │   │
│   │     資訊型 65%      │     │ 🔵 資訊型   ████████████████░░░░ 65%    │   │
│   │     商業型 25%      │     │ 🟠 商業型   ██████████░░░░░░░░░░ 25%    │   │
│   │     導航型 5%       │     │ 🟢 導航型   ██░░░░░░░░░░░░░░░░░░  5%    │   │
│   │     交易型 5%       │     │ 🔴 交易型   ██░░░░░░░░░░░░░░░░░░  5%    │   │
│   │                     │     │                                         │   │
│   └─────────────────────┘     └─────────────────────────────────────────┘   │
│                                                                              │
│   🔑 主要關鍵字                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ 關鍵字                        │ 意圖  │ 點擊 │ 曝光  │ 排名         │   │
│   │ facebook 廣告教學             │🔵 資訊│ 450  │ 12,345│ 2.1          │   │
│   │ fb 廣告 設定                  │🔵 資訊│ 320  │ 8,765 │ 3.4          │   │
│   │ facebook 廣告 費用            │🔴 交易│ 180  │ 5,432 │ 4.2          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**雷達圖實作 (Recharts)**:

```jsx
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

const IntentRadarChart = ({ distribution }) => {
    const data = [
        { intent: '資訊型', value: distribution.informational * 100 },
        { intent: '商業型', value: distribution.commercial * 100 },
        { intent: '導航型', value: distribution.navigational * 100 },
        { intent: '交易型', value: distribution.transactional * 100 },
    ];

    return (
        <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={data}>
                <PolarGrid />
                <PolarAngleAxis dataKey="intent" />
                <PolarRadiusAxis angle={30} domain={[0, 100]} />
                <Radar
                    name="Intent"
                    dataKey="value"
                    stroke="#8884d8"
                    fill="#8884d8"
                    fillOpacity={0.6}
                />
            </RadarChart>
        </ResponsiveContainer>
    );
};
```

---

#### 規則庫結構 (Constants)

```javascript
// frontend/src/constants/intentRules.js

export const INTENT_TYPES = {
    informational: {
        key: 'informational',
        label_zh: '資訊型',
        label_en: 'Informational',
        icon: '🔵',
        color: '#3b82f6',
        description_zh: '用戶想了解某事',
        description_en: 'User wants to learn something'
    },
    commercial: {
        key: 'commercial',
        label_zh: '商業型',
        label_en: 'Commercial',
        icon: '🟠',
        color: '#f59e0b',
        description_zh: '用戶在評估選項',
        description_en: 'User is evaluating options'
    },
    navigational: {
        key: 'navigational',
        label_zh: '導航型',
        label_en: 'Navigational',
        icon: '🟢',
        color: '#10b981',
        description_zh: '用戶想到達特定網站',
        description_en: 'User wants to reach a specific site'
    },
    transactional: {
        key: 'transactional',
        label_zh: '交易型',
        label_en: 'Transactional',
        icon: '🔴',
        color: '#ef4444',
        description_zh: '用戶準備購買或行動',
        description_en: 'User is ready to buy or take action'
    }
};

export const INTENT_KEYWORDS = {
    informational: {
        zh: ['如何', '是什麼', '為什麼', '教學', '方法', '步驟', '技巧', '入門', '指南', '完整', '介紹', '分析', '說明'],
        en: ['how', 'what', 'why', 'guide', 'tutorial', 'tips', 'learn', 'example', 'definition', 'explain', 'ways', 'steps']
    },
    commercial: {
        zh: ['推薦', '評價', '比較', '最佳', '排名', '優缺點', '選擇', 'vs', '差異', '評測', '分析', '哪個好'],
        en: ['best', 'review', 'vs', 'compare', 'top', 'alternative', 'recommendation', 'pros', 'cons', 'comparison', 'difference']
    },
    navigational: {
        zh: ['官網', '登入', '網站', '首頁'],
        en: ['login', 'sign in', 'official', 'website', 'home', 'portal']
    },
    transactional: {
        zh: ['購買', '價格', '費用', '下載', '報名', '訂閱', '折扣', '優惠', '免費', '試用', '申請', '註冊', '預約'],
        en: ['buy', 'price', 'discount', 'download', 'order', 'subscribe', 'free', 'trial', 'coupon', 'deal', 'cheap', 'cost']
    }
};
```

---

#### 實作優先級

| 優先級 | 項目 | 說明 | 狀態 |
|--------|------|------|------|
| ✅ 完成 | `AIIntentClassifier` | 後端 AI 分類服務 | `services/ai/intent_classifier.py` |
| 🔴 P1 | GSC API 整合 | `/api/gsc/{site}/pages/intents` 端點 | 待開發 |
| 🔴 P1 | 頁面列表標籤 UI | 表格新增「意圖」欄位 + pill 標籤 | 待開發 |
| 🟡 P2 | 頁面詳情雷達圖 | 點擊展開詳情 + Recharts 雷達圖 | 待開發 |
| 🟡 P2 | 意圖篩選功能 | 只看特定意圖類型的頁面 | 待開發 |
| 🟢 P3 | 品牌名稱自訂 | 讓用戶設定自家品牌名稱供導航型判斷 | 待開發 |

---

#### 規則儲存策略

##### 演進路徑

```
Phase 1 (MVP)              Phase 2 (進階)              Phase 3 (完整)
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ 純程式碼常數     │  →→→  │ 資料庫儲存       │  →→→  │ 視覺化管理介面   │
│ intentRules.js  │       │ intent_rules 表 │       │ 規則編輯 UI     │
└─────────────────┘       └─────────────────┘       └─────────────────┘
   ✅ 快速上線               ✅ 可跨裝置同步            ✅ 用戶自主管理
   ❌ 修改需部署             ✅ 用戶可自訂              ✅ 無需工程師
```

##### Phase 1: 程式碼常數 (目前規劃)

```
┌──────────────────────────────────────────────────────────────┐
│  frontend/src/constants/intentRules.js  ← 前端常數           │
│  backend/service_modules/intent_classifier.py ← 後端服務     │
└──────────────────────────────────────────────────────────────┘
```

| 優點 | 缺點 |
|------|------|
| ✅ 實作簡單、快速上線 | ❌ 修改規則需改程式碼 |
| ✅ 無需額外資料庫表 | ❌ 需重新部署才能生效 |
| ✅ 效能最佳 (無 DB 查詢) | ❌ 用戶無法自訂 |

##### Phase 2: 資料庫儲存 (未來)

```sql
-- Table: intent_rules
CREATE TABLE intent_rules (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),      -- NULL = 系統規則
    team_id INTEGER REFERENCES teams(id),      -- NULL = 個人規則
    intent_type VARCHAR(20) NOT NULL,          -- informational/commercial/...
    keyword VARCHAR(100) NOT NULL,
    language VARCHAR(10) DEFAULT 'zh',         -- zh/en/mixed
    weight FLOAT DEFAULT 1.0,                  -- 權重 (可調整優先級)
    source VARCHAR(20) DEFAULT 'custom',       -- base/template/custom
    created_at TIMESTAMP DEFAULT NOW()
);
```

| 規則來源 | user_id | team_id | 說明 |
|----------|---------|---------|------|
| 系統基礎 | NULL | NULL | 所有用戶共用 |
| 個人自訂 | 5 | NULL | 只有該用戶可見 |
| 團隊自訂 | NULL | 10 | 團隊成員共用 |

---

#### 行業規則模板 (Industry Templates)

##### 問題：不同類型網站的適用性

| 網站類型 | 通用規則適用度 | 特殊需求 |
|----------|:-------------:|----------|
| **部落格/媒體** | ✅ 高 | 主要是資訊型內容 |
| **電商網站** | ✅ 高 | 需加入購物流程關鍵字 |
| **SaaS/軟體** | 🟡 中 | 需加入試用、API 相關詞 |
| **品牌官網** | 🟡 中 | 需加入自家品牌名稱 |
| **在地服務** | 🟡 中 | 需加入地點相關關鍵字 |
| **教育培訓** | 🟡 中 | 需加入課程、認證關鍵字 |

##### 解決方案：三層規則架構

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: 通用規則 (Base Rules)                                  │
│  └ 所有網站都適用的基礎關鍵字 (如何、購買、推薦、官網...)         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: 行業模板 (Industry Templates) - 可選啟用               │
│  ├ 🛒 電商模板 → 加入購物車、結帳、運費、退貨、ATM...             │
│  ├ 💻 SaaS 模板 → API、整合、定價方案、企業版、試用...            │
│  ├ 📚 教育模板 → 課程、學習、認證、報名、講師...                  │
│  └ 🏪 在地商家模板 → 地址、營業時間、預約、附近...                │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: 用戶自訂 (Custom Rules) - 最高優先級                   │
│  └ 用戶自行新增的品牌名稱、產品名、專有名詞                       │
└─────────────────────────────────────────────────────────────────┘
```

##### 行業模板範例

```javascript
// constants/industryTemplates.js

export const INDUSTRY_TEMPLATES = {
    ecommerce: {
        id: 'ecommerce',
        name_zh: '電商網站',
        name_en: 'E-commerce',
        icon: '🛒',
        rules: {
            transactional: {
                zh: ['加入購物車', '結帳', '運費', '退貨', 'ATM', '貨到付款', '免運', '特價'],
                en: ['add to cart', 'checkout', 'shipping', 'refund', 'free delivery', 'on sale']
            },
            commercial: {
                zh: ['開箱', '評測', '使用心得', '值得買嗎'],
                en: ['unboxing', 'worth buying', 'honest review']
            }
        }
    },
    saas: {
        id: 'saas',
        name_zh: 'SaaS 軟體',
        name_en: 'SaaS Software',
        icon: '💻',
        rules: {
            commercial: {
                zh: ['定價', '方案', '企業版', 'API', '整合', '替代方案'],
                en: ['pricing', 'plan', 'enterprise', 'integration', 'alternative', 'features']
            },
            transactional: {
                zh: ['免費試用', '申請 Demo', '聯繫業務'],
                en: ['free trial', 'request demo', 'contact sales', 'start free']
            }
        }
    },
    education: {
        id: 'education',
        name_zh: '教育培訓',
        name_en: 'Education',
        icon: '📚',
        rules: {
            transactional: {
                zh: ['報名', '課程費用', '上課時間', '講師', '證照', '補習'],
                en: ['enroll', 'course fee', 'schedule', 'certification', 'instructor']
            },
            informational: {
                zh: ['筆記', '考古題', '心得', '準備方法'],
                en: ['notes', 'exam prep', 'study guide', 'learning path']
            }
        }
    },
    local_business: {
        id: 'local_business',
        name_zh: '在地商家',
        name_en: 'Local Business',
        icon: '🏪',
        rules: {
            transactional: {
                zh: ['預約', '訂位', '營業時間', '地址', '電話', '停車'],
                en: ['book', 'reservation', 'hours', 'location', 'directions', 'parking']
            },
            navigational: {
                zh: ['附近', '最近', '台北', '高雄'],  // 可動態加入城市名
                en: ['near me', 'nearby', 'closest']
            }
        }
    }
};
```

##### 模板選擇 UI 設計

```
┌──────────────────────────────────────────────────────────────────┐
│ ⚙️ 搜尋意圖設定                                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  選擇網站類型 (會自動套用對應的關鍵字規則)：                        │
│                                                                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │ 🌐 通用    │  │ 🛒 電商    │  │ 💻 SaaS   │  │ 📚 教育    │   │
│  │   (預設)   │  │            │  │            │  │            │   │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘   │
│  ┌────────────┐  ┌────────────┐                                   │
│  │ 🏪 在地商家│  │ ✏️ 自訂   │                                   │
│  │            │  │            │                                   │
│  └────────────┘  └────────────┘                                   │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

#### 用戶自訂規則功能

##### 核心需求：品牌名稱設定

**問題**：導航型意圖需要知道「品牌名稱」，這因網站而異。

| 情境 | 處理方式 |
|------|----------|
| 搜尋「DataVue 登入」 | 如果 DataVue 是用戶的品牌 → 導航型 |
| 搜尋「Google Analytics 替代」 | 如果 GA 是競品 → 商業型 (比較) |
| 搜尋「facebook 廣告費用」 | 通用詞 → 交易型 |

##### 設定介面設計

```
┌──────────────────────────────────────────────────────────────────┐
│ 🏷️ 品牌與自訂關鍵字                                               │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  您的品牌名稱 (搜尋這些詞會被歸類為「導航型」)：                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ DataVue, 數據視野, datavue.com                     [+ 新增] │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  自訂關鍵字規則：                                                  │
│  ┌──────────────────┬────────────────────┬─────────────────────┐  │
│  │ 關鍵字           │ 意圖類型           │ 操作                │  │
│  ├──────────────────┼────────────────────┼─────────────────────┤  │
│  │ 廣告成效診斷     │ 🟠 商業型          │ [編輯] [刪除]      │  │
│  │ 免費試用         │ 🔴 交易型          │ [編輯] [刪除]      │  │
│  │ API 文件         │ 🔵 資訊型          │ [編輯] [刪除]      │  │
│  └──────────────────┴────────────────────┴─────────────────────┘  │
│                                                       [+ 新增規則] │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

##### 後端資料結構

```python
# models/intent_settings.py

class UserIntentSettings(Base):
    __tablename__ = "user_intent_settings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    
    # 品牌名稱 (JSON array)
    brand_names = Column(JSON, default=[])  # ["DataVue", "數據視野"]
    
    # 選擇的行業模板
    industry_template = Column(String(50), default="general")
    
    # 自訂規則 (JSON array)
    custom_rules = Column(JSON, default=[])
    # [{"keyword": "API文件", "intent": "informational", "language": "zh"}]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

#### 規則管理 UI (Phase 3 - 未來)

##### 功能規劃

| 功能 | 說明 | 權限 |
|------|------|------|
| 查看系統規則 | 瀏覽所有基礎規則 (唯讀) | 所有用戶 |
| 選擇行業模板 | 選擇適合的行業模板 | 所有用戶 |
| 新增自訂規則 | 新增個人/團隊規則 | 所有用戶 |
| 編輯自訂規則 | 修改自己建的規則 | 創建者 |
| 匯入/匯出規則 | CSV/JSON 格式匯入匯出 | 進階用戶 |
| 規則測試器 | 輸入關鍵字即時測試分類結果 | 所有用戶 |

##### 規則測試器 UI

```
┌──────────────────────────────────────────────────────────────────┐
│ 🧪 規則測試器                                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  輸入關鍵字測試分類結果：                                           │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ facebook 廣告 教學                                  [測試]  │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  分類結果：                                                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  主要意圖：🔵 資訊型 (Informational)                        │   │
│  │                                                              │   │
│  │  匹配規則：                                                  │   │
│  │  ├ ✅ "教學" → 資訊型 (來源: 系統基礎規則)                  │   │
│  │  └ ✅ "廣告" → 無特定意圖                                   │   │
│  │                                                              │   │
│  │  信心分數：                                                  │   │
│  │  資訊型 72% ████████████████░░░░░░                          │   │
│  │  商業型 18% █████░░░░░░░░░░░░░░░░░                          │   │
│  │  導航型  5% ██░░░░░░░░░░░░░░░░░░░░                          │   │
│  │  交易型  5% ██░░░░░░░░░░░░░░░░░░░░                          │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

---

#### AI 分類快取架構 (Site-Based Caching) 🆕

##### 設計原則：以網站為中心，跨用戶共享

**問題**：每次呼叫 AI 分類關鍵字都有成本，同一網站的多個用戶不應重複付費。

**解決方案**：以 GSC 網站 (site_url) 為主鍵，所有有權限的用戶共享同一份快取。

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         關鍵字意圖快取                                   │
│                    (以網站為單位，跨用戶共享)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   example.com                       another-site.com                     │
│   ┌─────────────────────┐          ┌─────────────────────┐               │
│   │ facebook 廣告 教學   │          │ 瑜珈課程 推薦       │               │
│   │   → 🔵 資訊型       │          │   → 🟠 商業型       │               │
│   │                     │          │                     │               │
│   │ 廣告投放 費用        │          │ 瑜珈教室 預約       │               │
│   │   → 🔴 交易型       │          │   → 🔴 交易型       │               │
│   └─────────────────────┘          └─────────────────────┘               │
│         ↑                                  ↑                             │
│   ┌─────┴─────┐                      ┌─────┴─────┐                       │
│   │ 用戶 A    │                      │ 用戶 C    │                       │
│   │ 用戶 B    │ ← 共享快取           │ 用戶 D    │ ← 共享快取            │
│   └───────────┘                      └───────────┘                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

##### 資料庫設計

**表 1：關鍵字意圖快取 (`site_keyword_intents`)**

```sql
CREATE TABLE site_keyword_intents (
    id SERIAL PRIMARY KEY,
    
    -- 以網站為主鍵
    site_url VARCHAR(255) NOT NULL,  -- "sc-domain:example.com" 或 "https://example.com/"
    
    -- 關鍵字
    keyword VARCHAR(500) NOT NULL,
    keyword_hash VARCHAR(64) NOT NULL,  -- MD5 for fast lookup
    
    -- AI 分類結果
    intent VARCHAR(20) NOT NULL,  -- informational/commercial/navigational/transactional
    confidence FLOAT DEFAULT 0.9,
    
    -- 來源追蹤
    source VARCHAR(20) DEFAULT 'ai',  -- 'ai' / 'rule' / 'manual'
    model VARCHAR(50),  -- 'gemini-1.5-flash' / 'gpt-4o-mini'
    
    -- 時間
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    
    -- 聯合唯一鍵：同一網站同一關鍵字只有一筆
    UNIQUE(site_url, keyword_hash)
);

-- 索引：加速查詢
CREATE INDEX idx_site_keyword ON site_keyword_intents(site_url, keyword_hash);
```

**表 2：頁面意圖摘要 (`site_page_intents`)**

```sql
CREATE TABLE site_page_intents (
    id SERIAL PRIMARY KEY,
    
    -- 以網站 + 頁面為主鍵
    site_url VARCHAR(255) NOT NULL,
    page_path VARCHAR(1000) NOT NULL,
    
    -- 意圖分布 (JSON)
    intent_distribution JSONB NOT NULL,
    -- {"informational": 0.65, "commercial": 0.25, "navigational": 0.05, "transactional": 0.05}
    
    primary_intent VARCHAR(20) NOT NULL,
    
    -- 計算依據
    total_queries INT,
    date_range_start DATE,
    date_range_end DATE,
    
    -- 時間
    calculated_at TIMESTAMP DEFAULT NOW(),
    
    -- 聯合唯一鍵
    UNIQUE(site_url, page_path, date_range_start, date_range_end)
);

-- 索引
CREATE INDEX idx_site_page ON site_page_intents(site_url, page_path);
```

##### 跨用戶共享流程

```
用戶 A (有 example.com 權限) 查看頁面分析
                    ↓
        查詢 site_keyword_intents
        WHERE site_url = 'example.com'
                    ↓
        ┌─────有快取─────┴─────沒快取─────┐
        ↓                                  ↓
    返回已存意圖                      呼叫 AI 分類
    (0 費用, < 50ms)                  (有費用, 1-2s)
                                           ↓
                                    存入 DB (site_url = 'example.com')
                    ↓
═══════════════════════════════════════════════════════════════════════════
                    ↓
用戶 B (也有 example.com 權限) 查看同頁面
                    ↓
        查詢 site_keyword_intents
        WHERE site_url = 'example.com'
                    ↓
        已有快取 → 直接返回 (0 費用) ✅
```

##### 效益分析

| 方案 | 用戶 A 查詢 | 用戶 B 查詢 (同網站) | 總 AI 呼叫 | 費用 |
|------|-------------|---------------------|------------|------|
| ❌ 無快取 | AI 分類 | AI 分類 | 2 次 | $$ |
| ❌ 以用戶為主 | AI 分類 | AI 分類 | 2 次 | $$ |
| ✅ **以網站為主** | AI 分類 | **快取命中** | **1 次** | **$** |

##### 成本估算

| 規模 | 第一次 (冷啟動) | 之後 (有快取) |
|------|-----------------|---------------|
| 100 頁 × 50 關鍵字 | ~5,000 AI 呼叫 ≈ $0.50 | $0 |
| 1,000 頁 × 50 關鍵字 | ~50,000 AI 呼叫 ≈ $5.00 | $0 |
| 10,000 頁 × 50 關鍵字 | ~500,000 AI 呼叫 ≈ $50 | $0 |

> 使用 GPT-4o-mini 或 Gemini Flash 等低成本模型可進一步降低費用

##### 快取失效策略

| 情境 | 處理方式 |
|------|----------|
| 關鍵字意圖變化 | 設定 TTL (如 90 天) 自動過期重新分類 |
| 用戶手動修正 | 提供「重新分類」按鈕，刪除快取後重跑 AI |
| 新關鍵字出現 | 只對新關鍵字呼叫 AI，舊的繼續使用快取 |

---

#### 未來擴展

| 功能 | 說明 |
|------|------|
| **意圖趨勢分析** | 追蹤意圖分布隨時間的變化 |
| **內容建議** | 根據意圖缺口建議創作新內容 (例：缺乏交易型內容) |
| **競品意圖分析** | 比較與競品的意圖覆蓋差異 |

---

## 🚀 Future Roadmap (未來規劃)

預計於 v1.6+ 版本推出的功能。

### 1. 進階報表工具

#### 1.1 自訂指標 (Metric Customization) - 「指標超市」
**目標**: 讓用戶自由選擇想要顯示的欄位，打造個人化報表體驗。

**現況**: ✅ 已完成 (v1.5.3)
- ✅ `constants/analyticsConfig.js` 已定義 METRIC_GROUPS
- ✅ Analytics 頁面已有 View 切換 (總覽/電商/漏斗/自訂)
- ✅ MetricSelector 元件已建立 (Memoized)

**核心問題**: 現有 METRIC_GROUPS 僅包含 ~35 個指標，但 Facebook 有 100+ 可用指標。

##### 現有指標 vs 缺少的指標

| 類別 | 現有 | 缺少 |
|------|------|------|
| 通用 | spend, reach, impressions, cpc, ctr | frequency, unique_clicks |
| 電商 | roas, purchases, add_to_cart, cpa | checkout_initiated, payment_info_added |
| 漏斗 | cvr, cart_conversion, cart_dropoff | ✅ 已完整 |
| 互動 | comments, saves, shares, reactions | video_plays, photo_views |
| **影音** | ❌ 無 | video_p25_watched, video_p50_watched, video_p75_watched, video_p100_watched, video_avg_time_watched, thruplay |
| **訊息** | ❌ 無 | messaging_first_reply, messaging_conversation_started_7d |
| **潛在客戶** | ❌ 無 | leads, lead_cost, onsite_conversion.lead_grouped |
| **應用程式** | ❌ 無 | app_installs, mobile_app_install, app_custom_event |
| **歸因視窗** | ❌ 無 | 1d_click, 7d_click, 28d_click, 1d_view |
| **競標指標** | ⛔ 已棄用 | auction_bid, auction_competitiveness |

##### 競標指標說明 (Auction Metrics) - ⛔ 已確認不可用

> **測試結果 (2024-12-23)**：經本地 API 測試確認，Facebook Graph API v24.0 **不會回傳**這兩個指標的資料，即使在 Ad Set 層級請求也是如此。這些指標可能已被 Facebook 棄用或僅限特定帳號使用。

| 指標 | 中文名稱 | 狀態 | 說明 |
|------|----------|:----:|------|
| `auction_bid` | 競價金額 | ⛔ | API 無回傳資料 |
| `auction_competitiveness` | 競價競爭力 | ⛔ | API 無回傳資料 |

**原本預期的適用層級**（僅供參考）：

| 指標 | Campaign | Ad Set | Ad |
|:-----|:--------:|:------:|:--:|
| `auction_bid` | ⚠️ 無意義 | ✅ 主要層級 | ⚠️ 無意義 |
| `auction_competitiveness` | ⚠️ 無意義 | ✅ 主要層級 | ⚠️ 無意義 |

**結論**：暫不將這兩個指標加入系統。

##### 架構設計：指標資料庫 (Metrics Registry)

```
┌─────────────────────────────────────────────────────────┐
│                    Facebook Graph API                    │
│  (actions, action_values, video_views, video_p25, ...)  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           📦 指標資料庫 (Metrics Registry)               │
│  - 完整 FB 可用指標清單 (100+)                           │
│  - 各指標的中英文名稱、格式、計算方式                      │
│  - 分類標籤 (video, messaging, lead, ecommerce...)      │
│  - 是否需要特殊解析 (actions array 或直接欄位)           │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│            🛒 使用者啟用的指標 (Supermarket)              │
│  - 從 Registry 選取需要的指標                            │
│  - user_enabled_metrics / team_enabled_metrics          │
│  - 儲存到 localStorage (臨時) 或資料庫 (永久)            │
└─────────────────────────────────────────────────────────┘
```

##### 指標資料庫結構 (metrics_registry.json)

```json
{
  "video_p25_watched": {
    "key": "video_p25_watched",
    "label_zh": "影片觀看 25%",
    "label_en": "Video 25% Watched",
    "category": "video",
    "format": "number",
    "source": "actions",           // "actions" | "action_values" | "direct"
    "action_type": "video_view",   // actions array 內的 action_type
    "description_zh": "影片播放至 25% 的次數",
    "requires_video_objective": true,
    "is_default": false
  },
  "leads": {
    "key": "leads",
    "label_zh": "潛在客戶",
    "label_en": "Leads",
    "category": "lead_gen",
    "format": "number",
    "source": "actions",
    "action_type": "lead",
    "description_zh": "表單送出的潛在客戶數量",
    "is_default": false
  },
  "messaging_first_reply": {
    "key": "messaging_first_reply",
    "label_zh": "首次訊息回覆",
    "label_en": "First Message Reply",
    "category": "messaging",
    "format": "number",
    "source": "actions",
    "action_type": "onsite_conversion.messaging_first_reply",
    "description_zh": "用戶首次回覆訊息的數量",
    "is_default": false
  }
}
```

##### 實作優先級

| 優先級 | 項目 | 說明 | 工作量 |
|--------|------|------|--------|
| 🔴 P1 | 建立 `metricsRegistry.js` | 定義 100+ 指標的完整資料庫 | 2-3 小時 |
| 🔴 P1 | 更新後端解析邏輯 | 支援動態指標欄位請求 | 1-2 小時 |
| 🔴 P1 | 指標選擇 UI | 分類瀏覽 + 搜尋 | 2-3 小時 |
| 🟡 P2 | 偏好儲存 | localStorage + 資料庫同步 | 1-2 小時 |
| 🟢 P3 | 團隊指標設定 | 團隊層級的預設指標 | 1-2 小時 |

##### ⚠️ 安全實作策略 (Backward Compatible)

**原則**: 新增檔案，不修改現有程式碼。出問題時刪除新檔案即可回復。

```
📁 現有檔案 (保留不動)
├── constants/analyticsConfig.js  ← 原有 METRIC_GROUPS，完全不改
└── services.py                   ← 原有解析邏輯，完全不改

📁 新增檔案 (獨立擴展)
├── constants/metricsRegistry.js  ← 新的指標資料庫
└── hooks/useMetricsRegistry.js   ← 新的 React Hook (可選)
```

**切換機制**:
```javascript
// 功能開關 (預設關閉)
const USE_METRICS_REGISTRY = localStorage.getItem('feature_metrics_registry') === 'true';

// 使用時
const metrics = USE_METRICS_REGISTRY 
  ? getMetricsFromRegistry()   // 新系統
  : METRIC_GROUPS;              // 原系統 (預設)
```

**回滾步驟**:
| 步驟 | 操作 | 效果 |
|------|------|------|
| 1️⃣ | 關閉功能開關 | 立即切回原系統 |
| 2️⃣ | 刪除 `metricsRegistry.js` | 完全移除新程式碼 |
| 3️⃣ | `git revert` | 版本層級回退 |

##### 已完成功能 (2025-12-17 ~ 2025-12-18)

| 功能 | 說明 | 狀態 |
|------|------|------|
| 指標資料庫 | `metricsRegistry.js` - 70+ 指標 | ✅ 完成 |
| ~~指標實驗室~~ 指標管理 | `MetricsManager.jsx` - 瀏覽/搜尋 UI | ✅ 完成 |
| 儲存視角功能 | ~~localStorage~~ → 資料庫 `saved_views` 表儲存個人/團隊視角 | ✅ 完成 (升級) |
| 動態欄位 API | 後端支援 `?fields=` 參數動態請求 | ✅ 完成 |
| 側邊欄整合 | 「指標管理」選單已加入側邊欄 (`/metrics`) | ✅ 完成 |

> **命名變更 (2025-12-18)**:
> - `MetricsLab.jsx` → `MetricsManager.jsx`
> - `/lab` → `/metrics`
> - 🧪 指標實驗室 → 📋 指標管理

###### 儲存視角功能詳細說明 (Step 1)

| 功能 | 說明 |
|------|------|
| 儲存視角按鈕 | 點擊藍色「儲存視角」按鈕開啟命名 Modal |
| 命名 Modal | 輸入視角名稱，支援 Enter/Escape 快捷鍵 |
| 已儲存視角區塊 | 顯示所有已儲存視角，含指標數量標籤 |
| 載入視角 | 點擊「載入」恢復已儲存的指標選擇 |
| 刪除視角 | 點擊垃圾桶圖標刪除視角 |
| Toast 提示 | 操作成功後右上角顯示綠色提示 |
| 雙語支援 | 中文/英文介面完整翻譯 |

**技術實作**:
- localStorage Key: `metricslab_saved_views`
- 資料結構: `{ id, name, metrics[], createdAt }`

###### 儲存策略規劃

| 階段 | 儲存位置 | 說明 | 狀態 |
|------|----------|------|------|
| Phase 1 | ~~localStorage~~ | ~~瀏覽器本地儲存~~ | ✅ 已棄用 (遷移至資料庫) |
| Phase 2 | 資料庫 `saved_views` | 個人報表，跨裝置同步 | ✅ 已完成 (2025-12-18) |
| Phase 3 | 資料庫 `saved_views (team_id)` | 團隊共享報表 | ✅ 已完成 (2025-12-18) |

**localStorage 限制**:
- ❌ 無法跨裝置同步（換電腦/換瀏覽器就沒了）
- ❌ 無法分享給團隊成員
- ✅ 不需後端 API，開發快速

**升級路徑** (Phase 2):
```
1. 新增後端 API: POST /api/saved-views, GET /api/saved-views
2. 新增資料表: saved_views (id, user_id, team_id, name, metrics, created_at)
3. 前端改為呼叫 API，同時保留 localStorage 作為快取
```

**工作區視角共用策略** (2025-12-18 決議):

| 階段 | 模式 | 說明 |
|------|------|------|
| 現階段 | **共用** | 所有工作區（個人/團隊）共享同一份視角列表 |
| 未來 | 混合模式 | 個人視角跟著使用者；團隊視角存資料庫，僅團隊成員可見 |

> **設計理由**:
> - 現階段使用 localStorage，無法區分工作區
> - 共用模式可讓使用者在任何工作區都使用自己建立的視角
> - 未來實作資料庫同步時，再區分「個人視角」和「團隊視角」

##### 完整流程設計

```
┌─────────────────────────────────────────────────────────┐
│           🧪 MetricsLab (/lab)                           │
│                                                          │
│  [通用] [電商] [影音] [訊息] [潛在客戶] [應用程式]         │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ ☑ spend   ☑ roas   ☐ video_p25   ☐ messaging_reply │ │
│  │ ☑ reach   ☑ cpa    ☐ video_p50   ☐ leads           │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  [儲存為: 我的電商視角] [💾 儲存]                          │
└─────────────────────────────────────────────────────────┘
                           ↓
                    localStorage / DB
                           ↓
┌─────────────────────────────────────────────────────────┐
│           📊 Analytics (/analytics)                      │
│                                                          │
│  [總覽] [電商] [漏斗] [⭐ 我的電商視角]                    │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Campaign   │ spend │ roas │ video_p25 │ msgs_reply │ │
│  │ ────────── │ ───── │ ──── │ ───────── │ ────────── │ │
│  │ Campaign A │ $500  │ 2.5  │ 1,234     │ 89         │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

##### 待完成功能 (後續步驟)

| 優先級 | 功能 | 說明 | 工作量 | 狀態 |
|--------|------|------|--------|------|
| ~~🔴 P1~~ | ~~儲存為預設~~ | ~~MetricsLab 新增「儲存為我的視角」按鈕~~ | ~~1-2 小時~~ | ✅ 完成 |
| ~~🔴 P1~~ | ~~Analytics 讀取~~ | ~~Analytics 頁面讀取自訂視角並顯示~~ | ~~2-3 小時~~ | ✅ 完成 |
| ~~🟡 P2~~ | ~~後端動態欄位~~ | ~~根據選擇的指標動態請求 FB API 欄位~~ | ~~2-3 小時~~ | ✅ 完成 |
| 🟡 P2 | 拖曳排序 | 拖曳調整欄位顯示順序 (react-dnd) | 1-2 小時 | |
| ~~🟢 P3~~ | ~~團隊共享~~ | ~~團隊層級的自訂視角儲存~~ | ~~2-3 小時~~ | ✅ 已完成 (2025-12-18) |

##### 待優化項目 (UX 改進)

| 項目 | 說明 | 優先級 |
|------|------|--------|
| 視角數量上限 | 設定最多 5-10 個視角，避免 UI 擁擠 | 🟢 低 |
| 摺疊選單 | 超過 3 個視角時改用下拉選單 | 🟢 低 |
| 視角管理介面 | MetricsLab 提供編輯/重新命名功能 | ✅ 完成 |
| 視角排序 | 支援拖曳調整視角順序 | 🟢 低 |
| 團隊視角刪除權限 | 讓團隊擁有者/管理員可刪除成員建立的團隊視角 | 🟡 中 |

##### 刪除權限設計 (Current Design)

目前採用**「誰創建，誰管理」**原則：

| 視角類型 | 刪除權限 |
|----------|----------|
| 個人視角 (`user_id` = 我) | ✅ 只有自己可刪除 |
| 團隊視角 (`created_by` = 我) | ✅ 只有創建者可刪除 |
| 別人建的團隊視角 | ❌ 無法刪除 (即使是 Team Owner) |

> **設計理由**:
> - 防止意外刪除他人辛苦建立的視角
> - 責任歸屬明確：創建者對自己的視角負責
>
> **未來考量** (如有需求再實作):
> - Super Admin / Team Owner / Team Admin 可刪除該團隊的所有視角
> - 參考 `routers/saved_views.py` 第 144 行的授權邏輯

##### 實作順序

```
Step 1: MetricsLab 新增「儲存」功能 ✅ 已完成 (2025-12-17)
        → localStorage.setItem('metricslab_saved_views', [...])

Step 2: Analytics 新增已儲存視角 ✅ 已完成 (2025-12-17)
        → 金色星號按鈕顯示已儲存視角
        → 點擊載入對應指標組合

Step 3: Analytics 讀取 localStorage ✅ 已整合至 Step 2
        → const customMetrics = localStorage.getItem('metricslab_saved_views')

Step 4: 後端支援動態欄位 ✅ 已完成 (2025-12-18)
        → /api/analytics-data?fields=spend,roas,video_p25
        → 後端 build_fb_fields() 動態建構 API 請求
        → 前端 fetchAnalytics() 傳送 fields 參數
        → calculateSummary() 支援所有 57 個指標

Step 5: 完整整合測試 ✅ 已完成 (2025-12-18)
        → Video, Messaging, Lead, App 指標正常顯示
        → KPI 卡片摘要正確計算
        → 已推送至 dev-saas 分支
```

---

#### 1.2 競品廣告監測 (Ad Library API) - 🔒 需申請權限

**目標**: 搜尋任意品牌/粉絲頁的正在刊登廣告，下載廣告文案及素材。

**現況**: 🔲 未實作（需申請 `ads_archive` 權限）

**測試結果 (2024-12-23)**:
> 經本地 API 測試確認，目前的 Facebook Access Token 無法直接使用 Ad Library API。
> 錯誤訊息: `Authentication Error (InvalidValue): Token expired`
> 原因: 需要額外申請 `ads_archive` 權限並完成身份驗證。

##### Marketing API vs Ad Library API 差異

| 特性 | Marketing API (目前使用) | Ad Library API |
|------|------------------------|----------------|
| **用途** | 管理自己的廣告成效 | 查看任意品牌的公開廣告 |
| **資料範圍** | 私人帳號數據 | 公開廣告資料 |
| **需要權限** | `ads_read`, `ads_management` ✅ | `ads_archive` ❌ 未申請 |
| **可取得資料** | 點擊、轉換、ROAS、CPA 等 | 廣告素材、文案、曝光範圍 |

##### Ad Library API 可取得的資料

| 資料類型 | 可取得 | 備註 |
|---------|:------:|------|
| 廣告文案 (body text) | ✅ | 廣告內文 |
| 標題 (title) | ✅ | 廣告標題 |
| 圖片/影片連結 | ✅ | 可下載素材 |
| CTA 按鈕 | ✅ | 行動呼籲文字 |
| 廣告開始日期 | ✅ | |
| 曝光數範圍 | ✅ | 例如 "1K-5K" |
| 花費範圍 | ✅ | 例如 "$100-$499" |
| 點擊數/轉換數 | ❌ | 不提供 |

##### 取得權限步驟

1. **申請 `ads_archive` 權限**
   - 前往 [Facebook 開發者後台](https://developers.facebook.com/apps/)
   - 進入 App → 「App Review」→「Permissions and Features」
   - 搜尋並申請 `ads_archive` 權限

2. **完成身份驗證**
   - Facebook 可能要求上傳身份證明文件

3. **等待審核**
   - 審核時間通常需要幾天

##### 已準備的測試端點

```python
# backend/main.py
@app.get("/api/debug/test-ad-library")
async def test_ad_library(search_term: str, country: str = "TW"):
    """搜尋指定品牌的正在刊登廣告"""
    ...
```

**使用方式**: `/api/debug/test-ad-library?search_term=品牌名稱`

##### 功能規劃 (取得權限後)

| 優先級 | 功能 | 說明 |
|--------|------|------|
| 🔴 P1 | 品牌搜尋 | 輸入品牌名稱搜尋正在刊登的廣告 |
| 🔴 P1 | 廣告列表 | 顯示廣告文案、標題、素材預覽 |
| 🟡 P2 | 素材下載 | 下載廣告圖片/影片 |
| 🟡 P2 | 花費追蹤 | 追蹤競品廣告花費範圍變化 |
| 🟢 P3 | 監測提醒 | 競品有新廣告時發送通知 |

---

#### 1.3 下鑽分析 (Drill-down)
**目標**: 點擊圖表或表格行，直接深入查看底層數據。

**現況**: 🔲 未實作

**使用者流程**:
```
Account Overview → 點擊 Campaign → 顯示該 Campaign 的 Ad Sets
                → 點擊 Ad Set  → 顯示該 Ad Set 的 Ads
                → 點擊 Ad      → 顯示 Ad 詳細素材預覽
```

**技術需求**:
| 項目 | 說明 |
|------|------|
| 圖表點擊事件 | Recharts `onClick` handler |
| 動態 API 呼叫 | 傳入 `campaign_id` 或 `adset_id` 過濾 |
| 麵包屑導航 | `All Campaigns > Campaign A > Ad Set B` |
| URL 參數 | 支援直接分享連結 `?campaign_id=123` |

**API 端點 (現有)**:
```python
GET /api/analytics-data?account_id={id}&level=adset&campaign_id={cid}
GET /api/analytics-data?account_id={id}&level=ad&adset_id={asid}
```

**UI 設計方向**:
- 點擊表格 Row → 展開子表格 (Accordion Style)
- 或: 右側滑出 Panel 顯示詳細資訊

---

#### 1.3 儲存報表 (Saved Reports)
**目標**: 將篩選條件與指標設定存為預設值，一鍵還原常用視角。

**現況**: ✅ 已完成 (資料庫儲存 + 自動遷移)

**使用情境**:
| 預設名稱 | 說明 | 指標 |
|----------|------|------|
| 老闆視角 | 高層總覽 | Spend, ROAS, Purchases |
| 素材視角 | 廣告測試 | CTR, CPC, Engagement |
| 電商視角 | 購買漏斗 | ATC, CVR, Cart Dropoff |

**資料結構**:
```json
// saved_reports table
{
  "id": "uuid",
  "user_id": 123,
  "team_id": null,  // null = 個人, non-null = 團隊共享
  "name": "老闆視角",
  "icon": "📊",
  "config": {
    "level": "campaign",
    "datePreset": "last_7d",
    "metrics": ["spend", "roas", "purchases", "cpa"],
    "filters": {
      "keyword": "",
      "activeOnly": false
    },
    "sortBy": "spend",
    "sortOrder": "desc"
  },
  "is_default": false,
  "created_at": "2025-12-17T00:00:00Z"
}
```

**儲存位置策略**:
| 類型 | 儲存位置 | 說明 |
|------|----------|------|
| 臨時偏好 | ~~localStorage~~ | [已棄用] 改用資料庫儲存，已實作自動遷移至 `saved_views` 表 |
| 個人報表 | 資料庫 `saved_views` (user_id) | ✅ 已實作 (2025-12-18)，支援跨裝置同步 |
| 團隊報表 | 資料庫 `saved_views` (team_id) | ✅ 已實作 (2025-12-18)，團隊成員共用 |

**UI 設計**:
```
[View 選擇器]
├── 📊 總覽 (系統預設)
├── 🛒 電商 (系統預設)
├── 🌪️ 漏斗 (系統預設)
├── ─────────────────
├── ⭐ 老闆視角 (我的報表)
├── ⭐ 素材視角 (我的報表)
├── ─────────────────
├── 👥 團隊週報 (團隊共用)
└── ⚙️ 自訂...
```

### 2. AI 演進 (Phase 2 & 3)
*   **Copilot (Phase 2)**: 對話式助理 (Chatbot)，例如問：「為什麼昨天 ROAS 掉了？」。
*   **Autopilot (Phase 3)**: 自動化規則執行 (e.g., "CPA > $50 自動暫停廣告")。
*   **RAG 整合**: 結合知識庫，提供具備上下文的回答。

### 3. This section is renumbered to accommodate the new 1.4 section below.

#### 1.4 報告產生器 (Report Generator) - 混合式架構
**現況**: ✅ 已完成 (v1.5.4) - 支援 PDF 匯出與 AI 週報總結
**目標**: 產生專業的 PDF 週報，包含數據圖表與可選的 AI 總結。

**架構設計**: **「B. 選配式 (Optional)」**
1.  **數據報表 (Data Report)**:
    -   基礎功能，完全不需 AI。
    -   內容：目前的 Dashboard 快照 (KPI Cards + Charts + Top Campaigns)。
    -   格式：A4 橫向排版，適合列印/PDF 匯出。
2.  **AI 總結 (AI Summary)**:
    -   加值功能，按需觸發 (On-demand)。
    -   點擊「✨ Generate AI Summary」後，呼叫 Google Gemini 分析當前數據。
    -   產出：約 200-300 字的 Executive Summary (關鍵成效、風險、建議)。

**使用者流程**:
```
[User] 點擊 "Export Report"
   ↓
[System] 彈出預覽視窗 (Preview Modal)
   ├─ 顯示 Header (Logo, Date, Account)
   ├─ 顯示 KPI Cards & Charts (From Dashboard)
   └─ AI Section (Empty) ── [✨ Generate AI Insight] ──┐
                                                       ↓
                                                [AI Generating...]
                                                       ↓
                                                [Markdown Summary]
   ↓
[User] 點擊 "列印 / 儲存 PDF" (Browser Print)
```

**技術實作**:
-   **Frontend**: `ReportModal.jsx` (Preview), `window.print()` (瀏覽器原生列印，確保繁體中文支援)。
-   **Backend**: `AIService` 新增 `WEEKLY_SUMMARY` prompt。
-   **Print CSS**:
    -   A4 橫向自動排版
    -   表頭垂直旋轉以容納更多欄位
    -   KPI Cards 四欄網格
    -   字型使用「微軟正黑體」確保中文正常顯示
-   **已知問題**: 列印預覽可能產生空白頁，待後續優化。

---

#### 1.5 維度分析 (Dimension Analysis) - 獨立開發區
**現況**: 📋 規劃中 (Planned)
**目標**: 提供 Facebook 廣告的維度細分報告，例如依年齡、性別、國家、平台等進行分析。

**與一般指標的差異**:

| 類型 | API 參數 | 資料結構 |
|------|----------|----------|
| **指標 (Metrics)** | `fields=spend,clicks` | 每廣告一行 |
| **維度 (Dimensions)** | `breakdowns=age,gender` | 每廣告 × 每維度值 = 多行 |

**支援的維度** (來源: `ALL_AVAILABLE_METRICS.md`):
-   `age` - 年齡
-   `gender` - 性別
-   `country` - 國家
-   `region` - 地區
-   `impression_device` - 曝光裝置
-   `platform_position` - 版位
-   `publisher_platform` - 發佈平台 (FB/IG/Audience Network)

**架構需求** (獨立開發):
1.  **後端**: 新增 `breakdowns` 參數支援，回傳多行資料
2.  **前端**: 新增獨立的「維度報告」頁面或 Tab
3.  **視覺化**: 圓餅圖/長條圖顯示維度分佈

> ⚠️ **注意**: 此功能與現有指標系統架構不同，需獨立開發，不可直接混入現有表格。

---

#### 1.6 Google Search Console - API 能力與優化方向

**目標**: 充分利用 GSC API 的資料維度，提供更豐富的 SEO 分析報表。

##### 目前已實作的功能 ✅

| 端點 | 功能 | 回傳資料 |
|------|------|----------|
| `GET /api/gsc/sites` | 取得用戶驗證的網站清單 | `siteUrl`, `permissionLevel` |
| `GET /api/gsc/analytics` | 依日期取得搜尋效能 | `clicks`, `impressions`, `ctr`, `position` |

##### GSC API 可用維度 (Dimensions)

| 維度 | 說明 | 實作狀態 | 優先級 |
|------|------|---------|--------|
| `date` | 依日期分組 | ✅ 已實作 | - |
| `query` | 依搜尋關鍵字分組 | ✅ 已實作 (v1.5.6) | - |
| `page` | 依網頁 URL 分組 | ✅ 已實作 (v1.5.6) | - |
| `country` | 依國家/地區分組 | ❌ 待開發 | 🟡 中 |
| `device` | 依裝置類型分組 (DESKTOP, MOBILE, TABLET) | ❌ 待開發 | 🟡 中 |
| `searchAppearance` | 依搜尋外觀分組 (AMP, 精選摘要等) | ❌ 待開發 | 🟢 低 |

##### 功能優化待辦清單

1. **關鍵字分析報表** ✅ (v1.5.6 已完成)
   - ✅ 新增 `dimensions: ['query']` 的 API 呼叫
   - ✅ 顯示熱門關鍵字排行：點擊數、曝光、CTR、平均排名
   - ✅ 支援關鍵字搜尋/篩選
   - ✅ **關鍵字群組功能** - 將類似關鍵字歸為一組

2. **頁面效能報表** ✅ (v1.5.6 已完成)
   - ✅ 新增 `dimensions: ['page']` 的 API 呼叫
   - ✅ 顯示表現最佳/最差的頁面
   - ✅ URL 可點擊跳轉

3. **地區流量分佈** 🟡
   - 新增 `dimensions: ['country']` 的 API 呼叫
   - 地圖視覺化 或 國家表格排行

4. **裝置分佈分析** 🟡
   - 新增 `dimensions: ['device']` 的 API 呼叫
   - 圓餅圖顯示桌機/手機/平板比例

5. **多維度組合查詢** 🟢
   - 例如 `['query', 'page']` 可分析「特定關鍵字在哪些頁面出現」
   - 進階用戶功能

6. **日期範圍選擇器** ✅ (已完成)
   - 快捷選項：7 天、28 天、3 個月、自訂
   - 自訂日期輸入選擇器
   - 動態更新卡片標籤顯示天數

7. **資料匯出功能** 🟢
   - 匯出 CSV / Excel
   - 匯出 PDF 報表

##### 已完成開發項目 (2025-12-29) ✅

1. **Tab 導航系統**
   - 📈 每日成效 (Daily Performance) - 依日期分組
   - 🔍 關鍵字分析 (Keyword Analysis) - 依搜尋查詢分組
   - 📄 頁面分析 (Page Analysis) - 依頁面 URL 分組

2. **關鍵字分析功能**
   - 熱門關鍵字排行表格
   - 可點擊排序（點擊數、曝光、CTR、排名）
   - 關鍵字搜尋篩選
   - 數量限制選擇器 (Top 50/100/200)

3. **關鍵字群組功能** 📦
   - 點擊「群組」按鈕開啟/關閉群組模式
   - 相似度分群演算法（詞彙重疊度 + 包含檢測）
   - 可展開/收合的群組列表
   - 群組總點擊數與總曝光數統計
   - +N 標籤顯示群組內額外關鍵字數量

4. **頁面分析功能**
   - 頁面 URL 可點擊跳轉至實際網頁
   - URL 自動簡化顯示（移除 domain）

5. **部署問題修復**
   - 修正 405 錯誤：GSC 元件改用 `VITE_API_URL` 環境變數
   - 修正 500 錯誤：文件化 `GOOGLE_CLIENT_SECRET` 為必要環境變數

##### 關鍵字群組演算法說明

**相似度計算方式**：
```
1. 包含檢測：若 A 包含 B（或反之），相似度 = 0.8
2. 詞彙重疊度 (Jaccard Index)：交集詞數 / 聯集詞數
3. 分群閾值：相似度 ≥ 0.4 則歸為同組
```

**優化方向**：
| 方案 | 說明 | 優先級 |
|------|------|--------|
| N-gram 匹配 | 用 2-3 字元片段取代空格分詞，更適合中文 | 🟡 中 |
| 編輯距離 | Levenshtein distance 計算字元相似度 | 🟢 低 |
| 後端 NLP 服務 | 使用 jieba 中文分詞，提升分群精確度 | 🟢 低 |
| 可調整閾值 | 讓用戶調整分群敏感度 (0.3 ~ 0.6) | 🟢 低 |

##### 已完成開發項目 (2024-12-26) ✅

1. **GSC OAuth 連線修復**
   - 修正 `gsc_service.py` token exchange 時的 "Scope has changed" 錯誤
   - 解決方案：使用 `scopes=None` 讓後端接受 Google 核發的任何權限
   - 修正 `GSCStats.jsx` 使用錯誤的 localStorage key (`token` → `google_token`)

2. **手機版響應式優化**
   - `SearchConsole.jsx`: 加入 `isMobile` context，調整 padding (16px mobile / 24px desktop)
   - `GSCStats.jsx`: 響應式卡片 grid、表格水平捲動、字體大小調整
   - `Layout.jsx`: 修正 main-content 寬度計算，防止子元素溢出

3. **日期範圍選擇器**
   - 快捷選項下拉選單：7 天、28 天、3 個月、自訂
   - 自訂日期輸入 (date picker)
   - 卡片標籤動態顯示選擇的天數
   - 表格數字加入千位數分隔符號 (`toLocaleString()`)

4. **相關檔案異動**
   - `frontend/src/pages/SearchConsole.jsx` - 響應式容器樣式
   - `frontend/src/components/GSCStats.jsx` - 日期選擇器 + 響應式卡片與表格
   - `frontend/src/components/Layout.jsx` - 修正 main-content maxWidth 計算
   - `backend/gsc_service.py` - OAuth scopes 修復
   - `backend/routers/gsc.py` - 錯誤處理優化


---

#### 1.7 Google Search Console (Team Integration)
**目標**: 將目前個人的 GSC 綁定升級為「團隊共享」模式，讓團隊成員能共同檢視 GSC 數據。

**現況**: ⚠️ 僅支援個人綁定 (Personal Binding)
- 目前 GSC Token 綁定在 `User` 模型。
- 無論切換到哪個團隊，看到的都是當前使用者的私人 GSC 數據。

**架構升級計畫**:

##### 資料庫變更 (Database Schema)
- **`teams` table**: 新增 GSC 相關欄位，儲存團隊共用的 Token。
    - `gsc_access_token`
    - `gsc_refresh_token`
    - `gsc_expires_at`

##### 後端 API 調整 (Backend)
- **POST `/api/gsc/authorize`**:
    - 新增選填參數 `team_id`。
    - 若帶有 `team_id`，將 Token 存入 `teams` 表而非 `users` 表。
- **GET `/api/gsc/sites` & `/api/gsc/analytics`**:
    - 檢查 Header `X-Team-ID`。
    - 若有 `X-Team-ID`，優先從 `teams` 表讀取 Token。
    - 若無，則 Fallback 至 `users` 表 (或依據 Strict Token Mode 決定是否阻擋)。

##### 前端調整 (Frontend)
- **`GSCConnect.jsx`**: 授權時傳送當前 `selectedTeamId`。
- **`SearchConsole.jsx`**: 確保 API 請求帶有正確的 Header (目前 axios interceptor 已處理，需驗證)。

**預期效益**:
- 行銷代理商 (Agency) 可由主管綁定客戶 GSC，所有優化師皆可查看，無需分享 Google 帳號密碼。
- 企業內部行銷團隊可共享單一 GSC 資源。

---

### 3. 商業化與金流

#### 發展階段路線圖

| 階段 | 目標 | 說明 |
|------|------|------|
| **Phase 1** | 個人用戶 | 先吸引個人廣告主/自由工作者 |
| **Phase 2** | 團隊方案 | 解鎖團隊協作功能 |
| **Phase 3** | 企業版 | 視發展狀況調整，含白標、API 等 |

#### 定價方案設計 (Phase 1-2)

| 功能 | Free | Pro ($X/月) | Team ($X/月) |
|------|:----:|:-----------:|:------------:|
| **廣告帳號數** | 1 | 5 | 10+ |
| **團隊成員** | ❌ | ❌ | 5 人 |
| **數據回溯天數** | 7 天 | 30 天 | 90 天 |
| **儲存視角數** | 3 | 10 | 無限 |
| **自訂指標** | 基本 (10) | 全部 (70+) | 全部 |
| **AI 分析** | ❌ | 30 次/月 | 100 次/月 |
| **匯出報表** | ❌ | ✅ | ✅ |
| **優先支援** | ❌ | Email | Email |

> **定價原則**:
> - 免費版作為獲客入口，限制關鍵功能 (帳號數、回溯天數)
> - Pro 解鎖專業分析功能，吸引付費個人用戶
> - Team 加入協作功能，針對小型團隊

#### 架構調整需求

| 項目 | 說明 | 狀態 |
|------|------|------|
| `subscriptions` 資料表 | 儲存用戶/團隊的訂閱狀態與方案 | 🔲 待開發 |
| 配額檢查 Middleware | 後端檢查功能使用權限 | 🔲 待開發 |
| Stripe 整合 | 付款處理與 Webhook | 🔲 待開發 |
| 前端付費牆 (Paywall) | UI 提示升級 | 🔲 待開發 |
| 用量追蹤 | AI 呼叫次數等統計 | 🔲 待開發 |

#### 技術實作順序

```
Step 1: 資料模型 (subscriptions 表)
        └─ user_id/team_id, plan, status, payuni_token, period_dates

Step 2: 配額常數 (PLAN_LIMITS)
        └─ 定義各方案的功能限制

Step 3: 配額檢查 Middleware
        └─ 在 API 層檢查權限

Step 4: 前端 Paywall 元件
        └─ 顯示升級提示

Step 5: PAYUNi 整合
        └─ 付款頁面、Webhook 處理
```

#### PAYUNi 統一金流整合計畫

**選擇 PAYUNi 的原因**: 台灣本土金流，支援信用卡週期性扣款，適合 SaaS 訂閱制。

##### 技術概述

| 項目 | 說明 |
|------|------|
| **官方 SDK** | PHP SDK、.NET SDK (官方)、**無 Python SDK** |
| **API 類型** | RESTful API，需 AES 加密 EncryptInfo |
| **加密方式** | Hash Key + Hash IV (AES-128-CBC) |
| **API 文件** | https://www.payuni.com.tw/docs/web/#/7/34 |
| **GitHub** | https://github.com/payuni |

##### 支援的支付方式 (mode)

| Mode | 說明 | 適用場景 |
|------|------|----------|
| `upp` | 整合式支付頁 | 最簡單，適合首次導入 |
| `credit` | 信用卡幕後 | 自訂 UI |
| `credit_bind_query` | 信用卡 Token (約定) | **訂閱制必用** |
| `atm` | 虛擬帳號 | 一次性付款 |
| `cvs` | 超商代碼 | 一次性付款 |
| `linepay` | LINE Pay | 行動支付 |

##### 訂閱制流程 (信用卡 Token)

```
┌─────────────────────────────────────────────────────────────┐
│  首次訂閱流程                                                 │
│                                                             │
│  1. 用戶選擇方案 → 點擊「訂閱」                               │
│  2. 後端建立訂單 → 重導向 PAYUNi 支付頁                       │
│  3. 用戶完成付款 + 同意綁定信用卡                             │
│  4. PAYUNi 回調 Webhook → 儲存 Token 到 subscriptions         │
│  5. 訂閱啟用，解鎖 Pro 功能                                  │
│                                                             │
│  續約扣款流程 (自動)                                          │
│                                                             │
│  1. Cron Job 檢查即將到期的訂閱                              │
│  2. 使用儲存的 Token 向 PAYUNi 請款                          │
│  3. 成功 → 延長訂閱期限；失敗 → 通知用戶更新卡片              │
└─────────────────────────────────────────────────────────────┘
```

##### Python 實作方案 (FastAPI)

| 檔案 | 說明 | 狀態 |
|------|------|------|
| `services/payuni.py` | PAYUNi API 封裝 (AES 加密、HTTP 請求) | 🔲 待開發 |
| `routers/payments.py` | 付款相關 API 端點 | 🔲 待開發 |
| `routers/webhooks.py` | PAYUNi 回調處理 | 🔲 待開發 |
| `tasks/subscription_renewal.py` | 自動續約 Cron Job | 🔲 待開發 |

##### 必要環境變數

```env
PAYUNI_MER_ID=商店代號
PAYUNI_HASH_KEY=Hash Key
PAYUNI_HASH_IV=Hash IV
PAYUNI_IS_TEST=true  # 測試環境
```

##### 實作優先級

| 優先級 | 項目 | 說明 | 工作量 |
|--------|------|------|--------|
| 🔴 P1 | `PayuniService` 類別 | Python 實作 AES 加密 + API 呼叫 | 4-6 小時 |
| 🔴 P1 | `subscriptions` 資料表 | 儲存訂閱狀態、Token、到期日 | 2-3 小時 |
| 🟡 P2 | 前端付款流程 | 方案選擇 → 重導向 → 回調頁面 | 4-6 小時 |
| 🟡 P2 | Webhook 處理 | 接收付款成功/失敗通知 | 3-4 小時 |
| 🟢 P3 | 自動續約 Job | 定期檢查 + Token 請款 | 3-4 小時 |
| 🟢 P3 | 訂閱管理後台 | 查看/取消訂閱、更換卡片 | 4-6 小時 |

> **待確認事項**:
> - [ ] 取得 PAYUNi 商店帳號 (MerID, Hash Key, Hash IV)
> - [ ] 確認定價：月繳/年繳、試用期天數
> - [ ] 選擇首次導入方式：整合式支付頁 (upp) 或幕後信用卡綁定

### 4. 渠道擴充
*   **協作廣告 (CPAS)**: 針對零售通路的銷售指標 (Catalog 邏輯)。
*   **Google 整合**: 串接 GA4 實現全漏斗歸因 (Full-funnel Attribution)。
*   **隱藏受眾挖掘**: 尋找低競爭廣告關鍵字的工具。

---

## 📚 Technical Notes (技術筆記)

### Google 整合規則 (OAuth)
*   **測試模式 (Testing Mode)**: 需要手動將 Email 加入白名單。
*   **正式模式 (Production Mode)**: 若索取敏感權限 (如 GA4) 需通過 Google 驗證，否則會有 "Unverified App" 警告。
*   **策略**: 目前僅使用 `email/profile` 權限，避免繁瑣驗證。
*   **架構隔離 (Architecture Isolation)**:
    *   **個人 API 設定**: 存於 `users` 表，僅限個人工作區使用 (Strict Token Mode 保護)。
    *   **團隊 API 設定**: 存於 `teams` 表，僅限團隊工作區使用。兩者互不干擾。
*   **權限控制 (Permissions)**:
    *   **團隊 API 配置**: 僅限 **Team Owner** 與 **Team Admin** 有權限修改。
    *   **一般成員 (Member/Viewer)**: 僅能查看數據，無法更改 API 連線設定。

### 部署與效能
*   **Zeabur 部署**: 需設定特定環境變數 (`ZEABUR_AI_HUB_API_KEY`)。
*   **效能優化**:
    *   **分頁機制 (Pagination)**: 對於超過 50 個 Active Campaign 的帳號至關重要。
    *   **快取 (Caching)**: 使用 Redis/Memory cache 減少頻繁 API 呼叫。

---

## 📅 Roadmap Update: Google Search Console 整合 (2025-12-26)

### 1. 專案目標
將 Google Search Console (GSC) 報表功能整合至 Facebook Dashboard，提供 SEO 與廣告投放的全面數據視野。

### 2. 核心設計原則
-   **獨立分頁**: 建立獨立的 "Search Console" 頁面，區隔 FB 廣告與 SEO 數據。
-   **帳號彈性**: 允許使用者連結**任何**擁有目標網站權限的 Google 帳號，不強制綁定登入帳號。
-   **權限要求**: 連結的 Google 帳號必須在 GSC 擁有該網站的權限 (Owner 或 Full User)。

### 3. 實作計畫

#### 後端 (Backend)
-   **新 Router (`gsc.py`)**:
    -   `POST /api/gsc/auth`: 交換 Access/Refresh Tokens。
    -   `GET /api/gsc/sites`: 列出已驗證網站。
    -   `POST /api/gsc/analytics`: 抓取搜尋分析數據 (Clicks, Impressions, CTR, Position)。
-   **資料庫更新 (`User` 表)**:
    -   新增 `gsc_access_token`, `gsc_refresh_token`, `gsc_expires_at`。
    -   Token 進行加密儲存。
-   **相依套件**: 新增 `google-api-python-client`。

#### 前端 (Frontend)
-   **新元件 `GSCConnect.jsx`**:
    -   提供 OAuth 連線按鈕。
    -   權限範圍: `https://www.googleapis.com/auth/webmasters.readonly`。
-   **新元件 `GSCStats.jsx`**:
    -   顯示 SEO 關鍵指標與趨勢圖。
-   **新路由**: `/gsc` (Search Console)。

### 4. 驗證步驟
1.  點擊 "Connect Search Console" 並授權。
2.  確認後端成功交換並儲存加密 Token。
3.  進入 Search Console 分頁，確認能讀取網站列表與數據報表。