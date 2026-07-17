import React from 'react';
import { TABS } from './constants';
import BehaviorSection, { BehaviorControls } from './BehaviorSection';
import ContentSection, { ContentControls } from './ContentSection';
import EcommerceSection, { EcommerceControls } from './EcommerceSection';
import OverviewSection from './OverviewSection';
import TrafficSection, { TrafficControls } from './TrafficSection';

const GA4ContentPanel = ({
    activeTab,
    analyticsData,
    behaviorDimension,
    behaviorFilter,
    compareMode,
    contentDimension,
    contentGroups,
    contentTypeFilter,
    currentPage,
    ecommerceDimension,
    ecommerceFilter,
    ecommerceSecondaryDimension,
    ecommerceSecondaryFilter,
    error,
    ga4HasMore,
    ga4LoadingMore,
    getBehaviorColumnLabel,
    getBehaviorColumnOrder,
    getContentColumnLabel,
    getContentColumnOrder,
    getEcommerceColumnLabel,
    getEcommerceColumnOrder,
    getMetricLabel,
    getTrafficColumnLabel,
    getTrafficColumnOrder,
    isMobile,
    itemsPerPage,
    kpiData,
    language,
    loadMoreGa4Data,
    loading,
    selectedProperty,
    setActiveTab,
    setBehaviorDimension,
    setBehaviorFilter,
    setContentDimension,
    setContentTypeFilter,
    setCurrentPage,
    setEcommerceDimension,
    setEcommerceFilter,
    setEcommerceSecondaryDimension,
    setEcommerceSecondaryFilter,
    setEditingContentGroup,
    setEditingGroup,
    setItemsPerPage,
    setShowContentGroupModal,
    setShowGroupModal,
    setSortConfig,
    setSourceFilter,
    setTrafficDimension,
    sortConfig,
    sourceFilter,
    sourceGroups,
    t,
    trafficDimension
}) => (
    <div className="glass-panel" style={{
                padding: isMobile ? '16px' : '24px',
                borderRadius: '16px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--glass-border)',
                backdropFilter: 'blur(10px)'
            }}>
                {/* Tab Navigation */}
                <div style={{
                    display: 'flex',
                    borderBottom: '1px solid var(--glass-border)',
                    marginBottom: '24px',
                    overflowX: 'auto'
                }}>

                    {TABS.map(tab => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            style={{
                                padding: '12px 16px',
                                border: 'none',
                                background: activeTab === tab.key ? 'var(--accent-primary)' : 'transparent',
                                color: activeTab === tab.key ? 'white' : 'var(--text-secondary)',
                                borderRadius: '8px 8px 0 0',
                                fontSize: '14px',
                                fontWeight: '500',
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                marginRight: '4px'
                            }}
                        >
                            {language === 'zh' ? tab.label_zh : tab.label_en}
                        </button>
                    ))}
                </div>

                {/* Traffic Tab Controls */}
                {activeTab === 'traffic' && (
                    <TrafficControls
                        analyticsData={analyticsData}
                        isMobile={isMobile}
                        language={language}
                        setEditingGroup={setEditingGroup}
                        setShowGroupModal={setShowGroupModal}
                        setSourceFilter={setSourceFilter}
                        setTrafficDimension={setTrafficDimension}
                        sourceFilter={sourceFilter}
                        sourceGroups={sourceGroups}
                        t={t}
                        trafficDimension={trafficDimension}
                    />
                )}

                {/* Behavior Tab Controls */}
                {activeTab === 'behavior' && (
                    <BehaviorControls
                        analyticsData={analyticsData}
                        behaviorDimension={behaviorDimension}
                        behaviorFilter={behaviorFilter}
                        isMobile={isMobile}
                        language={language}
                        setBehaviorDimension={setBehaviorDimension}
                        setBehaviorFilter={setBehaviorFilter}
                        t={t}
                    />
                )}
                {/* Ecommerce Tab Controls */}
                {activeTab === 'ecommerce' && (
                    <EcommerceControls
                        analyticsData={analyticsData}
                        ecommerceDimension={ecommerceDimension}
                        ecommerceFilter={ecommerceFilter}
                        ecommerceSecondaryDimension={ecommerceSecondaryDimension}
                        ecommerceSecondaryFilter={ecommerceSecondaryFilter}
                        isMobile={isMobile}
                        language={language}
                        setEcommerceDimension={setEcommerceDimension}
                        setEcommerceFilter={setEcommerceFilter}
                        setEcommerceSecondaryDimension={setEcommerceSecondaryDimension}
                        setEcommerceSecondaryFilter={setEcommerceSecondaryFilter}
                        setEditingGroup={setEditingGroup}
                        setShowGroupModal={setShowGroupModal}
                        sourceGroups={sourceGroups}
                        t={t}
                    />
                )}
                {/* Content Tab Controls */}
                {activeTab === 'content' && (
                    <ContentControls
                        contentDimension={contentDimension}
                        contentGroups={contentGroups}
                        contentTypeFilter={contentTypeFilter}
                        isMobile={isMobile}
                        language={language}
                        setContentDimension={setContentDimension}
                        setContentTypeFilter={setContentTypeFilter}
                        setEditingContentGroup={setEditingContentGroup}
                        setShowContentGroupModal={setShowContentGroupModal}
                        t={t}
                    />
                )}
                <GA4LoadingState loading={loading} t={t} />
                <GA4ErrorState error={error} />
                <GA4KpiCards
                    compareMode={compareMode}
                    error={error}
                    isMobile={isMobile}
                    kpiData={kpiData}
                    loading={loading}
                    t={t}
                />
                {/* Data Table Placeholder */}
                {!loading && !error && analyticsData && activeTab === 'overview' && (
                    <OverviewSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getMetricLabel={getMetricLabel}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'traffic' && (
                    <TrafficSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getTrafficColumnLabel={getTrafficColumnLabel}
                        getTrafficColumnOrder={getTrafficColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'behavior' && (
                    <BehaviorSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getBehaviorColumnLabel={getBehaviorColumnLabel}
                        getBehaviorColumnOrder={getBehaviorColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'ecommerce' && (
                    <EcommerceSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getEcommerceColumnLabel={getEcommerceColumnLabel}
                        getEcommerceColumnOrder={getEcommerceColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}

                {!loading && !error && analyticsData && activeTab === 'content' && (
                    <ContentSection
                        analyticsData={analyticsData}
                        currentPage={currentPage}
                        ga4HasMore={ga4HasMore}
                        ga4LoadingMore={ga4LoadingMore}
                        getContentColumnLabel={getContentColumnLabel}
                        getContentColumnOrder={getContentColumnOrder}
                        isMobile={isMobile}
                        itemsPerPage={itemsPerPage}
                        loadMoreGa4Data={loadMoreGa4Data}
                        setCurrentPage={setCurrentPage}
                        setItemsPerPage={setItemsPerPage}
                        setSortConfig={setSortConfig}
                        sortConfig={sortConfig}
                        t={t}
                    />
                )}
                <GA4NoDataState
                    analyticsData={analyticsData}
                    error={error}
                    loading={loading}
                    selectedProperty={selectedProperty}
                    t={t}
                />
            </div>
);

export default GA4ContentPanel;
