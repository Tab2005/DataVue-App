/**
 * MetricsManager - Metrics Management Page
 * 
 * This page allows users to browse, select and save metric configurations.
 * Saved views can be used in the Analytics page.
 * 
 * Access via: /metrics
 */
import React, { useState, useMemo, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FiSearch, FiCheck, FiX, FiGrid, FiList, FiSave, FiTrash2, FiFolder, FiStar } from 'react-icons/fi';
import {
    METRICS_REGISTRY,
    METRIC_CATEGORIES,
    getDefaultMetrics,
    REGISTRY_STATS
} from '../constants/metricsRegistry';
import './MetricsManager.css';

// localStorage key for saved views
const SAVED_VIEWS_KEY = 'metricslab_saved_views';

// Helper to load saved views from localStorage
const loadSavedViews = () => {
    try {
        const saved = localStorage.getItem(SAVED_VIEWS_KEY);
        return saved ? JSON.parse(saved) : [];
    } catch (e) {
        console.error('Failed to load saved views:', e);
        return [];
    }
};

// Helper to save views to localStorage
const persistSavedViews = (views) => {
    try {
        localStorage.setItem(SAVED_VIEWS_KEY, JSON.stringify(views));
    } catch (e) {
        console.error('Failed to save views:', e);
    }
};

const MetricsManager = () => {
    const { language = 'zh' } = useOutletContext() || {};

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

    // Load saved views on mount
    useEffect(() => {
        setSavedViews(loadSavedViews());
    }, []);

    // Translations
    const t = {
        zh: {
            title: '📋 指標管理',
            subtitle: '瀏覽與設定 Facebook 廣告指標',
            search: '搜尋指標...',
            all: '全部',
            selected: '已選擇',
            default: '預設',
            extended: '擴展',
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
        },
        en: {
            title: '📋 Metrics Manager',
            subtitle: 'Browse & Configure Facebook Ads Metrics',
            search: 'Search metrics...',
            all: 'All',
            selected: 'Selected',
            default: 'Default',
            extended: 'Extended',
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

    // Save view handler
    const handleSaveView = () => {
        if (!newViewName.trim()) return;

        const newView = {
            id: Date.now().toString(),
            name: newViewName.trim(),
            metrics: Array.from(selectedMetrics),
            createdAt: new Date().toISOString(),
        };

        const updatedViews = [...savedViews, newView];
        setSavedViews(updatedViews);
        persistSavedViews(updatedViews);

        setNewViewName('');
        setShowSaveModal(false);
        showTemporaryMessage(txt.saveSuccess);
    };

    // Load view handler
    const handleLoadView = (view) => {
        setSelectedMetrics(new Set(view.metrics));
        showTemporaryMessage(txt.loadSuccess);
    };

    // Delete view handler
    const handleDeleteView = (viewId) => {
        const updatedViews = savedViews.filter(v => v.id !== viewId);
        setSavedViews(updatedViews);
        persistSavedViews(updatedViews);
        showTemporaryMessage(txt.deleteSuccess);
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
                                    <FiStar className="view-icon" />
                                    <span className="view-name">{view.name}</span>
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
                                    {metric.is_default && (
                                        <span className="default-badge">{txt.default}</span>
                                    )}
                                    {!metric.is_default && (
                                        <span className="extended-badge">{txt.extended}</span>
                                    )}
                                </div>
                                <div className="metric-label">
                                    {language === 'zh' ? metric.label_zh : metric.label_en}
                                </div>
                                {metric.description_zh && (
                                    <div className="metric-desc">
                                        {language === 'zh' ? metric.description_zh : metric.description_en || metric.description_zh}
                                    </div>
                                )}
                                <div className="metric-footer">
                                    <span className="format-badge">{metric.format}</span>
                                    <span className="source-badge">{metric.source}</span>
                                </div>
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
