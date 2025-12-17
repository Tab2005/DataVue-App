/**
 * useAnalyticsFilters Hook
 * 
 * Consolidated filter state management for Analytics page using useReducer.
 * Replaces 15+ individual useState calls with a single, structured state.
 */
import { useReducer, useCallback, useMemo } from 'react';
import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subWeeks, subMonths, subYears } from 'date-fns';
import { getAllMetricKeys, VIEW_PRESETS, METRIC_GROUPS } from '../constants/analyticsConfig';

// Initial state
const getInitialState = () => ({
    // Analysis level
    level: 'account',

    // Date range
    datePreset: 'last_7d',
    dateRange: {
        since: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
        until: format(subDays(new Date(), 1), 'yyyy-MM-dd')
    },

    // Comparison
    isCompareMode: false,
    comparePreset: 'previous_period',
    prevDateRange: { since: '', until: '' },

    // Metrics selection
    selectedMetrics: new Set(getAllMetricKeys()),
    activeView: 'summary',

    // Filters
    filterKeyword: '',
    filterMode: 'include',
    filterActiveOnly: false,

    // Sorting
    sortConfig: { key: null, direction: 'desc' },

    // Row selection
    selectedRowIds: new Set(),

    // UI state
    showMetricPanel: false,
    showKpiMenu: false,
});

// Action types
const ACTIONS = {
    SET_LEVEL: 'SET_LEVEL',
    SET_DATE_PRESET: 'SET_DATE_PRESET',
    SET_DATE_RANGE: 'SET_DATE_RANGE',
    SET_COMPARE_MODE: 'SET_COMPARE_MODE',
    SET_COMPARE_PRESET: 'SET_COMPARE_PRESET',
    SET_PREV_DATE_RANGE: 'SET_PREV_DATE_RANGE',
    SET_SELECTED_METRICS: 'SET_SELECTED_METRICS',
    TOGGLE_METRIC: 'TOGGLE_METRIC',
    SET_ACTIVE_VIEW: 'SET_ACTIVE_VIEW',
    SET_FILTER_KEYWORD: 'SET_FILTER_KEYWORD',
    SET_FILTER_MODE: 'SET_FILTER_MODE',
    SET_FILTER_ACTIVE_ONLY: 'SET_FILTER_ACTIVE_ONLY',
    SET_SORT_CONFIG: 'SET_SORT_CONFIG',
    SET_SELECTED_ROWS: 'SET_SELECTED_ROWS',
    TOGGLE_ROW: 'TOGGLE_ROW',
    SET_SHOW_METRIC_PANEL: 'SET_SHOW_METRIC_PANEL',
    SET_SHOW_KPI_MENU: 'SET_SHOW_KPI_MENU',
    RESET_FILTERS: 'RESET_FILTERS',
};

