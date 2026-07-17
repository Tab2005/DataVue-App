import { useCallback, useEffect, useRef, useState } from 'react';

import {
    batchDeleteMetaAndromedaReviewItems,
    deleteMetaAndromedaReviewItem,
    fetchMetaAndromedaReviewDetail,
    fetchMetaAndromedaReviewQueue,
} from '../services/metaAndromedaReviewQueueService';
import { PAGE_SIZE } from '../components/MetaAndromeda/reviewQueue/reviewQueueShared';

export const useReviewQueue = (t) => {
    const [statusFilter, setStatusFilter] = useState('completed');
    const [observationFilter, setObservationFilter] = useState('all');
    const [roasBandFilter, setRoasBandFilter] = useState('all');
    const [sourceFilter, setSourceFilter] = useState('all');
    const [scoringEngineFilter, setScoringEngineFilter] = useState('all');
    const [deletingId, setDeletingId] = useState(null);
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [batchDeleting, setBatchDeleting] = useState(false);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [queueItems, setQueueItems] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [detail, setDetail] = useState(null);
    const [loadingQueue, setLoadingQueue] = useState(true);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const searchTermRef = useRef('');
    const searchTimerRef = useRef(null);

    const loadQueue = useCallback(async (targetPage = 1, searchValue = searchTermRef.current) => {
        setLoadingQueue(true);
        setError(null);
        try {
            const has_observation =
                observationFilter === 'matched' ? true
                    : observationFilter === 'unmatched' ? false
                        : null;
            const data = await fetchMetaAndromedaReviewQueue({
                status: statusFilter === 'all' ? null : statusFilter,
                has_observation,
                roas_band: roasBandFilter === 'all' ? null : roasBandFilter,
                source: sourceFilter === 'all' ? null : sourceFilter,
                scoring_engine: scoringEngineFilter === 'all' ? null : scoringEngineFilter,
                search: searchValue.trim() || null,
                page: targetPage,
                page_size: PAGE_SIZE,
            });
            const items = data.items || [];
            setQueueItems(items);
            setTotalPages(data.summary?.total_pages ?? 1);
            setTotalCount(data.summary?.total ?? 0);
            setSelectedId(items[0]?.score_event_id ?? null);
            setSelectedIds(new Set());
        } catch (err) {
            setError(err.message || t('Failed to load records', '載入評估紀錄失敗'));
        } finally {
            setLoadingQueue(false);
        }
    }, [observationFilter, roasBandFilter, scoringEngineFilter, sourceFilter, statusFilter, t]);

    const handlePageChange = useCallback((newPage) => {
        if (newPage < 1 || newPage > totalPages) return;
        setPage(newPage);
        loadQueue(newPage);
    }, [loadQueue, totalPages]);

    const toggleSelect = useCallback((e, id) => {
        e.stopPropagation();
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) {
                next.delete(id);
            } else {
                next.add(id);
            }
            return next;
        });
    }, []);

    const toggleSelectAll = useCallback(() => {
        if (selectedIds.size === queueItems.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(queueItems.map(i => i.score_event_id)));
        }
    }, [queueItems, selectedIds.size]);

    const handleBatchDelete = useCallback(async () => {
        const ids = [...selectedIds];
        if (ids.length === 0) return;
        if (!window.confirm(t(`Delete ${ids.length} selected records?`, `確定要刪除已選取的 ${ids.length} 筆紀錄？`))) return;
        setBatchDeleting(true);
        try {
            await batchDeleteMetaAndromedaReviewItems(ids);
            if (ids.includes(selectedId)) setSelectedId(null);
            await loadQueue(page);
        } catch (err) {
            setError(err.message || t('Batch delete failed', '批次刪除失敗'));
        } finally {
            setBatchDeleting(false);
        }
    }, [loadQueue, page, selectedId, selectedIds, t]);

    const handleDelete = useCallback(async (e, scoreEventId) => {
        e.stopPropagation();
        if (!window.confirm(t(`Delete record ${scoreEventId}?`, `確定要刪除紀錄 ${scoreEventId}？`))) return;
        setDeletingId(scoreEventId);
        try {
            await deleteMetaAndromedaReviewItem(scoreEventId);
            if (selectedId === scoreEventId) setSelectedId(null);
            await loadQueue(page);
        } catch (err) {
            setError(err.message || t('Delete failed', '刪除失敗'));
        } finally {
            setDeletingId(null);
        }
    }, [loadQueue, page, selectedId, t]);

    const handleSearchChange = useCallback((e) => {
        const val = e.target.value;
        setSearchTerm(val);
        searchTermRef.current = val;
        clearTimeout(searchTimerRef.current);
        searchTimerRef.current = setTimeout(() => {
            setPage(1);
            loadQueue(1, val);
        }, 400);
    }, [loadQueue]);

    const loadDetail = useCallback(async (scoreEventId) => {
        if (!scoreEventId) {
            setDetail(null);
            return;
        }
        setLoadingDetail(true);
        setError(null);
        try {
            const detailData = await fetchMetaAndromedaReviewDetail(scoreEventId);
            setDetail(detailData);
        } catch (err) {
            setError(err.message || t('Failed to load detail', '載入明細失敗'));
        } finally {
            setLoadingDetail(false);
        }
    }, [t]);

    useEffect(() => {
        setPage(1);
        loadQueue(1);
    }, [loadQueue]);

    useEffect(() => {
        loadDetail(selectedId);
    }, [loadDetail, selectedId]);

    useEffect(() => () => clearTimeout(searchTimerRef.current), []);

    return {
        batchDeleting,
        deletingId,
        detail,
        error,
        filters: {
            observationFilter,
            roasBandFilter,
            scoringEngineFilter,
            sourceFilter,
            statusFilter,
        },
        handleBatchDelete,
        handleDelete,
        handlePageChange,
        handleSearchChange,
        loadingDetail,
        loadingQueue,
        page,
        queueItems,
        searchTerm,
        selectedId,
        selectedIds,
        setObservationFilter,
        setRoasBandFilter,
        setScoringEngineFilter,
        setSelectedId,
        setSourceFilter,
        setStatusFilter,
        toggleSelect,
        toggleSelectAll,
        totalCount,
        totalPages,
    };
};
