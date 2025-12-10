import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout = () => {
    // Global State
    const [accounts, setAccounts] = useState([]);
    const [selectedAccountId, setSelectedAccountId] = useState('');
    const [user, setUser] = useState({ name: 'User', avatar: '', access_token: '' });
    const [language, setLanguage] = useState('zh');
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    // Fetch Accounts Logic (Moved from Dashboard)
    useEffect(() => {
        const fetchAccounts = async (retries = 3) => {
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const token = localStorage.getItem('google_token');
            const userInfoStr = localStorage.getItem('user_info');

            if (token) {
                let userData = { access_token: token };
                if (userInfoStr) {
                    try {
                        const parsedUser = JSON.parse(userInfoStr);
                        userData = {
                            ...userData,
                            name: parsedUser.name || 'User',
                            email: parsedUser.email || '',
                            avatar: parsedUser.picture || parsedUser.avatar || ''
                        };
                    } catch (e) {
                        console.error("Failed to parse user info", e);
                    }
                }
                setUser(prev => ({ ...prev, ...userData }));
            }

            try {
                const response = await fetch(`${apiUrl}/api/ad-accounts`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const accList = await response.json();

                if (Array.isArray(accList)) {
                    setAccounts(accList);
                    if (accList.length > 0) {
                        // Maintain selection if exists, else default to first
                        setSelectedAccountId(prev => prev || accList[0].id);
                    }
                }
            } catch (err) {
                console.error(`Failed to fetch accounts (Retries left: ${retries})`, err);
                if (retries > 0) {
                    setTimeout(() => fetchAccounts(retries - 1), 1500);
                }
            }
        };

        fetchAccounts();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('google_token');
        localStorage.removeItem('selected_account_id');
        // Optional: clear user info if stored elsewhere
        window.location.href = '/login';
    };

    return (
        <div className="layout-container" style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-gradient)' }}>
            <Sidebar
                language={language}
                isCollapsed={isSidebarCollapsed}
                setIsCollapsed={setIsSidebarCollapsed}
            />
            <div className="main-content" style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                marginLeft: isSidebarCollapsed ? '80px' : '240px',
                transition: 'margin-left 0.3s ease'
            }}>
                <Header
                    language={language}
                    setLanguage={setLanguage}
                    accounts={accounts}
                    selectedAccountId={selectedAccountId}
                    setSelectedAccountId={setSelectedAccountId}
                    onGenerateReport={() => { }}
                    isSidebarCollapsed={isSidebarCollapsed}
                    onLogout={handleLogout}
                    user={user}
                />

                <div style={{ padding: '0', flex: 1, marginTop: '70px' }}>
                    <Outlet context={{ selectedAccountId, user, accounts, language }} />
                </div>
            </div>
        </div>
    );
};

export default Layout;
