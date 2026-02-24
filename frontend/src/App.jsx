import React, { Suspense, lazy, useCallback, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';

// Eager-loaded components (needed immediately)
import Login from './pages/Login';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import PageLoading from './components/PageLoading';
import { ProtectedModule, useTokenRefresh } from './hooks';
import { getAuthToken, isTokenExpired } from './utils/auth';

// Lazy-loaded pages (loaded on demand)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const TeamSettings = lazy(() => import('./pages/TeamSettings'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const InvitePage = lazy(() => import('./pages/InvitePage'));
const UserManagement = lazy(() => import('./pages/UserManagement'));
const MetricsManager = lazy(() => import('./pages/MetricsManager'));
const SearchConsole = lazy(() => import('./pages/SearchConsole'));
const GA4Analytics = lazy(() => import('./pages/GA4Analytics'));

/**
 * 內層 App 元件（需在 Router 內部才能使用 useNavigate）
 */
function AppInner() {
  const navigate = useNavigate();

  const handleTokenExpired = useCallback(() => {
    alert('您的登入已過期，請重新登入');
    navigate('/login');
  }, [navigate]);

  // 啟動 Token 過期自動監控（每分鐘檢查一次）
  useTokenRefresh(handleTokenExpired);

  // 初始載入時立即檢查 Token
  useEffect(() => {
    const token = getAuthToken();
    if (token && isTokenExpired(token)) {
      handleTokenExpired();
    }
  }, [handleTokenExpired]);

  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/invite/:code" element={<InvitePage />} />
              <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
                <Route path="/" element={
                  <ProtectedModule module="fb_ads">
                    <ErrorBoundary>
                      <Dashboard />
                    </ErrorBoundary>
                  </ProtectedModule>
                } />
                <Route path="/analytics" element={
                  <ProtectedModule module="fb_ads">
                    <ErrorBoundary>
                      <Analytics />
                    </ErrorBoundary>
                  </ProtectedModule>
                } />
                <Route path="/settings/team" element={
                  <ErrorBoundary>
                    <TeamSettings />
                  </ErrorBoundary>
                } />
                <Route path="/admin" element={
                  <ErrorBoundary>
                    <AdminDashboard />
                  </ErrorBoundary>
                } />
                <Route path="/metrics" element={
                  <ProtectedModule module="fb_ads">
                    <ErrorBoundary>
                      <MetricsManager />
                    </ErrorBoundary>
                  </ProtectedModule>
                } />
                <Route path="/gsc" element={
                  <ProtectedModule module="gsc">
                    <ErrorBoundary>
                      <SearchConsole />
                    </ErrorBoundary>
                  </ProtectedModule>
                } />
                <Route path="/ga4" element={
                  <ProtectedModule module="ga4">
                    <ErrorBoundary>
                      <GA4Analytics />
                    </ErrorBoundary>
                  </ProtectedModule>
                } />
              </Route>
            </Routes>
    </Suspense>
  );
}

function App() {
  // 優先從環境變數讀取 Client ID，如果沒有則使用空字串（避免報錯，但功能會失效）
  const clientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID || '').trim();

  return (
    <ErrorBoundary>
      <GoogleOAuthProvider clientId={clientId}>
        <Router>
          <AppInner />
        </Router>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}

export default App;
