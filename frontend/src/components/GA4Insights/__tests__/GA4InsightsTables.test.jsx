// docs/64：共用表格元件的測試。這些元件同時被應用內分頁與分享頁引用，所以
// 一份斷言等於同時鎖住兩個表面——這正是 docs/59 P2-3 想要的「靠結構保證，
// 不是靠人記得」。最後一組（分享頁回歸）直接對應 docs/64 §1 的落差表。
import React from 'react';
import { render, screen } from '@testing-library/react';

import {
    ChannelsTable,
    GrowthBadge,
    ItemLandingCrossTable,
    ItemsTable,
    LandingPagesTable,
    PayloadWarnings,
} from '../GA4InsightsTables';
import SharedGA4Insight from '../../../pages/SharedGA4Insight';
import { renderWithOutlet } from '../../../test/renderWithOutlet';
import { ga4InsightsService } from '../../../services/ga4InsightsService';

vi.mock('../../../services/ga4InsightsService', () => ({
    ga4InsightsService: { getSharedSnapshot: vi.fn() },
}));

const t = (en, zh) => zh;
const language = 'zh';

const PP_TITLE = 'pp＝百分點，是跟上一期的絕對差距（例如比率從 5% 變 6% 是 +1.0pp，不是成長 20%）。';

const landingPayload = (overrides = {}) => ({
    compare_enabled: true,
    key_events_count_definition: '關鍵事件次數的定義文字',
    session_key_event_rate_definition: '工作階段轉換率的定義文字',
    landing_pages: [],
    ...overrides,
});

const landingRow = (overrides = {}) => ({
    landingPage: '/product/a',
    category: 'product',
    sessions: 1200,
    sessions_growth_rate: 0.12,
    conversions: 30,
    conversions_growth_rate: -0.05,
    session_key_event_rate: 0.025,
    session_key_event_rate_delta_pp: 1.0,
    bounceRate: 0.4,
    bounce_rate_delta_pp: -2.5,
    ...overrides,
});

const itemsPayload = (overrides = {}) => ({
    compare_enabled: true,
    cart_to_view_rate_definition: '加購率定義文字',
    purchase_to_view_rate_definition: '購買率定義文字',
    items: [],
    ...overrides,
});

const itemRow = (overrides = {}) => ({
    itemName: '藍色 T 恤',
    item_category: '服飾',
    item_category_source: 'ga4',
    itemsViewed: 500,
    views_compare_growth_rate: 0.2,
    cart_to_view_rate: 0.1,
    cart_to_view_rate_delta_pp: 0.5,
    purchase_to_view_rate: 0.03,
    purchase_to_view_rate_delta_pp: -0.2,
    views_recent_7d: 300,
    views_prior_7d: 200,
    views_growth_rate: 0.5,
    itemRevenue: 12345,
    revenue_growth_rate: 0.08,
    ...overrides,
});

const crossRow = (overrides = {}) => ({
    itemName: '藍色 T 恤',
    primary_landing_page: '/product/tee',
    purchase_to_view_rate: 0.03,
    purchase_to_view_rate_delta_pp: 0.4,
    page_session_key_event_rate: 0.02,
    page_session_key_event_rate_delta_pp: -0.3,
    page_sessions: 800,
    page_sessions_growth_rate: 0.15,
    ...overrides,
});

describe('GrowthBadge', () => {
    it('次數類指標用相對成長率，不帶 pp 說明', () => {
        render(<GrowthBadge value={0.123} t={t} />);
        expect(screen.getByText('▲12%')).toBeInTheDocument();
        expect(screen.queryByTitle(PP_TITLE)).not.toBeInTheDocument();
    });

    it('比率類指標用百分點並附 pp 說明（docs/54：5%→6% 不是成長 20%）', () => {
        render(<GrowthBadge value={1.0} isPercentagePoint t={t} />);
        const badge = screen.getByText('▲1.0pp');
        expect(badge).toBeInTheDocument();
        expect(badge).toHaveAttribute('title', PP_TITLE);
    });

    it('下跌顯示向下箭頭且取絕對值', () => {
        render(<GrowthBadge value={-0.4} t={t} />);
        expect(screen.getByText('▼40%')).toBeInTheDocument();
    });

    it('沒有比較數值時整個不顯示', () => {
        const { container } = render(<GrowthBadge value={null} t={t} />);
        expect(container).toBeEmptyDOMElement();
    });
});

