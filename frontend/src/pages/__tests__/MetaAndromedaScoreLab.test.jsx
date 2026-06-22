import React from 'react';
import { act, fireEvent, screen, waitFor } from '@testing-library/react';

import MetaAndromedaScoreLab from '../MetaAndromedaScoreLab';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import { useModuleAccess } from '../../hooks/usePermission';
import {
    fetchMetaAndromedaScore,
    submitMetaAndromedaScore,
    uploadMetaAndromedaAsset,
} from '../../services/metaAndromedaWorkflowService';

vi.mock('../../hooks/usePermission', () => ({
    useModuleAccess: vi.fn(),
}));

vi.mock('../../services/metaAndromedaWorkflowService', () => ({
    uploadMetaAndromedaAsset: vi.fn(),
    submitMetaAndromedaScore: vi.fn(),
    fetchMetaAndromedaScore: vi.fn(),
}));

describe('MetaAndromedaScoreLab', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
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
        const { container } = renderWithOutlet(<MetaAndromedaScoreLab />);

        const file = new File(['image-bytes'], 'creative.png', { type: 'image/png' });
        fireEvent.change(container.querySelector('#file-upload-input'), {
            target: { files: [file] },
        });

        await screen.findByText('storage://meta-andromeda/uploads/test.png');

        fireEvent.click(screen.getByRole('button', { name: 'Submit Score' }));
        await screen.findByText('evt_score_001');

        await waitFor(() => expect(fetchMetaAndromedaScore).toHaveBeenCalledWith('evt_score_001'));
        await waitFor(() => expect(screen.getByText('91')).toBeInTheDocument());
        expect(screen.getByText('ready')).toBeInTheDocument();
    });

    it('blocks the page when module access is denied', () => {
        useModuleAccess.mockReturnValue({ hasAccess: false, loading: false, error: null });

        renderWithOutlet(<MetaAndromedaScoreLab />);

        expect(screen.getByText('You do not have access to Meta Andromeda in this workspace.')).toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Submit Score' })).not.toBeInTheDocument();
    });
});
