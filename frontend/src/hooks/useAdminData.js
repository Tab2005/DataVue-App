import { useEffect, useMemo, useState } from 'react';
import { AdminService } from '../services/adminService';

const itemsPerPage = 10;

const translations = {
    en: {
        title: 'Super Admin Dashboard',
        subtitle: 'Platform-wide management and statistics',
        loading: 'Loading Admin Dashboard...',
        retry: 'Retry',
        access_error: 'Access Error',
        total_users: 'Total Users',
        total_teams: 'Total Teams',
        search_placeholder: 'Search by name or ID...',
        prev: 'Previous',
        next: 'Next',
        page: 'Page',
        section_users: 'All Users',
        desc_users: 'Manage all registered users on the platform',
        th_name: 'Name',
        th_email: 'Email',
        th_role: 'Role',
        th_joined: 'Joined',
        th_actions: 'Actions',
        no_users: 'No users found matching your search.',
        section_teams: 'All Teams',
        desc_teams: 'Overview of all active teams and their owners',
        th_team_name: 'Team Name',
        th_owner_id: 'Owner ID',
        th_created_at: 'Created At',
        th_members: 'Members',
        no_teams: 'No teams found matching your search.',
        confirm_delete: 'Are you sure? This action is irreversible.',
        role_super: 'SUPER ADMIN',
        role_user: 'USER',
        delete_title: 'Force Delete User'
    },
    zh: {
        title: '超級管理員後台',
        subtitle: '平台全域管理與數據統計',
        loading: '載入管理後台...',
        retry: '重試',
        access_error: '存取錯誤',
        total_users: '總使用者數',
        total_teams: '總團隊數',
        search_placeholder: '搜尋名稱或 ID...',
        prev: '上一頁',
        next: '下一頁',
        page: '頁次',
        section_users: '所有使用者',
        desc_users: '管理平台所有註冊用戶',
        th_name: '姓名',
        th_email: 'Email',
        th_role: '角色',
        th_joined: '加入時間',
        th_actions: '操作',
        no_users: '找不到符合搜尋條件的使用者。',
        section_teams: '所有團隊',
        desc_teams: '瀏覽所有活躍團隊與擁有者',
        th_team_name: '團隊名稱',
        th_owner_id: '擁有者 ID',
        th_created_at: '建立時間',
        th_members: '成員數',
        no_teams: '找不到符合搜尋條件的團隊。',
        confirm_delete: '您確定嗎？此操作無法復原。',
        role_super: '超級管理員',
        role_user: '一般用戶',
        delete_title: '強制刪除用戶'
    }
};

const paginate = (items, page) => {
    return items.slice((page - 1) * itemsPerPage, page * itemsPerPage);
};

const useAdminData = (language) => {
    const t = translations[language] || translations.zh;
    const [stats, setStats] = useState({ user_count: 0, team_count: 0 });
    const [users, setUsers] = useState([]);
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [userSearch, setUserSearch] = useState('');
    const [userPage, setUserPage] = useState(1);
    const [teamSearch, setTeamSearch] = useState('');
    const [teamPage, setTeamPage] = useState(1);
    const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const [statsData, usersData, teamsData] = await Promise.all([
                AdminService.getStats(),
                AdminService.getAllUsers(),
                AdminService.getAllTeams()
            ]);
            setStats(statsData || { user_count: 0, team_count: 0 });
            setUsers(Array.isArray(usersData) ? usersData : []);
            setTeams(Array.isArray(teamsData) ? teamsData : []);
        } catch (err) {
            console.error('Dashboard Load Error:', err);
            setError(err instanceof Error ? err.message : String(err));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    useEffect(() => {
        setUserPage(1);
    }, [userSearch]);

    useEffect(() => {
        setTeamPage(1);
    }, [teamSearch]);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth < 768);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleDeleteUser = async (userId) => {
        if (!window.confirm(t.confirm_delete)) return;
        try {
            await AdminService.deleteUser(userId);
            setUsers(prev => prev.filter(u => u.id !== userId));
            setStats(prev => ({ ...prev, user_count: prev.user_count - 1 }));
        } catch (err) {
            alert(err instanceof Error ? err.message : String(err));
        }
    };

    const userData = useMemo(() => {
        const filtered = users.filter(u =>
            (u.name && u.name.toLowerCase().includes(userSearch.toLowerCase())) ||
            (u.email && u.email.toLowerCase().includes(userSearch.toLowerCase()))
        );
        const totalPages = Math.ceil(filtered.length / itemsPerPage);
        return {
            filtered,
            currentItems: paginate(filtered, userPage),
            totalPages
        };
    }, [users, userSearch, userPage]);

    const teamData = useMemo(() => {
        const filtered = teams.filter(tm =>
            (tm.name && tm.name.toLowerCase().includes(teamSearch.toLowerCase())) ||
            (tm.owner_id && tm.owner_id.toLowerCase().includes(teamSearch.toLowerCase()))
        );
        const totalPages = Math.ceil(filtered.length / itemsPerPage);
        return {
            filtered,
            currentItems: paginate(filtered, teamPage),
            totalPages
        };
    }, [teams, teamSearch, teamPage]);

    return {
        t,
        stats,
        loading,
        error,
        fetchData,
        isMobile,
        userSearch,
        setUserSearch,
        userPage,
        setUserPage,
        teamSearch,
        setTeamSearch,
        teamPage,
        setTeamPage,
        userData,
        teamData,
        handleDeleteUser
    };
};

export default useAdminData;
