import React from 'react';

import { MonitoringCampaignTrendPanel } from './MonitoringCampaignTrendPanel';
import { MonitoringDriftDiagnosticsDrawer } from './MonitoringDriftDiagnosticsDrawer';
import { MonitoringDriftReportsPanel } from './MonitoringDriftReportsPanel';
import { MonitoringEventsPanel } from './MonitoringEventsPanel';
import { MonitoringHeaderFilters } from './MonitoringHeaderFilters';
import { MonitoringModelSettingsPanel } from './MonitoringModelSettingsPanel';
import { MonitoringOverviewPanel } from './MonitoringOverviewPanel';
import { MonitoringScoringProfilesPanel } from './MonitoringScoringProfilesPanel';
import { infoPanelStyle, panelStyle } from './shared';

export const MonitoringDashboard = ({ isMobile, monitoring }) => {
    const {
        loading,
        hasAccess,
        loadingModuleAccess,
        t,
    } = monitoring;

    if (loadingModuleAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <div style={panelStyle}>{t('Checking workspace access...', '正在檢查工作區模組權限...')}</div>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <div style={infoPanelStyle}>
                    {t(
                        'You do not have access to Meta Andromeda in this workspace.',
                        '你目前沒有此工作區的 Meta Andromeda 模組存取權限。'
                    )}
                </div>
            </div>
        );
    }

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <MonitoringHeaderFilters isMobile={isMobile} monitoring={monitoring} />

            {loading ? (
                <div style={panelStyle}>{t('Loading monitoring summary...', '正在載入監控資料...')}</div>
            ) : (
                <>
                    <MonitoringOverviewPanel isMobile={isMobile} monitoring={monitoring} />

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)',
                        gap: '16px'
                    }}>
                        <MonitoringEventsPanel isMobile={isMobile} monitoring={monitoring} />
                        <MonitoringDriftReportsPanel isMobile={isMobile} monitoring={monitoring} />
                        <MonitoringScoringProfilesPanel isMobile={isMobile} monitoring={monitoring} />
                        <MonitoringModelSettingsPanel isMobile={isMobile} monitoring={monitoring} />
                    </div>
                </>
            )}

            <MonitoringCampaignTrendPanel monitoring={monitoring} />
            <MonitoringDriftDiagnosticsDrawer isMobile={isMobile} monitoring={monitoring} />
        </div>
    );
};
