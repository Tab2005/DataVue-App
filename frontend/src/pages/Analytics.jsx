import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import html2canvas from 'html2canvas';
import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, subMonths, differenceInDays } from 'date-fns';
import TrendSection from '../components/TrendSection';
// New modular imports
import { VIEW_PRESETS } from '../constants/analyticsConfig';
import ReportModal from '../components/Analytics/ReportModal';
import AnalyticsDataTable from '../components/Analytics/AnalyticsDataTable';
import MetaAndromedaImportActions from '../components/Analytics/MetaAndromedaImportActions';
import AnalyticsFiltersPanel from '../components/Analytics/AnalyticsFiltersPanel';
import AnalyticsKpiSection from '../components/Analytics/AnalyticsKpiSection';
import AnalyticsAiPanel from '../components/Analytics/AnalyticsAiPanel';
// Import Metrics Registry for extended metrics support
import { useModuleAccess, usePermission } from '../hooks/usePermission';
import useAnalyticsData from '../hooks/useAnalyticsData';
import useAnalyticsObservationImport from '../hooks/useAnalyticsObservationImport';
import { ALL_METRIC_GROUPS, METRIC_GROUPS, resolveObservationWindowKind } from '../components/Analytics/analyticsMetrics';

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

    const {
        handleBatchObservationImport,
        handleObservationImport,
    } = useAnalyticsObservationImport({
        datePreset,
        dateRange,
        language,
        selectedAccountId,
        selectedObservationRows,
        setObservationBatchSummary,
        setObservationImportState,
    });

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
        };

        // Recalculate derived rates
        total.cpc = total.link_clicks > 0 ? total.spend / total.link_clicks : 0;
        total.cpm = total.impressions > 0 ? (total.spend / total.impressions) * 1000 : 0;

        total.cpa = total.purchases > 0 ? total.spend / total.purchases : 0;
        total.cost_per_atc = total.add_to_cart > 0 ? total.spend / total.add_to_cart : 0;
        total.roas = total.spend > 0 ? total.purchase_value / total.spend : 0;
        total.shared_roas = total.spend > 0 ? total.shared_purchase_value / total.spend : 0;

        // CTR fields: per-row CTR values are rates (clicks/impressions), so they must be
        // recomputed from the summed raw counts (weighted average), never summed directly -
        // summing rates across rows inflates the total (e.g. 10 days at 2% becomes "20%").
        total.ctr = total.impressions > 0 ? (total.clicks / total.impressions) * 100 : 0;
        total.inline_link_click_ctr = total.impressions > 0 ? (total.link_clicks / total.impressions) * 100 : 0;
        total.unique_ctr = total.reach > 0 ? (total.unique_clicks / total.reach) * 100 : 0;
        total.outbound_clicks_ctr = total.impressions > 0 ? (total.outbound_clicks / total.impressions) * 100 : 0;

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

            <AnalyticsFiltersPanel
                activeView={activeView}
                compareDateRange={compareDateRange}
                comparePreset={comparePreset}
                datePreset={datePreset}
                dateRange={dateRange}
                fetchAnalytics={fetchAnalytics}
                filterActiveOnly={filterActiveOnly}
                filterKeyword={filterKeyword}
                filterMode={filterMode}
                filterObservationImported={filterObservationImported}
                handleComparePresetChange={handleComparePresetChange}
                handlePresetChange={handlePresetChange}
                handleViewChange={handleViewChange}
                isCompareMode={isCompareMode}
                isMobile={isMobile}
                language={language}
                level={level}
                reportData={reportData}
                savedViews={savedViews}
                selectedMetrics={selectedMetrics}
                setActiveView={setActiveView}
                setCompareDateRange={setCompareDateRange}
                setDateRange={setDateRange}
                setFilterActiveOnly={setFilterActiveOnly}
                setFilterKeyword={setFilterKeyword}
                setFilterMode={setFilterMode}
                setFilterObservationImported={setFilterObservationImported}
                setIsCompareMode={setIsCompareMode}
                setLevel={setLevel}
                setSelectedMetrics={setSelectedMetrics}
                setShowAiPanel={setShowAiPanel}
                setShowMetricPanel={setShowMetricPanel}
                setShowReportModal={setShowReportModal}
                showMetricPanel={showMetricPanel}
                toggleMetric={toggleMetric}
                txt={txt}
            />

            <AnalyticsKpiSection
                currentSummaryData={currentSummaryData}
                dateRange={dateRange}
                handleExportImage={handleExportImage}
                isCompareMode={isCompareMode}
                isMobile={isMobile}
                language={language}
                kpiRef={kpiRef}
                prevDateRange={prevDateRange}
                prevSummaryData={prevSummaryData}
                renderMetricValue={renderMetricValue}
                selectedMetrics={selectedMetrics}
                setShowKpiMenu={setShowKpiMenu}
                showKpiMenu={showKpiMenu}
                txt={txt}
            />

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

            <AnalyticsAiPanel
                aiError={aiError}
                analysisResult={analysisResult}
                handleStartAnalysis={handleStartAnalysis}
                isAnalyzing={isAnalyzing}
                isMobile={isMobile}
                language={language}
                setShowAiPanel={setShowAiPanel}
                showAiPanel={showAiPanel}
            />

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
