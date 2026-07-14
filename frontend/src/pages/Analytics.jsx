import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import html2canvas from 'html2canvas';
import { FiChevronUp, FiCpu, FiFileText, FiUsers, FiUser, FiX, FiZap } from 'react-icons/fi';
import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subMonths, differenceInDays } from 'date-fns';
import KPICard from '../components/KPICard';
import TrendSection from '../components/TrendSection';
// New modular imports
import { DATE_PRESETS, COMPARE_PRESETS, VIEW_PRESETS } from '../constants/analyticsConfig';
import ReportModal from '../components/Analytics/ReportModal';
import AnalyticsDataTable from '../components/Analytics/AnalyticsDataTable';
import MetaAndromedaImportActions from '../components/Analytics/MetaAndromedaImportActions';
// Import Metrics Registry for extended metrics support
import { useModuleAccess, usePermission } from '../hooks/usePermission';
import useAnalyticsData from '../hooks/useAnalyticsData';
import { ALL_METRIC_GROUPS, METRIC_GROUPS, resolveObservationWindowKind } from '../components/Analytics/analyticsMetrics';
import {
    fetchMetaAndromedaAiReady,
    fetchMetaAndromedaObservedImportStatus,
    importMetaAndromedaObservedFacebookAd,
} from '../services/metaAndromedaWorkflowService';

