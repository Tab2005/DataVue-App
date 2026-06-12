import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import MetaAndromedaReviewQueue from '../MetaAndromedaReviewQueue';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import {
    fetchMetaAndromedaReviewDetail,
    fetchMetaAndromedaReviewFeedback,
    fetchMetaAndromedaReviewQueue,
    submitMetaAndromedaReviewFeedback,
} from '../../services/metaAndromedaReviewQueueService';

vi.mock('../../hooks/usePermission', () => ({
    usePermission: vi.fn(() => ({ hasPermission: true, loading: false })),
}));

vi.mock('../../services/metaAndromedaReviewQueueService', () => ({
    fetchMetaAndromedaReviewQueue: vi.fn(),
    fetchMetaAndromedaReviewDetail: vi.fn(),
    fetchMetaAndromedaReviewFeedback: vi.fn(),
    submitMetaAndromedaReviewFeedback: vi.fn(),
}));

describe('MetaAndromedaReviewQueue', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        fetchMetaAndromedaReviewQueue.mockResolvedValue({
            items: [
                {
                    score_event_id: 'evt_review_001',
                    status: 'completed',
                    objective: 'purchase',
                    placement_family: 'feed',
                    market: 'TW',
                    overall_score: 88,
                    reviewed: false,
                    latest_feedback_decision: null,
                },
            ],
        });
        fetchMetaAndromedaReviewDetail.mockResolvedValue({
            score_event_id: 'evt_review_001',
            status: 'completed',
            asset_type: 'image',
            model_version: 'cand_v2026_06_05_a',
            explanations: { summary: 'review me' },
            overall_score: 88,
            roas_prediction: { band: 'high' },
            top_positive_drivers: ['clear CTA'],
            top_negative_drivers: ['text density'],
        });
        fetchMetaAndromedaReviewFeedback.mockResolvedValue({
            feedback: [],
        });
        submitMetaAndromedaReviewFeedback.mockResolvedValue({
            feedback_event_id: 'fb_001',
        });
    });

    it('submits reviewer feedback with parsed reason codes', async () => {
        renderWithOutlet(<MetaAndromedaReviewQueue />);

        await screen.findByText('evt_review_001');
        await screen.findByText('review me');

        const decisionSelect = screen.getAllByRole('combobox')[2];
        fireEvent.change(decisionSelect, { target: { value: 'revise' } });
        fireEvent.change(screen.getByPlaceholderText('reason codes, comma separated'), {
            target: { value: 'hook_soft, offer_late' },
        });
        fireEvent.change(screen.getByPlaceholderText('review notes'), {
            target: { value: 'Need sharper hook.' },
        });

        fireEvent.click(screen.getByRole('button', { name: 'Submit Feedback' }));

        await waitFor(() => expect(submitMetaAndromedaReviewFeedback).toHaveBeenCalledWith('evt_review_001', {
            decision: 'revise',
            reason_codes: ['hook_soft', 'offer_late'],
            comment: 'Need sharper hook.',
        }));
    });
});