describe('LandingPagesTable', () => {
    it('轉換次數與轉換率表頭帶得出 payload 的定義提示', () => {
        render(<LandingPagesTable language={language} t={t} payload={landingPayload()} rows={[landingRow()]} />);
        expect(screen.getByTitle('關鍵事件次數的定義文字')).toBeInTheDocument();
        expect(screen.getByTitle('工作階段轉換率的定義文字')).toBeInTheDocument();
    });

    it('次數欄走成長率、比率欄走百分點', () => {
        render(<LandingPagesTable language={language} t={t} payload={landingPayload()} rows={[landingRow()]} />);
        expect(screen.getByText('▲12%')).toBeInTheDocument();   // 工作階段
        expect(screen.getByText('▼5%')).toBeInTheDocument();    // 轉換次數
        expect(screen.getByText('▲1.0pp')).toBeInTheDocument(); // 轉換率
        expect(screen.getByText('▼2.5pp')).toBeInTheDocument(); // 跳出率
    });

    it('比較查詢失敗時不顯示任何成長標示', () => {
        const payload = landingPayload({ compare_query_error: 'boom' });
        render(<LandingPagesTable language={language} t={t} payload={payload} rows={[landingRow()]} />);
        expect(screen.queryByText('▲12%')).not.toBeInTheDocument();
        expect(screen.queryByText('▲1.0pp')).not.toBeInTheDocument();
    });

    it('新頁面只顯示「新」標籤，不顯示成長標示', () => {
        const rows = [landingRow({ is_new: true })];
        render(<LandingPagesTable language={language} t={t} payload={landingPayload()} rows={rows} />);
        expect(screen.getByText('🆕 新')).toBeInTheDocument();
        expect(screen.queryByText('▲12%')).not.toBeInTheDocument();
    });
});

describe('ItemsTable', () => {
    it('預設用靜態表頭，含「瀏覽成長」欄', () => {
        render(<ItemsTable language={language} t={t} payload={itemsPayload()} rows={[itemRow()]} />);
        expect(screen.getByText('瀏覽成長')).toBeInTheDocument();
        expect(screen.getByTitle('加購率定義文字')).toBeInTheDocument();
    });

    it('呼叫端可以用 renderHeader 換成可排序表頭', () => {
        const renderHeader = (key, label) => <th key={key} data-testid={`sort-${key}`}>{label}</th>;
        render(<ItemsTable language={language} t={t} payload={itemsPayload()} rows={[itemRow()]} renderHeader={renderHeader} />);
        expect(screen.getByTestId('sort-itemName')).toBeInTheDocument();
        expect(screen.getByTestId('sort-views_growth_rate')).toBeInTheDocument();
    });

    it('自訂規則分類標上 ✎', () => {
        const rows = [itemRow({ item_category_source: 'custom_rule' })];
        render(<ItemsTable language={language} t={t} payload={itemsPayload()} rows={rows} />);
        expect(screen.getByText(/服飾\s*✎/)).toBeInTheDocument();
    });

    it('前 7 天沒有瀏覽、近 7 天有的商品標「新進榜」', () => {
        const rows = [itemRow({ views_prior_7d: 0, views_recent_7d: 120 })];
        render(<ItemsTable language={language} t={t} payload={itemsPayload()} rows={rows} />);
        expect(screen.getByText('新進榜')).toBeInTheDocument();
    });
});

describe('ChannelsTable', () => {
    const payload = {
        dimension: 'sessionSource',
        attribution_model: 'last_click',
        total_closing_conversions: 200,
    };
    const rows = [{ channel: 'google', assisting_conversions: 40, closing_conversions: 50, ratio: 0.8, tag: 'close' }];

    it('標籤欄附上該渠道佔收單轉換的比例', () => {
        render(<ChannelsTable language={language} t={t} payload={payload} rows={rows} />);
        expect(screen.getByText('(佔收單 25.0%)')).toBeInTheDocument();
    });

    it('總收單為 0 時不顯示比例（避免除以零）', () => {
        render(<ChannelsTable language={language} t={t} payload={{ ...payload, total_closing_conversions: 0 }} rows={rows} />);
        expect(screen.queryByText(/佔收單/)).not.toBeInTheDocument();
    });
});

describe('ItemLandingCrossTable', () => {
    it('商品側查詢失敗時只關掉商品側的成長標示，到達頁側照常', () => {
        const payload = { compare_enabled: true, item_compare_query_error: 'boom' };
        render(<ItemLandingCrossTable t={t} payload={payload} rows={[crossRow()]} />);
        expect(screen.queryByText('▲0.4pp')).not.toBeInTheDocument(); // 商品購買率
        expect(screen.getByText('▼0.3pp')).toBeInTheDocument();       // 到達頁轉換率
        expect(screen.getByText('▲15%')).toBeInTheDocument();         // 到達頁工作階段
    });

    it('到達頁側查詢失敗時只關掉到達頁側的成長標示', () => {
        const payload = { compare_enabled: true, landing_compare_query_error: 'boom' };
        render(<ItemLandingCrossTable t={t} payload={payload} rows={[crossRow()]} />);
        expect(screen.getByText('▲0.4pp')).toBeInTheDocument();
        expect(screen.queryByText('▼0.3pp')).not.toBeInTheDocument();
        expect(screen.queryByText('▲15%')).not.toBeInTheDocument();
    });

    it('沒有對應到達頁的商品顯示替代文字', () => {
        const rows = [crossRow({ primary_landing_page: null })];
        render(<ItemLandingCrossTable t={t} payload={{}} rows={rows} />);
        expect(screen.getByText('無對應到達頁')).toBeInTheDocument();
    });
});

