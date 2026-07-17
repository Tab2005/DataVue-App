import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { getAllSourceGroups } from '../utils/sourceGroups';
import { getAllContentGroups } from '../utils/contentGroups';
import {
    TRAFFIC_METRICS,
    TRAFFIC_COLUMN_HEADERS,
    BEHAVIOR_METRICS,
    BEHAVIOR_COLUMN_HEADERS,
    ECOMMERCE_METRICS,
    ECOMMERCE_COLUMN_HEADERS,
    CONTENT_METRICS,
    CONTENT_COLUMN_HEADERS,
} from './GA4/constants';
import {
    getMetricLabel as getMetricLabelForLanguage,
    getTrafficColumnOrder as getTrafficColumnOrderForDimension,
    getTrafficColumnLabel as getTrafficColumnLabelForLanguage,
    getBehaviorColumnOrder as getBehaviorColumnOrderForDimension,
    getBehaviorColumnLabel as getBehaviorColumnLabelForLanguage,
    getEcommerceColumnOrder as getEcommerceColumnOrderForDimensions,
    getEcommerceColumnLabel as getEcommerceColumnLabelForLanguage,
    getContentColumnOrder as getContentColumnOrderForDimension,
    getContentColumnLabel as getContentColumnLabelForLanguage
} from './GA4/ga4Formatters';
import {
    getOverviewKPIData,
    getTrafficKPIData,
    getBehaviorKPIData,
    getEcommerceKPIData,
    getContentKPIData
} from './GA4/ga4Kpi';
import GA4ContentPanel from './GA4/GA4ContentPanel';
import GA4GroupModals from './GA4/GA4GroupModals';
import GA4SettingsPanel from './GA4/GA4SettingsPanel';
import { useGa4StatsData } from '../hooks/useGa4StatsData';


