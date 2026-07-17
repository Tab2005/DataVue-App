import { useCallback, useEffect, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const SAVED_VIEWS_KEY = 'metricslab_saved_views';
const MIGRATION_DONE_KEY = 'metricslab_migration_done';

const useSavedMetricViews = ({ user, selectedTeamId, language, selectedMetrics, setSelectedMetrics, txt }) => {
    const [savedViews, setSavedViews] = useState([]);
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [newViewName, setNewViewName] = useState('');
    const [saveMessage, setSaveMessage] = useState(null);
    const [saveToTeam, setSaveToTeam] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [editingView, setEditingView] = useState(null);
    const [editViewName, setEditViewName] = useState('');
    const [editViewMetrics, setEditViewMetrics] = useState(new Set());

    const getAuthToken = useCallback(() => {
        return localStorage.getItem('google_token');
    }, []);

    const showTemporaryMessage = useCallback((message) => {
        setSaveMessage(message);
        setTimeout(() => setSaveMessage(null), 2000);
    }, []);

    const fetchSavedViews = useCallback(async () => {
        if (!user?.id) return;
        setIsLoading(true);
        try {
            const params = new URLSearchParams({ user_id: user.id });
            if (selectedTeamId) params.append('team_id', selectedTeamId);

            const res = await fetch(`${API_BASE}/api/saved-views?${params}`, {
                headers: { Authorization: `Bearer ${getAuthToken()}` }
            });
            if (res.ok) {
                const data = await res.json();
                setSavedViews(data);
            }
        } catch (e) {
            console.error('Failed to fetch saved views:', e);
        } finally {
            setIsLoading(false);
        }
    }, [user?.id, selectedTeamId, getAuthToken]);

    const migrateLocalStorage = useCallback(async () => {
        if (!user?.id) return;
        const migrated = localStorage.getItem(MIGRATION_DONE_KEY);
        if (migrated) return;

        try {
            const localViews = localStorage.getItem(SAVED_VIEWS_KEY);
            if (localViews) {
                const views = JSON.parse(localViews);
                if (views.length > 0) {
                    const res = await fetch(`${API_BASE}/api/saved-views/migrate?user_id=${user.id}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            Authorization: `Bearer ${getAuthToken()}`
                        },
                        body: JSON.stringify({ views })
                    });
                    if (res.ok) {
                        console.log('Migration complete');
                    }
                }
            }
        } catch (e) {
            console.error('Migration failed:', e);
        } finally {
            localStorage.setItem(MIGRATION_DONE_KEY, 'true');
        }
    }, [user?.id, getAuthToken]);

    useEffect(() => {
        migrateLocalStorage().then(fetchSavedViews);
    }, [migrateLocalStorage, fetchSavedViews]);

    const handleSaveView = async () => {
        if (!newViewName.trim()) return;

        try {
            const body = {
                name: newViewName.trim(),
                metrics: Array.from(selectedMetrics),
                team_id: saveToTeam && selectedTeamId ? selectedTeamId : null
            };

            const token = getAuthToken();
            if (!token) {
                alert(language === 'zh' ? '請先登入' : 'Please login first');
                return;
            }

            const res = await fetch(`${API_BASE}/api/saved-views`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                const newView = await res.json();
                setSavedViews(prev => [...prev, newView]);
                setShowSaveModal(false);
                setNewViewName('');
                showTemporaryMessage(txt.saveSuccess);
            } else {
                const errData = await res.json().catch(() => ({}));
                console.error('Save failed:', res.status, errData);
                alert(language === 'zh'
                    ? `儲存失敗 (${res.status}): ${errData.detail || '未知錯誤'}`
                    : `Save failed (${res.status}): ${errData.detail || 'Unknown error'}`
                );
            }
        } catch (error) {
            console.error('Failed to save view:', error);
            const targetUrl = `${API_BASE}/api/saved-views`;
            alert(language === 'zh'
                ? `儲存時發生錯誤: ${error.message}\n請求網址: ${targetUrl}`
                : `Error saving view: ${error.message}\nRequest URL: ${targetUrl}`
            );
        }
    };

    const handleLoadView = (view) => {
        setSelectedMetrics(new Set(view.metrics));
        showTemporaryMessage(txt.loadSuccess);
    };

    const handleDeleteView = async (viewId) => {
        if (!user?.id) return;

        try {
            const params = new URLSearchParams({ user_id: user.id });
            const res = await fetch(`${API_BASE}/api/saved-views/${viewId}?${params}`, {
                method: 'DELETE',
                headers: { Authorization: `Bearer ${getAuthToken()}` }
            });

            if (res.ok) {
                showTemporaryMessage(txt.deleteSuccess);
                fetchSavedViews();
            }
        } catch (e) {
            console.error('Failed to delete view:', e);
        }
    };

    const handleEditView = (view) => {
        setEditingView(view);
        setEditViewName(view.name);
        setEditViewMetrics(new Set(view.metrics));
        setShowEditModal(true);
    };

    const toggleEditMetric = (key) => {
        const newSet = new Set(editViewMetrics);
        if (newSet.has(key)) {
            newSet.delete(key);
        } else {
            newSet.add(key);
        }
        setEditViewMetrics(newSet);
    };

    const handleUpdateView = async () => {
        if (!editingView || !editViewName.trim()) return;

        try {
            const token = getAuthToken();
            if (!token) {
                alert(language === 'zh' ? '請先登入' : 'Please login first');
                return;
            }

            const res = await fetch(`${API_BASE}/api/saved-views/${editingView.id}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: editViewName.trim(),
                    metrics: Array.from(editViewMetrics)
                })
            });

            if (res.ok) {
                const updatedView = await res.json();
                setSavedViews(prev => prev.map(v => v.id === updatedView.id ? updatedView : v));
                setShowEditModal(false);
                setEditingView(null);
                showTemporaryMessage(txt.updateSuccess);
            } else {
                const errData = await res.json().catch(() => ({}));
                alert(language === 'zh'
                    ? `更新失敗: ${errData.detail || '未知錯誤'}`
                    : `Update failed: ${errData.detail || 'Unknown error'}`
                );
            }
        } catch (error) {
            console.error('Failed to update view:', error);
            alert(language === 'zh'
                ? `更新時發生錯誤: ${error.message}`
                : `Error updating view: ${error.message}`
            );
        }
    };

    return {
        savedViews,
        showSaveModal,
        setShowSaveModal,
        newViewName,
        setNewViewName,
        saveMessage,
        saveToTeam,
        setSaveToTeam,
        isLoading,
        showEditModal,
        setShowEditModal,
        editingView,
        setEditingView,
        editViewName,
        setEditViewName,
        editViewMetrics,
        handleSaveView,
        handleLoadView,
        handleDeleteView,
        handleEditView,
        toggleEditMetric,
        handleUpdateView
    };
};

export default useSavedMetricViews;
