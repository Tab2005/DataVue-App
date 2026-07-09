import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import ContributionAnalysis, { evaluateRefreshPoll } from '../ContributionAnalysis';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import {
    createAnalysis,
    getAnalysis,
    getGroups,
    listAnalyses,
    listCampaignSummaries,
    refreshContributionData,
    updateGroups,
} from '../../services/contributionService';

vi.mock('../../services/contributionService', () => ({
    createAnalysis: vi.fn(),
    getGroups: vi.fn(),
    listAnalyses: vi.fn(),
    listCampaignSummaries: vi.fn(),
    refreshContributionData: vi.fn(),
    updateGroups: vi.fn(),
    getAnalysis: vi.fn(),
    saveAiSummary: vi.fn(),
    pingContribution: vi.fn(),
}));

vi.mock('../../services/aiService', () => ({
    aiService: {
        analyzeDataStream: vi.fn(),
        testConnection: vi.fn(),
    },
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

    it('renders a historical snapshot using its own group_snapshot, not the current groups state (docs/27 任務 4.1)', async () => {
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });

        // 目前的分組（使用者已改組，名稱與分析當時不同）
        getGroups.mockResolvedValue({
            account_id: 'act_001',
            source: 'manual',
            groups: [{ group_key: 'G1', group_name: '新名稱（現在）', campaign_ids: ['c1'], source: 'manual' }],
        });
        listAnalyses.mockResolvedValue({
            account_id: 'act_001',
            total: 1,
            analyses: [
                {
                    snapshot_id: 'csn_hist_1',
                    account_id: 'act_001',
                    status: 'completed',
                    date_start: '2026-01-01',
                    date_end: '2026-06-30',
                    created_at: null,
                    completed_at: null,
                    error_message: null,
                    has_ai_summary: false,
                },
            ],
        });
        getAnalysis.mockResolvedValue({
            snapshot_id: 'csn_hist_1',
            account_id: 'act_001',
            status: 'completed',
            date_start: '2026-01-01',
            date_end: '2026-06-30',
            config: {
                metric_key: 'omni_purchase',
                n_restarts: 5,
                holdout_days: 45,
                // 分析當時的分組快照——名稱與目前的 groups state 不同
                group_snapshot: [
                    { group_key: 'G1', group_name: '舊名稱（分析當時）', campaign_ids: ['c1'], source: 'auto' },
                ],
            },
            results: {
                groups: {
                    G1: {
                        spend_share: 0.5,
                        contribution_share: { median: 0.4, min: 0.3, max: 0.5 },
                        marginal: { step: 100, per_step: { median: 1.2, min: 1.0, max: 1.4 } },
                    },
                },
                base_share: { median: 0.1, min: 0.05, max: 0.15 },
                r2: { holdout: { median: 0.2 }, full: { median: 0.5 } },
                seeds: [1, 2, 3],
            },
            diagnostics: {
                collinearity_warnings: [],
                poisson_ceiling_r2: { holdout: 0.3, full: 0.6 },
                data_summary: { days: 180, mean_daily_conversions: 10 },
            },
            error_message: null,
            runtime_job_id: null,
            ai_summary: null,
            ai_summary_generated_at: null,
            created_at: null,
            completed_at: null,
        });

        renderWithOutlet(<ContributionAnalysis />, {
            outletContext: { isMobile: false, language: 'zh', selectedTeamId: null },
        });

        // 點選歷史快照列表中的該筆分析
        const historyEntry = await screen.findByText('csn_hist_1');
        fireEvent.click(historyEntry.closest('button'));

        await waitFor(() => expect(getAnalysis).toHaveBeenCalledWith('csn_hist_1'));

        // 渲染應使用 group_snapshot 的名稱（分析當時），而非目前 groups state 的新名稱
        await waitFor(() => {
            expect(screen.getByText('G1 · 舊名稱（分析當時）')).toBeTruthy();
        });
        expect(screen.queryByText('G1 · 新名稱（現在）')).toBeNull();
    });

    it('computes reportedByGroup from the snapshot date range, not the full campaign history (docs/27 任務 4.2)', async () => {
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });

        getGroups.mockResolvedValue({
            account_id: 'act_001',
            source: 'auto',
            groups: [
                { group_key: 'G1', group_name: '主力', campaign_ids: ['c1'], source: 'auto' },
                { group_key: 'G2', group_name: '影片', campaign_ids: ['c2'], source: 'auto' },
            ],
        });
        listAnalyses.mockResolvedValue({
            account_id: 'act_001',
            total: 1,
            analyses: [
                {
                    snapshot_id: 'csn_scope_1',
                    account_id: 'act_001',
                    status: 'completed',
                    date_start: '2026-03-01',
                    date_end: '2026-03-31',
                    created_at: null,
                    completed_at: null,
                    error_message: null,
                    has_ai_summary: false,
                },
            ],
        });
        getAnalysis.mockResolvedValue({
            snapshot_id: 'csn_scope_1',
            account_id: 'act_001',
            status: 'completed',
            date_start: '2026-03-01',
            date_end: '2026-03-31',
            config: { metric_key: 'omni_purchase', n_restarts: 5, holdout_days: 45 },
            results: {
                groups: {
                    G1: {
                        spend_share: 0.3,
                        contribution_share: { median: 0.35, min: 0.25, max: 0.45 },
                        marginal: { step: 100, per_step: { median: 1, min: 1, max: 1 } },
                    },
                    G2: {
                        spend_share: 0.7,
                        contribution_share: { median: 0.65, min: 0.55, max: 0.75 },
                        marginal: { step: 100, per_step: { median: 1, min: 1, max: 1 } },
                    },
                },
                base_share: { median: 0.1, min: 0.05, max: 0.15 },
                r2: { holdout: { median: 0.2 }, full: { median: 0.5 } },
                seeds: [1],
            },
            diagnostics: {
                collinearity_warnings: [],
                poisson_ceiling_r2: { holdout: 0.3, full: 0.6 },
                data_summary: { days: 31, mean_daily_conversions: 5 },
            },
            error_message: null,
            runtime_job_id: null,
            ai_summary: null,
            ai_summary_generated_at: null,
            created_at: null,
            completed_at: null,
        });

        // 全歷史彙總（分組編輯器 / 快取活動數提示用）：c1/c2 轉換相同 → 50/50
        // 快照區間彙總（date_start=2026-03-01 / date_end=2026-03-31）：
        // c1=8、c2=2 → 80%/20%，刻意與全歷史差異拉大以便從渲染結果分辨
        // 究竟用了哪一種資料源。
        listCampaignSummaries.mockImplementation(({ dateStart, dateEnd } = {}) => {
            if (dateStart === '2026-03-01' && dateEnd === '2026-03-31') {
                return Promise.resolve({
                    account_id: 'act_001',
                    total: 2,
                    campaigns: [
                        { campaign_id: 'c1', campaign_name: 'C1', spend: 100, impressions: 10, conversions: 8, conversion_value: 0, active_days: 31 },
                        { campaign_id: 'c2', campaign_name: 'C2', spend: 100, impressions: 10, conversions: 2, conversion_value: 0, active_days: 31 },
                    ],
                });
            }
            return Promise.resolve({
                account_id: 'act_001',
                total: 2,
                campaigns: [
                    { campaign_id: 'c1', campaign_name: 'C1', spend: 1000, impressions: 100, conversions: 100, conversion_value: 0, active_days: 180 },
                    { campaign_id: 'c2', campaign_name: 'C2', spend: 1000, impressions: 100, conversions: 100, conversion_value: 0, active_days: 180 },
                ],
            });
        });

        renderWithOutlet(<ContributionAnalysis />, {
            outletContext: { isMobile: false, language: 'zh', selectedTeamId: null },
        });

        const historyEntry = await screen.findByText('csn_scope_1');
        fireEvent.click(historyEntry.closest('button'));

        // 快照區間查詢確實有帶上 activeSnapshot 的 date_start/date_end
        await waitFor(() => {
            expect(listCampaignSummaries).toHaveBeenCalledWith(
                expect.objectContaining({
                    accountId: 'act_001',
                    dateStart: '2026-03-01',
                    dateEnd: '2026-03-31',
                })
            );
        });

        // 自報占比欄應為 80.0% / 20.0%（快照區間彙總 8:2 的轉換比）；若修復前
        // 用全歷史彙總（c1/c2 轉換相同）會得到 50.0%/50.0%，不會出現 80/20。
        await waitFor(() => {
            expect(screen.getByText('80.0%')).toBeTruthy();
        });
        expect(screen.getByText('20.0%')).toBeTruthy();
    });

    it('shows each group\'s own marginal step, not the first group\'s step for all rows (docs/27 任務 4.3)', async () => {
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });

        getGroups.mockResolvedValue({
            account_id: 'act_001',
            source: 'auto',
            groups: [
                { group_key: 'G1', group_name: '主力', campaign_ids: ['c1'], source: 'auto' },
                { group_key: 'G2', group_name: '大包裝', campaign_ids: ['c2'], source: 'auto' },
            ],
        });
        listAnalyses.mockResolvedValue({
            account_id: 'act_001',
            total: 1,
            analyses: [
                {
                    snapshot_id: 'csn_step_1',
                    account_id: 'act_001',
                    status: 'completed',
                    date_start: '2026-01-01',
                    date_end: '2026-06-30',
                    created_at: null,
                    completed_at: null,
                    error_message: null,
                    has_ai_summary: false,
                },
            ],
        });
        getAnalysis.mockResolvedValue({
            snapshot_id: 'csn_step_1',
            account_id: 'act_001',
            status: 'completed',
            date_start: '2026-01-01',
            date_end: '2026-06-30',
            config: { metric_key: 'omni_purchase', n_restarts: 5, holdout_days: 45 },
            results: {
                groups: {
                    // G1 步長 100（小額日均花費組）；G2 步長 500（大額日均花費組）
                    // ——舊版 bug 會把 G1 的 step=100 套用到兩列，G2 顯示 +100 而非 +500
                    G1: {
                        spend_share: 0.3,
                        contribution_share: { median: 0.35, min: 0.25, max: 0.45 },
                        marginal: { step: 100, per_step: { median: 1.2, min: 1.0, max: 1.4 } },
                    },
                    G2: {
                        spend_share: 0.7,
                        contribution_share: { median: 0.65, min: 0.55, max: 0.75 },
                        marginal: { step: 500, per_step: { median: 3.0, min: 2.5, max: 3.5 } },
                    },
                },
                base_share: { median: 0.1, min: 0.05, max: 0.15 },
                r2: { holdout: { median: 0.2 }, full: { median: 0.5 } },
                seeds: [1],
            },
            diagnostics: {
                collinearity_warnings: [],
                poisson_ceiling_r2: { holdout: 0.3, full: 0.6 },
                data_summary: { days: 180, mean_daily_conversions: 10 },
            },
            error_message: null,
            runtime_job_id: null,
            ai_summary: null,
            ai_summary_generated_at: null,
            created_at: null,
            completed_at: null,
        });
        listCampaignSummaries.mockResolvedValue({ account_id: 'act_001', total: 0, campaigns: [] });

        renderWithOutlet(<ContributionAnalysis />, {
            outletContext: { isMobile: false, language: 'zh', selectedTeamId: null },
        });

        const historyEntry = await screen.findByText('csn_step_1');
        fireEvent.click(historyEntry.closest('button'));

        // G1 該列顯示自己的步長 +100，G2 該列顯示自己的步長 +500——
        // 不是兩列都顯示同一個（舊版取第一組 step 的 bug）。
        await waitFor(() => {
            expect(screen.getByText('+1.20（/ +100）')).toBeTruthy();
        });
        expect(screen.getByText('+3.00（/ +500）')).toBeTruthy();
    });

    it('warns about and filters out emptied groups on save (docs/27 任務 4.4)', async () => {
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });

        listCampaignSummaries.mockResolvedValue({
            account_id: 'act_001',
            total: 1,
            campaigns: [
                { campaign_id: 'c1', campaign_name: 'C1', spend: 100, impressions: 10, conversions: 5, conversion_value: 0, active_days: 30 },
            ],
        });
        getGroups.mockResolvedValue({
            account_id: 'act_001',
            source: 'manual',
            groups: [
                { group_key: 'G1', group_name: '主力', campaign_ids: ['c1'], source: 'manual' },
                { group_key: 'G2', group_name: '影片', campaign_ids: [], source: 'manual' },
            ],
        });
        updateGroups.mockResolvedValue({
            account_id: 'act_001',
            groups: [{ group_key: 'G2', group_name: '影片', campaign_ids: ['c1'], source: 'manual' }],
            updated_count: 1,
        });

        renderWithOutlet(<ContributionAnalysis />, {
            outletContext: { isMobile: false, language: 'zh', selectedTeamId: null },
        });

        // 等待分組載入（G1 的名稱輸入框出現）
        await screen.findByDisplayValue('主力');

        // 把 c1 從 G1 移到 G2（觸發 handleMove，G1 隨即變空）——這個 combobox
        // 的初始 value 是活動目前所在的 group_key，即 'G1'。
        const selects = screen.getAllByRole('combobox');
        const moveSelect = selects.find((el) => el.value === 'G1');
        expect(moveSelect).toBeTruthy();
        fireEvent.change(moveSelect, { target: { value: 'G2' } });

        // G1 應顯示「將於儲存時移除」警示
        await waitFor(() => {
            expect(screen.getByText('此組已無任何活動，將於儲存時移除。')).toBeTruthy();
        });

        // 點擊儲存分組
        const saveButton = screen.getByRole('button', { name: '儲存分組' });
        fireEvent.click(saveButton);

        await waitFor(() => expect(updateGroups).toHaveBeenCalledTimes(1));
        const payload = updateGroups.mock.calls[0][0];
        // 已空的 G1 不應出現在送出的 payload 中
        expect(payload.groups.map((g) => g.group_key)).toEqual(['G2']);
        expect(payload.groups[0].campaign_ids).toEqual(['c1']);
    });

    it('shows a success notice once the polled campaign count increases after refresh (docs/27 任務 4.5)', async () => {
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });

        getGroups.mockResolvedValue({ account_id: 'act_001', source: 'auto', groups: [] });
        listAnalyses.mockResolvedValue({ account_id: 'act_001', total: 0, analyses: [] });
        refreshContributionData.mockResolvedValue({
            account_id: 'act_001',
            status: 'accepted',
            message: '已排程補抓',
        });
        // 初始快取為空（loadCampaigns 呼叫）；第一次輪詢仍是 0（背景抓取尚未
        // 寫入）；第二次輪詢活動數增加 → 應停止輪詢並顯示成功提示。
        listCampaignSummaries
            .mockResolvedValueOnce({ account_id: 'act_001', total: 0, campaigns: [] })
            .mockResolvedValueOnce({ account_id: 'act_001', total: 0, campaigns: [] })
            .mockResolvedValueOnce({
                account_id: 'act_001',
                total: 1,
                campaigns: [
                    { campaign_id: 'c1', campaign_name: 'C1', spend: 100, impressions: 10, conversions: 5, conversion_value: 0, active_days: 1 },
                ],
            });

        renderWithOutlet(<ContributionAnalysis />, {
            outletContext: { isMobile: false, language: 'zh', selectedTeamId: null },
        });

        const refreshButton = await screen.findByRole('button', { name: '抓取資料' });
        // 帳戶需先自動帶入（單一帳戶）按鈕才會真正啟用；太早點擊
        // handleRefreshData 會因 accountId 尚為空字串而直接 return。
        await waitFor(() => expect(refreshButton.disabled).toBe(false));
        fireEvent.click(refreshButton);

        // 按鈕在輪詢期間維持「抓取中…」
        await waitFor(() => {
            expect(screen.getByRole('button', { name: '抓取中…' })).toBeTruthy();
        });
        expect(refreshContributionData).toHaveBeenCalledWith({ accountId: 'act_001' });

        // 第一次真實輪詢 tick（間隔 3 秒）活動數仍不變，第二次才增加——
        // 用真實計時器等待，避免 fake timers 與內部 async setInterval
        // callback 交錯造成的測試脆弱性。
        await waitFor(
            () => {
                expect(screen.getByText('資料已抓取完成。')).toBeTruthy();
            },
            { timeout: 8000, interval: 200 }
        );
        // 輪詢停止後按鈕應恢復可點擊狀態
        await waitFor(() => {
            expect(screen.getByRole('button', { name: '抓取資料' }).disabled).toBe(false);
        });
    }, 10000);
});

