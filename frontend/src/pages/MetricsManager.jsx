/**
 * MetricsManager - Metrics Management Page
 * 
 * This page allows users to browse, select and save metric configurations.
 * Saved views can be used in the Analytics page.
 * 
 * Access via: /metrics
 */
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FiSearch, FiCheck, FiX, FiGrid, FiList, FiSave, FiTrash2, FiFolder, FiStar, FiUser, FiUsers } from 'react-icons/fi';
import {
    METRICS_REGISTRY,
    METRIC_CATEGORIES,
    getDefaultMetrics,
    REGISTRY_STATS
} from '../constants/metricsRegistry';
import './MetricsManager.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// localStorage key for migration detection
const SAVED_VIEWS_KEY = 'metricslab_saved_views';
const MIGRATION_DONE_KEY = 'metricslab_migration_done';

const MetricsManager = () => {
    const { language = 'zh', user, selectedTeamId } = useOutletContext() || {};

    // State
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [viewMode, setViewMode] = useState('grid'); // grid | list
    const [selectedMetrics, setSelectedMetrics] = useState(new Set(
        getDefaultMetrics().map(m => m.key)
    ));
    const [showOnlySelected, setShowOnlySelected] = useState(false);

    // Save functionality state
    const [savedViews, setSavedViews] = useState([]);
    const [showSaveModal, setShowSaveModal] = useState(false);
    const [newViewName, setNewViewName] = useState('');
    const [saveMessage, setSaveMessage] = useState(null);
    const [saveToTeam, setSaveToTeam] = useState(false); // New: save to team or personal
    const [isLoading, setIsLoading] = useState(false);

    // Get auth token
    const getAuthToken = useCallback(() => {
        return localStorage.getItem('google_token');
    }, []);

    // Fetch saved views from API
    const fetchSavedViews = useCallback(async () => {
        if (!user?.id) return;
        setIsLoading(true);
        try {
            const params = new URLSearchParams({ user_id: user.id });
            if (selectedTeamId) params.append('team_id', selectedTeamId);

            const res = await fetch(`${API_BASE}/api/saved-views?${params}`, {
                headers: { 'Authorization': `Bearer ${getAuthToken()}` }
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

    // Migrate localStorage views to database (one-time)
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
                            'Authorization': `Bearer ${getAuthToken()}`
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

    // Load saved views on mount
    useEffect(() => {
        migrateLocalStorage().then(fetchSavedViews);
    }, [migrateLocalStorage, fetchSavedViews]);

    // Translations
    const t = {
        zh: {
            title: '📋 指標管理',
            subtitle: '瀏覽與設定 Facebook 廣告指標',
            search: '搜尋指標...',
            all: '全部',
            selected: '已選擇',
            stats: '統計',
            totalMetrics: '總指標數',
            selectedCount: '已選擇',
            clear: '清除全部',
            selectDefaults: '選擇預設',
            selectAll: '全選',
            showSelected: '只顯示已選',
            // Save functionality translations
            saveView: '儲存視角',
            savedViews: '已儲存的視角',
            noSavedViews: '尚未儲存任何視角',
            viewNamePlaceholder: '輸入視角名稱...',
            save: '儲存',
            cancel: '取消',
            load: '載入',
            delete: '刪除',
            saveSuccess: '視角已儲存！',
            deleteSuccess: '視角已刪除',
            loadSuccess: '視角已載入',
            metricsCount: '個指標',
            // Team/Personal labels
            personal: '個人',
            team: '團隊',
            saveAsPersonal: '儲存為個人視角',
            saveAsTeam: '儲存為團隊視角',
        },
        en: {
            title: '📋 Metrics Manager',
            subtitle: 'Browse & Configure Facebook Ads Metrics',
            search: 'Search metrics...',
            all: 'All',
            selected: 'Selected',
            stats: 'Stats',
            totalMetrics: 'Total Metrics',
            selectedCount: 'Selected',
            clear: 'Clear All',
            selectDefaults: 'Select Defaults',
            selectAll: 'Select All',
            showSelected: 'Show Selected Only',
            // Save functionality translations
            saveView: 'Save View',
            savedViews: 'Saved Views',
            noSavedViews: 'No saved views yet',
            viewNamePlaceholder: 'Enter view name...',
            save: 'Save',
            cancel: 'Cancel',
            load: 'Load',
            delete: 'Delete',
            saveSuccess: 'View saved!',
            deleteSuccess: 'View deleted',
            loadSuccess: 'View loaded',
            metricsCount: 'metrics',
            // Team/Personal labels
            personal: 'Personal',
            team: 'Team',
            saveAsPersonal: 'Save as personal view',
            saveAsTeam: 'Save as team view',
        }
    };
    const txt = t[language] || t.zh;

    // Filtered metrics
    const filteredMetrics = useMemo(() => {
        let metrics = Object.values(METRICS_REGISTRY);

        // Filter by category
        if (selectedCategory !== 'all') {
            metrics = metrics.filter(m => m.category === selectedCategory);
        }

        // Filter by search query
        if (searchQuery) {
            const lowerQuery = searchQuery.toLowerCase();
            metrics = metrics.filter(m =>
                m.label_zh.toLowerCase().includes(lowerQuery) ||
                m.label_en.toLowerCase().includes(lowerQuery) ||
                m.key.toLowerCase().includes(lowerQuery)
            );
        }

        // Filter by selected only
        if (showOnlySelected) {
            metrics = metrics.filter(m => selectedMetrics.has(m.key));
        }

        return metrics;
    }, [selectedCategory, searchQuery, showOnlySelected, selectedMetrics]);

    // Handlers
    const toggleMetric = (key) => {
        const newSet = new Set(selectedMetrics);
        if (newSet.has(key)) {
            newSet.delete(key);
        } else {
            newSet.add(key);
        }
        setSelectedMetrics(newSet);
    };

    const selectDefaults = () => {
        setSelectedMetrics(new Set(getDefaultMetrics().map(m => m.key)));
    };

    const selectAll = () => {
        setSelectedMetrics(new Set(Object.keys(METRICS_REGISTRY)));
    };

    const clearAll = () => {
        setSelectedMetrics(new Set());
    };

    // Get auth token


    // Save view handler - using API
    const handleSaveView = async () => {
        if (!newViewName.trim()) return;

        try {
            // Backend now extracts user from token, so no need to pass user_id in params
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
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                const newView = await res.json();
                setSavedViews(prev => [...prev, newView]);
                setShowSaveModal(false);
                setNewViewName('');
                showTemporaryMessage(txt.saveSuccess); // Assuming txt.saveSuccess is the correct key
            } else {
                const errData = await res.json().catch(() => ({}));
                console.error("Save failed:", res.status, errData);
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

    // Load view handler
    const handleLoadView = (view) => {
        setSelectedMetrics(new Set(view.metrics));
        showTemporaryMessage(txt.loadSuccess);
    };

    // Delete view handler - using API
    const handleDeleteView = async (viewId) => {
        if (!user?.id) return;

        try {
            const params = new URLSearchParams({ user_id: user.id });
            const res = await fetch(`${API_BASE}/api/saved-views/${viewId}?${params}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${getAuthToken()}` }
            });

            if (res.ok) {
                showTemporaryMessage(txt.deleteSuccess);
                fetchSavedViews(); // Refresh list
            }
        } catch (e) {
            console.error('Failed to delete view:', e);
        }
    };

    // Show temporary message
    const showTemporaryMessage = (message) => {
        setSaveMessage(message);
        setTimeout(() => setSaveMessage(null), 2000);
    };

    // Category counts
    const categoryCounts = useMemo(() => {
        const counts = { all: Object.keys(METRICS_REGISTRY).length };
        Object.keys(METRIC_CATEGORIES).forEach(cat => {
            counts[cat] = Object.values(METRICS_REGISTRY).filter(m => m.category === cat).length;
        });
        return counts;
    }, []);

    return (
        <div className="metrics-lab">
            {/* Toast Message */}
            {saveMessage && (
                <div className="toast-message">
                    <FiCheck /> {saveMessage}
                </div>
            )}

            {/* Header */}
            <div className="lab-header">
                <div className="lab-title">
                    <h1>{txt.title}</h1>
                    <p>{txt.subtitle}</p>
                </div>
                <div className="lab-stats">
                    <div className="stat-item">
                        <span className="stat-value">{REGISTRY_STATS.totalMetrics}</span>
                        <span className="stat-label">{txt.totalMetrics}</span>
                    </div>
                    <div className="stat-item highlight">
                        <span className="stat-value">{selectedMetrics.size}</span>
                        <span className="stat-label">{txt.selectedCount}</span>
                    </div>
                </div>
            </div>

            {/* Controls */}
            <div className="lab-controls">
                {/* Search */}
                <div className="search-box">
                    <FiSearch />
                    <input
                        type="text"
                        placeholder={txt.search}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                        <button onClick={() => setSearchQuery('')} className="clear-btn">
                            <FiX />
                        </button>
                    )}
                </div>

                {/* Actions */}
                <div className="action-buttons">
                    <button onClick={selectDefaults} className="btn-secondary">
                        {txt.selectDefaults}
                    </button>
                    <button onClick={selectAll} className="btn-secondary">
                        {txt.selectAll}
                    </button>
                    <button onClick={clearAll} className="btn-danger">
                        {txt.clear}
                    </button>
                    {/* Save Button */}
                    <button
                        onClick={() => setShowSaveModal(true)}
                        className="btn-primary"
                        disabled={selectedMetrics.size === 0}
                    >
                        <FiSave /> {txt.saveView}
                    </button>
                </div>

                {/* View Toggle */}
                <div className="view-toggle">
                    <button
                        className={viewMode === 'grid' ? 'active' : ''}
                        onClick={() => setViewMode('grid')}
                    >
                        <FiGrid />
                    </button>
                    <button
                        className={viewMode === 'list' ? 'active' : ''}
                        onClick={() => setViewMode('list')}
                    >
                        <FiList />
                    </button>
                </div>

                {/* Show Selected Toggle */}
                <label className="checkbox-label">
                    <input
                        type="checkbox"
                        checked={showOnlySelected}
                        onChange={(e) => setShowOnlySelected(e.target.checked)}
                    />
                    {txt.showSelected}
                </label>
            </div>

            {/* Saved Views Section */}
            {savedViews.length > 0 && (
                <div className="saved-views-section">
                    <h3><FiFolder /> {txt.savedViews}</h3>
                    <div className="saved-views-list">
                        {savedViews.map(view => (
                            <div key={view.id} className="saved-view-item">
                                <div className="view-info">
                                    {view.is_personal ? <FiUser className="view-icon" style={{ color: 'var(--accent-primary)' }} /> : <FiUsers className="view-icon" style={{ color: '#10b981' }} />}
                                    <span className="view-name">{view.name}</span>
                                    <span className="view-type-badge" style={{
                                        backgroundColor: view.is_personal ? 'rgba(45, 136, 255, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                                        color: view.is_personal ? 'var(--accent-primary)' : '#10b981',
                                        padding: '2px 8px',
                                        borderRadius: '4px',
                                        fontSize: '0.7rem',
                                        fontWeight: 500
                                    }}>
                                        {view.is_personal ? txt.personal : txt.team}
                                    </span>
                                    <span className="view-count">{view.metrics.length} {txt.metricsCount}</span>
                                </div>
                                <div className="view-actions">
                                    <button
                                        onClick={() => handleLoadView(view)}
                                        className="btn-load"
                                        title={txt.load}
                                    >
                                        {txt.load}
                                    </button>
                                    <button
                                        onClick={() => handleDeleteView(view.id)}
                                        className="btn-delete"
                                        title={txt.delete}
                                    >
                                        <FiTrash2 />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Save Modal */}
            {showSaveModal && (
                <div className="modal-overlay" onClick={() => setShowSaveModal(false)}>
                    <div className="save-modal" onClick={e => e.stopPropagation()}>
                        <h3><FiSave /> {txt.saveView}</h3>
                        <p>{selectedMetrics.size} {txt.metricsCount} {txt.selected.toLowerCase()}</p>
                        <input
                            type="text"
                            value={newViewName}
                            onChange={(e) => setNewViewName(e.target.value)}
                            placeholder={txt.viewNamePlaceholder}
                            autoFocus
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') handleSaveView();
                                if (e.key === 'Escape') setShowSaveModal(false);
                            }}
                        />

                        {/* Personal/Team Toggle - only show if in a team workspace */}
                        {selectedTeamId && (
                            <div style={{
                                display: 'flex',
                                gap: '8px',
                                margin: '16px 0',
                                padding: '12px',
                                backgroundColor: 'var(--bg-tertiary)',
                                borderRadius: '8px'
                            }}>
                                <button
                                    onClick={() => setSaveToTeam(false)}
                                    style={{
                                        flex: 1,
                                        padding: '10px',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '6px',
                                        backgroundColor: !saveToTeam ? 'var(--accent-primary)' : 'transparent',
                                        color: !saveToTeam ? '#fff' : 'var(--text-secondary)',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <FiUser /> {txt.personal}
                                </button>
                                <button
                                    onClick={() => setSaveToTeam(true)}
                                    style={{
                                        flex: 1,
                                        padding: '10px',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '6px',
                                        backgroundColor: saveToTeam ? '#10b981' : 'transparent',
                                        color: saveToTeam ? '#fff' : 'var(--text-secondary)',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <FiUsers /> {txt.team}
                                </button>
                            </div>
                        )}

                        <div className="modal-actions">
                            <button onClick={() => setShowSaveModal(false)} className="btn-secondary">
                                {txt.cancel}
                            </button>
                            <button
                                onClick={handleSaveView}
                                className="btn-primary"
                                disabled={!newViewName.trim()}
                            >
                                <FiSave /> {txt.save}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Category Tabs */}
            <div className="category-tabs">
                <button
                    className={selectedCategory === 'all' ? 'active' : ''}
                    onClick={() => setSelectedCategory('all')}
                >
                    {txt.all} ({categoryCounts.all})
                </button>
                {Object.entries(METRIC_CATEGORIES).map(([key, cat]) => (
                    <button
                        key={key}
                        className={selectedCategory === key ? 'active' : ''}
                        onClick={() => setSelectedCategory(key)}
                        style={{ borderColor: cat.color }}
                    >
                        {cat.icon} {language === 'zh' ? cat.label_zh : cat.label_en} ({categoryCounts[key] || 0})
                    </button>
                ))}
            </div>

            {/* Metrics Grid/List */}
            <div className={`metrics-container ${viewMode}`}>
                {filteredMetrics.length === 0 ? (
                    <div className="empty-state">
                        {language === 'zh' ? '找不到符合的指標' : 'No metrics found'}
                    </div>
                ) : (
                    filteredMetrics.map(metric => {
                        const isSelected = selectedMetrics.has(metric.key);
                        const category = METRIC_CATEGORIES[metric.category];

                        return (
                            <div
                                key={metric.key}
                                className={`metric-card ${isSelected ? 'selected' : ''}`}
                                onClick={() => toggleMetric(metric.key)}
                                style={{ borderColor: isSelected ? category?.color : 'transparent' }}
                            >
                                <div className="metric-header">
                                    <span
                                        className="category-dot"
                                        style={{ backgroundColor: category?.color }}
                                    />
                                    <span className="metric-key">{metric.key}</span>
                                </div>
                                <div className="metric-label">
                                    {language === 'zh' ? metric.label_zh : metric.label_en}
                                </div>
                                {metric.description_zh && (
                                    <div className="metric-desc">
                                        {language === 'zh' ? metric.description_zh : metric.description_en || metric.description_zh}
                                    </div>
                                )}

                                <div className="check-indicator">
                                    {isSelected ? <FiCheck /> : null}
                                </div>
                            </div>
                        );
                    })
                )}
            </div>

            {/* Footer */}
            <div className="lab-footer">
                <p>
                    {language === 'zh'
                        ? '✅ 已選擇的指標可以儲存為自訂視角，稍後可在 Analytics 頁面使用。'
                        : '✅ Selected metrics can be saved as custom views for later use in the Analytics page.'}
                </p>
            </div>
        </div>
    );
};

export default MetricsManager;
