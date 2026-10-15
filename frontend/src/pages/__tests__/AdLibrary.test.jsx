import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import AdLibrary from '../AdLibrary';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import {
    getAdAssetInsights, getAiAnalysis, getComparisons, getRefreshJob, getTree, listAccounts, listAds, startRefresh,
    streamAiAnalysis,
} from '../../services/adLibraryService';

vi.mock('../../services/adLibraryService', () => ({
    listAccounts: vi.fn(),
    listAds: vi.fn(),
    startRefresh: vi.fn(),
    getRefreshJob: vi.fn(),
    getTree: vi.fn(),
    getComparisons: vi.fn(),
    getAdAssetInsights: vi.fn(),
    getAiAnalysis: vi.fn(),
    streamAiAnalysis: vi.fn(),
    downloadCsv: vi.fn(),
    fetchMediaBlobUrl: vi.fn(() => new Promise(() => {})),
}));

const outletContext = { isMobile: false, language: 'zh', selectedTeamId: null };

const sampleItem = {
    id: 'ali_1',
    account_id: 'act_001',
    ad_id: '111',
    ad_name: '春季主打',
    campaign_name: '春季活動',
    effective_status: 'ACTIVE',
    media_type: 'dynamic',
    primary_texts: ['文案一', '文案二'],
    headlines: ['立即選購'],
    descriptions: [],
    cta_types: ['SHOP_NOW'],
    link_url: 'https://shop.example.com',
    media: [],
    preview_link: null,
    impressions: 12345,
    reach: 0,
    clicks: 0,
    spend: 99.5,
    ctr: 1.234,
    ad_created_at: '2026-03-01T02:00:00',
};

