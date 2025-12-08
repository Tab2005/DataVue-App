# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## 部署說明 (Deployment Guide)

### 解決 "Failed to fetch" 連線錯誤

當您將此專案部署到 Zeabur 或其他雲端平台時，前端預設會嘗試連線到 `http://localhost:8000`，這在正式環境中會導致連線失敗。

**解決步驟：**

1. **取得後端網址**：
   - 確保您的後端 (Backend) 服務已部署成功。
   - 複製後端的公開網址 (例如：`https://your-backend.zeabur.app`)。

2. **設定環境變數**：
   - 在 Zeabur 的 Frontend 服務頁面中，點選 **Variables** (環境變數)。
   - 新增一個變數：
     - Key: `VITE_API_URL`
     - Value: `https://your-backend.zeabur.app` (您的後端網址)
   - **重要**：請務必使用 `https://` 開頭，否則會出現 "Mixed Content" 錯誤。
   - **注意**：網址結尾不需要加斜線 `/`。

3. **重新部署**：
   - 設定完成後，請重新部署 (Redeploy) Frontend 服務以套用變更。

### 本地開發 (Local Development)

- 本地開發時，系統會自動讀取 `.env.development` 檔案，預設連線至 `http://localhost:8000`。
- 您不需要在本地手動設定 `VITE_API_URL`，除非您的後端跑在不同的 Port。
