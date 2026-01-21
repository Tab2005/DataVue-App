# 站略 (Site-tegy) - 多平台數據分析儀表板

> **站略 (Site-tegy)** 是一個功能強大且模組化的多平台數據儀表板，旨在幫助行銷團隊與開發者整合分散的數據來源，透過 AI 驅動的洞察力制定更精準的網站策略。

---

## 📅 專案狀態 (Project Status)

![Version](https://img.shields.io/badge/Version-v2.0.0--modular-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Tech](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%20%7C%20SQLAlchemy-orange)

---

## ✨ 核心功能特色

| 功能模組 | 說明 |
| :--- | :--- |
| **🌍 跨平台數據整合** | 一站式管理 **Facebook Ads**、**Google Search Console** 與 **Google Analytics 4**。 |
| **🤖 AI 智慧分析** | 整合 **Gemini** 與 **Zeabur AI**，提供自動化數據意圖分析與 SSE 串流智慧對話。 |
| **🔐 精細權限管理** | 基於 RBAC 的權限體系，支援工作區分離、模組開關與訂閱方案 (Free/Pro) 控制。 |
| **👑 高效團隊協作** | 完善的邀請連結系統與成員角色管理 (Owner/Admin/Member/Viewer)。 |
| **💾 自訂數據視角** | 隨時保存常用的篩選條件，一鍵切換多維度數據視圖。 |
| **🛡️ 安全與加密** | 敏感資料 (API Keys/Tokens) 使用 Fernet 加密儲存，確保數據安全。 |

---

## 🎯 技術文件索引

為了協助開發者與維護者快速上手，本專案提供了一套編號引導技術文件：

1. [**01_專案概覽**](documentation/01_專案概覽.md)：核心價值、功能模組與詳細技術棧。
2. [**02_系統架構**](documentation/02_系統架構.md)：模組化後端 (Core/Modules) 與 React 前端架構設計。
3. [**03_資料庫設計**](documentation/03_資料庫設計.md)：資料表結構、關聯性與模組化資料管理。
4. [**04_權限管理系統**](documentation/04_權限管理系統.md)：RBAC、模組權限與訂閱方案深度解析。
5. [**05_API_參考手冊**](documentation/05_API_參考手冊.md)：核心 API 端點、認證流程與 AI 規格。
6. [**06_部署指南**](documentation/06_部署指南.md)：Zeabur 部署流程、環境變數配置與實戰建議。
7. [**07_開發與擴充手冊**](documentation/07_開發與擴充手冊.md)：模組開發實踐、本地開發流程與規格。

---

## 🚀 快速啟動 (Local Development)

### 1. 後端啟動 (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # 填寫必要的 API Keys
uvicorn main:app --reload
```

### 2. 前端啟動 (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ 核心技術棧 (Core Technology Stack)

- **Backend:** FastAPI (Python), SQLAlchemy, Alembic, Pydantic, Fernet Encryption.
- **Frontend:** React 19, Vite, Vanilla CSS, Lucide Icons.
- **Intelligence:** Google Gemini API, Zeabur AI Hub.
- **Database:** PostgreSQL (Production), SQLite (Local Dev).

---

## 📄 授權協議 (License)

本專案採用 [MIT License](LICENSE) 授權。

---

**維護者：** Tab2005 (Site-tegy Team)  
**最後更新：** 2026-01-21
