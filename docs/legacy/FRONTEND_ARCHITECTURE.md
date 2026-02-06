# DataVue-App - 前端架構文件

## 📖 概述

本文件詳細說明 DataVue-App 前端的架構設計、元件組織、狀態管理及最佳實踐。

---

## 🏗️ 整體架構

### 技術棧

- **框架：** React 19.2.0
- **建置工具：** Vite 7.2.4
- **路由：** React Router DOM 7.10.1
- **UI 圖表：** Recharts 3.5.1
- **認證：** @react-oauth/google 0.12.2
- **樣式：** CSS Modules / Inline Styles
- **圖示：** React Icons 5.5.0
- **Markdown：** react-markdown 10.1.0

### 設計原則

1. **元件化 (Component-based)：** 可重用的 UI 元件
2. **單向資料流：** Props 向下傳遞、事件向上傳遞
3. **關注點分離：** UI 元件、業務邏輯、API 服務分離
4. **效能優化：** Lazy Loading、Code Splitting、Memoization
5. **使用者體驗：** Loading 狀態、錯誤處理、友善提示

---

## 📁 目錄結構詳解

```
frontend/
├── public/                    # 靜態資源
│   └── vite.svg
│
├── src/
│   ├── main.jsx               # React 應用入口
│   ├── App.jsx                # 路由配置、Layout
│   │
│   ├── components/            # UI 元件
│   │   ├── Layout.jsx         # 主版面配置
│   │   ├── Header.jsx         # 頂部導航列
│   │   ├── Sidebar.jsx        # 側邊欄選單
│   │   ├── ProtectedRoute.jsx # 路由保護
│   │   ├── ErrorBoundary.jsx  # 錯誤邊界
│   │   ├── PageLoading.jsx    # 頁面載入動畫
│   │   ├── Skeleton.jsx       # 骨架屏
│   │   ├── KPICard.jsx        # KPI 卡片元件
│   │   ├── TrendsChart.jsx    # 趨勢圖表
│   │   ├── SettingsModal.jsx  # 設定模態框
│   │   ├── InviteModal.jsx    # 邀請成員模態框
│   │   ├── PermissionManager.jsx  # 權限管理元件
│   │   ├── UserModuleManager.jsx  # 使用者模組管理
│   │   ├── GA4Stats.jsx       # GA4 統計元件
│   │   ├── GA4Connect.jsx     # GA4 連線元件
│   │   ├── GSCStats.jsx       # GSC 統計元件
│   │   ├── GSCConnect.jsx     # GSC 連線元件
│   │   ├── ContentGroupModal.jsx  # 內容分組模態框
│   │   └── SourceGroupModal.jsx   # 來源分組模態框
│   │
│   ├── pages/                 # 頁面元件
│   │   ├── Login.jsx          # 登入頁
│   │   ├── Dashboard.jsx      # Facebook Ads 儀表板
│   │   ├── Analytics.jsx      # Facebook Ads 分析
│   │   ├── SearchConsole.jsx  # GSC 分析頁
│   │   ├── GA4Analytics.jsx   # GA4 分析頁
│   │   ├── TeamSettings.jsx   # 團隊設定
│   │   ├── UserManagement.jsx # 使用者管理
│   │   ├── AdminDashboard.jsx # 管理員儀表板
│   │   ├── InvitePage.jsx     # 邀請接受頁
│   │   └── MetricsManager.jsx # 指標管理器
│   │
│   ├── services/              # API 服務層
│   │   ├── aiService.js       # AI API 呼叫
│   │   └── ...
│   │
│   ├── hooks/                 # 自訂 Hooks
│   │   └── index.js           # ProtectedModule Hook
│   │
│   ├── utils/                 # 工具函式
│   │   ├── contentGroups.js   # 內容分組工具
│   │   └── ...
│   │
│   └── styles/                # 全域樣式
│       └── ...
│
├── index.html                 # HTML 模板
├── package.json               # 依賴管理
├── vite.config.js             # Vite 配置
└── eslint.config.js           # ESLint 配置
```

---

## 🧩 核心元件詳解

### 1. 應用入口 (`App.jsx`)

```jsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';

function App() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  return (
    <ErrorBoundary>
      <GoogleOAuthProvider clientId={clientId}>
        <Router>
          <Suspense fallback={<PageLoading />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/invite/:code" element={<InvitePage />} />
              
              <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route path="/" element={
                  <ProtectedModule module="fb_ads">
                    <Dashboard />
                  </ProtectedModule>
                } />
                {/* 其他路由... */}
              </Route>
            </Routes>
          </Suspense>
        </Router>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}
```