describe('evaluateRefreshPoll (docs/27 任務 4.5，純函數，脫離計時器測試停止條件)', () => {
    it('stops with reason "increased" when the polled count exceeds the baseline', () => {
        const result = evaluateRefreshPoll({ count: 5, baselineCount: 3, lastCount: 3, elapsedMs: 3000, timeoutMs: 60000 });
        expect(result).toEqual({ stop: true, reason: 'increased' });
    });

    it('stops with reason "stabilized" when count is unchanged across two polls and > 0', () => {
        // count 未超過 baselineCount（不落入 "increased" 分支），但與上次
        // 輪詢結果相同且 > 0 → 視為已抓完並穩定。
        const result = evaluateRefreshPoll({ count: 4, baselineCount: 4, lastCount: 4, elapsedMs: 6000, timeoutMs: 60000 });
        expect(result).toEqual({ stop: true, reason: 'stabilized' });
    });

    it('does not stop for "unchanged" when the count is still 0 (nothing fetched yet)', () => {
        const result = evaluateRefreshPoll({ count: 0, baselineCount: 0, lastCount: 0, elapsedMs: 3000, timeoutMs: 60000 });
        expect(result).toEqual({ stop: false, reason: null });
    });

    it('stops with reason "timeout" once elapsed time reaches the timeout threshold', () => {
        const result = evaluateRefreshPoll({ count: 0, baselineCount: 0, lastCount: 0, elapsedMs: 60000, timeoutMs: 60000 });
        expect(result).toEqual({ stop: true, reason: 'timeout' });
    });

    it('continues polling when none of the stop conditions are met', () => {
        const result = evaluateRefreshPoll({ count: 3, baselineCount: 3, lastCount: null, elapsedMs: 3000, timeoutMs: 60000 });
        expect(result).toEqual({ stop: false, reason: null });
    });
});
