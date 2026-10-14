import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import AdLibrary from '../AdLibrary';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import { getRefreshJob, listAccounts, listAds, startRefresh } from '../../services/adLibraryService';

vi.mock('../../services/adLibraryService', () => ({
    listAccounts: vi.fn(),
    listAds: vi.fn(),
    startRefresh: vi.fn(),
    getRefreshJob: vi.fn(),
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
});