**關鍵功能：**
- **Google OAuth Provider：** 包裹整個應用，提供 OAuth 上下文
- **路由保護：** 使用 `ProtectedRoute` 和 `ProtectedModule` 保護路由
- **錯誤邊界：** 捕捉 React 錯誤，避免整個應用崩潰
- **Lazy Loading：** 使用 `React.lazy()` 延遲載入頁面元件

### 2. 版面配置 (`Layout.jsx`)

```jsx
function Layout() {
  return (
    <div className="app-container">
      <Header />
      <div className="content-wrapper">
        <Sidebar />
        <main className="main-content">
          <Outlet />  {/* 子路由渲染位置 */}
        </main>
      </div>
    </div>
  );
}
```

**職責：**
- 提供統一的頁面結構
- 包含 Header、Sidebar、Main Content 區域
- 使用 `<Outlet />` 渲染子路由

### 3. 路由保護 (`ProtectedRoute.jsx`)

```jsx
function ProtectedRoute({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('google_token');
    if (token) {
      // 驗證 Token 有效性
      verifyToken(token).then(valid => {
        setIsAuthenticated(valid);
      });
    } else {
      setIsAuthenticated(false);
    }
  }, []);

  if (isAuthenticated === null) return <PageLoading />;
  if (!isAuthenticated) return <Navigate to="/login" />;

  return children;
}
```

**保護邏輯：**
1. 檢查 `localStorage` 是否有 `google_token`
2. 驗證 Token 有效性（呼叫後端 `/api/auth/me`）
3. 未登入自動跳轉到 `/login`

### 4. 模組權限保護 (`hooks/index.js`)

```jsx
export function ProtectedModule({ module, children }) {
  const [hasAccess, setHasAccess] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('google_token');
    
    fetch(`${API_URL}/api/permissions/check/${module}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setHasAccess(data.has_access))
      .catch(() => setHasAccess(false));
  }, [module]);

  if (hasAccess === null) return <PageLoading />;
  if (!hasAccess) return <div>無權限存取此功能模組</div>;

  return children;
}
```

**使用方式：**
```jsx
<Route path="/gsc" element={
  <ProtectedModule module="gsc">
    <SearchConsole />
  </ProtectedModule>
} />
```

### 5. 錯誤邊界 (`ErrorBoundary.jsx`)

```jsx
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-container">
          <h1>😞 發生錯誤</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            重新整理
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

---

## 📄 頁面元件詳解

### 1. 登入頁 (`Login.jsx`)

```jsx
import { GoogleLogin } from '@react-oauth/google';

function Login() {
  const handleSuccess = async (credentialResponse) => {
    const token = credentialResponse.credential;
    localStorage.setItem('google_token', token);

    // 驗證並取得使用者資訊
    const response = await fetch(`${API_URL}/api/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (response.ok) {
      navigate('/');
    }
  };

  return (
    <div className="login-page">
      <h1>DataVue Analytics</h1>
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={() => alert('登入失敗')}
      />
    </div>
  );
}
```

### 2. Facebook Ads 儀表板 (`Dashboard.jsx`)

**功能：**
- 選擇廣告帳戶
- 日期範圍選擇
- KPI 卡片顯示（花費、觸及、點擊、互動）
- 趨勢圖表
- AI 分析建議

**資料流：**
```
1. useEffect 載入廣告帳戶列表
2. 使用者選擇帳戶 + 日期範圍
3. 呼叫 /api/dashboard-data
4. 渲染 KPICard 和 TrendsChart
5. (選用) 呼叫 /api/ai/analyze 取得 AI 建議
```

### 3. GSC 分析頁 (`SearchConsole.jsx`)

**功能：**
- OAuth 授權流程
- 網站列表選擇
- 查詢條件篩選（日期、維度、頁面/查詢）
- 資料表格顯示
- 頁面標題抓取
- AI 意圖分析

**關鍵元件：**
```jsx
<SearchConsole>
  <GSCConnect />  {/* 授權與網站選擇 */}
  <GSCStats />    {/* 數據顯示與分析 */}
