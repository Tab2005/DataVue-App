import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import UserManagement from './pages/UserManagement';
import InvitePage from './pages/InvitePage';
import AdminDashboard from './pages/AdminDashboard';
import TeamSettings from './pages/TeamSettings';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  // 優先從環境變數讀取 Client ID，如果沒有則使用空字串 (避免報錯，但功能會失效)
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  return (
    <ErrorBoundary>
      <GoogleOAuthProvider clientId={clientId}>
        <Router>
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
            </Route>
          </Routes>
        </Router>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}

export default App;

