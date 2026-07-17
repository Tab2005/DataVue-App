import React, { useMemo, useState } from 'react';
import {
    DATE_PRESETS,
    TABS,
    TREND_SUBTABS,
    COUNTRY_NAMES,
    DEVICE_NAMES
} from './GSC/constants';
import {
    getDateRangeFromPreset,
    getTitleFromUrl,
    escapeCSV,
    downloadCSV
} from './GSC/gscUtils';
import { getSortIndicator, GscSummaryCards } from './GSC/GSCShared';
import GSCSettingsPanel from './GSC/GSCSettingsPanel';
import { GSCDataLoadingState, GSCErrorState, GSCInitialLoadingState } from './GSC/GSCUiStates';
import { useGscStyles } from './GSC/useGscStyles';
import TrendTab from './GSC/TrendTab';
import CountryTab from './GSC/CountryTab';
import DeviceTab from './GSC/DeviceTab';
import KeywordGapTab from './GSC/KeywordGapTab';
import DailyTab from './GSC/DailyTab';
import QueryTab from './GSC/QueryTab';
import PageTab from './GSC/PageTab';
import SearchAppearanceTab from './GSC/SearchAppearanceTab';
import { useGscAnalytics } from '../hooks/useGscAnalytics';
import { useGscPageAnalysis } from '../hooks/useGscPageAnalysis';
import { useGscTableData } from '../hooks/useGscTableData';
import { useGscSearchAppearance } from '../hooks/useGscSearchAppearance';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const GSCStats = ({ language, isMobile = false }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;
    const [rowLimit, setRowLimit] = useState(50);

    const queryPageSize = useMemo(() => {
        if (rowLimit === 99999) return 5000;
        return Math.max(rowLimit * 5, 2000);
    }, [rowLimit]);

    const analyticsState = useGscAnalytics({
        apiUrl: API_URL,
        rowLimit,
        queryPageSize
    });

    const {
        sites,
        loading,
        error,
        selectedSite,
        setSelectedSite,
        analytics,
        analyticsLoading,
        queryHasMore,
        queryLoadingMore,
        activeTab,
        setActiveTab,
        datePreset,
        dateRange,
        setDateRange,
        activeDateRange,
        showCustomDate,
        setShowCustomDate,
        compareMode,
        setCompareMode,
        trendSubTab,
        setTrendSubTab,
        trendData,
        trendLoading,
        loadMoreQueryData,
        handlePresetChange,
        handleRunAnalysis,
        handleCustomDateChange,
        getDaysInRange,
        getCompareDateRange,
        calculateChange,
        getCompareTotals
    } = analyticsState;

    const tableData = useGscTableData({
        analytics,
        activeTab,
        trendData,
        trendSubTab,
        selectedSite,
        dateRange,
        rowLimit
    });

    const searchAppearanceState = useGscSearchAppearance({
        apiUrl: API_URL,
        selectedSite,
        activeDateRange,
        activeTab
    });

    const pageAnalysis = useGscPageAnalysis({
        apiUrl: API_URL,
        selectedSite,
        dateRange,
        datePreset,
        activeDateRange,
        activeTab,
        analytics,
        trendData,
        rowLimit,
        setActiveTab,
        language
    });

    const styles = useGscStyles(isMobile);
    const { containerStyle, tabContainerStyle, tabStyle } = styles;
    const { displayData: sortedData, totalCount: sortedDataTotal, hasMore: sortedDataHasMore } = tableData.getSortedFilteredData();
    const showGroupedView = tableData.groupingEnabled && activeTab === 'query' && tableData.groupedData;
    const renderSortIndicator = (key) => getSortIndicator(tableData.sortConfig, key);

    if (loading) return <GSCInitialLoadingState t={t} />;
    if (error) return <GSCErrorState error={error} t={t} />;

    const settingsContext = {
        compareMode,
        datePreset,
        dateRange,
        getCompareDateRange,
        getDaysInRange,
        handleCustomDateChange,
        handlePresetChange,
        handleRunAnalysis,
        isMobile,
        language,
        selectedSite,
        setCompareMode,
        setDateRange,
        setSelectedSite,
        setShowCustomDate,
        showCustomDate,
        sites,
        t
    };

    const tabContext = {
        ...styles,
        ...tableData,
        ...pageAnalysis,
        ...searchAppearanceState,
        activeTab,
        analytics,
        COUNTRY_NAMES,
        DATE_PRESETS,
        DEVICE_NAMES,
        downloadCSV,
        escapeCSV,
        getDateRangeFromPreset,
        getDaysInRange,
        getTitleFromUrl,
        isMobile,
        language,
        loadMoreQueryData,
        queryHasMore,
        queryLoadingMore,
        renderSortIndicator,
        rowLimit,
        setDateRange,
        setRowLimit,
        setTrendSubTab,
        showGroupedView,
        sortedData,
        sortedDataHasMore,
        sortedDataTotal,
        t,
        TREND_SUBTABS,
        trendSubTab
    };

    return (
        <div style={containerStyle}>
            <GSCSettingsPanel context={settingsContext} />

            <div style={tabContainerStyle}>
                {TABS.map(tab => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        style={tabStyle(activeTab === tab.key)}
                    >
                        {language === 'zh' ? tab.label_zh : tab.label_en}
                    </button>
                ))}
            </div>

            {(analyticsLoading || (activeTab === 'trend' && trendLoading)) ? (
                <GSCDataLoadingState t={t} />
            ) : (
                <>
                    <GscSummaryCards
                        analytics={analytics}
                        activeTab={activeTab}
                        compareMode={compareMode}
                        calculateChange={calculateChange}
                        getCompareTotals={getCompareTotals}
                        getDaysInRange={getDaysInRange}
                        isMobile={isMobile}
                        t={t}
                    />

                    {activeTab === 'trend' ? (
                        <TrendTab context={tabContext} />
                    ) : activeTab === 'country' ? (
                        <CountryTab context={tabContext} />
                    ) : activeTab === 'device' ? (
                        <DeviceTab context={tabContext} />
                    ) : activeTab === 'gap' ? (
                        <KeywordGapTab context={tabContext} />
                    ) : activeTab === 'searchAppearance' ? (
                        <SearchAppearanceTab context={tabContext} />
                    ) : activeTab === 'query' ? (
                        <QueryTab context={tabContext} />
                    ) : activeTab === 'page' ? (
                        <PageTab context={tabContext} />
                    ) : (
                        <DailyTab context={tabContext} />
                    )}
                </>
            )}
        </div>
    );
};

export default GSCStats;