</SearchConsole>
```

### 4. GA4 分析頁 (`GA4Analytics.jsx`)

**功能：**
- GA4 OAuth 授權
- 帳戶/資源選擇
- 多頁籤分析（流量、行為、內容、電商）
- 內容分組管理
- 來源分組管理

**頁籤結構：**
```jsx
const tabs = [
  { id: 'traffic', name: '流量分析' },
  { id: 'behavior', name: '行為分析' },
  { id: 'content', name: '內容分析' },
  { id: 'ecommerce', name: '電商分析' }
];

{activeTab === 'traffic' && <TrafficStats />}
{activeTab === 'behavior' && <BehaviorStats />}
{activeTab === 'content' && <ContentStats />}
{activeTab === 'ecommerce' && <EcommerceStats />}
```

### 5. 團隊設定 (`TeamSettings.jsx`)

**功能：**
- 顯示團隊列表
- 建立/編輯/刪除團隊
- 管理團隊成員
- 設定團隊 Facebook Token
- 生成邀請連結

---

## 🔌 服務層 (`services/`)

### AI Service (`aiService.js`)

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const aiService = {
  testConnection: async (apiKey = null) => {
    const token = localStorage.getItem('google_token');
    const res = await fetch(`${API_URL}/api/ai/test-connection`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ api_key: apiKey })
    });

    if (!res.ok) throw new Error('Connection failed');
    return await res.json();
  },

  analyzeStream: async (data, context, onChunk, onDone) => {
    const token = localStorage.getItem('google_token');
    const res = await fetch(`${API_URL}/api/ai/analyze-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ data, context })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        onDone();
        break;
      }

      const chunk = decoder.decode(value);
      onChunk(chunk);
    }
  }
};
```

---

## 🎨 UI 元件庫

### KPI Card (`KPICard.jsx`)

```jsx
function KPICard({ title, value, change, icon, trend }) {
  const trendColor = trend === 'up' ? 'green' : trend === 'down' ? 'red' : 'gray';

  return (
    <div className="kpi-card">
      <div className="kpi-header">
        <span className="kpi-icon">{icon}</span>
        <span className="kpi-title">{title}</span>
      </div>
      <div className="kpi-value">{value}</div>
      <div className={`kpi-change ${trendColor}`}>
        {change > 0 ? '↑' : '↓'} {Math.abs(change)}%
      </div>
    </div>
  );
}
```

### Trends Chart (`TrendsChart.jsx`)

```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

