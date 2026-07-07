import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import ContributionAnalysis from '../ContributionAnalysis';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import {
    createAnalysis,
    getGroups,
    listAnalyses,
    listCampaignSummaries,
    refreshContributionData,
} from '../../services/contributionService';

vi.mock('../../services/contributionService', () => ({
    createAnalysis: vi.fn(),
    getGroups: vi.fn(),
    listAnalyses: vi.fn(),
    listCampaignSummaries: vi.fn(),
    refreshContributionData: vi.fn(),
    updateGroups: vi.fn(),
    getAnalysis: vi.fn(),
    pingContribution: vi.fn(),
}));

vi.mock('../../hooks/usePermission', () => ({
    usePermission: vi.fn(),
    useModuleAccess: vi.fn(),
    useUserModules: vi.fn(() => ({ modules: ['contribution'], loading: false, error: null, refetch: vi.fn() })),
}));

vi.mock('../../services/teamService', () => ({
    TeamService: {
        getAllAdAccounts: vi.fn().mockResolvedValue([
            { id: 'act_001', name: '測試帳戶' },
        ]),
    },
}));

const usePermission = (await import('../../hooks/usePermission')).usePermission;
const useModuleAccess = (await import('../../hooks/usePermission')).useModuleAccess;

describe('ContributionAnalysis', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        listCampaignSummaries.mockResolvedValue({ account_id: 'act_001', campaigns: [], total: 0 });
        getGroups.mockResolvedValue({ account_id: 'act_001', groups: [], source: 'auto' });
        listAnalyses.mockResolvedValue({ account_id: 'act_001', analyses: [], total: 0 });
        refreshContributionData.mockResolvedValue({ account_id: 'act_001', status: 'accepted', message: '已排程' });
        createAnalysis.mockResolvedValue({
            snapshot_id: 'csn_test_001',
            status: 'queued',
            account_id: 'act_001',
            queue_host: 'apscheduler',
            message: '已加入背景排程',
        });
    });

    it('blocks the page when contribution module access is denied', () => {
        useModuleAccess.mockReturnValue({ hasAccess: false, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: false, loading: false, error: null });

        renderWithOutlet(<ContributionAnalysis />, {
            outletContext: { isMobile: false, language: 'zh', selectedTeamId: null },
        });

        expect(
            screen.getByText('此工作區無「貢獻分析」模組存取權限，請聯絡管理員開通。')
        ).toBeTruthy();
    });

    it('runs analysis end-to-end after groups are present', async () => {
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });
        listCampaignSummaries.mockResolvedValue({
            account_id: 'act_001',
            campaigns: [
                { campaign_id: 'c1', campaign_name: 'C1', spend: 1000, impressions: 100, conversions: 5, conversion_value: 0, active_days: 30 },
            ],
            total: 1,
        });
        getGroups.mockResolvedValue({
            account_id: 'act_001',
            source: 'auto',
            groups: [{ group_key: 'G1', group_name: '主力', campaign_ids: ['c1'], source: 'auto' }],
        });

        renderWithOutlet(<ContributionAnalysis />, {
            outletContext: { isMobile: false, language: 'zh', selectedTeamId: null },
        });

        // 帳戶自動帶入（單一帳戶）+ groups 載入完成 → 開始分析按鈕變為可點
        const button = await screen.findByRole('button', { name: '開始分析' });
        await waitFor(() => expect(button.disabled).toBe(false));

        fireEvent.click(button);

        await waitFor(() => {
            expect(createAnalysis).toHaveBeenCalledTimes(1);
        });
        const payload = createAnalysis.mock.calls[0][0];
        expect(payload.accountId).toBe('act_001');
        expect(payload.dateStart).toBeTruthy();
        expect(payload.dateEnd).toBeTruthy();
    });
});