// Reducer function
function filterReducer(state, action) {
    switch (action.type) {
        case ACTIONS.SET_LEVEL:
            return { ...state, level: action.payload };

        case ACTIONS.SET_DATE_PRESET:
            return { ...state, datePreset: action.payload };

        case ACTIONS.SET_DATE_RANGE:
            return { ...state, dateRange: action.payload };

        case ACTIONS.SET_COMPARE_MODE:
            return { ...state, isCompareMode: action.payload };

        case ACTIONS.SET_COMPARE_PRESET:
            return { ...state, comparePreset: action.payload };

        case ACTIONS.SET_PREV_DATE_RANGE:
            return { ...state, prevDateRange: action.payload };

        case ACTIONS.SET_SELECTED_METRICS:
            return { ...state, selectedMetrics: action.payload };

        case ACTIONS.TOGGLE_METRIC: {
            const { groupId, key } = action.payload;
            const compositeKey = `${groupId}:${key}`;
            const newSet = new Set(state.selectedMetrics);
            if (newSet.has(compositeKey)) {
                newSet.delete(compositeKey);
            } else {
                newSet.add(compositeKey);
            }
            return { ...state, selectedMetrics: newSet };
        }

        case ACTIONS.SET_ACTIVE_VIEW:
            return { ...state, activeView: action.payload };

        case ACTIONS.SET_FILTER_KEYWORD:
            return { ...state, filterKeyword: action.payload };

        case ACTIONS.SET_FILTER_MODE:
            return { ...state, filterMode: action.payload };

        case ACTIONS.SET_FILTER_ACTIVE_ONLY:
            return { ...state, filterActiveOnly: action.payload };

        case ACTIONS.SET_SORT_CONFIG:
            return { ...state, sortConfig: action.payload };

        case ACTIONS.SET_SELECTED_ROWS:
            return { ...state, selectedRowIds: action.payload };

        case ACTIONS.TOGGLE_ROW: {
            const newSet = new Set(state.selectedRowIds);
            if (newSet.has(action.payload)) {
                newSet.delete(action.payload);
            } else {
                newSet.add(action.payload);
            }
            return { ...state, selectedRowIds: newSet };
        }

        case ACTIONS.SET_SHOW_METRIC_PANEL:
            return { ...state, showMetricPanel: action.payload };

        case ACTIONS.SET_SHOW_KPI_MENU:
            return { ...state, showKpiMenu: action.payload };

        case ACTIONS.RESET_FILTERS:
            return getInitialState();

        default:
            return state;
    }
}

/**
 * Calculate date range from preset
 */