describe('AdLibrary', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        listAccounts.mockResolvedValue([{ id: 'act_001', name: '測試帳戶' }]);
    });

    it('shows empty state guiding the user to fetch when nothing is cached', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        renderWithOutlet(<AdLibrary />, { outletContext });

        expect(await screen.findByText(/尚未抓取資料/)).toBeInTheDocument();
        expect(listAds).toHaveBeenCalledWith(expect.objectContaining({ accountId: 'act_001', sort: 'impressions' }));
    });

    it('renders ad cards and switches dynamic creative variants', async () => {
        listAds.mockResolvedValue({ items: [sampleItem], total: 1, page: 1, page_size: 24, latest_job: null });
        renderWithOutlet(<AdLibrary />, { outletContext });

        expect(await screen.findByText('文案一')).toBeInTheDocument();
        expect(screen.getByText('立即選購')).toBeInTheDocument();
        expect(screen.getAllByText('投放中').some((el) => el.classList.contains('adlib-badge'))).toBe(true);
        expect(screen.getByText('12,345')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '2' }));
        expect(screen.getByText('文案二')).toBeInTheDocument();
    });

    it('starts a refresh and reloads the list once the job finishes', async () => {
        vi.useFakeTimers({ shouldAdvanceTime: true });
        try {
            listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
            startRefresh.mockResolvedValue({ job_id: 'alj_1', account_id: 'act_001', status: 'queued', ads_fetched: 0, media_stored: 0 });
            getRefreshJob.mockResolvedValue({ job_id: 'alj_1', account_id: 'act_001', status: 'succeeded', ads_fetched: 3, media_stored: 2 });
            renderWithOutlet(<AdLibrary />, { outletContext });

            const button = await screen.findByRole('button', { name: /從 Facebook 重新抓取/ });
            await waitFor(() => expect(button).not.toBeDisabled());
            fireEvent.click(button);

            await waitFor(() => expect(startRefresh).toHaveBeenCalledWith('act_001'));
            expect(await screen.findByRole('button', { name: /抓取中/ })).toBeDisabled();

            await vi.advanceTimersByTimeAsync(3100);
            await waitFor(() => expect(getRefreshJob).toHaveBeenCalledWith('alj_1'));
            await waitFor(() => expect(listAds.mock.calls.length).toBeGreaterThanOrEqual(2));
        } finally {
            vi.useRealTimers();
        }
    });

    it('shows the campaign → ad set → ad structure with settings', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        getTree.mockResolvedValue({
            account_id: 'act_001',
            latest_job: null,
            campaigns: [{
                id: 'alc_1', campaign_id: 'c1', name: '春季活動', settings_available: true,
                objective: 'OUTCOME_SALES', effective_status: 'ACTIVE', budget_level: 'campaign',
                currency: 'TWD', daily_budget: 500, lifetime_budget: null,
                metrics: { impressions: 1000, reach: 800, clicks: 10, spend: 300, ctr: 1 },
                adsets: [{
                    id: 'ala_1', adset_id: 's1', name: '女性 25-45', settings_available: true,
                    effective_status: 'ACTIVE', optimization_goal: 'OFFSITE_CONVERSIONS',
                    currency: 'TWD', daily_budget: null, lifetime_budget: null,
                    targeting_summary: { age_min: 25, age_max: 45, genders: ['female'], countries: ['TW'], advantage_audience: true },
                    metrics: { impressions: 1000, reach: 800, clicks: 10, spend: 300, ctr: 1 },
                    ads: [{
                        id: 'ali_1', ad_id: 'a1', name: '主打廣告', effective_status: 'ACTIVE', media_type: 'image',
                        primary_text: '結構裡的文案', headline: '立即購買', variant_count: 1, thumbnail: null,
                        metrics: { impressions: 1000, reach: 800, clicks: 10, spend: 300, ctr: 1 },
                    }],
                }],
            }],
        });
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('tab', { name: '結構' }));
        const campaign = await screen.findByRole('button', { name: /^春季活動/ });
        expect(getTree).toHaveBeenCalledWith({ accountId: 'act_001', status: '' });
        expect(screen.getByText('行銷活動預算')).toBeInTheDocument();
        expect(screen.getByText('日預算 TWD 500')).toBeInTheDocument();
        expect(screen.queryByText('女性 25-45')).not.toBeInTheDocument();

        fireEvent.click(campaign);
        const adset = await screen.findByRole('button', { name: /女性 25-45/ });
        expect(screen.getByText('最佳化：轉換')).toBeInTheDocument();
        expect(screen.getByText('25–45 歲')).toBeInTheDocument();
        expect(screen.getByText('Advantage+ 受眾')).toBeInTheDocument();

        fireEvent.click(adset);
        expect(await screen.findByText('結構裡的文案')).toBeInTheDocument();
    });

    it('flags placeholder nodes whose settings were not fetched yet', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        getTree.mockResolvedValue({
            account_id: 'act_001',
            latest_job: null,
            campaigns: [{
                id: null, campaign_id: 'c9', name: '舊活動', settings_available: false, objective: null,
                effective_status: null, metrics: { impressions: 0, reach: null, clicks: 0, spend: 0, ctr: 0 }, adsets: [],
            }],
        });
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('tab', { name: '結構' }));
        expect(await screen.findByText('設定未抓取')).toBeInTheDocument();
        expect(screen.getByText(/請重新從 Facebook 抓取一次/)).toBeInTheDocument();
    });
    it('filters the ad list by same copy when clicking the card badge', async () => {
        listAds.mockResolvedValue({
            items: [{ ...sampleItem, copy_key: 'a'.repeat(64), same_copy_count: 2 }],
            total: 1, page: 1, page_size: 24, latest_job: null,
        });
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('button', { name: '同文案 2 則' }));
        await waitFor(() => expect(listAds).toHaveBeenLastCalledWith(expect.objectContaining({ copyKey: 'a'.repeat(64) })));
        expect(screen.getByText('只看使用相同文案的廣告')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '清除' }));
        await waitFor(() => expect(listAds.mock.lastCall[0]).not.toHaveProperty('copyKey'));
    });

    it('shows media tests with the best CTR variant and the attribution note', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        const metrics = (impressions, clicks, spend) => ({ impressions, clicks, spend, ctr: (clicks / impressions) * 100 });
        const ad = (id, name) => ({ id, ad_id: id, name, adset_name: '女性 25-45', metrics: metrics(2000, 20, 100) });
        getComparisons.mockResolvedValue({
            account_id: 'act_001',
            scope: 'adset',
            counts: { media_test: 1, copy_test: 0, duplicate: 0 },
            coverage: { ads: 2, without_copy_key: 0, without_media_key: 0 },
            note: '成效為廣告層級數字',
            groups: [{
                relation: 'media_test',
                scope: { level: 'adset', id: 's1', name: '女性 25-45', campaign_id: 'c1', campaign_name: '春季活動' },
                fixed: { kind: 'copy', key: 'b'.repeat(64), preview: { primary_texts: ['固定的那段文案'], headlines: [], descriptions: [] } },
                metrics: metrics(4000, 60, 200),
                variants: [
                    { key: 'm1', preview: { media_type: 'image', media_count: 1, thumbnail: null }, ads: [ad('a1', '圖 A')], metrics: metrics(2000, 20, 100) },
                    { key: 'm2', preview: { media_type: 'image', media_count: 1, thumbnail: null }, ads: [ad('a2', '圖 B')], metrics: metrics(2000, 40, 100) },
                ],
            }],
        });
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('tab', { name: '比對' }));
        expect(await screen.findByText('固定的那段文案')).toBeInTheDocument();
        expect(getComparisons).toHaveBeenCalledWith({ accountId: 'act_001', scope: 'adset', relation: '' });
        expect(screen.getByText('成效為廣告層級數字')).toBeInTheDocument();
        const best = screen.getByText('CTR 最高').closest('.adlib-cmp-variant');
        expect(best).toHaveTextContent('圖 B');

        fireEvent.click(screen.getByRole('button', { name: '查看所有使用此文案的廣告' }));
        await waitFor(() => expect(listAds).toHaveBeenLastCalledWith(expect.objectContaining({ copyKey: 'b'.repeat(64) })));
        expect(screen.getByRole('tab', { name: '廣告' })).toHaveAttribute('aria-selected', 'true');
    });
    it('shows per-asset results for dynamic creative ads', async () => {
        listAds.mockResolvedValue({ items: [sampleItem], total: 1, page: 1, page_size: 24, latest_job: null });
        const entry = (id, text, impressions, clicks) => ({
            content_id: id, kind: 'primary_text', text_value: text, impressions, reach: 0, clicks,
            spend: 10, ctr: (clicks / impressions) * 100,
        });
        getAdAssetInsights.mockResolvedValue({
            item_id: 'ali_1', ad_id: '111', fetched_at: null, note: '元件成效由 Meta 依元件拆分',
            entries: { primary_text: [entry('t1', '文案甲', 2000, 10), entry('t2', '文案乙', 2000, 50)] },
        });
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('button', { name: '查看元件成效' }));
        expect(await screen.findByText('文案乙')).toBeInTheDocument();
        expect(getAdAssetInsights).toHaveBeenCalledWith('ali_1');
        expect(screen.getByText('文案乙').closest('li')).toHaveTextContent('CTR 最高');
        expect(screen.getByText('文案甲').closest('li')).not.toHaveTextContent('CTR 最高');
        expect(screen.getByText('元件成效由 Meta 依元件拆分')).toBeInTheDocument();
    });

    it('explains how to get per-asset results when none are stored', async () => {
        listAds.mockResolvedValue({ items: [sampleItem], total: 1, page: 1, page_size: 24, latest_job: null });
        getAdAssetInsights.mockResolvedValue({ item_id: 'ali_1', ad_id: '111', fetched_at: null, note: '', entries: {} });
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('button', { name: '查看元件成效' }));
        expect(await screen.findByText(/尚無元件成效/)).toBeInTheDocument();
    });
    const treeWithCampaign = {
        account_id: 'act_001',
        latest_job: null,
        campaigns: [{
            id: 'alc_1', campaign_id: 'c1', name: '春季活動', settings_available: true, objective: 'OUTCOME_SALES',
            effective_status: 'ACTIVE', budget_level: 'adset', currency: 'TWD', daily_budget: null, lifetime_budget: null,
            metrics: { impressions: 0, reach: 0, clicks: 0, spend: 0, ctr: 0 }, adsets: [],
        }],
    };
    const aiMeta = (overrides = {}) => ({
        analysis: null, is_stale: false, context_hash: 'h', context_chars: 12345, model: 'deepseek/deepseek-v4-flash',
        has_api_key: true, data_fetched_at: '2026-10-14T10:00:00', ...overrides,
    });

    it('opens the AI panel with the saved analysis and a stale notice', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        getTree.mockResolvedValue(treeWithCampaign);
        getAiAnalysis.mockResolvedValue(aiMeta({
            is_stale: true,
            analysis: {
                id: 'alai_1', model: 'openai/gpt-x', status: 'succeeded', content: '## 📌 重點摘要\n- 舊的分析結果',
                context_hash: 'old', context_chars: 100, created_at: '2026-10-13T10:00:00',
            },
        }));
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('tab', { name: '結構' }));
        fireEvent.click(await screen.findByRole('button', { name: 'AI 分析：春季活動' }));
        expect(await screen.findByText('舊的分析結果')).toBeInTheDocument();
        expect(getAiAnalysis).toHaveBeenCalledWith({ accountId: 'act_001', campaignId: 'c1' });
        expect(screen.getByRole('heading', { name: /重點摘要/ })).toBeInTheDocument();
        expect(screen.getByText(/資料已重新抓取/)).toBeInTheDocument();
        expect(screen.getByText(/openai\/gpt-x/)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /重新分析/ })).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: '關閉' }));
        await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    });

    it('guides the user to settings when no AI key is configured', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        getTree.mockResolvedValue(treeWithCampaign);
        getAiAnalysis.mockResolvedValue(aiMeta({ has_api_key: false }));
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('tab', { name: '結構' }));
        fireEvent.click(await screen.findByRole('button', { name: 'AI 分析：春季活動' }));
        expect(await screen.findByText(/設定 → OpenRouter/)).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /開始分析/ })).not.toBeInTheDocument();
    });

    it('streams a new analysis and reloads the saved result', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        getTree.mockResolvedValue(treeWithCampaign);
        getAiAnalysis.mockResolvedValueOnce(aiMeta()).mockResolvedValue(aiMeta({
            analysis: {
                id: 'alai_2', model: 'deepseek/deepseek-v4-flash', status: 'succeeded', content: '## 建議下一步\n1. 加碼 P1',
                context_hash: 'h', context_chars: 12345, created_at: '2026-10-14T11:00:00',
            },
        }));
        streamAiAnalysis.mockImplementation(async ({ onChunk }) => {
            onChunk('## 建議');
            onChunk('## 建議下一步\n1. 加碼 P1');
            return '## 建議下一步\n1. 加碼 P1';
        });
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('tab', { name: '結構' }));
        fireEvent.click(await screen.findByRole('button', { name: 'AI 分析：春季活動' }));
        expect(await screen.findByText(/資料約 12,345 字元/)).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: /開始分析/ }));

        await waitFor(() => expect(streamAiAnalysis).toHaveBeenCalledWith(
            expect.objectContaining({ accountId: 'act_001', campaignId: 'c1' }),
        ));
        expect(await screen.findByText('加碼 P1')).toBeInTheDocument();
        await waitFor(() => expect(getAiAnalysis).toHaveBeenCalledTimes(2));
    });
    it('labels catalog ads that have no previewable media', async () => {
        listAds.mockResolvedValue({
            items: [{ ...sampleItem, id: 'ali_cat', primary_texts: [], headlines: ['{{product.name}}'], media: [] }],
            total: 1, page: 1, page_size: 24, latest_job: null,
        });
        renderWithOutlet(<AdLibrary />, { outletContext });
        expect(await screen.findByText('商品目錄廣告：素材來自商品目錄')).toBeInTheDocument();
    });

    it('wraps AI report tables in a horizontal scroll container', async () => {
        listAds.mockResolvedValue({ items: [], total: 0, page: 1, page_size: 24, latest_job: null });
        getTree.mockResolvedValue(treeWithCampaign);
        getAiAnalysis.mockResolvedValue(aiMeta({
            analysis: {
                id: 'alai_3', model: 'm', status: 'succeeded', context_hash: 'h', context_chars: 1, created_at: '2026-10-15T01:00:00',
                content: '## 文案與素材測試\n\n| 版本 | 曝光 |\n|---|---|\n| P1 | 19,799 |\n',
            },
        }));
        renderWithOutlet(<AdLibrary />, { outletContext });

        fireEvent.click(await screen.findByRole('tab', { name: '結構' }));
        fireEvent.click(await screen.findByRole('button', { name: 'AI 分析：春季活動' }));
        const cell = await screen.findByText('19,799');
        expect(cell.closest('.adlib-ai-table')).not.toBeNull();
    });
});
