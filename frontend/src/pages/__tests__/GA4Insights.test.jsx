// docs/66：到達頁與商品的狀態抽成 hook 之後的行為鎖。
//
// 最重要的一條是「切走再切回來不重載」——那是把狀態留在父層（而不是照
// docs/59 字面移進分頁元件）的唯一理由，沒有測試釘住的話很容易在之後某次
// 重構被順手改掉。
import React from 'react';
import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import GA4Insights from '../GA4Insights';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import { ga4Service } from '../../services/ga4Service';
import { ga4InsightsService } from '../../services/ga4InsightsService';
import { lineService } from '../../services/lineService';
import { useModuleAccess, usePermission, useSelectedTeamId } from '../../hooks/usePermission';

vi.mock('../../services/ga4Service', () => ({
    ga4Service: { getProperties: vi.fn() },
}));

vi.mock('../../services/lineService', () => ({
    lineService: { getStatus: vi.fn() },
}));

vi.mock('../../hooks/usePermission', () => ({
    useModuleAccess: vi.fn(),
    usePermission: vi.fn(),
    useSelectedTeamId: vi.fn(),
}));

vi.mock('../../services/ga4InsightsService', () => ({
    ga4InsightsService: {
        listRules: vi.fn(),
        listEvents: vi.fn(),
        getDashboard: vi.fn(),
        getRealtime: vi.fn(),
        getChannels: vi.fn(),
        getLandingPages: vi.fn(),
        getItems: vi.fn(),
        listLandingPageRules: vi.fn(),
        listItemCategoryRules: vi.fn(),
        listChannelGroups: vi.fn(),
        listChannelGroupRules: vi.fn(),
        upsertLandingPageRule: vi.fn(),
        deleteLandingPageRule: vi.fn(),
        upsertItemCategoryRule: vi.fn(),
        deleteItemCategoryRule: vi.fn(),
        upsertChannelGroupRule: vi.fn(),
        deleteChannelGroupRule: vi.fn(),
        getItemLandingCross: vi.fn(),
        listKpiTargets: vi.fn(),
        getRuleAvailableKeyEvents: vi.fn(),
    },
}));

const landingSnapshot = (overrides = {}) => ({
    snapshot_id: 'snap-landing-1',
    payload: {
        start_date: '2026-07-28',
        end_date: '2026-08-03',
        available_key_events: ['purchase'],
        category_counts: { product: 1, article: 1 },
        landing_pages: [
            { landingPage: '/products/a', category: 'product', sessions: 400, conversions: 12, session_key_event_rate: 0.03, bounceRate: 0.4 },
            { landingPage: '/blog/b', category: 'article', sessions: 90, conversions: 1, session_key_event_rate: 0.01, bounceRate: 0.7 },
        ],
        ...overrides,
    },
});

const itemsSnapshot = () => ({
    snapshot_id: 'snap-items-1',
    payload: {
        start_date: '2026-07-28',
        end_date: '2026-08-03',
        category_counts: { Apparel: 2 },
        items: [
            { itemName: 'Alpha', item_category: 'Apparel', item_category_source: 'ga4', itemsViewed: 100, cart_to_view_rate: 0.2, purchase_to_view_rate: 0.05, itemRevenue: 900, views_recent_7d: 60, views_prior_7d: 40, views_growth_rate: 0.5 },
            { itemName: 'Beta', item_category: 'Apparel', item_category_source: 'ga4', itemsViewed: 300, cart_to_view_rate: 0.1, purchase_to_view_rate: 0.02, itemRevenue: 300, views_recent_7d: 100, views_prior_7d: 200, views_growth_rate: -0.5 },
        ],
    },
});

const openTab = async (user, label) => {
    await user.click(screen.getByRole('button', { name: label }));
};

