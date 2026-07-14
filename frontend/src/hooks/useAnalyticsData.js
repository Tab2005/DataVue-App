import { useCallback, useEffect, useState } from 'react';
import { format, subDays, subYears, differenceInDays } from 'date-fns';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ESSENTIAL_ANALYTICS_METRICS = [
    'spend', 'impressions', 'link_clicks', 'clicks', 'reach',
    'purchases', 'purchase_value', 'add_to_cart', 'atc_value',
    'view_content', 'initiate_checkout', 'add_payment_info',
    'outbound_clicks',
];

const selectedMetricKeys = (selectedMetrics) => Array.from(selectedMetrics).map((compositeKey) => {
    const parts = compositeKey.split(':');
    return parts.length > 1 ? parts[1] : parts[0];
});

const resolvePreviousRange = ({ comparePreset, compareDateRange, dateRange }) => {
    const startDate = new Date(dateRange.since);
    const endDate = new Date(dateRange.until);
    const diffDays = differenceInDays(endDate, startDate) + 1;

    if (comparePreset === 'year_over_year') {
        return {
            since: format(subYears(startDate, 1), 'yyyy-MM-dd'),
            until: format(subYears(endDate, 1), 'yyyy-MM-dd'),
        };
    }

    if (comparePreset === 'custom') {
        return {
            since: compareDateRange.since || format(subDays(startDate, diffDays), 'yyyy-MM-dd'),
            until: compareDateRange.until || format(subDays(endDate, diffDays), 'yyyy-MM-dd'),
        };
    }

    return {
        since: format(subDays(startDate, diffDays), 'yyyy-MM-dd'),
        until: format(subDays(endDate, diffDays), 'yyyy-MM-dd'),
    };
};

export const useAnalyticsData = ({
    selectedAccountId,
    selectedTeamId,
    user,
    selectedMetrics,
    dateRange,
    level,
    isCompareMode,
    comparePreset,
    compareDateRange,
}) => {
    const [savedViews, setSavedViews] = useState([]);
    const [reportData, setReportData] = useState(null);
    const [prevReportData, setPrevReportData] = useState(null);
    const [prevDateRange, setPrevDateRange] = useState({ since: '', until: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchSavedViews = async () => {
            if (!user?.id) return;
            try {
                const params = new URLSearchParams({ user_id: user.id });
                if (selectedTeamId) params.append('team_id', selectedTeamId);

                const token = localStorage.getItem('google_token');
                const res = await fetch(`${API_BASE}/api/saved-views?${params}`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                if (res.ok) {
                    const data = await res.json();
                    setSavedViews(data);
                }
            } catch (err) {
                console.error('Failed to fetch saved views:', err);
            }
        };

        fetchSavedViews();
    }, [selectedTeamId, user?.id]);

    const fetchAnalytics = useCallback(async () => {
        if (!selectedAccountId || !user) return;

        setLoading(true);
        setError(null);
        try {
            const idToken = localStorage.getItem('google_token');
            const selectedKeys = selectedMetricKeys(selectedMetrics);
            const allKeys = new Set([...selectedKeys, ...ESSENTIAL_ANALYTICS_METRICS]);
            const fieldsParam = Array.from(allKeys).join(',');
            console.log('[Analytics] Requesting fields (with essentials):', fieldsParam);

            const currentQuery = new URLSearchParams({
                account_id: selectedAccountId,
                since: dateRange.since,
                until: dateRange.until,
                level,
            });

            if (fieldsParam) currentQuery.append('fields', fieldsParam);

            const headers = { Authorization: `Bearer ${idToken}` };
            if (selectedTeamId) headers['X-Team-ID'] = selectedTeamId;

            const res = await fetch(`${API_BASE}/api/analytics-data?${currentQuery}`, { headers });

            if (!res.ok) {
                if (res.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                throw new Error('Failed to fetch data');
            }

            const json = await res.json();
            setReportData(json.data);

            if (isCompareMode) {
                const previousRange = resolvePreviousRange({ comparePreset, compareDateRange, dateRange });
                setPrevDateRange(previousRange);

                const prevQuery = new URLSearchParams({
                    account_id: selectedAccountId,
                    since: previousRange.since,
                    until: previousRange.until,
                    level,
                });

                if (fieldsParam) prevQuery.append('fields', fieldsParam);

                const prevRes = await fetch(`${API_BASE}/api/analytics-data?${prevQuery}`, { headers });

                if (prevRes.ok) {
                    const prevJson = await prevRes.json();
                    setPrevReportData(prevJson.data);
                } else {
                    console.warn('Failed to fetch previous data');
                    setPrevReportData([]);
                }
            } else {
                setPrevReportData(null);
            }
        } catch (err) {
            console.error(err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [
        compareDateRange,
        comparePreset,
        dateRange,
        isCompareMode,
        level,
        selectedAccountId,
        selectedMetrics,
        selectedTeamId,
        user,
    ]);

    useEffect(() => {
        if (selectedAccountId) {
            fetchAnalytics();
        }
    }, [fetchAnalytics, selectedAccountId]);

    return {
        savedViews,
        reportData,
        prevReportData,
        prevDateRange,
        loading,
        error,
        fetchAnalytics,
    };
};

export default useAnalyticsData;
