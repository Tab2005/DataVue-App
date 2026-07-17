import ReviewQueuePagination from './ReviewQueuePagination';
import {
    getStatusLabel,
    panelStyle,
    queueItemStyle,
    resolvePreviewUrl,
    roasBandColor,
    searchInputStyle,
    sectionTitleStyle,
    sourceMeta,
    statusToneMap,
} from './reviewQueueShared';

const ReviewQueueList = ({
    batchDeleting,
    deletingId,
    handleBatchDelete,
    handleDelete,
    handlePageChange,
    handleSearchChange,
    loadingQueue,
    page,
    queueItems,
    searchTerm,
    selectedId,
    selectedIds,
    setSelectedId,
    t,
    toggleSelect,
    toggleSelectAll,
    totalCount,
    totalPages,
}) => (
    <section style={panelStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h2 style={{ ...sectionTitleStyle, margin: 0 }}>{t('Scored Assets', '已評估素材')}</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {!loadingQueue && queueItems.length > 0 && (
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)', fontSize: '0.78rem', cursor: 'pointer', userSelect: 'none' }}>
                        <input
                            type="checkbox"
                            checked={selectedIds.size === queueItems.length && queueItems.length > 0}
                            onChange={toggleSelectAll}
                            style={{ cursor: 'pointer' }}
                        />
                        {t('All', '全選')}
                    </label>
                )}
                {selectedIds.size > 0 && (
                    <button
                        type="button"
                        onClick={handleBatchDelete}
                        disabled={batchDeleting}
                        style={{ padding: '4px 10px', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.35)', background: 'rgba(239,68,68,0.12)', color: '#ef4444', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, opacity: batchDeleting ? 0.5 : 1 }}
                    >
                        {batchDeleting ? t('Deleting...', '刪除中...') : t(`Delete (${selectedIds.size})`, `刪除 (${selectedIds.size})`)}
                    </button>
                )}
                {!loadingQueue && selectedIds.size === 0 && (
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.78rem' }}>
                        {t(`${totalCount} total`, `共 ${totalCount} 筆`)}
                    </span>
                )}
            </div>
        </div>

        <input
            type="text"
            placeholder={t('Search ID, ad name, objective, market...', '搜尋 ID、廣告名稱、目標、市場...')}
            value={searchTerm}
            onChange={handleSearchChange}
            style={searchInputStyle}
        />

        {loadingQueue ? (
            <div style={{ color: 'var(--text-secondary)', padding: '16px 0' }}>{t('Loading...', '載入中...')}</div>
        ) : queueItems.length === 0 ? (
            <div style={{ color: 'var(--text-secondary)', padding: '16px 0' }}>{t('No records found.', '目前沒有符合條件的紀錄。')}</div>
        ) : (
            <div
                className="queue-scroll-box"
                style={{ display: 'grid', gap: '8px', maxHeight: 'calc(100vh - 360px)', minHeight: '200px', overflowY: 'auto', paddingRight: '4px' }}
            >
                {queueItems.map((item) => (
                    <ReviewQueueListItem
                        key={item.score_event_id}
                        deletingId={deletingId}
                        handleDelete={handleDelete}
                        item={item}
                        selectedId={selectedId}
                        selectedIds={selectedIds}
                        setSelectedId={setSelectedId}
                        t={t}
                        toggleSelect={toggleSelect}
                    />
                ))}
            </div>
        )}

        <ReviewQueuePagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />
        {totalPages > 1 && (
            <div style={{ textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '8px' }}>
                {t(`Page ${page} / ${totalPages}`, `第 ${page} 頁，共 ${totalPages} 頁`)}
            </div>
        )}
    </section>
);

const ReviewQueueListItem = ({
    deletingId,
    handleDelete,
    item,
    selectedId,
    selectedIds,
    setSelectedId,
    t,
    toggleSelect,
}) => {
    const previewUrl = resolvePreviewUrl(item);
    const isVideo = item.asset_type === 'video';
    const sm = sourceMeta[item.source] || sourceMeta.score_lab;
    const sourceLabel = item.source === 'analytics'
        ? t('Analytics', '成效分析')
        : t('Score Lab', '評分工作台');

    return (
        <div className="queue-item-wrap" style={{ position: 'relative' }}>
            <button
                type="button"
                onClick={() => setSelectedId(item.score_event_id)}
                style={{
                    ...queueItemStyle,
                    display: 'flex',
                    gap: '10px',
                    alignItems: 'center',
                    borderColor: selectedIds.has(item.score_event_id) ? 'rgba(239,68,68,0.5)' : selectedId === item.score_event_id ? 'var(--accent-primary)' : 'var(--glass-border)',
                    background: selectedIds.has(item.score_event_id) ? 'rgba(239,68,68,0.04)' : selectedId === item.score_event_id ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.01)',
                }}
            >
                <input
                    type="checkbox"
                    checked={selectedIds.has(item.score_event_id)}
                    onClick={(e) => toggleSelect(e, item.score_event_id)}
                    onChange={() => {}}
                    style={{ cursor: 'pointer', flexShrink: 0, accentColor: '#ef4444' }}
                />
                <div style={{ width: '52px', height: '52px', borderRadius: '8px', overflow: 'hidden', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    {previewUrl
                        ? isVideo
                            ? <video src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} muted playsInline />
                            : <img src={previewUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="" />
                        : <span style={{ fontSize: '1.2rem' }}>{isVideo ? 'video' : 'image'}</span>
                    }
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '6px', alignItems: 'center', marginBottom: '4px' }}>
                        <strong style={{ color: 'var(--text-primary)', fontSize: '0.82rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {item.score_event_id}
                        </strong>
                        <span style={{ padding: '1px 7px', borderRadius: '999px', background: statusToneMap[item.status] || 'rgba(255,255,255,0.08)', color: 'var(--text-primary)', fontSize: '0.7rem', fontWeight: 600, flexShrink: 0 }}>
                            {getStatusLabel(item.status, t)}
                        </span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: item.ad_name ? '2px' : '5px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {item.objective} · {item.placement_family} · {item.market}
                    </div>
                    {item.ad_name && (
                        <div style={{ color: 'var(--text-primary)', fontSize: '0.73rem', marginBottom: '5px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', opacity: 0.75 }}>
                            {item.ad_name}
                        </div>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', flexWrap: 'wrap' }}>
                        <span style={{ padding: '1px 7px', borderRadius: '999px', background: sm.bg, color: sm.color, fontWeight: 600 }}>
                            {sourceLabel}
                        </span>
                        <span style={{ color: 'var(--text-secondary)' }}>
                            {t('Score', '評分')}: <strong style={{ color: 'var(--text-primary)' }}>{item.overall_score ?? '--'}</strong>
                        </span>
                        {item.roas_band && (
                            <span style={{ padding: '1px 7px', borderRadius: '999px', background: `${roasBandColor[item.roas_band]}22`, color: roasBandColor[item.roas_band], fontWeight: 700 }}>
                                {item.roas_band.toUpperCase()}
                            </span>
                        )}
                        {item.has_observation && (
                            <span style={{ padding: '1px 7px', borderRadius: '999px', background: 'rgba(16,185,129,0.12)', color: '#10b981', fontWeight: 600 }}>
                                {t('Matched', '已匹配')}
                            </span>
                        )}
                    </div>
                </div>
            </button>
            <button
                type="button"
                className="queue-delete-btn"
                onClick={(e) => handleDelete(e, item.score_event_id)}
                disabled={deletingId === item.score_event_id}
                title={t('Delete record', '刪除紀錄')}
                style={{ position: 'absolute', bottom: '8px', right: '8px', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: '6px', color: '#ef4444', cursor: 'pointer', fontSize: '0.72rem', padding: '2px 7px', lineHeight: 1.5, opacity: deletingId === item.score_event_id ? 0.5 : undefined }}
            >
                {deletingId === item.score_event_id ? '...' : t('Delete', '刪除')}
            </button>
        </div>
    );
};

export default ReviewQueueList;
