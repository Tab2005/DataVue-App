// 使用者回報：從成效分析匯入時，批次摘要只顯示「本次送出/成功/失敗」——
// 這些只代表匯入請求本身是否被接受，實際 AI 評分是背景非同步進行的
// （docs/68 B1），使用者看不到成功匯入的項目裡到底有幾筆真的評估完成、
// 進了評估紀錄。這裡驗證批次摘要面板會即時彙總 observationImportState
// 算出「評估完成」筆數，並隨評分狀態更新而重新計算。
import React from 'react';
import { render, screen } from '@testing-library/react';

import MetaAndromedaImportActions from '../MetaAndromedaImportActions';

const baseProps = {
    canUseObservationImport: true,
    isMobile: false,
    language: 'zh',
    selectedObservationRows: [],
    observationImportableRows: [],
    observationWindowKind: 'last_7d',
    handleToggleAllObservationRows: vi.fn(),
    handleBatchObservationImport: vi.fn(),
};

describe('MetaAndromedaImportActions evaluation summary (使用者回報：批次摘要看不到評估完成筆數)', () => {
    it('does not render an evaluation stat card before any batch has been sent', () => {
        render(<MetaAndromedaImportActions {...baseProps} observationBatchSummary={null} observationImportState={{}} />);

        expect(screen.queryByText('評估完成（進評估紀錄）')).not.toBeInTheDocument();
    });

    it('shows 0/N evaluated while scoring is still in progress for every successfully imported row', () => {
        const observationBatchSummary = {
            status: 'success',
            attemptedCount: 3,
            successCount: 3,
            failureCount: 0,
            rowIds: ['row_1', 'row_2', 'row_3'],
            message: '批次送出完成，成功送出 3 筆，失敗 0 筆。',
        };
        const observationImportState = {
            row_1: { scoreStatus: 'pending_observation' },
            row_2: { scoreStatus: 'queued_background' },
            row_3: { scoreStatus: 'processing' },
        };

        render(
            <MetaAndromedaImportActions
                {...baseProps}
                observationBatchSummary={observationBatchSummary}
                observationImportState={observationImportState}
            />
        );

        expect(screen.getByText('評估完成（進評估紀錄）')).toBeInTheDocument();
        expect(screen.getByText('0 / 3')).toBeInTheDocument();
        expect(screen.getByText('評估中 3')).toBeInTheDocument();
    });

    it('updates the evaluated count live as observationImportState resolves each row to a terminal score status', () => {
        const observationBatchSummary = {
            status: 'success',
            attemptedCount: 3,
            successCount: 3,
            failureCount: 0,
            rowIds: ['row_1', 'row_2', 'row_3'],
            message: '批次送出完成，成功送出 3 筆，失敗 0 筆。',
        };
        const observationImportState = {
            row_1: { scoreStatus: 'completed' },
            row_2: { scoreStatus: 'completed' },
            row_3: { scoreStatus: 'failed' },
        };

        render(
            <MetaAndromedaImportActions
                {...baseProps}
                observationBatchSummary={observationBatchSummary}
                observationImportState={observationImportState}
            />
        );

        expect(screen.getByText('2 / 3')).toBeInTheDocument();
        expect(screen.getByText('失敗 1')).toBeInTheDocument();
    });

    it('excludes rows outside this batch (rowIds) from the evaluation count even if they exist in observationImportState', () => {
        const observationBatchSummary = {
            status: 'success',
            attemptedCount: 1,
            successCount: 1,
            failureCount: 0,
            rowIds: ['row_current_batch'],
            message: '批次送出完成，成功送出 1 筆，失敗 0 筆。',
        };
        const observationImportState = {
            row_current_batch: { scoreStatus: 'completed' },
            row_from_earlier_unrelated_batch: { scoreStatus: 'failed' },
        };

        render(
            <MetaAndromedaImportActions
                {...baseProps}
                observationBatchSummary={observationBatchSummary}
                observationImportState={observationImportState}
            />
        );

        expect(screen.getByText('1 / 1')).toBeInTheDocument();
        expect(screen.queryByText('失敗 1')).not.toBeInTheDocument();
    });
});