export function calculateDateRange(preset) {
    const today = new Date();
    const yesterday = subDays(today, 1);

    switch (preset) {
        case 'today':
            return { since: format(today, 'yyyy-MM-dd'), until: format(today, 'yyyy-MM-dd') };
        case 'yesterday':
            return { since: format(yesterday, 'yyyy-MM-dd'), until: format(yesterday, 'yyyy-MM-dd') };
        case 'this_week':
            return { since: format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd'), until: format(today, 'yyyy-MM-dd') };
        case 'last_week': {
            const lastWeek = subWeeks(today, 1);
            return { since: format(startOfWeek(lastWeek, { weekStartsOn: 1 }), 'yyyy-MM-dd'), until: format(endOfWeek(lastWeek, { weekStartsOn: 1 }), 'yyyy-MM-dd') };
        }
        case 'this_month':
            return { since: format(startOfMonth(today), 'yyyy-MM-dd'), until: format(today, 'yyyy-MM-dd') };
        case 'last_month': {
            const lastMonth = subMonths(today, 1);
            return { since: format(startOfMonth(lastMonth), 'yyyy-MM-dd'), until: format(endOfMonth(lastMonth), 'yyyy-MM-dd') };
        }
        case 'last_7d':
            return { since: format(subDays(today, 7), 'yyyy-MM-dd'), until: format(yesterday, 'yyyy-MM-dd') };
        case 'last_14d':
            return { since: format(subDays(today, 14), 'yyyy-MM-dd'), until: format(yesterday, 'yyyy-MM-dd') };
        case 'last_30d':
            return { since: format(subDays(today, 30), 'yyyy-MM-dd'), until: format(yesterday, 'yyyy-MM-dd') };
        default:
            return null; // Custom - don't auto-calculate
    }
}

/**
 * Calculate comparison date range
 */
export function calculateCompareRange(dateRange, comparePreset) {
    const { since, until } = dateRange;
    const sinceDate = new Date(since);
    const untilDate = new Date(until);
    const daysDiff = Math.round((untilDate - sinceDate) / (1000 * 60 * 60 * 24)) + 1;

    switch (comparePreset) {
        case 'previous_period': {
            const prevUntil = subDays(sinceDate, 1);
            const prevSince = subDays(prevUntil, daysDiff - 1);
            return { since: format(prevSince, 'yyyy-MM-dd'), until: format(prevUntil, 'yyyy-MM-dd') };
        }
        case 'year_over_year': {
            const yoySince = subYears(sinceDate, 1);
            const yoyUntil = subYears(untilDate, 1);
            return { since: format(yoySince, 'yyyy-MM-dd'), until: format(yoyUntil, 'yyyy-MM-dd') };
        }
        default:
            return null; // Custom
    }
}

/**
 * useAnalyticsFilters Hook
 */
export function useAnalyticsFilters() {
    const [state, dispatch] = useReducer(filterReducer, null, getInitialState);

    // Action creators
    const actions = useMemo(() => ({
        setLevel: (level) => dispatch({ type: ACTIONS.SET_LEVEL, payload: level }),
        setDatePreset: (preset) => dispatch({ type: ACTIONS.SET_DATE_PRESET, payload: preset }),
        setDateRange: (range) => dispatch({ type: ACTIONS.SET_DATE_RANGE, payload: range }),
        setCompareMode: (enabled) => dispatch({ type: ACTIONS.SET_COMPARE_MODE, payload: enabled }),
        setComparePreset: (preset) => dispatch({ type: ACTIONS.SET_COMPARE_PRESET, payload: preset }),
        setPrevDateRange: (range) => dispatch({ type: ACTIONS.SET_PREV_DATE_RANGE, payload: range }),
        setSelectedMetrics: (metrics) => dispatch({ type: ACTIONS.SET_SELECTED_METRICS, payload: metrics }),
        toggleMetric: (groupId, key) => dispatch({ type: ACTIONS.TOGGLE_METRIC, payload: { groupId, key } }),
        setActiveView: (view) => dispatch({ type: ACTIONS.SET_ACTIVE_VIEW, payload: view }),
        setFilterKeyword: (keyword) => dispatch({ type: ACTIONS.SET_FILTER_KEYWORD, payload: keyword }),
        setFilterMode: (mode) => dispatch({ type: ACTIONS.SET_FILTER_MODE, payload: mode }),
        setFilterActiveOnly: (active) => dispatch({ type: ACTIONS.SET_FILTER_ACTIVE_ONLY, payload: active }),
        setSortConfig: (config) => dispatch({ type: ACTIONS.SET_SORT_CONFIG, payload: config }),
        setSelectedRows: (rows) => dispatch({ type: ACTIONS.SET_SELECTED_ROWS, payload: rows }),
        toggleRow: (id) => dispatch({ type: ACTIONS.TOGGLE_ROW, payload: id }),
        setShowMetricPanel: (show) => dispatch({ type: ACTIONS.SET_SHOW_METRIC_PANEL, payload: show }),
        setShowKpiMenu: (show) => dispatch({ type: ACTIONS.SET_SHOW_KPI_MENU, payload: show }),
        resetFilters: () => dispatch({ type: ACTIONS.RESET_FILTERS }),
    }), []);

    // Handle preset change with auto date calculation
    const handlePresetChange = useCallback((preset) => {
        actions.setDatePreset(preset);
        const range = calculateDateRange(preset);
        if (range) {
            actions.setDateRange(range);
        }
    }, [actions]);

    // Handle view change with metric selection
    const handleViewChange = useCallback((view) => {
        actions.setActiveView(view);
        if (view !== 'custom' && VIEW_PRESETS[view]) {
            const viewMetrics = VIEW_PRESETS[view].metrics;
            const newSelected = new Set();
            METRIC_GROUPS.forEach(group => {
                group.metrics.forEach(metric => {
                    if (viewMetrics.includes(metric.key)) {
                        newSelected.add(`${group.id}:${metric.key}`);
                    }
                });
            });
            actions.setSelectedMetrics(newSelected);
        }
    }, [actions]);

    // Handle sort
    const handleSort = useCallback((key) => {
        const { sortConfig } = state;
        let direction = 'desc';
        if (sortConfig.key === key && sortConfig.direction === 'desc') {
            direction = 'asc';
        }
        actions.setSortConfig({ key, direction });
    }, [state.sortConfig, actions]);

    return {
        state,
        actions,
        handlePresetChange,
        handleViewChange,
        handleSort,
        calculateCompareRange: (preset) => calculateCompareRange(state.dateRange, preset),
    };
}

export default useAnalyticsFilters;
