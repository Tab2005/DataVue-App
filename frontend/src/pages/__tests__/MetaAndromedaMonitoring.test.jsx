import React from 'react';
import { fireEvent, screen, waitFor } from '@testing-library/react';

import MetaAndromedaMonitoring from '../MetaAndromedaMonitoring';
import { renderWithOutlet } from '../../test/renderWithOutlet';
import { useModuleAccess } from '../../hooks/usePermission';
import { fetchMetaAndromedaMonitoringSummary } from '../../services/metaAndromedaMonitoringService';

vi.mock('../../hooks/usePermission', () => ({
    useModuleAccess: vi.fn(),
}));

vi.mock('../../services/metaAndromedaMonitoringService', () => ({
    fetchMetaAndromedaMonitoringSummary: vi.fn(),
}));

const monitoringSummary = {
    worker_host: {
        active_host: 'redis_stream',
        host_strategy: 'shared_queue_host_adapter',
        dead_letter_count: 1,
        recent_events: [
            {
                worker_event_id: 'we_1',
                event_type: 'redis_stream_consumed',
                queue_host: 'redis_stream',
                score_event_id: 'evt_001',
                runtime_job_id: 'job_001',
                message: 'consumed from stream',
                status: 'queued',
                attempt_count: 1,
            },
            {
                worker_event_id: 'we_2',
                event_type: 'external_worker_completed',
                queue_host: 'external_webhook',
                score_event_id: 'evt_002',
                runtime_job_id: 'job_002',
                message: 'worker completed',
                status: 'completed',
                attempt_count: 1,
            },
        ],
        dead_letters: [
            {
                dead_letter_id: 'dl_1',
                queue_host: 'redis_stream',
                score_event_id: 'evt_003',
                runtime_job_id: 'job_003',
                failure_stage: 'runtime',
                final_error_message: 'timed out',
            },
        ],
    },
    jobs: {
        'score-request': {
            queued_total: 3,
            completed_total: 2,
            failure_total: 1,
            queue_depth: { current: 1, peak: 2 },
            latency_ms: { avg: 10, p95: 20, max: 30 },
        },
    },
    prediction_distribution: { high: 1, mid: 1, low: 0 },
    latest_drift_reports: [],
    active_alerts: [],
    notes: ['note'],
};

describe('MetaAndromedaMonitoring', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useModuleAccess.mockReturnValue({ hasAccess: true, loading: false, error: null });
        fetchMetaAndromedaMonitoringSummary.mockResolvedValue(monitoringSummary);
    });

    it('loads monitoring data and filters by query state', async () => {
        renderWithOutlet(<MetaAndromedaMonitoring />, {
            route: '/?host=redis_stream&q=evt_001',
        });

        expect(screen.getByText('Loading monitoring summary...')).toBeInTheDocument();

        await screen.findByText('Monitoring Summary');
        expect(screen.getByText('redis_stream_consumed · redis_stream')).toBeInTheDocument();
        expect(screen.queryByText('external_worker_completed · external_webhook')).not.toBeInTheDocument();
    });

    it('can switch to dead-letter-only mode and refresh', async () => {
        renderWithOutlet(<MetaAndromedaMonitoring />);

        await screen.findByText('Monitoring Summary');
        fireEvent.click(screen.getByLabelText('Dead Letters Only'));

        expect(screen.getByText('runtime · redis_stream')).toBeInTheDocument();
        expect(screen.queryByText('redis_stream_consumed · redis_stream')).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
        await waitFor(() => expect(fetchMetaAndromedaMonitoringSummary).toHaveBeenCalledTimes(2));
    });

    it('blocks the page when module access is denied', () => {
        useModuleAccess.mockReturnValue({ hasAccess: false, loading: false, error: null });

        renderWithOutlet(<MetaAndromedaMonitoring />);

        expect(screen.getByText('You do not have access to Meta Andromeda in this workspace.')).toBeInTheDocument();
        expect(screen.queryByText('Monitoring Summary')).not.toBeInTheDocument();
    });
});
