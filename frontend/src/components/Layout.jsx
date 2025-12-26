import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { TeamService } from '../services/teamService';

const Layout = () => {
    // Global State
    const [accounts, setAccounts] = useState([]);
    const [selectedAccountId, setSelectedAccountId] = useState('');

    // Team State
    const [teams, setTeams] = useState([]);
    const [selectedTeamId, setSelectedTeamId] = useState('');
    const [visibleError, setVisibleError] = useState('');

    const [user, setUser] = useState({ name: 'User', avatar: '', access_token: '' });
    const [language, setLanguage] = useState('zh');
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    // Mobile Detection
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

    useEffect(() => {
        const handleResize = () => {
            const mobile = window.innerWidth < 768;
            setIsMobile(mobile);
            // Auto-collapse on mobile if resizing down
            if (mobile && !isSidebarCollapsed) {
                setIsSidebarCollapsed(true);
            }
        };

        window.addEventListener('resize', handleResize);
        handleResize(); // Init

        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // Fetch Teams Logic
    useEffect(() => {
        const fetchTeams = async () => {
            try {
                const myTeams = await TeamService.getMyTeams();
                setTeams(myTeams);

                // Restore selection or default to Personal (empty string)
                const savedTeamId = localStorage.getItem('selected_team_id');
                if (savedTeamId && myTeams.find(t => t.id === savedTeamId)) {
                    setSelectedTeamId(savedTeamId);
                }
            } catch (err) {
                console.error("Failed to fetch teams", err);
            }
        };
        fetchTeams();
    }, [user.access_token]); // Re-fetch when user/token changes

    // Persist Team Selection
    useEffect(() => {
        if (selectedTeamId) {
            localStorage.setItem('selected_team_id', selectedTeamId);
        } else {
            localStorage.removeItem('selected_team_id');
        }
    }, [selectedTeamId]);

    // Fetch Accounts Logic (Moved from Dashboard)
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
            const headers = {
                'Authorization': `Bearer ${token}`
            };
            if (selectedTeamId) {
                headers['X-Team-ID'] = selectedTeamId;
            }

            const response = await fetch(`${apiUrl}/api/ad-accounts`, {
                headers: headers
            });

            if (!response.ok) {
                if (response.status === 401) {
                    console.warn("Token expired or invalid in Layout, logging out...");
                    handleLogout();
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const accList = await response.json();

            if (Array.isArray(accList)) {
                setAccounts(accList);
                if (accList.length > 0) {
                    // Reset selection on account list refresh
                    setSelectedAccountId(accList[0].id);
                } else {
                    setSelectedAccountId('');
                }
            }
        } catch (err) {
            console.error(`Failed to fetch accounts (Retries left: ${retries})`, err);
            setVisibleError(`Account Fetch Error: ${err.message}`); // Show error to user
            if (retries > 0) {
                setTimeout(() => fetchAccounts(retries - 1), 1500);
            }
        }
    };

    useEffect(() => {

        fetchAccounts();
    }, [selectedTeamId, user.access_token]); // Re-fetch on Team Change or Token Change

    // Fetch Real User Profile (Backend)
    useEffect(() => {
        if (user.access_token) {
            const fetchUserProfile = async () => {
                try {
                    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                    const response = await fetch(`${apiUrl}/api/users/me`, {
                        headers: { 'Authorization': `Bearer ${user.access_token}` }
                    });
                    if (response.ok) {
                        const profile = await response.json();
                        // Update user with backend data (role, is_super_admin)
                        setUser(prev => ({ ...prev, ...profile }));
                    } else {
                        setVisibleError(`Fetch Profile Failed: ${response.status}`);
                    }
                } catch (err) {
                    console.error("Failed to fetch user profile", err);
                    setVisibleError(`Fetch Profile Error: ${err.message}`);
                }
            };
            fetchUserProfile();
        }
    }, [user.access_token]);

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
                isMobile={isMobile}
                selectedTeamId={selectedTeamId}
                selectedTeamName={teams.find(t => t.id === selectedTeamId)?.name}
                // New Props for Switcher
                teams={teams}
                setSelectedTeamId={setSelectedTeamId}
                onRefresh={() => fetchAccounts()} // Pass fetch trigger
            />
            <div className="main-content" style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                marginLeft: isMobile ? '0' : (isSidebarCollapsed ? '80px' : '240px'),
                transition: 'margin-left 0.3s ease',
                minWidth: 0,
                maxWidth: isMobile ? '100vw' : 'calc(100vw - ' + (isSidebarCollapsed ? '80px' : '240px') + ')',
                overflow: 'hidden'
            }}>
                <Header
                    language={language}
                    setLanguage={setLanguage}
                    accounts={accounts}
                    selectedAccountId={selectedAccountId}
                    setSelectedAccountId={setSelectedAccountId}
                    // Team Props
                    teams={teams}
                    selectedTeamId={selectedTeamId}
                    setSelectedTeamId={setSelectedTeamId}

                    onGenerateReport={() => { }}
                    isSidebarCollapsed={isSidebarCollapsed}
                    setIsSidebarCollapsed={setIsSidebarCollapsed}
                    isMobile={isMobile}
                    onLogout={handleLogout}
                    user={user}
                />

                <div style={{ padding: '0', flex: 1, marginTop: '70px', minWidth: 0, width: '100%', maxWidth: '100%', overflowX: 'auto', boxSizing: 'border-box' }}>
                    <Outlet context={{ selectedAccountId, user, accounts, language, isSidebarCollapsed, isMobile, teams, setTeams, selectedTeamId, setSelectedTeamId }} />
                </div>

            </div>
        </div>
    );
};

export default Layout;
