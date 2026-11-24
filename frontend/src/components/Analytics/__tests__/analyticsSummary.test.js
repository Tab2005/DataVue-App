// docs/33 第 7 波：Analytics.jsx 組合層瘦身時把 calculateSummary 抽成獨立
// 純函數（見 ../analyticsSummary.js），原本沒有任何測試直接鎖住這份
// 115 行的加總/衍生指標公式，抽出後補上基本驗證。
import { describe, expect, it } from 'vitest';

import { calculateSummary, renderMetricValue } from '../analyticsSummary';

describe('calculateSummary', () => {
    const rows = [
        { id: 'a', spend: 100, impressions: 1000, clicks: 20, link_clicks: 10, reach: 500, unique_clicks: 5, purchases: 2, purchase_value: 300, add_to_cart: 4 },
        { id: 'b', spend: 200, impressions: 2000, clicks: 40, link_clicks: 30, reach: 1000, unique_clicks: 15, purchases: 3, purchase_value: 600, add_to_cart: 6 },
    ];

    it('returns null when no rows match the current selection', () => {
        expect(calculateSummary([], new Set(['a']))).toBeNull();
        expect(calculateSummary(rows, new Set(['not-a-row']))).toBeNull();
    });

    it('sums additive metrics only across selected rows', () => {
        const summary = calculateSummary(rows, new Set(['a']));
        expect(summary.spend).toBe(100);
        expect(summary.impressions).toBe(1000);
        expect(summary.purchases).toBe(2);
    });

    it('sums additive metrics across all rows when all are selected', () => {
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.spend).toBe(300);
        expect(summary.impressions).toBe(3000);
        expect(summary.clicks).toBe(60);
        expect(summary.link_clicks).toBe(40);
        expect(summary.purchases).toBe(5);
        expect(summary.purchase_value).toBe(900);
    });

    it('recomputes rate metrics from summed raw counts instead of summing per-row rates', () => {
        // docs/58 既有註解強調的陷阱：CTR 類欄位絕不能逐列加總，必須用
        // 加總後的原始數字重新計算，否則會膨脹（10 天各 2% 加總變 20%）。
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.ctr).toBeCloseTo((60 / 3000) * 100, 6);
        expect(summary.roas).toBeCloseTo(900 / 300, 6);
        expect(summary.cpa).toBeCloseTo(300 / 5, 6);
        expect(summary.cvr).toBeCloseTo((5 / 40) * 100, 6);
    });

    it('avoids division by zero for derived rates when the denominator is zero', () => {
        const zeroRow = [{ id: 'z', spend: 0, impressions: 0, clicks: 0, link_clicks: 0, reach: 0, purchases: 0, purchase_value: 0 }];
        const summary = calculateSummary(zeroRow, new Set(['z']));
        expect(summary.roas).toBe(0);
        expect(summary.ctr).toBe(0);
        expect(summary.cpa).toBe(0);
    });
});

describe('renderMetricValue', () => {
    it('renders a dash for missing/NaN values', () => {
        expect(renderMetricValue(undefined)).toBe('-');
        expect(renderMetricValue(null)).toBe('-');
        expect(renderMetricValue(NaN)).toBe('-');
    });

    it('formats currency, percent, and decimal values', () => {
        expect(renderMetricValue(1234.5, 'currency')).toBe('$1,235');
        expect(renderMetricValue(12.345, 'percent')).toBe('12.35%');
        expect(renderMetricValue(3.14159, 'decimal')).toBe('3.14');
    });

    it('shows currency_decimal with a decimal only when the value is not whole', () => {
        expect(renderMetricValue(10, 'currency_decimal')).toBe('$10');
        expect(renderMetricValue(10.5, 'currency_decimal')).toBe('$10.5');
    });
});

describe('calculateSummary messaging metrics', () => {
    const rows = [
        { id: 'a', spend: 100, messaging_conversation_started: 10, messaging_depth_2: 5, messaging_conversation_replied: 8, messaging_blocks: 1, messaging_welcome_message_view: 40 },
        { id: 'b', spend: 300, messaging_conversation_started: 30, messaging_depth_2: 9, messaging_conversation_replied: 12, messaging_blocks: 3, messaging_welcome_message_view: 60 },
    ];

    it('sums raw messaging counts', () => {
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.messaging_conversation_started).toBe(40);
        expect(summary.messaging_welcome_message_view).toBe(100);
        expect(summary.messaging_blocks).toBe(4);
    });

    it('recomputes messaging rates from summed counts instead of summing row rates', () => {
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.cost_per_conversation_started).toBe(10);
        expect(summary.messaging_depth_2_rate).toBeCloseTo(35);
        expect(summary.messaging_reply_rate).toBeCloseTo(50);
        expect(summary.messaging_block_rate).toBeCloseTo(10);
    });

    it('returns 0 rates when no conversations started', () => {
        const summary = calculateSummary([{ id: 'x', spend: 50, messaging_blocks: 2 }], new Set(['x']));
        expect(summary.messaging_block_rate).toBe(0);
        expect(summary.cost_per_conversation_started).toBe(0);
    });
});

describe('calculateSummary IG and 6-second video metrics', () => {
    const rows = [
        { id: 'a', spend: 100, impressions: 1000, video_6_sec_views: 200, instagram_profile_visits: 5, instagram_profile_follow: 1 },
        { id: 'b', spend: 300, impressions: 3000, video_6_sec_views: 200, instagram_profile_visits: 7, instagram_profile_follow: 2 },
    ];

    it('sums IG profile counts and 6-second views', () => {
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.instagram_profile_visits).toBe(12);
        expect(summary.instagram_profile_follow).toBe(3);
        expect(summary.video_6_sec_views).toBe(400);
    });

    it('recomputes 6-second rate and cost from summed counts', () => {
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.video_6_sec_view_rate).toBeCloseTo(10);
        expect(summary.cost_per_6_sec_video_view).toBe(1);
    });
});

describe('calculateSummary results', () => {
    it('sums results when all rows share one result type', () => {
        const rows = [
            { id: 'a', spend: 200, results: 10, result_type: '購買' },
            { id: 'b', spend: 100, results: 5, result_type: '購買' },
        ];
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.results).toBe(15);
        expect(summary.result_type).toBe('購買');
        expect(summary.cost_per_result).toBe(20);
    });

    it('does not add up different result types', () => {
        const rows = [
            { id: 'a', spend: 200, results: 10, result_type: '購買' },
            { id: 'b', spend: 100, results: 50, result_type: '開始對話' },
        ];
        const summary = calculateSummary(rows, new Set(['a', 'b']));
        expect(summary.results).toBeNull();
        expect(summary.result_type).toBe('多種');
        expect(summary.cost_per_result).toBeNull();
    });

    it('treats a single mixed-objective row as having no total', () => {
        const summary = calculateSummary([{ id: 'a', spend: 100, results: null, result_type: '多種' }], new Set(['a']));
        expect(summary.results).toBeNull();
        expect(summary.result_type).toBe('多種');
    });

    it('leaves results empty when rows have no results (account level)', () => {
        const summary = calculateSummary([{ id: 'a', spend: 100, results: null, result_type: '' }], new Set(['a']));
        expect(summary.results).toBeNull();
        expect(summary.result_type).toBeNull();
    });
});