describe('PayloadWarnings', () => {
    it('商品快照顯示分類抓取失敗與本地估算比率的但書', () => {
        const payload = { used_fallback_conversion_metrics: true, category_breakdown_error: 'boom' };
        render(<PayloadWarnings t={t} payload={payload} kind="item" />);
        expect(screen.getByText(/以下商品因此都顯示「未分類」/)).toBeInTheDocument();
        expect(screen.getByText(/改顯示本地計算的比率/)).toBeInTheDocument();
    });

    it('橫幅只在屬於該 kind 時出現', () => {
        const payload = { category_breakdown_error: 'boom', truncated: true, total_row_count: 57 };
        render(<PayloadWarnings t={t} payload={payload} kind="daily_channel" />);
        expect(screen.getByText(/共 57 個項目/)).toBeInTheDocument();
        expect(screen.queryByText(/未分類/)).not.toBeInTheDocument();
    });

    it('比較相關的橫幅要 compare_enabled 才算數', () => {
        const { container } = render(
            <PayloadWarnings t={t} payload={{ compare_query_error: 'boom' }} kind="landing_page" />
        );
        expect(container).toBeEmptyDOMElement();
    });

    it('商品頁面比對缺對照資料時提醒「無對應到達頁」不是長期缺資料', () => {
        render(<PayloadWarnings t={t} payload={{ mapping_query_error: 'boom' }} kind="item_landing_cross" />);
        expect(screen.getByText(/非長期缺資料/)).toBeInTheDocument();
    });

    it('沒有任何狀況時不佔版面', () => {
        const { container } = render(<PayloadWarnings t={t} payload={{}} kind="item" />);
        expect(container).toBeEmptyDOMElement();
    });
});

// docs/64 §1：以下每一條都是共用化之前分享頁「應用內分頁有、分享頁沒有」的
// 缺漏。共用之後它們會自動跟著分頁走，這組測試就是防止有人把分享頁又切回
// 第二套實作。
describe('SharedGA4Insight 吃共用元件（回歸鎖）', () => {
    const renderShared = async (snapshot) => {
        ga4InsightsService.getSharedSnapshot.mockResolvedValue(snapshot);
        renderWithOutlet(<SharedGA4Insight />, { route: '/share/ga4/tok1', path: '/share/ga4/:token' });
        await screen.findByRole('heading', { level: 1 });
    };

    it('商品分享頁有「瀏覽成長」欄與兩條資料品質橫幅', async () => {
        await renderShared({
            kind: 'item',
            date: '2026-08-01',
            property_id: '123456',
            payload: itemsPayload({
                items: [itemRow({ item_category_source: 'custom_rule' })],
                category_counts: { 服飾: 1 },
                used_fallback_conversion_metrics: true,
                category_breakdown_error: 'boom',
            }),
        });
        expect(screen.getByText('瀏覽成長')).toBeInTheDocument();
        expect(screen.getByText(/以下商品因此都顯示「未分類」/)).toBeInTheDocument();
        expect(screen.getByText(/改顯示本地計算的比率/)).toBeInTheDocument();
        expect(screen.getByText(/服飾\s*✎/)).toBeInTheDocument();
    });

    it('到達頁分享頁的表頭帶得出定義提示', async () => {
        await renderShared({
            kind: 'landing_page',
            date: '2026-08-01',
            property_id: '123456',
            payload: landingPayload({ landing_pages: [landingRow()], category_counts: { product: 1 } }),
        });
        expect(screen.getByTitle('關鍵事件次數的定義文字')).toBeInTheDocument();
        expect(screen.getByText('▲1.0pp')).toBeInTheDocument();
    });

    it('渠道分享頁有截斷但書與佔收單比例', async () => {
        await renderShared({
            kind: 'daily_channel',
            date: '2026-08-01',
            property_id: '123456',
            payload: {
                dimension: 'sessionSource',
                attribution_model: 'last_click',
                total_closing_conversions: 200,
                truncated: true,
                total_row_count: 57,
                channels: [{ channel: 'google', assisting_conversions: 40, closing_conversions: 50, ratio: 0.8, tag: 'close' }],
            },
        });
        expect(screen.getByText(/共 57 個項目/)).toBeInTheDocument();
        expect(screen.getByText('(佔收單 25.0%)')).toBeInTheDocument();
    });

    it('商品頁面比對分享頁有對照資料缺漏的但書', async () => {
        await renderShared({
            kind: 'item_landing_cross',
            date: '2026-08-01',
            property_id: '123456',
            payload: {
                compare_enabled: true,
                used_fallback_conversion_metrics: true,
                landing_query_error: 'boom',
                items: [crossRow()],
            },
        });
        expect(screen.getByText(/非長期缺資料/)).toBeInTheDocument();
        expect(screen.getByText(/改顯示本地計算的比率/)).toBeInTheDocument();
    });
});
