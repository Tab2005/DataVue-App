import React from 'react';
import { act, fireEvent, screen, waitFor } from '@testing-library/react';

import MetaAndromedaScoreLab from '../MetaAndromedaScoreLab';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import {
    fetchMetaAndromedaScore,
    submitMetaAndromedaScore,
    uploadMetaAndromedaAsset,
} from '../../services/metaAndromedaWorkflowService';

vi.mock('../../hooks/usePermission', () => ({
    usePermission: vi.fn(() => ({ hasPermission: true, loading: false })),
}));

vi.mock('../../services/metaAndromedaWorkflowService', () => ({
    uploadMetaAndromedaAsset: vi.fn(),
    submitMetaAndromedaScore: vi.fn(),
    fetchMetaAndromedaScore: vi.fn(),
}));

describe('MetaAndromedaScoreLab', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.spyOn(window, 'setInterval').mockImplementation((callback) => {
            Promise.resolve().then(() => callback());
            return 1;
        });
        vi.spyOn(window, 'clearInterval').mockImplementation(() => {});
        uploadMetaAndromedaAsset.mockResolvedValue({
            asset_uri: 'storage://meta-andromeda/uploads/test.png',
            asset_id: 'asset_001',
            asset_type: 'image',
            storage_key: 'uploads/test.png',
        });
        submitMetaAndromedaScore.mockResolvedValue({
            score_event_id: 'evt_score_001',
            status: 'queued',
            attempt_count: 0,
        });
        fetchMetaAndromedaScore.mockResolvedValue({
            score_event_id: 'evt_score_001',
            status: 'completed',
            attempt_count: 1,
            overall_score: 91,
            explanations: { summary: 'ready' },
        });
    });

    afterEach(() => {
        window.setInterval.mockRestore();
        window.clearInterval.mockRestore();
    });

    it('uploads, submits, and polls until completed', async () => {
        renderWithOutlet(<MetaAndromedaScoreLab />);

        const file = new File(['image-bytes'], 'creative.png', { type: 'image/png' });
        fireEvent.change(screen.getByLabelText('Asset File'), {
            target: { files: [file] },
        });

        fireEvent.click(screen.getByRole('button', { name: 'Upload Asset' }));
        await screen.findByText('storage://meta-andromeda/uploads/test.png');

        fireEvent.click(screen.getByRole('button', { name: 'Submit Score' }));
        await screen.findByText('evt_score_001');

        await waitFor(() => expect(fetchMetaAndromedaScore).toHaveBeenCalledWith('evt_score_001'));
        await waitFor(() => expect(screen.getByText('91')).toBeInTheDocument());
        expect(screen.getByText('ready')).toBeInTheDocument();
    });
});
