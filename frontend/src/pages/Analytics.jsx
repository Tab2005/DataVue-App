import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import TrendSection from '../components/TrendSection';
import ReportModal from '../components/Analytics/ReportModal';
import AnalyticsDataTable from '../components/Analytics/AnalyticsDataTable';
import MetaAndromedaImportActions from '../components/Analytics/MetaAndromedaImportActions';
import AnalyticsFiltersPanel from '../components/Analytics/AnalyticsFiltersPanel';
import AnalyticsKpiSection from '../components/Analytics/AnalyticsKpiSection';
import AnalyticsAiInsightCard from '../components/Analytics/AnalyticsAiInsightCard';
import { ANALYTICS_TRANSLATIONS } from '../components/Analytics/analyticsTranslations';
import { renderMetricValue } from '../components/Analytics/analyticsSummary';
import { buildAnalyticsAiPayload } from '../components/Analytics/analyticsAiPayload';
import { ALL_METRIC_GROUPS } from '../components/Analytics/analyticsMetrics';
import { useModuleAccess, usePermission } from '../hooks/usePermission';
import useAnalyticsData from '../hooks/useAnalyticsData';
import useAnalyticsMetricSelection from '../hooks/useAnalyticsMetricSelection';
import useAnalyticsDateControls from '../hooks/useAnalyticsDateControls';
import useAnalyticsFilters from '../hooks/useAnalyticsFilters';
import useAnalyticsSort from '../hooks/useAnalyticsSort';
import useAnalyticsSummary from '../hooks/useAnalyticsSummary';
import useAnalyticsObservationSelection from '../hooks/useAnalyticsObservationSelection';
import useAnalyticsKpiExport from '../hooks/useAnalyticsKpiExport';