const Analytics = () => {
    // 1. Get shared context
    const { selectedAccountId, user, language, isSidebarCollapsed, selectedTeamId } = useOutletContext();
    const [showReportModal, setShowReportModal] = useState(false);
    const { hasAccess: hasMetaAndromedaAccess } = useModuleAccess('meta_andromeda', selectedTeamId);
    const { hasPermission: hasFbAnalyticsPermission } = usePermission('fb_ads:analytics:view', selectedTeamId);

    // 2. Translations
    const t = {
        zh: {
            title: "深度成效分析",
            subtitle: "自訂報表與漏斗分析",
            mainSettings: "主要設定",
            level: "分析層級",
            dateRange: "日期範圍",
            customStart: "開始",
            customEnd: "結束",
            advanced: "進階選項",
            compareMode: "V.S 比較模式",
            comparePeriod: "比較期間",
            updateReport: "更新報表",
            keyMetrics: "指標總覽",
            customMetrics: "自訂表格指標欄位",
            levels: {
                campaign: "按活動名稱",
                adset: "按廣告組合名稱",
                ad: "按廣告名稱",
                account: "整體總覽",
            },
            presets: {
                today: "今日",
                yesterday: "昨天",
                this_week: "本週",
                last_week: "上週",
                this_month: "本月",
                last_month: "上月",
                last_7d: "過去 7 天",
                last_14d: "過去 14 天",
                last_30d: "過去 30 天",
                lifetime: "累積歷史成效",
                custom: "自訂",
            },
            comparePresets: {
                previous_period: "前一期",
                year_over_year: "去年同期",
                custom: "自訂",
            },
            table: {
                name: "名稱",
                headers: {
                    campaign: "活動名稱",
                    adset: "廣告組合名稱",
                    ad: "廣告名稱",
                    account: "名稱"
                },
                spend: "花費",
                roas: "回報率 (ROAS)",
                purchases: "購買數",
                cpa: "CPA",
                clicks: "點擊數",
                cvr: "轉換率",
                atc: "購物車",
                dropoff: "流失率",
            }
        },
        en: {
            title: "Deep Analytics",
            subtitle: "Custom Reports & Funnel Analysis",
            mainSettings: "Main Settings",
            level: "Analysis Level",
            dateRange: "Date Range",
            customStart: "Start",
            customEnd: "End",
            advanced: "Advanced",
            compareMode: "Comparison Mode",
            comparePeriod: "Compare Period",
            updateReport: "Run Report",
            keyMetrics: "Metrics Overview",
            customMetrics: "Custom Report Metrics",
            levels: {
                campaign: "By Campaign",
                adset: "By Ad Set",
                ad: "By Ad",
                account: "Account Overview",
            },
            presets: {
                today: "Today",
                yesterday: "Yesterday",
                this_week: "This Week",
                last_week: "Last Week",
                this_month: "This Month",
                last_month: "Last Month",
                last_7d: "Past 7 Days",
                last_14d: "Past 14 Days",
                last_30d: "Past 30 Days",
                lifetime: "Lifetime",
                custom: "Custom",
            },
            comparePresets: {
                previous_period: "Previous Period",
                year_over_year: "Year Over Year",
                custom: "Custom",
            },
            table: {
                name: "Name",
                headers: {
                    campaign: "Campaign Name",
                    adset: "Ad Set Name",
                    ad: "Ad Name",
                    account: "Name"
                },
                spend: "Spend",
                roas: "ROAS",
                purchases: "Purchases",
                cpa: "CPA",
                clicks: "Link Clicks",
                cvr: "CVR",
                atc: "Add to Cart",
                dropoff: "Drop-off",
            }
        }
    };

    const txt = t[language] || t.zh;

    // 2. Local State for Controls
    const [level, setLevel] = useState('account');
    const [datePreset, setDatePreset] = useState('last_7d');
    const [dateRange, setDateRange] = useState({
        since: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
        until: format(subDays(new Date(), 1), 'yyyy-MM-dd')
    });
    // Comparison State
    const [isCompareMode, setIsCompareMode] = useState(false);
    const [comparePreset, setComparePreset] = useState('previous_period');
    const [compareDateRange, setCompareDateRange] = useState({ since: '', until: '' });

    // Metric Selector State (Default: Select all keys from all groups)
    // Use composite keys "group:metric" to allow independent selection of same metric in different groups
    const [selectedMetrics, setSelectedMetrics] = useState(new Set(
        METRIC_GROUPS.flatMap(g => g.metrics.map(m => `${g.id}:${m.key}`))
    ));

    // View State
    const [activeView, setActiveView] = useState('summary');

    // 1. Filter State

    const [filterKeyword, setFilterKeyword] = useState('');
    const [filterMode, setFilterMode] = useState('include'); // include, exclude
    const [filterActiveOnly, setFilterActiveOnly] = useState(false);
    const [filterObservationImported, setFilterObservationImported] = useState('all'); // 'all', 'imported', 'not_imported'

    // Sorting State
    const [sortConfig, setSortConfig] = useState({ key: null, direction: 'desc' });

    // Table Row Selection State
    const [selectedRowIds, setSelectedRowIds] = useState(new Set()); // IDs of selected rows
    const [selectedObservationIds, setSelectedObservationIds] = useState(new Set());
    const [observationImportState, setObservationImportState] = useState({});
    const [observationBatchSummary, setObservationBatchSummary] = useState(null);

    const getObservationStatusText = useCallback((status) => {
        const map = {
            queued: language === 'zh' ? '排隊中' : 'Queued',
            processing: language === 'zh' ? '背景處理中' : 'Processing',
            completed: language === 'zh' ? '已匯入' : 'Imported',
            failed: language === 'zh' ? '匯入失敗' : 'Import failed',
            not_found: language === 'zh' ? '尚未建立' : 'Not found',
        };
        return map[status] || status || (language === 'zh' ? '未送出' : 'Idle');
    }, [language]);

    const getScoreStatusText = useCallback((status) => {
        const map = {
            pending_observation: language === 'zh' ? '等待匯入完成' : 'Waiting for import',
            pending_score_event: language === 'zh' ? '等待建立評分事件' : 'Waiting for score event',
            queued_background: language === 'zh' ? '背景建立中' : 'Creating in background',
            queued: language === 'zh' ? '評分已排隊' : 'Queued',
            processing: language === 'zh' ? '評分中' : 'Processing',
            completed: language === 'zh' ? '評分完成' : 'Completed',
            failed: language === 'zh' ? '評分失敗' : 'Failed',
            skipped_no_asset: language === 'zh' ? '無素材，略過' : 'Skipped: no asset',
            blocked_by_observation_failure: language === 'zh' ? '因匯入失敗未建立' : 'Blocked by import failure',
        };
        return map[status] || status || (language === 'zh' ? '未建立' : 'Not created');
    }, [language]);

    // UI: Toggle Metric Panel
    const [showMetricPanel, setShowMetricPanel] = useState(false);

    // KPI Export State
    const kpiRef = useRef(null);
    const [showKpiMenu, setShowKpiMenu] = useState(false);

    const handleExportImage = async () => {
        if (!kpiRef.current) return;

        try {
            const canvas = await html2canvas(kpiRef.current, {
                backgroundColor: '#18191a', // Match theme background
                scale: 2, // High resolution
                useCORS: true // Allow cross-origin images
            });

            // Generate Filename: YYYYMMDD_Random3
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
            const randomStr = Math.floor(Math.random() * 900 + 100).toString();
            const filename = `${dateStr}_${randomStr}.png`;

            const link = document.createElement('a');
            link.download = filename;
            link.href = canvas.toDataURL();
            link.click();

            setShowKpiMenu(false);
        } catch (err) {
            console.error("Export failed", err);
        }
    };

    // Initial Load - Set default view to Summary to fix overflow
    useEffect(() => {
        handleViewChange('summary');
    }, []);

    const handleViewChange = (view) => {
        // Toggle logic if clicking "Custom" while already on "Custom"
        if (view === 'custom' && activeView === 'custom') {
            setShowMetricPanel(prev => !prev);
            return;
        }

        setActiveView(view);
        if (view !== 'custom') {
            const presetMetrics = VIEW_PRESETS[view].metrics;
            const newSet = new Set();

            // Map preset simple keys to composite keys
            // Strategy: Find the first occurrence of the metric in any group and add it.
            // This ensures standard presets work visually.
            presetMetrics.forEach(key => {
                for (const group of METRIC_GROUPS) {
                    const match = group.metrics.find(m => m.key === key);
                    if (match) {
                        newSet.add(`${group.id}:${key}`);
                        break; // Stop after first match to avoid duplicates in presets
                    }
                }
            });

            setSelectedMetrics(newSet);
            setShowMetricPanel(false); // Hide panel when using preset
        } else {
            // When switching to custom, always show the panel initially
            setShowMetricPanel(true);
        }
    };

    // 2.1 Handle Preset Change
    const handlePresetChange = (e) => {
        const preset = e.target.value;
        setDatePreset(preset);

        const today = new Date();
        let newRange = { since: '', until: '' };

        switch (preset) {
            case 'today': newRange.since = format(today, 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'yesterday': { const yest = subDays(today, 1); newRange.since = format(yest, 'yyyy-MM-dd'); newRange.until = format(yest, 'yyyy-MM-dd'); break; }
            case 'this_week': newRange.since = format(startOfWeek(today, { weekStartsOn: 1 }), 'yyyy-MM-dd'); newRange.until = format(today, 'yyyy-MM-dd'); break;
            case 'last_week': { const start = startOfWeek(subDays(today, 7), { weekStartsOn: 1 }); const end = endOfWeek(subDays(today, 7), { weekStartsOn: 1 }); newRange.since = format(start, 'yyyy-MM-dd'); newRange.until = format(end, 'yyyy-MM-dd'); break; }
            case 'this_month': newRange.since = format(startOfMonth(today), 'yyyy-MM-dd'); newRange.until = format(endOfMonth(today), 'yyyy-MM-dd'); break;
            case 'last_month': { const lm = subMonths(today, 1); newRange.since = format(startOfMonth(lm), 'yyyy-MM-dd'); newRange.until = format(endOfMonth(lm), 'yyyy-MM-dd'); break; }
            case 'last_7d': newRange.since = format(subDays(today, 7), 'yyyy-MM-dd'); newRange.until = format(subDays(today, 1), 'yyyy-MM-dd'); break; // Exclude today
            case 'last_14d': newRange.since = format(subDays(today, 14), 'yyyy-MM-dd'); newRange.until = format(subDays(today, 1), 'yyyy-MM-dd'); break;
            case 'last_30d': newRange.since = format(subDays(today, 30), 'yyyy-MM-dd'); newRange.until = format(subDays(today, 1), 'yyyy-MM-dd'); break;
            case 'custom': return;
        }

        setDateRange(newRange);
    };
    
    // 2.2 Handle Compare Preset Change
    const handleComparePresetChange = (e) => {
        const preset = e.target.value;
        setComparePreset(preset);

        if (preset === 'custom' && (!compareDateRange.since || !compareDateRange.until)) {
            // Calculate previous period as default custom compare dates
            const startDate = new Date(dateRange.since);
            const endDate = new Date(dateRange.until);
            const diffDays = differenceInDays(endDate, startDate) + 1; // Inclusive
            const prevSince = format(subDays(startDate, diffDays), 'yyyy-MM-dd');
            const prevUntil = format(subDays(endDate, diffDays), 'yyyy-MM-dd');
            setCompareDateRange({ since: prevSince, until: prevUntil });
        }
    };

    const {
        savedViews,
        reportData,
        prevReportData,
        prevDateRange,
        loading,
        error,
        fetchAnalytics,
    } = useAnalyticsData({
        selectedAccountId,
        selectedTeamId,
        user,
        selectedMetrics,
        dateRange,
        level,
        isCompareMode,
        comparePreset,
        compareDateRange,
    });

    // AI Analyst State
    const [showAiPanel, setShowAiPanel] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState('');
    const [aiError, setAiError] = useState(null);

    const handleStartAnalysis = async () => {
        setIsAnalyzing(true);
        setAnalysisResult('');
        setAiError(null);

        try {
            // 1. Prepare Data context
            // Truncate table data to avoid token limits (Top 20 rows?)
            const topRows = filteredData.slice(0, 20); // Top 20 by current sort

            const contextData = {
                period: `${dateRange.since} to ${dateRange.until}`,
                level: level,
                metrics_summary: {
                    total_spend: currentSummaryData?.spend,
                    total_roas: currentSummaryData?.roas,
                    total_purchases: currentSummaryData?.purchases,
                },
                rows: topRows
            };

            const token = localStorage.getItem('google_token');
            const localKey = localStorage.getItem('ai_api_key');
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

            const payload = {
                data: contextData,
                context: `Analyzing ${level} performance for period: ${dateRange.since} to ${dateRange.until}. Language: ${language}`,
                api_key: localKey || null // Send local key if exists (Dual Mode)
            };

            const response = await fetch(`${apiUrl}/api/ai/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Analysis Failed');
            }

            // Stream Reader
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                setAnalysisResult(prev => prev + chunk);
            }

        } catch (err) {
            console.error("AI Analysis Error", err);
            setAiError(err.message);
        } finally {
            setIsAnalyzing(false);
        }
    };


    // 3.1 Toggle Metric (Checkbox)
    // 3.1 Toggle Metric (Checkbox)
    const toggleMetric = (groupId, key) => {
        const compositeKey = `${groupId}:${key}`;
        const newSet = new Set(selectedMetrics);
        if (newSet.has(compositeKey)) {
            newSet.delete(compositeKey);
        } else {
            newSet.add(compositeKey);
        }
        setSelectedMetrics(newSet);
    };

    // Helper to get active columns based on order defined in ALL_METRIC_GROUPS
    const getActiveColumns = () => {
        const cols = [];
        // Flatten groups to preserve order (includes extended metrics)
        ALL_METRIC_GROUPS.forEach(group => {
            group.metrics.forEach(m => {
                const compositeKey = `${group.id}:${m.key}`;
                if (selectedMetrics.has(compositeKey)) {
                    // Add composite key for React unique mapping
                    cols.push({ ...m, uniqueKey: compositeKey });
                }
            });
        });
        return cols;
    };

    const activeCols = getActiveColumns();

    // 6. Filter Data
    const filteredData = React.useMemo(() => {
        if (!reportData) return [];

        return reportData.filter(row => {
            // 1. Status Filter
            if (filterActiveOnly) {
                const status = (row.status || '').toUpperCase();
                if (status !== 'ACTIVE') return false;
            }

            // 2. Keyword Filter
            if (filterKeyword.trim()) {
                const keyword = filterKeyword.toLowerCase();
                // Check all name fields
                const name = (row.name || row.campaign_name || row.adset_name || row.ad_name || '').toLowerCase();
                const match = name.includes(keyword);

                if (filterMode === 'include') {
                    if (!match) return false;
                } else {
                    if (match) return false;
                }
            }

            // 3. Observation Filter (Only when level is 'ad')
            if (level === 'ad' && filterObservationImported !== 'all') {
                const importState = observationImportState[row.id]?.observationStatus;
                if (filterObservationImported === 'imported') {
                    if (importState !== 'completed') return false;
                } else if (filterObservationImported === 'not_imported') {
                    if (importState === 'completed') return false;
                }
            }

            return true;
        });
    }, [reportData, filterKeyword, filterMode, filterActiveOnly, filterObservationImported, observationImportState, level]);

    const filteredPrevData = React.useMemo(() => {
        if (!prevReportData) return [];
        return prevReportData.filter(row => {
            if (filterActiveOnly) {
                const status = (row.status || '').toUpperCase();
                if (status !== 'ACTIVE') return false;
            }
            if (filterKeyword.trim()) {
                const keyword = filterKeyword.toLowerCase();
                const name = (row.name || row.campaign_name || row.adset_name || row.ad_name || '').toLowerCase();
                const match = name.includes(keyword);
                if (filterMode === 'include') {
                    if (!match) return false;
                } else {
                    if (match) return false;
                }
            }
            if (level === 'ad' && filterObservationImported !== 'all') {
                const importState = observationImportState[row.id]?.observationStatus;
                if (filterObservationImported === 'imported') {
                    if (importState !== 'completed') return false;
                } else if (filterObservationImported === 'not_imported') {
                    if (importState === 'completed') return false;
                }
            }
            return true;
        });
    }, [prevReportData, filterKeyword, filterMode, filterActiveOnly, filterObservationImported, observationImportState, level]);

    const canUseObservationImport = level === 'ad' && hasMetaAndromedaAccess && hasFbAnalyticsPermission;
    const observationWindowKind = useMemo(() => resolveObservationWindowKind(datePreset), [datePreset]);
    const observationImportableRows = useMemo(() => {
        if (!canUseObservationImport) {
            return [];
        }
        return filteredData.filter((row) => Boolean(row?.ad_id));
    }, [canUseObservationImport, filteredData]);

    const selectedObservationRows = useMemo(() => {
        if (!canUseObservationImport) {
            return [];
        }
        return observationImportableRows.filter((row) => selectedObservationIds.has(row.id));
    }, [canUseObservationImport, observationImportableRows, selectedObservationIds]);


    // Sync selectedRowIds with filteredData
    // Default Behavior: When filteredData changes (e.g. date change), Select All by default.
    useEffect(() => {
        if (filteredData) {
            const allIds = new Set(filteredData.map(item => item.id));
            setSelectedRowIds(allIds);
        }
    }, [filteredData]);

    useEffect(() => {
        if (!canUseObservationImport) {
            setSelectedObservationIds(new Set());
            setObservationBatchSummary(null);
            return;
        }

        setSelectedObservationIds((prev) => {
            const next = new Set();
            observationImportableRows.forEach((row) => {
                if (prev.has(row.id)) {
                    next.add(row.id);
                }
            });
            return next;
        });
    }, [canUseObservationImport, observationImportableRows]);

    const handleToggleObservationRow = useCallback((rowId, checked) => {
        setSelectedObservationIds((prev) => {
            const next = new Set(prev);
            if (checked) {
                next.add(rowId);
            } else {
                next.delete(rowId);
            }
            return next;
        });
    }, []);

    const handleToggleAllObservationRows = useCallback((checked) => {
        if (!checked) {
            setSelectedObservationIds(new Set());
            return;
        }

        setSelectedObservationIds(new Set(observationImportableRows.map((row) => row.id)));
    }, [observationImportableRows]);

    const importObservationRow = useCallback(async (row) => {
        if (!row?.ad_id || !selectedAccountId) {
            const message = language === 'zh'
                ? '缺少廣告或帳號資訊，無法匯入。'
                : 'Missing ad or account information.';
            setObservationImportState((prev) => ({
                ...prev,
                [row?.id || 'unknown']: {
                    status: 'failed',
                    observationStatus: 'failed',
                    scoreStatus: 'blocked_by_observation_failure',
                    message,
                },
            }));
            return { ok: false };
        }

        const rowKey = row.id;
        setObservationImportState((prev) => ({
            ...prev,
            [rowKey]: {
                ...(prev[rowKey] || {}),
                status: 'loading',
                observationStatus: 'queued',
                scoreStatus: 'pending_observation',
                message: language === 'zh' ? '送出匯入請求中...' : 'Submitting import request...',
            },
        }));

        try {
            const observationWindowKind = resolveObservationWindowKind(datePreset);
            const payload = {
                account_id: selectedAccountId,
                ad_id: row.ad_id,
                observation_window_kind: observationWindowKind,
                since: observationWindowKind === 'custom' ? dateRange.since : undefined,
                until: observationWindowKind === 'custom' ? dateRange.until : undefined,
                market: 'TW',
                placement_family: 'all',
                primary_text: row.primary_text || row.body || null,
                headline: row.headline || row.title || row.name || null,
                cta: row.cta || null,
            };

            const accepted = await importMetaAndromedaObservedFacebookAd(payload);
            const observedCreativeId = accepted?.observed_creative_id;

            setObservationImportState((prev) => ({
                ...prev,
                [rowKey]: {
                    ...(prev[rowKey] || {}),
                    status: 'accepted',
                    observedCreativeId,
                    observationStatus: accepted?.status === 'accepted' ? 'queued' : (accepted?.status || 'queued'),
                    scoreStatus: accepted?.score_status || 'pending_observation',
                    message: language === 'zh' ? '已送出，等待背景匯入。' : 'Accepted, waiting for background import.',
                },
            }));

            if (observedCreativeId) {
                try {
                    const status = await fetchMetaAndromedaObservedImportStatus(observedCreativeId);
                    setObservationImportState((prev) => ({
                        ...prev,
                        [rowKey]: {
                            ...(prev[rowKey] || {}),
                            status: status?.observation_status === 'completed' || status?.observation_status === 'failed'
                                ? status.observation_status
                                : 'polling',
                            observedCreativeId,
                            observationStatus: status?.observation_status || 'queued',
                            scoreStatus: status?.score_status || accepted?.score_status || 'pending_observation',
                            message: status?.observation_message || (language === 'zh' ? '匯入狀態已更新。' : 'Import status updated.'),
                        },
                    }));
                } catch {
                    setObservationImportState((prev) => ({
                        ...prev,
                        [rowKey]: {
                            ...(prev[rowKey] || {}),
                            status: 'polling',
                            observedCreativeId,
                            message: language === 'zh' ? '已送出，暫時無法讀取最新狀態。' : 'Accepted; latest status is not available yet.',
                        },
                    }));
                }
            }

            return { ok: true };
        } catch (err) {
            setObservationImportState((prev) => ({
                ...prev,
                [rowKey]: {
                    ...(prev[rowKey] || {}),
                    status: 'failed',
                    observationStatus: 'failed',
                    scoreStatus: 'blocked_by_observation_failure',
                    message: err?.message || (language === 'zh' ? '匯入失敗。' : 'Import failed.'),
                },
            }));
            return { ok: false };
        }
    }, [datePreset, dateRange, language, selectedAccountId]);

    const handleObservationImport = useCallback(async (row) => {
        await importObservationRow(row);
    }, [importObservationRow]);

    const handleBatchObservationImport = useCallback(async () => {
        if (!selectedObservationRows.length) {
            return;
        }

        // Pre-flight AI readiness check
        try {
            const aiStatus = await fetchMetaAndromedaAiReady();
            if (aiStatus && !aiStatus.ready && aiStatus.warning) {
                const continueAnyway = window.confirm(
                    (language === 'zh' ? '⚠️ AI 評分連線異常\n\n' : '⚠️ AI Scoring Unavailable\n\n') +
                    aiStatus.warning +
                    (language === 'zh'
                        ? '\n\n是否仍要繼續批次匯入？（評分將使用啟發式備用模式）'
                        : '\n\nContinue with batch import anyway? (Scoring will use heuristic fallback)')
                );
                if (!continueAnyway) return;
            }
        } catch {
            // AI check failed → proceed silently (don't block import)
        }

        setObservationBatchSummary({
            status: 'loading',
            attemptedCount: selectedObservationRows.length,
            successCount: 0,
            failureCount: 0,
            message: language === 'zh'
                ? `批次送出中，共 ${selectedObservationRows.length} 筆。`
                : `Batch submission in progress for ${selectedObservationRows.length} ads.`,
        });

        let successCount = 0;
        let failureCount = 0;

        for (const row of selectedObservationRows) {
            const result = await importObservationRow(row);
            if (result.ok) {
                successCount += 1;
            } else {
                failureCount += 1;
            }
        }

        setObservationBatchSummary({
            status: failureCount === 0 ? 'success' : 'warning',
            attemptedCount: selectedObservationRows.length,
            successCount,
            failureCount,
            message: language === 'zh'
                ? `批次送出完成，成功送出 ${successCount} 筆，失敗 ${failureCount} 筆。`
                : `Batch submission completed: ${successCount} accepted, ${failureCount} failed.`,
        });
    }, [importObservationRow, language, selectedObservationRows]);

    // 7. Calculate Summary for KPI Cards (Dynamic Selection)
    const calculateSummary = (dataSource) => {
        if (!dataSource || dataSource.length === 0) return null;

        // Filter by Selection
        // Logic: If selectedRowIds exists, only sum items in it.
        const targetData = dataSource.filter(item => selectedRowIds.has(item.id));

        if (targetData.length === 0) return null; // Or return all zeros? Returning null usually hides cards or shows 0.

        // Sum basic additive metrics
        const sum = (key) => targetData.reduce((acc, row) => acc + (row[key] || 0), 0);

        const total = {
            spend: sum('spend'),
            impressions: sum('impressions'),
            reach: sum('reach'), // Approximation
            frequency: sum('frequency'),  // NEW
            clicks: sum('clicks'),  // NEW
            link_clicks: sum('link_clicks'),
            unique_clicks: sum('unique_clicks'),  // NEW
            outbound_clicks: sum('outbound_clicks'), // NEW for Cost Per Outbound Click
            view_content: sum('view_content'),
            add_to_cart: sum('add_to_cart'),
            initiate_checkout: sum('initiate_checkout'),
            add_payment_info: sum('add_payment_info'),
            purchases: sum('purchases'),
            purchase_value: sum('purchase_value'),
            atc_value: sum('atc_value'),
            // Engagement (New)
            post_comments: sum('post_comments'),
            post_saves: sum('post_saves'),
            post_shares: sum('post_shares'),
            post_engagement: sum('post_engagement'),
            post_reactions: sum('post_reactions'),
            page_likes: sum('page_likes'),
            // CPAS (New)
            shared_purchases: sum('shared_purchases'),
            shared_purchase_value: sum('shared_purchase_value'),
            shared_add_to_cart: sum('shared_add_to_cart'),
            shared_atc_value: sum('shared_atc_value'),
            shared_view_content: sum('shared_view_content'),
            // Video Metrics
            video_views: sum('video_views'),
            video_thruplay: sum('video_thruplay'),
            video_p25_watched: sum('video_p25_watched'),
            video_p50_watched: sum('video_p50_watched'),
            video_p75_watched: sum('video_p75_watched'),
            video_p100_watched: sum('video_p100_watched'),
            video_avg_time_watched: sum('video_avg_time_watched'),
            // Messaging Metrics
            messaging_first_reply: sum('messaging_first_reply'),
            messaging_conversation_started: sum('messaging_conversation_started'),
            // Lead Metrics
            leads: sum('leads'),
            onsite_leads: sum('onsite_leads'),
            // App Metrics
            app_installs: sum('app_installs'),
            app_events: sum('app_events'),
            // Instant Experience (New)
            instant_experience_open: sum('instant_experience_open'),
            instant_experience_start: sum('instant_experience_start'),
            // CTR fields (from Facebook API, not calculated)
            ctr: sum('ctr'),
            inline_link_click_ctr: sum('inline_link_click_ctr'),
            unique_ctr: sum('unique_ctr'),
            outbound_clicks_ctr: sum('outbound_clicks_ctr'),
        };

        // Recalculate derived rates
        total.cpc = total.link_clicks > 0 ? total.spend / total.link_clicks : 0;
        total.cpm = total.impressions > 0 ? (total.spend / total.impressions) * 1000 : 0;

        // Debug CTR calculation
        console.log('[Analytics Debug] CTR from API:', {
            ctr: total.ctr,
            inline_link_click_ctr: total.inline_link_click_ctr,
            link_clicks: total.link_clicks,
            impressions: total.impressions,
            targetData_count: targetData.length,
            sample_rows: targetData.slice(0, 3).map(r => ({
                id: r.id,
                ctr: r.ctr,
                inline_link_click_ctr: r.inline_link_click_ctr,
                link_clicks: r.link_clicks,
                impressions: r.impressions
            }))
        });

        total.cpa = total.purchases > 0 ? total.spend / total.purchases : 0;
        total.cost_per_atc = total.add_to_cart > 0 ? total.spend / total.add_to_cart : 0;
        total.roas = total.spend > 0 ? total.purchase_value / total.spend : 0;
        total.shared_roas = total.spend > 0 ? total.shared_purchase_value / total.spend : 0;

        // CTR Recalculations (REMOVED - use direct values from API)
        // If API doesn't provide these values, fallback to calculation
        if (!total.unique_ctr && total.reach > 0) {
            total.unique_ctr = (total.unique_clicks / total.reach) * 100;
        }
        if (!total.outbound_clicks_ctr && total.impressions > 0) {
            total.outbound_clicks_ctr = (total.outbound_clicks / total.impressions) * 100;
        }
        // Note: ctr and inline_link_click_ctr should come from API, not calculated

        // Cost & Spend Derived
        total.cpp = total.reach > 0 ? (total.spend / total.reach) * 1000 : 0;
        total.cost_per_unique_click = total.unique_clicks > 0 ? total.spend / total.unique_clicks : 0;
        total.cost_per_conversion = total.purchases > 0 ? total.spend / total.purchases : 0;
        // Approximation for others where denominator might be missing or using generic clicks
        total.cost_per_inline_link_click = total.link_clicks > 0 ? total.spend / total.link_clicks : 0;

        // Cost Per Outbound Click
        total.cost_per_outbound_click = total.outbound_clicks > 0 ? total.spend / total.outbound_clicks : 0;

        // Calculated Extended Costs
        total.cost_per_message = total.messaging_first_reply > 0 ? total.spend / total.messaging_first_reply : 0;
        total.cost_per_install = total.app_installs > 0 ? total.spend / total.app_installs : 0;
        total.cost_per_lead = total.leads > 0 ? total.spend / total.leads : 0;

        // Funnel Rates
        total.cvr = total.link_clicks > 0 ? (total.purchases / total.link_clicks) * 100 : 0;
        total.view_to_cart = total.view_content > 0 ? (total.add_to_cart / total.view_content) * 100 : 0;
        total.cart_conversion = total.add_to_cart > 0 ? (total.purchases / total.add_to_cart) * 100 : 0;
        total.cart_dropoff = total.add_to_cart > 0 ? (1 - (total.purchases / total.add_to_cart)) * 100 : 0;
        total.cart_value_realization = total.atc_value > 0 ? (total.purchase_value / total.atc_value) * 100 : 0;

        // Video Derived Rates
        total.cost_per_thruplay = total.video_thruplay > 0 ? total.spend / total.video_thruplay : 0;

        // Messaging Derived Rates
        total.cost_per_message = total.messaging_first_reply > 0 ? total.spend / total.messaging_first_reply : 0;

        // Lead Derived Rates
        total.cost_per_lead = total.leads > 0 ? total.spend / total.leads : 0;

        // App Derived Rates
        total.cost_per_install = total.app_installs > 0 ? total.spend / total.app_installs : 0;

        return total;
    };




    const currentSummaryData = React.useMemo(() => calculateSummary(filteredData), [filteredData, selectedRowIds]);

    const prevSummaryData = React.useMemo(() => {
        if (!filteredPrevData) return null;
        return calculateSummary(filteredPrevData);
    }, [filteredPrevData, selectedRowIds]);

    const renderMetricValue = (val, format) => {
        if (val === undefined || val === null || isNaN(val)) return '-';
        if (format === 'currency') return `$${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`; // Round currency on cards
        if (format === 'currency_decimal') {
            // Smart decimal: show .X only if not a whole number
            const isWholeNumber = Number.isInteger(val) || Math.abs(val - Math.round(val)) < 0.01;
            return `$${val.toLocaleString(undefined, { minimumFractionDigits: isWholeNumber ? 0 : 1, maximumFractionDigits: isWholeNumber ? 0 : 1 })}`;
        }
        if (format === 'percent') return `${val.toFixed(2)}%`;
        if (format === 'decimal') return val.toFixed(2);
        return val.toLocaleString();
    };


    // Sorting Logic
    const handleSort = (key) => {
        let direction = 'desc';
        if (sortConfig.key === key && sortConfig.direction === 'desc') {
            direction = 'asc';
        }
        setSortConfig({ key, direction });
    };

    const sortedData = React.useMemo(() => {
        if (!filteredData) return [];
        let sortableItems = [...filteredData];
        if (sortConfig.key !== null) {
            sortableItems.sort((a, b) => {
                let aValue = a[sortConfig.key];
                let bValue = b[sortConfig.key];

                // Handle missing values
                if (aValue === undefined || aValue === null) aValue = -Infinity; // Treat nulls as smallest
                if (bValue === undefined || bValue === null) bValue = -Infinity;

                // Numeric sort
                if (typeof aValue === 'number' && typeof bValue === 'number') {
                    return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
                }

                // String sort (fallback)
                aValue = String(aValue).toLowerCase();
                bValue = String(bValue).toLowerCase();
                if (aValue < bValue) {
                    return sortConfig.direction === 'asc' ? -1 : 1;
                }
                if (aValue > bValue) {
                    return sortConfig.direction === 'asc' ? 1 : -1;
                }
                return 0;
            });
        }
        return sortableItems;
    }, [filteredData, sortConfig]);


    // 6. Basic UI Components
    const { isMobile } = useOutletContext(); // Destructure isMobile

    return (
        <div style={{ padding: isMobile ? '16px' : '24px', width: '100%', maxWidth: '100%', overflow: 'hidden', boxSizing: 'border-box' }}>
            {/* Header Section */}
            <div style={{ marginBottom: '24px', display: 'flex', flexDirection: isMobile ? 'column' : 'row', justifyContent: 'space-between', alignItems: isMobile ? 'flex-start' : 'center', gap: isMobile ? '8px' : '0' }}>
                <div>
                    <h1 style={{ fontSize: isMobile ? '1.5rem' : '1.8rem', fontWeight: '700', color: 'var(--text-primary)' }}>
                        {txt.title}
                    </h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: isMobile ? '0.9rem' : '1rem' }}>
                        {txt.subtitle}
                    </p>
                </div>
            </div>

            {/* Split Layout Control Panel (Top) */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '3fr 1fr',
                gap: '24px',
                marginBottom: '24px'
            }}>

                {/* Left Panel: Primary Settings */}
                <div className="glass-panel" style={{ padding: isMobile ? '16px' : '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

                    <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>{txt.mainSettings}</h3>

                    <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: '20px', flexWrap: 'wrap' }}>
                        {/* Level Selector */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.level}</label>
                            <select
                                value={level}
                                onChange={(e) => setLevel(e.target.value)}
                                style={{
                                    padding: '10px',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'var(--text-primary)',
                                    width: '100%'
                                }}
                            >
                                <option value="campaign" style={{ color: 'black' }}>{txt.levels.campaign}</option>
                                <option value="adset" style={{ color: 'black' }}>{txt.levels.adset}</option>
                                <option value="ad" style={{ color: 'black' }}>{txt.levels.ad}</option>
                                <option value="account" style={{ color: 'black' }}>{txt.levels.account}</option>
                            </select>
                        </div>

                        {/* Date Preset Selector */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: isMobile ? '100%' : '180px' }}>
                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.dateRange}</label>
                            <select
                                value={datePreset}
                                onChange={handlePresetChange}
                                style={{
                                    padding: '10px',
                                    borderRadius: '8px',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'var(--text-primary)',
                                    width: '100%'
                                }}
                            >
                                {DATE_PRESETS.map(p => (
                                    <option key={p.value} value={p.value} style={{ color: 'black' }}>
                                        {txt.presets[p.value] || p.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Custom Date Inputs (Conditional) */}
                    {datePreset === 'custom' && (
                        <div style={{ display: 'flex', gap: '16px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.customStart}</label>
                                <input type="date" value={dateRange.since} onChange={(e) => setDateRange({ ...dateRange, since: e.target.value })}
                                    style={{ padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', colorScheme: 'dark', width: '100%' }} />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.customEnd}</label>
                                <input type="date" value={dateRange.until} onChange={(e) => setDateRange({ ...dateRange, until: e.target.value })}
                                    style={{ padding: '10px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', colorScheme: 'dark', width: '100%' }} />
                            </div>
                        </div>
                    )}


                    {/* Metric Selector Toggle (Now includes ALL groups) */}
                    <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '16px' }}>

                        {/* View Tabs */}
                        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                            {Object.entries(VIEW_PRESETS).map(([key, preset]) => (
                                <button
                                    key={key}
                                    onClick={() => handleViewChange(key)}
                                    style={{
                                        padding: '6px 12px',
                                        borderRadius: '20px',
                                        border: '1px solid var(--glass-border)',
                                        background: activeView === key ? 'var(--accent-primary)' : 'rgba(255,255,255,0.05)',
                                        color: 'white',
                                        fontSize: '0.85rem',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    {language === 'zh' ? preset.label_zh : preset.label_en}
                                </button>
                            ))}

                            {/* AI Analyst Button - Placed right after Custom tab */}
                            <button
                                onClick={() => setShowAiPanel(true)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: '6px',
                                    padding: '6px 16px', borderRadius: '20px',
                                    background: 'linear-gradient(135deg, #6366f1, #a855f7)', // Indigo to Purple
                                    border: 'none', color: 'white',
                                    fontSize: '0.9rem', fontWeight: 'bold', cursor: 'pointer',
                                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
                                    transition: 'transform 0.2s',
                                }}
                                onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                                onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                            >
                                🤖 {language === 'zh' ? 'AI 廣告分析' : 'AI Analyst'}
                            </button>

                            {/* Saved Views from MetricsLab */}
                            {savedViews.length > 0 && (
                                <>
                                    <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)', margin: '0 4px' }} />
                                    {savedViews.map(view => (
                                        <button
                                            key={`saved-${view.id}`}
                                            onClick={() => {
                                                // Load saved view metrics
                                                const newSet = new Set();
                                                view.metrics.forEach(metricKey => {
                                                    // Map registry keys to composite keys (search in ALL groups including extended)
                                                    for (const group of ALL_METRIC_GROUPS) {
                                                        const match = group.metrics.find(m => m.key === metricKey);
                                                        if (match) {
                                                            newSet.add(`${group.id}:${metricKey}`);
                                                            break;
                                                        }
                                                    }
                                                });
                                                setSelectedMetrics(newSet);
                                                setActiveView(`saved-${view.id}`);
                                                setShowMetricPanel(false);
                                            }}
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '4px',
                                                padding: '6px 12px',
                                                borderRadius: '20px',
                                                border: view.is_personal ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)',
                                                background: activeView === `saved-${view.id}`
                                                    ? (view.is_personal ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)')
                                                    : (view.is_personal ? 'rgba(59, 130, 246, 0.05)' : 'rgba(16, 185, 129, 0.05)'),
                                                color: view.is_personal ? '#60a5fa' : '#34d399',
                                                fontSize: '0.85rem',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s'
                                            }}
                                            title={view.is_personal ? (language === 'zh' ? '個人視角' : 'Personal View') : (language === 'zh' ? '團隊視角' : 'Team View')}
                                        >
                                            {view.is_personal ? <FiUser size={12} /> : <FiUsers size={12} />}
                                            {view.name}
                                        </button>
                                    ))}
                                </>
                            )}
                        </div>
                    </div>

                    {/* Row 2: Filter Toolbar (Moved here) */}
                    <div style={{
                        display: 'flex',
                        flexDirection: isMobile ? 'column' : 'row',
                        gap: '16px',
                        alignItems: isMobile ? 'stretch' : 'center',
                        marginBottom: '16px',
                        background: 'rgba(255,255,255,0.03)',
                        padding: '12px',
                        borderRadius: '12px',
                        border: '1px solid var(--glass-border)'
                    }}>
                        {/* Keyword Search */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1 }}>
                            <span style={{ fontSize: '1.2rem' }}>🔍</span>
                            <input
                                type="text"
                                placeholder={language === 'zh' ? "搜尋關鍵字..." : "Search keyword..."}
                                value={filterKeyword}
                                onChange={(e) => setFilterKeyword(e.target.value)}
                                style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: 'var(--text-primary)',
                                    fontSize: '1rem',
                                    width: '100%',
                                    outline: 'none'
                                }}
                            />
                        </div>

                        <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)' }}></div>

                        {/* Filter Mode */}
                        <select
                            value={filterMode}
                            onChange={(e) => setFilterMode(e.target.value)}
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--glass-border)',
                                color: 'var(--text-primary)',
                                fontSize: '0.9rem',
                                cursor: 'pointer',
                                outline: 'none',
                                padding: '6px 10px',
                                borderRadius: '6px'
                            }}
                        >
                            <option value="include">{language === 'zh' ? '包含 (Include)' : 'Include'}</option>
                            <option value="exclude">{language === 'zh' ? '排除 (Exclude)' : 'Exclude'}</option>
                        </select>

                        <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)' }}></div>

                        {/* Active Only Toggle */}
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                            <span style={{ fontSize: '0.9rem', color: filterActiveOnly ? '#4ade80' : 'var(--text-secondary)', fontWeight: filterActiveOnly ? 600 : 400 }}>
                                ⚡ {language === 'zh' ? '只看快篩 (Active)' : 'Active Only'}
                            </span>
                            <div className="switch" style={{ position: 'relative', display: 'inline-block', width: '36px', height: '20px' }}>
                                <input type="checkbox" checked={filterActiveOnly} onChange={(e) => setFilterActiveOnly(e.target.checked)} style={{ opacity: 0, width: 0, height: 0 }} />
                                <span style={{
                                    position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                                    backgroundColor: filterActiveOnly ? '#4ade80' : '#4b5563', borderRadius: '20px', transition: '.4s'
                                }}>
                                    <span style={{
                                        position: 'absolute', content: "", height: '14px', width: '14px', left: '3px', bottom: '3px',
                                        backgroundColor: 'white', transition: '.4s', borderRadius: '50%',
                                        transform: filterActiveOnly ? 'translateX(16px)' : 'translateX(0)'
                                    }}></span>
                                </span>
                            </div>
                        </label>

                        {level === 'ad' && (
                            <>
                                <div style={{ width: '1px', height: '24px', background: 'var(--glass-border)' }}></div>
                                <select
                                    value={filterObservationImported}
                                    onChange={(e) => setFilterObservationImported(e.target.value)}
                                    style={{
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'var(--text-primary)',
                                        fontSize: '0.9rem',
                                        cursor: 'pointer',
                                        outline: 'none',
                                        padding: '6px 10px',
                                        borderRadius: '6px'
                                    }}
                                >
                                    <option value="all">{language === 'zh' ? '全部匯入狀態' : 'All Import Status'}</option>
                                    <option value="imported">{language === 'zh' ? '已送出' : 'Imported'}</option>
                                    <option value="not_imported">{language === 'zh' ? '未送出' : 'Not Imported'}</option>
                                </select>
                            </>
                        )}
                    </div>

                    {activeView === 'custom' && showMetricPanel && (
                        <div style={{ marginTop: '16px', animation: 'fadeIn 0.3s' }}>
                            {ALL_METRIC_GROUPS.map(group => (
                                <div key={group.id} style={{ marginBottom: '16px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <div style={{ fontSize: '0.85rem', color: group.color || 'var(--accent-primary)', fontWeight: 'bold' }}>
                                            {language === 'zh' ? group.label_zh : group.label_en}
                                        </div>
                                        <div style={{ fontSize: '0.75rem', display: 'flex', gap: '8px' }}>
                                            <span
                                                onClick={() => {
                                                    const newSet = new Set(selectedMetrics);
                                                    // Use composite keys
                                                    group.metrics.forEach(m => newSet.add(`${group.id}:${m.key}`));
                                                    setSelectedMetrics(newSet);
                                                }}
                                                style={{ color: 'var(--accent-primary)', cursor: 'pointer', textDecoration: 'underline' }}
                                            >
                                                {language === 'zh' ? '全選' : 'Select All'}
                                            </span>
                                            <span style={{ color: 'var(--text-tertiary)' }}>|</span>
                                            <span
                                                onClick={() => {
                                                    const newSet = new Set(selectedMetrics);
                                                    group.metrics.forEach(m => newSet.delete(`${group.id}:${m.key}`));
                                                    setSelectedMetrics(newSet);
                                                }}
                                                style={{ color: 'var(--accent-primary)', cursor: 'pointer', textDecoration: 'underline' }}
                                            >
                                                {language === 'zh' ? '全消' : 'Deselect All'}
                                            </span>
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                                        {group.metrics.map(metric => (
                                            <label key={metric.key} style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedMetrics.has(`${group.id}:${metric.key}`)}
                                                    onChange={() => toggleMetric(group.id, metric.key)}
                                                    style={{ accentColor: 'var(--accent-primary)' }}
                                                />
                                                {language === 'zh' ? metric.label_zh : metric.label_en}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                            ))}

                            {/* Done / Collapse Button */}
                            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--glass-border)' }}>
                                <button
                                    onClick={() => setShowMetricPanel(false)}
                                    style={{
                                        padding: '8px 24px',
                                        borderRadius: '20px',
                                        background: 'rgba(255,255,255,0.1)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'white',
                                        fontSize: '0.9rem',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        display: 'flex', alignItems: 'center', gap: '8px'
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                                >
                                    <FiChevronUp /> {language === 'zh' ? '完成並收合' : 'Done & Collapse'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>


                {/* Right Panel: Actions */}
                <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    {/* (Same advanced options) */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--text-secondary)' }}>{txt.advanced}</h3>
                        </div>

                        {/* Comparison Toggle */}
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>{txt.compareMode}</span>
                            <label className="switch" style={{ position: 'relative', display: 'inline-block', width: '40px', height: '24px' }}>
                                <input type="checkbox" checked={isCompareMode} onChange={(e) => setIsCompareMode(e.target.checked)} style={{ opacity: 0, width: 0, height: 0 }} />
                                <span style={{
                                    position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0,
                                    backgroundColor: isCompareMode ? 'var(--accent-primary)' : '#ccc', borderRadius: '24px', transition: '.4s'
                                }}>
                                    <span style={{
                                        position: 'absolute', content: "", height: '16px', width: '16px', left: '4px', bottom: '4px',
                                        backgroundColor: 'white', transition: '.4s', borderRadius: '50%',
                                        transform: isCompareMode ? 'translateX(16px)' : 'translateX(0)'
                                    }}></span>
                                </span>
                            </label>
                        </div>

                        {/* Comparison Date Selector (Visible only if enabled) */}
                        {isCompareMode && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', transition: 'all 0.3s' }}>
                                <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>{txt.comparePeriod}</label>
                                <select
                                    value={comparePreset}
                                    onChange={handleComparePresetChange}
                                    style={{
                                        padding: '10px',
                                        borderRadius: '8px',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--glass-border)',
                                        color: 'var(--text-primary)',
                                        width: '100%'
                                    }}
                                >
                                    {COMPARE_PRESETS.map(p => (
                                        <option key={p.value} value={p.value} style={{ color: 'black' }}>
                                            {txt.comparePresets[p.value] || p.label}
                                        </option>
                                    ))}
                                </select>

                                {/* Custom Compare Date Inputs */}
                                {comparePreset === 'custom' && (
                                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                                {language === 'zh' ? '比較開始日期' : 'Compare Start'}
                                            </label>
                                            <input 
                                                type="date" 
                                                value={compareDateRange.since} 
                                                onChange={(e) => setCompareDateRange({ ...compareDateRange, since: e.target.value })}
                                                style={{ 
                                                    padding: '10px', 
                                                    borderRadius: '8px', 
                                                    background: 'rgba(255,255,255,0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    color: 'var(--text-primary)',
                                                    colorScheme: 'dark',
                                                    width: '100%' 
                                                }} 
                                            />
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                                            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                                                {language === 'zh' ? '比較結束日期' : 'Compare End'}
                                            </label>
                                            <input 
                                                type="date" 
                                                value={compareDateRange.until} 
                                                onChange={(e) => setCompareDateRange({ ...compareDateRange, until: e.target.value })}
                                                style={{ 
                                                    padding: '10px', 
                                                    borderRadius: '8px', 
                                                    background: 'rgba(255,255,255,0.05)',
                                                    border: '1px solid var(--glass-border)',
                                                    color: 'var(--text-primary)',
                                                    colorScheme: 'dark',
                                                    width: '100%' 
                                                }} 
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    <button
                        onClick={() => setShowReportModal(true)}
                        style={{
                            marginTop: '20px',
                            padding: '12px 24px',
                            background: 'rgba(255,255,255,0.05)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            color: 'var(--text-primary)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '1rem',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: '8px',
                            opacity: reportData && reportData.length > 0 ? 1 : 0.5,
                            pointerEvents: reportData && reportData.length > 0 ? 'auto' : 'none'
                        }}
                    >
                        <FiFileText /> {language === 'zh' ? '匯出報表' : 'Export Report'}
                    </button>

                    <button
                        onClick={fetchAnalytics}
                        style={{
                            marginTop: '20px',
                            padding: '12px 24px',
                            background: 'var(--accent-primary)',
                            border: 'none',
                            borderRadius: '8px',
                            color: 'white',
                            fontWeight: 600,
                            cursor: 'pointer',
                            fontSize: '1rem',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            gap: '8px'
                        }}
                    >
                        {txt.updateReport}
                    </button>
                </div>
            </div>

            {/* KPI Section */}
            <div>
                {currentSummaryData && (
                    <div ref={kpiRef} className="glass-panel" style={{ marginBottom: '32px', padding: '24px', borderRadius: '16px', position: 'relative' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px' }}>
                            <h2 style={{
                                fontSize: '1.2rem',
                                color: '#fbbf24',
                                display: 'flex',
                                flexDirection: 'row', // Always row, let wrap handle it
                                flexWrap: 'wrap',
                                alignItems: 'baseline',
                                gap: '8px',
                                margin: 0,
                                lineHeight: 1.5
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap' }}>
                                    ⭐ {txt.keyMetrics}
                                </div>
                                <span style={{
                                    fontSize: isMobile ? '0.8rem' : '0.9rem',
                                    color: 'var(--text-secondary)',
                                    fontWeight: 'normal',
                                    lineHeight: isMobile ? '1.4' : 'inherit'
                                }}>
                                    ({dateRange.since} ~ {dateRange.until}
                                    {isCompareMode && prevDateRange.since ? ` vs ${prevDateRange.since} ~ ${prevDateRange.until}` : ''})
                                </span>
                            </h2>

                            {/* More Options Menu */}
                            <div style={{ position: 'relative' }} data-html2canvas-ignore="true">
                                <button
                                    onClick={() => setShowKpiMenu(!showKpiMenu)}
                                    style={{
                                        background: 'transparent',
                                        border: 'none',
                                        color: 'var(--text-secondary)',
                                        fontSize: '1.2rem',
                                        cursor: 'pointer',
                                        padding: '4px',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        transition: 'background 0.2s'
                                    }}
                                    onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                                    onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                >
                                    ⋮
                                </button>

                                {showKpiMenu && (
                                    <div style={{
                                        position: 'absolute',
                                        top: '100%',
                                        right: 0,
                                        marginTop: '8px',
                                        background: '#242526',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '8px',
                                        padding: '4px',
                                        zIndex: 100,
                                        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                                        minWidth: '140px'
                                    }}>
                                        <button
                                            onClick={handleExportImage}
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px',
                                                width: '100%',
                                                padding: '8px 12px',
                                                background: 'transparent',
                                                border: 'none',
                                                color: 'var(--text-primary)',
                                                fontSize: '0.9rem',
                                                cursor: 'pointer',
                                                borderRadius: '4px',
                                                textAlign: 'left'
                                            }}
                                            onMouseEnter={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
                                            onMouseLeave={(e) => e.target.style.background = 'transparent'}
                                        >
                                            ⬇️ {language === 'zh' ? '匯出圖片' : 'Export Image'}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            {ALL_METRIC_GROUPS.map((group, gIdx) => {
                                // Filter metrics for this group that are currently selected using composite key
                                const activeGroupMetrics = group.metrics.filter(m => selectedMetrics.has(`${group.id}:${m.key}`));

                                // If no metrics in this group are selected, don't render the group title or container
                                if (activeGroupMetrics.length === 0) return null;

                                return (
                                    <div key={gIdx}>
                                        <h3 style={{ fontSize: '1rem', color: group.color || '#3b82f6', marginBottom: '12px', borderLeft: `3px solid ${group.color || '#3b82f6'}`, paddingLeft: '8px' }}>
                                            {language === 'zh' ? group.label_zh : group.label_en}
                                        </h3>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                                            {activeGroupMetrics.map(m => {
                                                const currentVal = currentSummaryData ? (currentSummaryData[m.key] || 0) : 0;
                                                const prevVal = prevSummaryData ? (prevSummaryData[m.key] || 0) : null;

                                                // Debug: Log each metric's value
                                                if (m.key === 'ctr') {
                                                    console.log('[Analytics Debug] Rendering CTR card:', {
                                                        key: m.key,
                                                        currentVal,
                                                        raw_value: currentSummaryData?.[m.key],
                                                        summaryData_exists: !!currentSummaryData,
                                                        format: m.format
                                                    });
                                                }

                                                // Diff calculation
                                                let diff = null;
                                                let percent = null;
                                                let isIncrease = false;

                                                if (prevSummaryData) {
                                                    const d = currentVal - prevVal;
                                                    isIncrease = d >= 0;

                                                    // Format Difference
                                                    if (m.format === 'currency') diff = `${d >= 0 ? '+' : ''}$${Math.abs(d).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
                                                    else if (m.format === 'percent') diff = `${d >= 0 ? '+' : ''}${d.toFixed(2)}%`;
                                                    else if (m.format === 'decimal') diff = `${d >= 0 ? '+' : ''}${d.toFixed(2)}`;
                                                    else diff = `${d >= 0 ? '+' : ''}${Math.abs(d).toLocaleString()}`;

                                                    // Calculate Percent Change
                                                    if (prevVal !== 0) {
                                                        const p = (d / prevVal) * 100;
                                                        percent = `${p >= 0 ? '+' : ''}${p.toFixed(1)}%`;
                                                    } else if (currentVal !== 0) {
                                                        percent = '+100%';
                                                    } else {
                                                        percent = '0%';
                                                    }
                                                }

                                                return (
                                                    <KPICard
                                                        key={m.key}
                                                        title={language === 'zh' ? m.label_zh : m.label_en}
                                                        value={renderMetricValue(currentVal, m.format)}
                                                        sub_value={prevSummaryData ? `(${renderMetricValue(prevVal, m.format)})` : ''}
                                                        diff={diff}
                                                        percent={percent}
                                                        is_increase={isIncrease}
                                                        is_inverse={m.isInverse || false}
                                                    />
                                                );
                                            })}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )
                }
            </div>


            {/* NEW: Trend Section (Collapsible) */}
            <TrendSection
                accountId={selectedAccountId}
                dateRange={dateRange}
                prevDateRange={prevDateRange}
                isCompareMode={isCompareMode}
                selectedMetrics={selectedMetrics}
                metricGroups={ALL_METRIC_GROUPS}
                selectedRowIds={selectedRowIds} // Pass selection to filter chart
            />

            <MetaAndromedaImportActions
                canUseObservationImport={canUseObservationImport}
                isMobile={isMobile}
                language={language}
                selectedObservationRows={selectedObservationRows}
                observationImportableRows={observationImportableRows}
                observationWindowKind={observationWindowKind}
                observationBatchSummary={observationBatchSummary}
                handleToggleAllObservationRows={handleToggleAllObservationRows}
                handleBatchObservationImport={handleBatchObservationImport}
            />

            <AnalyticsDataTable
                loading={loading}
                error={error}
                isMobile={isMobile}
                isSidebarCollapsed={isSidebarCollapsed}
                isCompareMode={isCompareMode}
                filteredData={filteredData}
                selectedRowIds={selectedRowIds}
                setSelectedRowIds={setSelectedRowIds}
                txt={txt}
                level={level}
                activeCols={activeCols}
                handleSort={handleSort}
                sortConfig={sortConfig}
                language={language}
                dateRange={dateRange}
                prevDateRange={prevDateRange}
                canUseObservationImport={canUseObservationImport}
                sortedData={sortedData}
                prevReportData={prevReportData}
                renderMetricValue={renderMetricValue}
                selectedObservationIds={selectedObservationIds}
                handleToggleObservationRow={handleToggleObservationRow}
                handleObservationImport={handleObservationImport}
                observationImportState={observationImportState}
                observationWindowKind={observationWindowKind}
                getObservationStatusText={getObservationStatusText}
                getScoreStatusText={getScoreStatusText}
            />

            {/* AI Analyst Slide-over Panel */}
            <div style={{
                position: 'fixed',
                top: 0,
                right: showAiPanel ? 0 : '-500px', // Slide in/out
                width: isMobile ? '100%' : '500px',
                height: '100vh',
                backgroundColor: 'var(--bg-secondary)',
                boxShadow: showAiPanel ? '-4px 0 20px rgba(0,0,0,0.5)' : 'none',
                transition: 'right 0.3s ease',
                zIndex: 2000,
                display: 'flex',
                flexDirection: 'column',
                borderLeft: '1px solid var(--glass-border)'
            }}>
                {/* Header */}
                <div style={{
                    padding: '16px',
                    borderBottom: '1px solid var(--glass-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'var(--bg-primary)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '1.1rem' }}>
                        <FiCpu style={{ color: '#a855f7' }} />
                        <span style={{ background: 'linear-gradient(to right, #6366f1, #a855f7)', WebkitBackgroundClip: 'text', color: 'transparent' }}>
                            {language === 'zh' ? 'AI 廣告分析師' : 'AI Ad Analyst'}
                        </span>
                    </div>
                    <button
                        onClick={() => setShowAiPanel(false)}
                        style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}
                    >
                        <FiX />
                    </button>
                </div>

                {/* Content */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>

                    {!isAnalyzing && !analysisResult && !aiError && (
                        <div style={{ textAlign: 'center', marginTop: '40px', color: 'var(--text-secondary)' }}>
                            <div style={{ fontSize: '3rem', marginBottom: '16px', opacity: 0.5 }}>🤖</div>
                            <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>
                                {language === 'zh' ? '準備好分析您的數據了嗎？' : 'Ready to analyze your data?'}
                            </h3>
                            <p style={{ fontSize: '0.9rem', maxWidth: '80%', margin: '0 auto 24px' }}>
                                {language === 'zh'
                                    ? 'AI 將會讀取您當前選取的報表數據（前 20 筆），並提供見解與優化建議。'
                                    : 'AI will read your current report data (top 20 rows) and provide insights and optimization suggestions.'}
                            </p>
                            <button
                                onClick={handleStartAnalysis}
                                style={{
                                    padding: '10px 24px',
                                    background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    color: 'white',
                                    fontWeight: 'bold',
                                    cursor: 'pointer',
                                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                                    boxShadow: '0 4px 12px rgba(168, 85, 247, 0.4)'
                                }}
                            >
                                <FiZap />
                                {language === 'zh' ? '開始分析' : 'Start Analysis'}
                            </button>
                        </div>
                    )}

                    {
                        isAnalyzing && (
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '60px' }}>
                                <div className="spinner" style={{
                                    width: '40px', height: '40px',
                                    border: '3px solid rgba(168, 85, 247, 0.3)',
                                    borderTop: '3px solid #a855f7',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite'
                                }}></div>
                                <p style={{ marginTop: '16px', color: 'var(--text-secondary)', animation: 'pulse 1.5s infinite' }}>
                                    {language === 'zh' ? 'AI 正在思考中...' : 'AI is thinking...'}
                                </p>
                                {analysisResult && (
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '8px' }}>
                                        {language === 'zh' ? '正在接收分析結果...' : 'Receiving insights...'}
                                    </div>
                                )}
                            </div>
                        )
                    }

                    {
                        aiError && (
                            <div style={{
                                padding: '16px',
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid #ef4444',
                                borderRadius: '8px',
                                color: '#ef4444'
                            }}>
                                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Analysis Failed</div>
                                <div style={{ fontSize: '0.9rem' }}>{aiError}</div>
                                <button
                                    onClick={handleStartAnalysis}
                                    style={{
                                        marginTop: '12px',
                                        padding: '6px 12px',
                                        background: '#ef4444',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem'
                                    }}
                                >
                                    {language === 'zh' ? '重試' : 'Retry'}
                                </button>
                            </div>
                        )
                    }

                    {
                        analysisResult && (
                            <div className="markdown-content" style={{
                                lineHeight: '1.6',
                                fontSize: '0.95rem',
                                color: 'var(--text-primary)',
                                whiteSpace: 'pre-wrap'
                            }}>
                                {/* Simple render for now, replace with ReactMarkdown later if needed */}
                                {analysisResult}
                            </div>
                        )
                    }

                    {/* Bottom Padding */}
                    <div style={{ height: '50px' }}></div>
                </div>
            </div>

            {/* Backdrop */}
            {
                showAiPanel && (
                    <div
                        onClick={() => setShowAiPanel(false)}
                        style={{
                            position: 'fixed',
                            top: 0, left: 0, right: 0, bottom: 0,
                            background: 'rgba(0,0,0,0.5)',
                            zIndex: 1999,
                            backdropFilter: 'blur(2px)'
                        }}
                    />
                )
            }

            <ReportModal
                isOpen={showReportModal}
                onClose={() => setShowReportModal(false)}
                data={reportData || []}
                dateRange={dateRange}
                summaryData={currentSummaryData}
                selectedMetrics={selectedMetrics}
                language={language}
                user={user}
            />
        </div >
    );
};

export default Analytics;
