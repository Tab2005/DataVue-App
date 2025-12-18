import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';

// Eager-loaded components (needed immediately)
import Login from './pages/Login';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import PageLoading from './components/PageLoading';

// Lazy-loaded pages (loaded on demand)
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const TeamSettings = lazy(() => import('./pages/TeamSettings'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const InvitePage = lazy(() => import('./pages/InvitePage'));
const UserManagement = lazy(() => import('./pages/UserManagement'));
const MetricsManager = lazy(() => import('./pages/MetricsManager'));

function App() {
  // 優先從環境變數讀取 Client ID，如果沒有則使用空字串 (避免報錯，但功能會失效)
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

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
                  <ErrorBoundary>
                    <Dashboard />
                  </ErrorBoundary>
                } />
                <Route path="/analytics" element={
                  <ErrorBoundary>
                    <Analytics />
                  </ErrorBoundary>
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
                  <ErrorBoundary>
                    <MetricsManager />
                  </ErrorBoundary>
                } />
              </Route>
            </Routes>
          </Suspense>
        </Router>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}

export default App;