const Analytics = () => {
    // 1. Get shared context
    const { selectedAccountId, user, language, isSidebarCollapsed, selectedTeamId, isMobile } = useOutletContext();
    const [showReportModal, setShowReportModal] = useState(false);
    const { hasAccess: hasMetaAndromedaAccess } = useModuleAccess('meta_andromeda', selectedTeamId);
    const { hasPermission: hasFbAnalyticsPermission } = usePermission('fb_ads:analytics:view', selectedTeamId);

    const txt = ANALYTICS_TRANSLATIONS[language] || ANALYTICS_TRANSLATIONS.zh;

    // Analysis Level（帳戶/活動/組合/廣告）——多個 hook 共用，留在頁面層
    // （比照 docs/33 第 7 波 ContributionAnalysis.jsx 的 accountId/periodDays
    // 處理方式：真正跨關注點共用的狀態才留頁面層，其餘各自下放到 hook）。
    const [level, setLevel] = useState('account');

    // observationImportState/observationBatchSummary 也留頁面層：
    // useAnalyticsFilters 的篩選需要讀 observationImportState，
    // useAnalyticsObservationSelection 的 observationImportableRows 又需要
    // 篩選後的 filteredData——兩個 hook 互相需要對方的輸出，把這兩個 state
    // 的擁有權留在頁面層兩邊當輸入，避免循環依賴（見
    // useAnalyticsObservationSelection.js 開頭說明）。
    const [observationImportState, setObservationImportState] = useState({});
    const [observationBatchSummary, setObservationBatchSummary] = useState(null);

    // docs/33 第 7 波：每個關注點（指標選擇、日期/比較期間、篩選、排序、
    // KPI 加總、觀測匯入選取、KPI 圖片匯出）各自抽成獨立 hook（原本全部
    // 內嵌在本檔，含一份 114 行的翻譯字典與一份 115 行的 KPI 加總函式）。
    const metricSelection = useAnalyticsMetricSelection();
    const { selectedMetrics, activeCols } = metricSelection;

    const dateControls = useAnalyticsDateControls();
    const { datePreset, dateRange, isCompareMode, comparePreset, compareDateRange } = dateControls;

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

    const { filteredData, filteredPrevData, ...filterState } = useAnalyticsFilters({
        reportData,
        prevReportData,
        observationImportState,
        level,
    });

    const { sortConfig, handleSort, sortedData } = useAnalyticsSort({ filteredData });

    const { selectedRowIds, setSelectedRowIds, currentSummaryData, prevSummaryData } = useAnalyticsSummary({
        filteredData, filteredPrevData,
    });

    const observationSelection = useAnalyticsObservationSelection({
        level, hasMetaAndromedaAccess, hasFbAnalyticsPermission,
        filteredData, datePreset, dateRange, language, selectedAccountId,
        setObservationBatchSummary, setObservationImportState,
    });

    const kpiExport = useAnalyticsKpiExport();

    const buildPayload = () => buildAnalyticsAiPayload({
        sortedData, activeCols, language, currentSummaryData,
        selectedAccountId, selectedTeamId, level, dateRange,
    });

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
                activeView={metricSelection.activeView}
                compareDateRange={compareDateRange}
                comparePreset={comparePreset}
                datePreset={datePreset}
                dateRange={dateRange}
                fetchAnalytics={fetchAnalytics}
                filterActiveOnly={filterState.filterActiveOnly}
                filterKeyword={filterState.filterKeyword}
                filterMode={filterState.filterMode}
                filterObservationImported={filterState.filterObservationImported}
                handleComparePresetChange={dateControls.handleComparePresetChange}
                handlePresetChange={dateControls.handlePresetChange}
                handleViewChange={metricSelection.handleViewChange}
                isCompareMode={isCompareMode}
                isMobile={isMobile}
                language={language}
                level={level}
                reportData={reportData}
                savedViews={savedViews}
                selectedMetrics={selectedMetrics}
                setActiveView={metricSelection.setActiveView}
                setCompareDateRange={dateControls.setCompareDateRange}
                setDateRange={dateControls.setDateRange}
                setFilterActiveOnly={filterState.setFilterActiveOnly}
                setFilterKeyword={filterState.setFilterKeyword}
                setFilterMode={filterState.setFilterMode}
                setFilterObservationImported={filterState.setFilterObservationImported}
                setIsCompareMode={dateControls.setIsCompareMode}
                setLevel={setLevel}
                setSelectedMetrics={metricSelection.setSelectedMetrics}
                setShowMetricPanel={metricSelection.setShowMetricPanel}
                setShowReportModal={setShowReportModal}
                showMetricPanel={metricSelection.showMetricPanel}
                toggleMetric={metricSelection.toggleMetric}
                txt={txt}
            />

            <AnalyticsKpiSection
                currentSummaryData={currentSummaryData}
                dateRange={dateRange}
                handleExportImage={kpiExport.handleExportImage}
                isCompareMode={isCompareMode}
                isMobile={isMobile}
                language={language}
                kpiRef={kpiExport.kpiRef}
                prevDateRange={prevDateRange}
                prevSummaryData={prevSummaryData}
                renderMetricValue={renderMetricValue}
                selectedMetrics={selectedMetrics}
                setShowKpiMenu={kpiExport.setShowKpiMenu}
                showKpiMenu={kpiExport.showKpiMenu}
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
                canUseObservationImport={observationSelection.canUseObservationImport}
                isMobile={isMobile}
                language={language}
                selectedObservationRows={observationSelection.selectedObservationRows}
                observationImportableRows={observationSelection.observationImportableRows}
                observationWindowKind={observationSelection.observationWindowKind}
                observationBatchSummary={observationBatchSummary}
                observationImportState={observationImportState}
                handleToggleAllObservationRows={observationSelection.handleToggleAllObservationRows}
                handleBatchObservationImport={observationSelection.handleBatchObservationImport}
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
                canUseObservationImport={observationSelection.canUseObservationImport}
                sortedData={sortedData}
                prevReportData={prevReportData}
                renderMetricValue={renderMetricValue}
                selectedObservationIds={observationSelection.selectedObservationIds}
                handleToggleObservationRow={observationSelection.handleToggleObservationRow}
                handleObservationImport={observationSelection.handleObservationImport}
                observationImportState={observationImportState}
                observationWindowKind={observationSelection.observationWindowKind}
                getObservationStatusText={observationSelection.getObservationStatusText}
                getScoreStatusText={observationSelection.getScoreStatusText}
            />

            <AnalyticsAiInsightCard
                language={language}
                buildPayload={buildPayload}
                contextLabel={`${txt.levels[level]}; ${dateRange.since} ~ ${dateRange.until}`}
                disabled={activeCols.length === 0 || !sortedData || sortedData.length === 0}
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
        </div>
    );
};

export default Analytics;