const GA4Stats = ({ language, isMobile }) => {
    const t = (zh, en) => language === 'zh' ? zh : en;

    // Table Pagination State
    const [currentPage, setCurrentPage] = useState(1);
    const [itemsPerPage, setItemsPerPage] = useState(20);

    const ga4PageSize = useMemo(() => {
        return Math.max(itemsPerPage * 10, 1000);
    }, [itemsPerPage]);

    // Traffic Tab State
    const [trafficDimension, setTrafficDimension] = useState('sessionDefaultChannelGrouping');
    const [sourceFilter, setSourceFilter] = useState('all'); // 'all' or specific source value
    const [sourceGroups, setSourceGroups] = useState([]);
    const [showGroupModal, setShowGroupModal] = useState(false);
    const [editingGroup, setEditingGroup] = useState(null);

    // Behavior Tab State
    const [behaviorDimension, setBehaviorDimension] = useState('deviceCategory');
    const [behaviorFilter, setBehaviorFilter] = useState('all'); // 'all' or specific value

    // Ecommerce Tab State
    const [ecommerceDimension, setEcommerceDimension] = useState('itemName');
    const [ecommerceSecondaryDimension, setEcommerceSecondaryDimension] = useState('none');
    const [ecommerceFilter, setEcommerceFilter] = useState('all');
    const [ecommerceSecondaryFilter, setEcommerceSecondaryFilter] = useState('all');

    // Content Tab State
    const [contentDimension, setContentDimension] = useState('pageTitle');
    const [contentTypeFilter, setContentTypeFilter] = useState('all');
    const [contentGroups, setContentGroups] = useState([]);
    const [showContentGroupModal, setShowContentGroupModal] = useState(false);
    const [editingContentGroup, setEditingContentGroup] = useState(null);

    const {
        properties,
        propertiesLoading,
        selectedProperty,
        setSelectedProperty,
        analyticsData,
        summaryData,
        compareData,
        compareSummaryData,
        loading,
        error,
        activeTab,
        setActiveTab,
        ga4HasMore,
        ga4LoadingMore,
        compareMode,
        setCompareMode,
        dateRange,
        setDateRange,
        fetchAnalytics,
        loadMoreGa4Data,
        handleDatePresetChange,
        getCompareDateRange,
        handleCustomDateChange
    } = useGa4StatsData({
        trafficDimension,
        behaviorDimension,
        ecommerceDimension,
        ecommerceSecondaryDimension,
        contentDimension,
        ga4PageSize,
        setCurrentPage
    });

    const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

    // Load source groups when property changes
    useEffect(() => {
        if (selectedProperty) {
            setSourceGroups(getAllSourceGroups(selectedProperty));
        }
    }, [selectedProperty]);

    // Reload source groups (called after add/edit/delete)
    const reloadSourceGroups = useCallback(() => {
        if (selectedProperty) {
            setSourceGroups(getAllSourceGroups(selectedProperty));
        }
    }, [selectedProperty]);

    // Load content groups when property changes
    useEffect(() => {
        if (selectedProperty) {
            setContentGroups(getAllContentGroups(selectedProperty));
        }
    }, [selectedProperty]);

    // Reload content groups (called after add/edit/delete)
    const reloadContentGroups = useCallback(() => {
        if (selectedProperty) {
            setContentGroups(getAllContentGroups(selectedProperty));
        }
    }, [selectedProperty]);


    const getMetricLabel = (metric) => getMetricLabelForLanguage(metric, language);

    const getTrafficColumnOrder = () => getTrafficColumnOrderForDimension(trafficDimension);

    const getTrafficColumnLabel = (col) => getTrafficColumnLabelForLanguage(col, language);

    const getBehaviorColumnOrder = () => getBehaviorColumnOrderForDimension(behaviorDimension);

    const getBehaviorColumnLabel = (col) => getBehaviorColumnLabelForLanguage(col, language);

    const getEcommerceColumnOrder = () => getEcommerceColumnOrderForDimensions(ecommerceDimension, ecommerceSecondaryDimension);

    const getEcommerceColumnLabel = (col) => getEcommerceColumnLabelForLanguage(col, language);

    const getContentColumnOrder = () => getContentColumnOrderForDimension(contentDimension);

    const getContentColumnLabel = (col) => getContentColumnLabelForLanguage(col, language);

    // Reset source filter when dimension changes (for traffic tab)
    useEffect(() => {
        setSourceFilter('all');
    }, [trafficDimension]);

    // Reset behavior filter when dimension changes (for behavior tab)
    useEffect(() => {
        setBehaviorFilter('all');
    }, [behaviorDimension]);

    // Reset ecommerce filters when dimensions change
    useEffect(() => {
        setEcommerceFilter('all');
    }, [ecommerceDimension]);

    useEffect(() => {
        setEcommerceSecondaryFilter('all');
    }, [ecommerceSecondaryDimension]);

    // Reset pagination when tab, filters, or data changes
    useEffect(() => {
        setCurrentPage(1);
    }, [activeTab, trafficDimension, sourceFilter, behaviorDimension, behaviorFilter, ecommerceDimension, ecommerceSecondaryDimension, ecommerceFilter, ecommerceSecondaryFilter, contentDimension, contentTypeFilter, analyticsData]);

    // Reset content filter when dimension changes
    useEffect(() => {
        setContentTypeFilter('all');
    }, [contentDimension]);


    // Use tab-specific KPIs
    const kpiData = useMemo(() => {
        const shared = { analyticsData, compareData, compareMode, language };
        if (activeTab === 'traffic') {
            return getTrafficKPIData({ ...shared, sourceFilter, sourceGroups, trafficDimension });
        } else if (activeTab === 'behavior') {
            return getBehaviorKPIData({ ...shared, behaviorFilter, behaviorDimension });
        } else if (activeTab === 'ecommerce') {
            return getEcommerceKPIData({ ...shared, ecommerceFilter, ecommerceDimension, ecommerceSecondaryFilter, ecommerceSecondaryDimension, sourceGroups });
        } else if (activeTab === 'content') {
            return getContentKPIData({ ...shared, contentTypeFilter, contentGroups, contentDimension });
        }
        return getOverviewKPIData({ ...shared, summaryData, compareSummaryData });
    }, [analyticsData, summaryData, compareData, compareSummaryData, compareMode, activeTab, sourceFilter, sourceGroups, trafficDimension, behaviorFilter, behaviorDimension, ecommerceFilter, ecommerceDimension, ecommerceSecondaryFilter, ecommerceSecondaryDimension, contentDimension, contentTypeFilter, contentGroups, language]);


    return (
        <div style={{ width: '100%', padding: isMobile ? '16px' : '24px' }}>
            <GA4SettingsPanel
                compareMode={compareMode}
                dateRange={dateRange}
                fetchAnalytics={fetchAnalytics}
                getCompareDateRange={getCompareDateRange}
                handleCustomDateChange={handleCustomDateChange}
                handleDatePresetChange={handleDatePresetChange}
                isMobile={isMobile}
                language={language}
                loading={loading}
                properties={properties}
                propertiesLoading={propertiesLoading}
                selectedProperty={selectedProperty}
                setCompareMode={setCompareMode}
                setDateRange={setDateRange}
                setSelectedProperty={setSelectedProperty}
                t={t}
            />

            <GA4ContentPanel
                activeTab={activeTab}
                analyticsData={analyticsData}
                behaviorDimension={behaviorDimension}
                behaviorFilter={behaviorFilter}
                compareMode={compareMode}
                contentDimension={contentDimension}
                contentGroups={contentGroups}
                contentTypeFilter={contentTypeFilter}
                currentPage={currentPage}
                ecommerceDimension={ecommerceDimension}
                ecommerceFilter={ecommerceFilter}
                ecommerceSecondaryDimension={ecommerceSecondaryDimension}
                ecommerceSecondaryFilter={ecommerceSecondaryFilter}
                error={error}
                ga4HasMore={ga4HasMore}
                ga4LoadingMore={ga4LoadingMore}
                getBehaviorColumnLabel={getBehaviorColumnLabel}
                getBehaviorColumnOrder={getBehaviorColumnOrder}
                getContentColumnLabel={getContentColumnLabel}
                getContentColumnOrder={getContentColumnOrder}
                getEcommerceColumnLabel={getEcommerceColumnLabel}
                getEcommerceColumnOrder={getEcommerceColumnOrder}
                getMetricLabel={getMetricLabel}
                getTrafficColumnLabel={getTrafficColumnLabel}
                getTrafficColumnOrder={getTrafficColumnOrder}
                isMobile={isMobile}
                itemsPerPage={itemsPerPage}
                kpiData={kpiData}
                language={language}
                loadMoreGa4Data={loadMoreGa4Data}
                loading={loading}
                selectedProperty={selectedProperty}
                setActiveTab={setActiveTab}
                setBehaviorDimension={setBehaviorDimension}
                setBehaviorFilter={setBehaviorFilter}
                setContentDimension={setContentDimension}
                setContentTypeFilter={setContentTypeFilter}
                setCurrentPage={setCurrentPage}
                setEcommerceDimension={setEcommerceDimension}
                setEcommerceFilter={setEcommerceFilter}
                setEcommerceSecondaryDimension={setEcommerceSecondaryDimension}
                setEcommerceSecondaryFilter={setEcommerceSecondaryFilter}
                setEditingContentGroup={setEditingContentGroup}
                setEditingGroup={setEditingGroup}
                setItemsPerPage={setItemsPerPage}
                setShowContentGroupModal={setShowContentGroupModal}
                setShowGroupModal={setShowGroupModal}
                setSortConfig={setSortConfig}
                setSourceFilter={setSourceFilter}
                setTrafficDimension={setTrafficDimension}
                sortConfig={sortConfig}
                sourceFilter={sourceFilter}
                sourceGroups={sourceGroups}
                t={t}
                trafficDimension={trafficDimension}
            />

            <GA4GroupModals
                analyticsData={analyticsData}
                contentDimension={contentDimension}
                editingContentGroup={editingContentGroup}
                editingGroup={editingGroup}
                language={language}
                reloadContentGroups={reloadContentGroups}
                reloadSourceGroups={reloadSourceGroups}
                selectedProperty={selectedProperty}
                setContentTypeFilter={setContentTypeFilter}
                setEditingContentGroup={setEditingContentGroup}
                setEditingGroup={setEditingGroup}
                setShowContentGroupModal={setShowContentGroupModal}
                setShowGroupModal={setShowGroupModal}
                showContentGroupModal={showContentGroupModal}
                showGroupModal={showGroupModal}
            />
        </div>
    );

};
export default GA4Stats;
