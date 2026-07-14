import React from 'react';
import { screen } from '@testing-library/react';

import Analytics from '../Analytics';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import useAnalyticsData from '../../hooks/useAnalyticsData';
import { useModuleAccess, usePermission } from '../../hooks/usePermission';

vi.mock('html2canvas', () => ({
    default: vi.fn(),
}));

vi.mock('../../components/KPICard', () => ({
    default: ({ title, value }) => (
        <div data-testid="kpi-card">
            {title}: {value}
        </div>
    ),
}));

vi.mock('../../components/TrendSection', () => ({
    default: () => <div data-testid="trend-section" />,
}));

vi.mock('../../components/Analytics/ReportModal', () => ({
    default: () => null,
}));

vi.mock('../../components/Analytics/AnalyticsDataTable', () => ({
    default: () => <div data-testid="analytics-data-table" />,
}));

vi.mock('../../components/Analytics/MetaAndromedaImportActions', () => ({
    default: ({ observationWindowKind }) => (
        <div data-testid="meta-andromeda-import-actions">
            {observationWindowKind}
        </div>
    ),
}));

vi.mock('../../hooks/useAnalyticsData', () => ({
    default: vi.fn(),
}));

vi.mock('../../hooks/usePermission', () => ({
    useModuleAccess: vi.fn(),
    usePermission: vi.fn(),
}));

vi.mock('../../services/metaAndromedaWorkflowService', () => ({
    fetchMetaAndromedaAiReady: vi.fn(),
    fetchMetaAndromedaObservedImportStatus: vi.fn(),
    importMetaAndromedaObservedFacebookAd: vi.fn(),
}));

describe('Analytics', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });
        useAnalyticsData.mockReturnValue({
            savedViews: [],
            reportData: [],
            prevReportData: [],
            prevDateRange: null,
            loading: false,
            error: null,
            fetchAnalytics: vi.fn(),
        });
    });

    it('renders the account-level analytics page without tripping runtime reference errors', () => {
        renderWithOutlet(<Analytics />, {
            route: '/analytics',
            path: '/analytics',
            outletContext: {
                selectedAccountId: 'act_001',
                selectedTeamId: 'team_001',
                user: { id: 'user_001', email: 'tester@example.com' },
                language: 'zh',
                isMobile: false,
                isSidebarCollapsed: false,
            },
        });

        expect(screen.getByRole('heading', { name: '深度成效分析' })).toBeInTheDocument();
        expect(screen.getByTestId('meta-andromeda-import-actions')).toHaveTextContent('last_7d');
        expect(screen.getByTestId('analytics-data-table')).toBeInTheDocument();
    });
});
