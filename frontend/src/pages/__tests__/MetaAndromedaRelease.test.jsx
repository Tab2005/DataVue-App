import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import MetaAndromedaRelease from '../MetaAndromedaRelease';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import {
    approveMetaAndromedaRelease,
    fetchMetaAndromedaReleaseOverview,
} from '../../services/metaAndromedaReleaseService';

vi.mock('../../hooks/usePermission', () => ({
    usePermission: vi.fn(() => ({ hasPermission: true, loading: false })),
}));

vi.mock('../../services/metaAndromedaReleaseService', () => ({
    fetchMetaAndromedaReleaseOverview: vi.fn(),
    approveMetaAndromedaRelease: vi.fn(),
    rejectMetaAndromedaRelease: vi.fn(),
    rollbackMetaAndromedaRelease: vi.fn(),
}));

describe('MetaAndromedaRelease', () => {
    beforeEach(() => {
        vi.clearAllMocks();
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
});
