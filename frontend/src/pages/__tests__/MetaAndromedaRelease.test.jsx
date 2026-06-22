import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import MetaAndromedaRelease from '../MetaAndromedaRelease';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import { useModuleAccess } from '../../hooks/usePermission';
import {
    approveMetaAndromedaRelease,
    fetchMetaAndromedaReleaseOverview,
} from '../../services/metaAndromedaReleaseService';
import { fetchMetaAndromedaMonitoringSummary } from '../../services/metaAndromedaMonitoringService';

vi.mock('../../hooks/usePermission', () => ({
    useModuleAccess: vi.fn(),
}));

vi.mock('../../services/metaAndromedaReleaseService', () => ({
    fetchMetaAndromedaReleaseOverview: vi.fn(),
    approveMetaAndromedaRelease: vi.fn(),
    rejectMetaAndromedaRelease: vi.fn(),
    rollbackMetaAndromedaRelease: vi.fn(),
}));

vi.mock('../../services/metaAndromedaMonitoringService', () => ({
    fetchMetaAndromedaMonitoringSummary: vi.fn(() => Promise.resolve({ latest_drift_reports: [] })),
    fetchMetaAndromedaMonitoringTimeline: vi.fn(),
    triggerMetaAndromedaDriftReport: vi.fn(),
    syncMetaAndromedaCalibrationDataset: vi.fn(),
}));

describe('MetaAndromedaRelease', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        fetchMetaAndromedaReleaseOverview.mockResolvedValue({
            current_production: {
                model_version: 'prod_v1',
                release_status: 'production',
                approved_by: 'owner',
                pairwise_ranking_accuracy: 0.8,
                mean_band_error: 0.2,
            },
            previous_production: {
                model_version: 'prod_v0',
                release_status: 'superseded',
                approved_by: 'owner',
                pairwise_ranking_accuracy: 0.75,
                mean_band_error: 0.22,
            },
            candidates: [
                {
                    model_version: 'cand_v2',
                    release_status: 'candidate',
                    pairwise_ranking_accuracy: 0.85,
                    mean_band_error: 0.18,
                    promotion_gate_summary: { sample_size_ok: true },
                },
            ],
            history: [],
            notes: ['note'],
        });
        approveMetaAndromedaRelease.mockResolvedValue({
            action: 'approve',
            model_version: 'cand_v2',
        });
        vi.spyOn(window, 'prompt').mockReturnValue('Ship it');
    });

    afterEach(() => {
        window.prompt.mockRestore();
    });

    it('approves a release candidate', async () => {
        renderWithOutlet(<MetaAndromedaRelease />);

        await screen.findByText('cand_v2');
        fireEvent.click(screen.getByRole('button', { name: 'Approve' }));

        await waitFor(() => expect(approveMetaAndromedaRelease).toHaveBeenCalledWith({
            model_version: 'cand_v2',
            note: 'Ship it',
        }));
        expect(fetchMetaAndromedaReleaseOverview).toHaveBeenCalledTimes(2);
    });

    it('disables Approve button and shows warning if online model is drifted', async () => {
        fetchMetaAndromedaMonitoringSummary.mockResolvedValue({
            latest_drift_reports: [
                {
                    drift_report_id: 'dr_001',
                    window_kind: 'last_7d',
                    drift_status: 'drifted',
                    summary: 'Significant prediction accuracy drop detected',
                    severity: 'critical',
                    triggered_by: 'system',
                    created_at: '2026-06-16T12:00:00Z',
                    report_payload: { accuracy: 0.4, mae: 0.8 }
                }
            ]
        });

        renderWithOutlet(<MetaAndromedaRelease />, {
            outletContext: { language: 'zh', isMobile: false }
        });

        await screen.findByText('cand_v2');

        // 線上實測對照證據面板應該顯示 drifted 狀態
        expect(await screen.findByText('嚴重預估偏差')).toBeInTheDocument();

        // 批准 (Approve) 按鈕應該被 disabled
        const approveButton = screen.getByRole('button', { name: '批准' });
        expect(approveButton).toBeDisabled();

        // 應該顯示警告訊息
        expect(screen.getByText(/再行核准新模型/)).toBeInTheDocument();
    });

    it('blocks the page when module access is denied', () => {
        useModuleAccess.mockReturnValue({ hasAccess: false, loading: false, error: null });

        renderWithOutlet(<MetaAndromedaRelease />);

        expect(screen.getByText('You do not have access to Meta Andromeda in this workspace.')).toBeInTheDocument();
        expect(screen.queryByText('Release Overview')).not.toBeInTheDocument();
    });
});
