import React from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';

import MetaAndromedaReviewQueue from '../MetaAndromedaReviewQueue';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import {
    batchDeleteMetaAndromedaReviewItems,
    deleteMetaAndromedaReviewItem,
    fetchMetaAndromedaReviewDetail,
    fetchMetaAndromedaReviewQueue,
} from '../../services/metaAndromedaReviewQueueService';

vi.mock('../../hooks/usePermission', () => ({
    useModuleAccess: vi.fn(() => ({ hasAccess: true, loading: false })),
}));

vi.mock('../../services/metaAndromedaReviewQueueService', () => ({
    fetchMetaAndromedaReviewQueue: vi.fn(),
    fetchMetaAndromedaReviewDetail: vi.fn(),
    deleteMetaAndromedaReviewItem: vi.fn(),
    batchDeleteMetaAndromedaReviewItems: vi.fn(),
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
                    source: 'score_lab',
                    asset_type: 'image',
                    roas_band: 'high',
                },
            ],
            summary: { total: 1, total_pages: 1 },
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
        deleteMetaAndromedaReviewItem.mockResolvedValue({ ok: true });
        batchDeleteMetaAndromedaReviewItems.mockResolvedValue({ deleted: 1 });
    });

    it('loads the review queue and selected record detail', async () => {
        renderWithOutlet(<MetaAndromedaReviewQueue />);

        await screen.findByText('evt_review_001');
        await screen.findByText('review me');

        expect(fetchMetaAndromedaReviewQueue).toHaveBeenCalledWith({
            status: 'completed',
            has_observation: null,
            roas_band: null,
            source: null,
            scoring_engine: null,
            search: null,
            page: 1,
            page_size: 25,
        });
        await waitFor(() => expect(fetchMetaAndromedaReviewDetail).toHaveBeenCalledWith('evt_review_001'));
    });
});