function TrendsChart({ data }) {
  return (
    <LineChart width={800} height={400} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Line type="monotone" dataKey="spend" stroke="#8884d8" />
      <Line type="monotone" dataKey="reach" stroke="#82ca9d" />
    </LineChart>
  );
}
```

### Settings Modal (`SettingsModal.jsx`)

```jsx
function SettingsModal({ isOpen, onClose, onSave }) {
  const [settings, setSettings] = useState({
    appId: '',
    appSecret: '',
    shortToken: ''
  });

  const handleSave = async () => {
    const token = localStorage.getItem('google_token');
    await fetch(`${API_URL}/api/auth/exchange-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(settings)
    });

    onSave();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Facebook 設定</h2>
        <input
          placeholder="App ID"
          value={settings.appId}
          onChange={e => setSettings({...settings, appId: e.target.value})}
        />
        {/* 其他欄位... */}
        <button onClick={handleSave}>儲存</button>
        <button onClick={onClose}>取消</button>
      </div>
    </div>
  );
}
```

---

## 🔄 狀態管理策略

### 1. Local State (useState)

**適用場景：**
- 元件內部狀態（表單輸入、開關狀態）
- 不需要跨元件共享的資料

```jsx
const [isModalOpen, setIsModalOpen] = useState(false);
const [selectedDate, setSelectedDate] = useState(new Date());
```

### 2. Context API (選用)

**適用場景：**
- 使用者資訊
- 主題設定
- 全域通知

```jsx
const UserContext = createContext();

function UserProvider({ children }) {
  const [user, setUser] = useState(null);

  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
}

// 使用
const { user } = useContext(UserContext);
```

### 3. LocalStorage

**儲存資料：**
- `google_token` - Google OAuth Token
- `selected_team` - 當前選擇的團隊 ID
- `user_preferences` - 使用者偏好設定

```javascript
// 儲存
localStorage.setItem('google_token', token);

// 讀取
const token = localStorage.getItem('google_token');

// 刪除
localStorage.removeItem('google_token');
```

---

## 🚀 效能優化

### 1. Code Splitting

```jsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));

function App() {
  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
      </Routes>
    </Suspense>
  );
}
```

### 2. Memoization

```jsx
import { useMemo, useCallback } from 'react';

function ExpensiveComponent({ data }) {
  // 緩存計算結果
  const processedData = useMemo(() => {
    return data.map(item => heavyProcessing(item));
  }, [data]);

  // 緩存函式
  const handleClick = useCallback((id) => {
    console.log('Clicked:', id);
  }, []);

  return <div>{/* ... */}</div>;
}
```

### 3. 虛擬化長列表

```jsx
// 使用 react-window 或 react-virtualized
import { FixedSizeList } from 'react-window';

function LargeList({ items }) {
  const Row = ({ index, style }) => (
    <div style={style}>{items[index]}</div>
  );

  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

---

## 🛡️ 安全性最佳實踐

### 1. XSS 防護

```jsx
// ✅ React 自動跳脫
<div>{userInput}</div>

// ❌ 危險：直接插入 HTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// ✅ 使用 DOMPurify 清理
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />
```

### 2. CSRF 防護

```javascript
// 使用 Bearer Token，不依賴 Cookies
fetch(`${API_URL}/api/endpoint`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('google_token')}`
  }
});
```

### 3. 敏感資料處理

```javascript
// ❌ 不要在前端儲存敏感資料
localStorage.setItem('password', userPassword);  // 絕不這樣做

// ✅ 僅儲存 Token
localStorage.setItem('google_token', token);

// ❌ 不要在 console.log 輸出敏感資料
console.log('User password:', password);

// ✅ 移除生產環境的 console.log
if (import.meta.env.MODE === 'development') {
  console.log('Debug info:', data);
}
```

---

## 📱 響應式設計

### 1. CSS Media Queries

```css
/* Mobile First */
.container {
  padding: 10px;
}

/* Tablet */
@media (min-width: 768px) {
  .container {
    padding: 20px;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .container {
    padding: 30px;
    max-width: 1200px;
    margin: 0 auto;
  }
}
```

### 2. 彈性佈局

```css
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}
```

---

## 🧪 測試策略

### 1. 單元測試 (Vitest)

```jsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import KPICard from './KPICard';

describe('KPICard', () => {
  it('renders title and value', () => {
    render(<KPICard title="花費" value="$1,000" />);
    
    expect(screen.getByText('花費')).toBeInTheDocument();
    expect(screen.getByText('$1,000')).toBeInTheDocument();
  });
});
```

### 2. 整合測試

```jsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('saves settings on submit', async () => {
  render(<SettingsModal isOpen={true} onSave={mockOnSave} />);
  
  await userEvent.type(screen.getByPlaceholderText('App ID'), '12345');
  await userEvent.click(screen.getByText('儲存'));
  
  await waitFor(() => {
    expect(mockOnSave).toHaveBeenCalled();
  });
});
```

---

## 📝 開發規範

### 1. 命名規範

```jsx
// 元件：PascalCase
function UserProfile() {}

// 函式：camelCase
function handleSubmit() {}

// 常數：UPPER_SNAKE_CASE
const API_URL = 'http://localhost:8000';

// CSS 類別：kebab-case
<div className="user-profile-card" />
```

### 2. 檔案組織

```
✅ 一個檔案一個元件
✅ 元件檔名與元件名稱一致
✅ 相關元件放在同一資料夾

pages/
  Dashboard/
    Dashboard.jsx
    Dashboard.css
    DashboardKPI.jsx
    DashboardChart.jsx
```

### 3. Props 驗證

```jsx
import PropTypes from 'prop-types';

KPICard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number
  ]).isRequired,
  change: PropTypes.number,
  trend: PropTypes.oneOf(['up', 'down', 'neutral'])
};

KPICard.defaultProps = {
  change: 0,
  trend: 'neutral'
};
```

---

## 🔧 建置與部署

### 開發環境

```bash
npm run dev
```

### 生產建置

```bash
npm run build

# 輸出到 dist/ 資料夾
# 包含：
# - 最小化的 JS/CSS
# - 靜態資源
# - index.html
```

### 環境變數 (`.env`)

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_client_id_here
```

**使用方式：**
```javascript
const apiUrl = import.meta.env.VITE_API_URL;
```

---

## 📚 參考資源

- [React 官方文件](https://react.dev/)
- [Vite 文件](https://vitejs.dev/)
- [React Router 文件](https://reactrouter.com/)
- [Recharts 文件](https://recharts.org/)

---

**文件版本：** 2.0  
**最後更新：** 2026-01-15
