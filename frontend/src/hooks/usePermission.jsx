/**
 * 權限管理 Hooks
 * 用於前端權限檢查和路由保護
 */
import { useState, useEffect, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SELECTED_TEAM_STORAGE_KEY = 'selected_team_id';
const SELECTED_TEAM_EVENT = 'datavue:selected-team-changed';
const RETRYABLE_STATUSES = new Set([502, 503, 504]);
const RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 1200;

const readSelectedTeamId = () => localStorage.getItem(SELECTED_TEAM_STORAGE_KEY) || null;
const buildModulesCacheKey = (teamId) => `datavue:user-modules:${teamId || 'personal'}`;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const fetchWithRetry = async (url, options, retries = RETRY_ATTEMPTS) => {
    let lastError = null;

    for (let attempt = 0; attempt < retries; attempt += 1) {
        try {
            const res = await fetch(url, options);
            if (RETRYABLE_STATUSES.has(res.status) && attempt < retries - 1) {
                await sleep(RETRY_DELAY_MS * (attempt + 1));
                continue;
            }
            return res;
        } catch (err) {
            lastError = err;
            if (attempt < retries - 1) {
                await sleep(RETRY_DELAY_MS * (attempt + 1));
                continue;
            }
        }
    }

    throw lastError || new Error('Request failed');
};

const getAuthHeaders = () => {
    const token = localStorage.getItem('google_token');
    return {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
};

export const useSelectedTeamId = () => {
    const [selectedTeamId, setSelectedTeamId] = useState(readSelectedTeamId);

    useEffect(() => {
        const handleStorageChange = (event) => {
            if (!event.key || event.key === SELECTED_TEAM_STORAGE_KEY) {
                setSelectedTeamId(readSelectedTeamId());
            }
        };

        const handleSelectedTeamChange = (event) => {
            const nextTeamId = event?.detail?.teamId;
            setSelectedTeamId(nextTeamId || null);
        };

        window.addEventListener('storage', handleStorageChange);
        window.addEventListener(SELECTED_TEAM_EVENT, handleSelectedTeamChange);

        return () => {
            window.removeEventListener('storage', handleStorageChange);
            window.removeEventListener(SELECTED_TEAM_EVENT, handleSelectedTeamChange);
        };
    }, []);

    return selectedTeamId;
};

export const useModuleAccess = (moduleKey, teamId) => {
    const [hasAccess, setHasAccess] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const selectedTeamId = useSelectedTeamId();
    const resolvedTeamId = teamId === undefined ? selectedTeamId : teamId;

    useEffect(() => {
        const checkAccess = async () => {
            if (!moduleKey) {
                setLoading(false);
                return;
            }

            try {
                const url = resolvedTeamId
                    ? `${API_URL}/api/permissions/me/module/${moduleKey}?team_id=${resolvedTeamId}`
                    : `${API_URL}/api/permissions/me/module/${moduleKey}`;

                const res = await fetchWithRetry(url, { headers: getAuthHeaders() });

                if (res.ok) {
                    const data = await res.json();
                    setHasAccess(data.has_access);
                    setError(null);
                } else {
                    setError('Failed to check module access');
                }
            } catch (err) {
                console.error('Module access check failed:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        checkAccess();
    }, [moduleKey, resolvedTeamId]);

    return { hasAccess, loading, error };
};

export const usePermission = (permissionKey, teamId) => {
    const [hasPermission, setHasPermission] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const selectedTeamId = useSelectedTeamId();
    const resolvedTeamId = teamId === undefined ? selectedTeamId : teamId;

    useEffect(() => {
        const checkPermission = async () => {
            if (!permissionKey) {
                setLoading(false);
                return;
            }

            try {
                const url = resolvedTeamId
                    ? `${API_URL}/api/permissions/me/check/${permissionKey}?team_id=${resolvedTeamId}`
                    : `${API_URL}/api/permissions/me/check/${permissionKey}`;

                const res = await fetchWithRetry(url, { headers: getAuthHeaders() });

                if (res.ok) {
                    const data = await res.json();
                    setHasPermission(data.has_permission);
                    setError(null);
                } else {
                    setError('Failed to check permission');
                }
            } catch (err) {
                console.error('Permission check failed:', err);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        checkPermission();
    }, [permissionKey, resolvedTeamId]);

    return { hasPermission, loading, error };
};

export const useUserModules = (teamId) => {
    const selectedTeamId = useSelectedTeamId();
    const resolvedTeamId = teamId === undefined ? selectedTeamId : teamId;
    const cacheKey = buildModulesCacheKey(resolvedTeamId);
    const [modules, setModules] = useState(() => {
        try {
            const cached = sessionStorage.getItem(cacheKey);
            return cached ? JSON.parse(cached) : [];
        } catch {
            return [];
        }
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchModules = useCallback(async () => {
        setLoading(true);
        try {
            const url = resolvedTeamId
                ? `${API_URL}/api/permissions/me/modules?team_id=${resolvedTeamId}`
                : `${API_URL}/api/permissions/me/modules`;

            const res = await fetchWithRetry(url, { headers: getAuthHeaders() });

            if (res.ok) {
                const data = await res.json();
                const nextModules = data.modules || [];
                setModules(nextModules);
                sessionStorage.setItem(cacheKey, JSON.stringify(nextModules));
                setError(null);
            } else {
                setError('Failed to fetch modules');
            }
        } catch (err) {
            console.error('Fetch modules failed:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [cacheKey, resolvedTeamId]);

    useEffect(() => {
        fetchModules();
    }, [fetchModules]);

    return { modules, loading, error, refetch: fetchModules };
};

export const useUserPermissions = (teamId) => {
    const [permissions, setPermissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const selectedTeamId = useSelectedTeamId();
    const resolvedTeamId = teamId === undefined ? selectedTeamId : teamId;

    const fetchPermissions = useCallback(async () => {
        setLoading(true);
        try {
            const url = resolvedTeamId
                ? `${API_URL}/api/permissions/me/permissions?team_id=${resolvedTeamId}`
                : `${API_URL}/api/permissions/me/permissions`;

            const res = await fetchWithRetry(url, { headers: getAuthHeaders() });

            if (res.ok) {
                const data = await res.json();
                setPermissions(data.permissions || []);
                setError(null);
            } else {
                setError('Failed to fetch permissions');
            }
        } catch (err) {
            console.error('Fetch permissions failed:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [resolvedTeamId]);

    useEffect(() => {
        fetchPermissions();
    }, [fetchPermissions]);

    return { permissions, loading, error, refetch: fetchPermissions };
};

export const ProtectedModule = ({ module, teamId, fallback = null, children }) => {
    const { hasAccess, loading } = useModuleAccess(module, teamId);

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '48px',
                color: 'var(--text-secondary)'
            }}>
                載入中...
            </div>
        );
    }

    if (!hasAccess) {
        return fallback || (
            <div style={{
                textAlign: 'center',
                padding: '48px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderRadius: '12px',
                border: '1px solid rgba(239, 68, 68, 0.2)'
            }}>
                <h3 style={{ color: '#ef4444', marginBottom: '8px' }}>🔒 存取受限</h3>
                <p style={{ color: 'var(--text-secondary)' }}>
                    您沒有此模組的存取權限。請聯繫管理員或升級方案。
                </p>
            </div>
        );
    }

    return children;
};

export const ProtectedPermission = ({ permission, teamId, fallback = null, children }) => {
    const { hasPermission, loading } = usePermission(permission, teamId);

    if (loading) return null;
    if (!hasPermission) return fallback || null;

    return children;
};

export default {
    useModuleAccess,
    usePermission,
    useSelectedTeamId,
    useUserModules,
    useUserPermissions,
    ProtectedModule,
    ProtectedPermission
};