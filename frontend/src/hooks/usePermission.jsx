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
const REQUEST_TIMEOUT_MS = 10000;

const readSelectedTeamId = () => localStorage.getItem(SELECTED_TEAM_STORAGE_KEY) || null;
const buildModulesCacheKey = (teamId) => `datavue:user-modules:${teamId || 'personal'}`;
const buildModuleAccessCacheKey = (moduleKey, teamId) => `datavue:module-access:${moduleKey}:${teamId || 'personal'}`;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// 每次嘗試都掛 timeout：若沒有這個保護，網路卡住時 fetch() 可能永遠不 resolve/reject，
// 呼叫端的 loading 狀態就會永久卡住轉圈（docs/24 Wave 3.2）。
const fetchWithRetry = async (url, options, retries = RETRY_ATTEMPTS) => {
    let lastError = null;

    for (let attempt = 0; attempt < retries; attempt += 1) {
        try {
            const res = await fetch(url, { ...options, signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS) });
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
    const selectedTeamId = useSelectedTeamId();
    const resolvedTeamId = teamId === undefined ? selectedTeamId : teamId;
    const cacheKey = buildModuleAccessCacheKey(moduleKey, resolvedTeamId);

    // 先讀 sessionStorage 快取立即渲染，背景 revalidate 更新（docs/24 Wave 3.1）：
    // 匯入/評分批次跑很久時，權限 API 本身不會再被卡住（docs/24 Wave 1/2 已解決），
    // 但 request 仍需要一次來回；有快取時就不要讓 ProtectedModule 又轉圈一次。
    const [hasAccess, setHasAccess] = useState(() => {
        try {
            const cached = sessionStorage.getItem(cacheKey);
            return cached ? JSON.parse(cached).hasAccess : false;
        } catch {
            return false;
        }
    });
    const [loading, setLoading] = useState(() => {
        try {
            return sessionStorage.getItem(cacheKey) === null;
        } catch {
            return true;
        }
    });
    const [error, setError] = useState(null);

    useEffect(() => {
        let cancelled = false;

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
                if (cancelled) return;

                if (res.ok) {
                    const data = await res.json();
                    setHasAccess(data.has_access);
                    setError(null);
                    try {
                        sessionStorage.setItem(cacheKey, JSON.stringify({ hasAccess: data.has_access }));
                    } catch {
                        // sessionStorage 滿了或被瀏覽器封鎖時忽略，不影響本次請求結果
                    }
                } else {
                    setError('Failed to check module access');
                }
            } catch (err) {
                if (cancelled) return;
                console.error('Module access check failed:', err);
                setError(err.message);
            } finally {
                if (!cancelled) setLoading(false);
            }
        };

        checkAccess();
        return () => {
            cancelled = true;
        };
    }, [moduleKey, resolvedTeamId, cacheKey]);

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
    const { hasAccess, loading, error } = useModuleAccess(module, teamId);

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

    // 逾時/請求失敗且沒有快取可用時，跟「沒有權限」分開顯示，避免使用者誤以為
    // 真的被拒絕存取（docs/24 Wave 3.2）；有快取的話 hasAccess 已經是快取值，
    // 不會走到這裡。
    if (error && !hasAccess) {
        return (
            <div style={{
                textAlign: 'center',
                padding: '48px',
                backgroundColor: 'rgba(234, 179, 8, 0.1)',
                borderRadius: '12px',
                border: '1px solid rgba(234, 179, 8, 0.2)'
            }}>
                <h3 style={{ color: '#eab308', marginBottom: '8px' }}>⚠️ 連線逾時</h3>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '12px' }}>
                    無法確認模組權限，請檢查網路連線後重新整理頁面。
                </p>
                <button
                    type="button"
                    onClick={() => window.location.reload()}
                    style={{
                        padding: '8px 16px',
                        borderRadius: '8px',
                        border: '1px solid var(--border-color, #ccc)',
                        background: 'transparent',
                        color: 'var(--text-secondary)',
                        cursor: 'pointer'
                    }}
                >
                    重新整理
                </button>
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