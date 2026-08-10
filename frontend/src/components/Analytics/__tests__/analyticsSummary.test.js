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