describe('GA4Insights（docs/66 分頁狀態抽 hook）', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        usePermission.mockReturnValue({ hasPermission: true, loading: false, error: null });
        useSelectedTeamId.mockReturnValue('team-1');

        ga4Service.getProperties.mockResolvedValue([
            { property_id: '111111', display_name: 'Site A' },
            { property_id: '222222', display_name: 'Site B' },
        ]);
        lineService.getStatus.mockResolvedValue({ configured: false });
        ga4InsightsService.listRules.mockResolvedValue({ rules: [] });
        ga4InsightsService.listEvents.mockResolvedValue({ events: [], page: 1, total: 0, unacknowledged_total: 0 });
        ga4InsightsService.getDashboard.mockResolvedValue({ payload: {} });
        ga4InsightsService.getRealtime.mockResolvedValue(null);
        ga4InsightsService.getLandingPages.mockResolvedValue(landingSnapshot());
        ga4InsightsService.getItems.mockResolvedValue(itemsSnapshot());
        ga4InsightsService.listLandingPageRules.mockResolvedValue({ rules: [] });
        ga4InsightsService.listItemCategoryRules.mockResolvedValue({ rules: [] });
        ga4InsightsService.listChannelGroups.mockResolvedValue({ groups: [] });
        ga4InsightsService.listChannelGroupRules.mockResolvedValue({ rules: [] });
        ga4InsightsService.getChannels.mockResolvedValue({ payload: { channels: [] } });
    });

    const renderPage = async () => {
        renderWithOutlet(<GA4Insights />, {
            route: '/ga4-insights', path: '/ga4-insights',
            // renderWithOutlet 預設 language 是 'en'，這裡的斷言用中文標籤。
            outletContext: { isMobile: false, language: 'zh' },
        });
        await screen.findByRole('button', { name: '到達頁' });
    };

    it('切到到達頁只載入一次；切走再切回來不重載，且篩選條件還在', async () => {
        const user = userEvent.setup();
        await renderPage();

        await openTab(user, '到達頁');
        await waitFor(() => expect(ga4InsightsService.getLandingPages).toHaveBeenCalledTimes(1));
        await screen.findByText('/products/a');

        // 選一個分類篩選，只留文章
        await user.click(screen.getByRole('button', { name: /文章 \(1\)/ }));
        expect(screen.queryByText('/products/a')).not.toBeInTheDocument();

        // 切到商品分頁再切回來
        await openTab(user, '商品');
        await waitFor(() => expect(ga4InsightsService.getItems).toHaveBeenCalledTimes(1));
        await openTab(user, '到達頁');

        // 沒有重新請求，篩選條件也還在（快照與篩選都留在父層的 hook 裡）
        expect(ga4InsightsService.getLandingPages).toHaveBeenCalledTimes(1);
        await screen.findByText('/blog/b');
        expect(screen.queryByText('/products/a')).not.toBeInTheDocument();
    });

    it('切換 GA4 屬性會清掉兩個分頁的快照與篩選，回到該分頁時重新載入', async () => {
        const user = userEvent.setup();
        await renderPage();

        await openTab(user, '到達頁');
        await waitFor(() => expect(ga4InsightsService.getLandingPages).toHaveBeenCalledTimes(1));
        await user.click(screen.getByRole('button', { name: /文章 \(1\)/ }));

        // 頁面最上方的 GA4 屬性下拉是第一個 combobox。
        await user.selectOptions(screen.getAllByRole('combobox')[0], '222222');

        await waitFor(() => expect(ga4InsightsService.getLandingPages).toHaveBeenCalledTimes(2));
        // 分類篩選回到「全部」——兩列都在
        await screen.findByText('/products/a');
        await screen.findByText('/blog/b');
        expect(ga4InsightsService.getLandingPages).toHaveBeenLastCalledWith('222222', 7, null, null, null, null, false);
    });

    it('新增到達頁分類規則後，規則列表與到達頁資料都會重載', async () => {
        const user = userEvent.setup();
        ga4InsightsService.upsertLandingPageRule.mockResolvedValue({});
        await renderPage();

        await openTab(user, '到達頁');
        await waitFor(() => expect(ga4InsightsService.listLandingPageRules).toHaveBeenCalledTimes(1));

        await user.click(screen.getByRole('button', { name: /分類規則/ }));
        await user.type(screen.getByPlaceholderText(/比對字串/), '/promo');
        await user.click(screen.getByRole('button', { name: '新增規則' }));

        await waitFor(() => expect(ga4InsightsService.upsertLandingPageRule).toHaveBeenCalledTimes(1));
        expect(ga4InsightsService.upsertLandingPageRule).toHaveBeenCalledWith(
            expect.objectContaining({ property_id: '111111', pattern: '/promo' })
        );
        await waitFor(() => expect(ga4InsightsService.listLandingPageRules).toHaveBeenCalledTimes(2));
        await waitFor(() => expect(ga4InsightsService.getLandingPages).toHaveBeenCalledTimes(2));
    });

    it('商品表格點表頭會切換排序欄位與方向', async () => {
        const user = userEvent.setup();
        await renderPage();

        await openTab(user, '商品');
        await screen.findByText('Alpha');

        const rowNames = () => screen.getAllByRole('row').slice(1).map((row) => within(row).getAllByRole('cell')[0].textContent);

        // 預設排序（潛力商品優先，兩者皆非潛力→維持原順序）
        expect(rowNames()).toEqual(['Alpha', 'Beta']);

        // 點「瀏覽」→ 數字欄預設由大到小
        await user.click(screen.getByRole('columnheader', { name: '瀏覽' }));
        expect(rowNames()).toEqual(['Beta', 'Alpha']);

        // 再點一次同一欄 → 反向
        // 欄名已經帶上排序箭頭，用完整文字匹配
        await user.click(screen.getByRole('columnheader', { name: '瀏覽 ▼' }));
        expect(rowNames()).toEqual(['Alpha', 'Beta']);
    });

    it('DaySelector 自訂天數：有效值生效、無效值還原顯示', async () => {
        const user = userEvent.setup();
        await renderPage();

        await openTab(user, '到達頁');
        await waitFor(() => expect(ga4InsightsService.getLandingPages).toHaveBeenCalledTimes(1));

        const custom = screen.getByPlaceholderText('自訂');
        await user.type(custom, '45');
        await user.tab();
        await waitFor(() => expect(ga4InsightsService.getLandingPages).toHaveBeenLastCalledWith('111111', 45, null, null, null, null, false));

        // 超出 1-90 範圍：不送出請求，輸入框還原成目前的值
        const callsBefore = ga4InsightsService.getLandingPages.mock.calls.length;
        await user.clear(custom);
        await user.type(custom, '999');
        await user.tab();
        expect(ga4InsightsService.getLandingPages).toHaveBeenCalledTimes(callsBefore);
        expect(custom).toHaveValue(45);
    });
});
