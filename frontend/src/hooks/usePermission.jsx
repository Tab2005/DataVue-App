/**
 * 權限管理 Hooks
 * 用於前端權限檢查和路由保護
 */
import { useState, useEffect, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * 取得 API 請求 headers
 */
const getAuthHeaders = () => {
    const token = localStorage.getItem('google_token');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
};

/**
 * useModuleAccess Hook
 * 檢查使用者是否可存取指定模組
 * 
 * @param {string} moduleKey - 模組 key (如 'fb_ads', 'gsc', 'ga4')
 * @param {string|null} teamId - 團隊 ID (null = 個人工作區)
 * @returns {{ hasAccess: boolean, loading: boolean, error: string|null }}
 * 
 * @example
 * const { hasAccess, loading } = useModuleAccess('gsc');
 * if (!hasAccess) return <AccessDenied />;
 */
export const useModuleAccess = (moduleKey, teamId = null) => {
    const [hasAccess, setHasAccess] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const checkAccess = async () => {
            if (!moduleKey) {
                setLoading(false);
                return;
            }

            try {
                const url = teamId
                    ? `${API_URL}/api/permissions/me/module/${moduleKey}?team_id=${teamId}`
                    : `${API_URL}/api/permissions/me/module/${moduleKey}`;

                const res = await fetch(url, { headers: getAuthHeaders() });

                if (res.ok) {
                    const data = await res.json();
                    setHasAccess(data.has_access);
                } else {
                    setHasAccess(false);
                    setError('Failed to check module access');
                }
            } catch (err) {
                console.error('Module access check failed:', err);
                setHasAccess(false);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        checkAccess();
    }, [moduleKey, teamId]);

    return { hasAccess, loading, error };
};

/**
 * usePermission Hook
 * 檢查使用者是否有指定權限
 * 
 * @param {string} permissionKey - 權限 key (如 'fb_ads:analytics:view')
 * @param {string|null} teamId - 團隊 ID
 * @returns {{ hasPermission: boolean, loading: boolean, error: string|null }}
 * 
 * @example
 * const { hasPermission } = usePermission('fb_ads:ai:use');
 * if (!hasPermission) return <UpgradePrompt />;
 */
export const usePermission = (permissionKey, teamId = null) => {
    const [hasPermission, setHasPermission] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const checkPermission = async () => {
            if (!permissionKey) {
                setLoading(false);
                return;
            }

            try {
                const url = teamId
                    ? `${API_URL}/api/permissions/me/check/${permissionKey}?team_id=${teamId}`
                    : `${API_URL}/api/permissions/me/check/${permissionKey}`;

                const res = await fetch(url, { headers: getAuthHeaders() });

                if (res.ok) {
                    const data = await res.json();
                    setHasPermission(data.has_permission);
                } else {
                    setHasPermission(false);
                    setError('Failed to check permission');
                }
            } catch (err) {
                console.error('Permission check failed:', err);
                setHasPermission(false);
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        checkPermission();
    }, [permissionKey, teamId]);

    return { hasPermission, loading, error };
};

/**
 * useUserModules Hook
 * 取得使用者可存取的所有模組列表
 * 
 * @param {string|null} teamId - 團隊 ID
 * @returns {{ modules: string[], loading: boolean, error: string|null, refetch: Function }}
 * 
 * @example
 * const { modules } = useUserModules();
 * // modules = ['fb_ads', 'gsc']
 */
export const useUserModules = (teamId = null) => {
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchModules = useCallback(async () => {
        setLoading(true);
        try {
            const url = teamId
                ? `${API_URL}/api/permissions/me/modules?team_id=${teamId}`
                : `${API_URL}/api/permissions/me/modules`;

            const res = await fetch(url, { headers: getAuthHeaders() });

            if (res.ok) {
                const data = await res.json();
                setModules(data.modules || []);
            } else {
                setModules([]);
                setError('Failed to fetch modules');
            }
        } catch (err) {
            console.error('Fetch modules failed:', err);
            setModules([]);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId]);

    useEffect(() => {
        fetchModules();
    }, [fetchModules]);

    return { modules, loading, error, refetch: fetchModules };
};

/**
 * useUserPermissions Hook
 * 取得使用者的所有權限列表
 * 
 * @param {string|null} teamId - 團隊 ID
 * @returns {{ permissions: string[], loading: boolean, error: string|null, refetch: Function }}
 */
export const useUserPermissions = (teamId = null) => {
    const [permissions, setPermissions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchPermissions = useCallback(async () => {
        setLoading(true);
        try {
            const url = teamId
                ? `${API_URL}/api/permissions/me/permissions?team_id=${teamId}`
                : `${API_URL}/api/permissions/me/permissions`;

            const res = await fetch(url, { headers: getAuthHeaders() });

            if (res.ok) {
                const data = await res.json();
                setPermissions(data.permissions || []);
            } else {
                setPermissions([]);
                setError('Failed to fetch permissions');
            }
        } catch (err) {
            console.error('Fetch permissions failed:', err);
            setPermissions([]);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [teamId]);

    useEffect(() => {
        fetchPermissions();
    }, [fetchPermissions]);

    return { permissions, loading, error, refetch: fetchPermissions };
};

/**
 * ProtectedModule Component
 * 模組存取保護組件
 * 
 * @example
 * <ProtectedModule module="gsc" fallback={<UpgradePrompt />}>
 *   <GSCDashboard />
 * </ProtectedModule>
 */
export const ProtectedModule = ({ module, teamId = null, fallback = null, children }) => {
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

/**
 * ProtectedPermission Component
 * 權限保護組件
 * 
 * @example
 * <ProtectedPermission permission="fb_ads:ai:use" fallback={<UpgradeButton />}>
 *   <AIAnalystButton />
 * </ProtectedPermission>
 */
export const ProtectedPermission = ({ permission, teamId = null, fallback = null, children }) => {
    const { hasPermission, loading } = usePermission(permission, teamId);

    if (loading) return null; // 不顯示 loading 狀態

    if (!hasPermission) {
        return fallback || null; // 沒有權限時隱藏或顯示 fallback
    }

    return children;
};

export default {
    useModuleAccess,
    usePermission,
    useUserModules,
    useUserPermissions,
    ProtectedModule,
    ProtectedPermission
};
