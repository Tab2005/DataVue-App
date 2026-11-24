// 回歸測試：KpiTab 切換「按月 / 按季」時會呼叫 currentMonthKey / currentQuarterKey，
// 這兩個函式曾在拆分元件時漏 import，一切換就 ReferenceError 讓整個分頁壞掉。
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';

import KpiTab from '../KpiTab';
import { currentMonthKey, currentQuarterKey } from '../GA4InsightsShared';

const renderKpiTab = (setKpiForm) => render(
    <KpiTab
        t={(en, zh) => zh}
        isMobile={false}
        kpiForm={{ metric_key: 'sessions', period_type: 'month', period_key: currentMonthKey(), target_value: '' }}
        setKpiForm={setKpiForm}
        kpiSaving={false}
        handleCreateKpiTarget={vi.fn()}
        kpiError={null}
        kpiLoading={false}
        kpiTargets={[]}
        language="zh"
        handleDeleteKpiTarget={vi.fn()}
    />,
);

const applyUpdate = (setKpiForm, prev) => setKpiForm.mock.calls.at(-1)[0](prev);

describe('KpiTab period type switch', () => {
    it('switches to quarter and fills the current quarter key', () => {
        const setKpiForm = vi.fn();
        renderKpiTab(setKpiForm);
        fireEvent.change(screen.getByDisplayValue('按月'), { target: { value: 'quarter' } });
        const next = applyUpdate(setKpiForm, { period_type: 'month', period_key: 'x' });
        expect(next).toMatchObject({ period_type: 'quarter', period_key: currentQuarterKey() });
    });

    it('switches back to month and fills the current month key', () => {
        const setKpiForm = vi.fn();
        renderKpiTab(setKpiForm);
        fireEvent.change(screen.getByDisplayValue('按月'), { target: { value: 'month' } });
        const next = applyUpdate(setKpiForm, { period_type: 'quarter', period_key: 'x' });
        expect(next).toMatchObject({ period_type: 'month', period_key: currentMonthKey() });
    });
});
