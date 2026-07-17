import { pagebtnStyle } from './reviewQueueShared';

const ReviewQueuePagination = ({ page, totalPages, onPageChange }) => {
    if (totalPages <= 1) return null;

    const pages = [];
    const delta = 2;
    const left = Math.max(1, page - delta);
    const right = Math.min(totalPages, page + delta);

    if (left > 1) {
        pages.push(1);
        if (left > 2) pages.push('...');
    }
    for (let i = left; i <= right; i += 1) pages.push(i);
    if (right < totalPages) {
        if (right < totalPages - 1) pages.push('...');
        pages.push(totalPages);
    }

    return (
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap', marginTop: '14px' }}>
            <button
                type="button"
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                style={{ ...pagebtnStyle, opacity: page <= 1 ? 0.35 : 1 }}
            >
                {'<'}
            </button>
            {pages.map((p, i) =>
                p === '...'
                    ? <span key={`ellipsis-${i}`} style={{ color: 'var(--text-secondary)', padding: '0 4px' }}>...</span>
                    : (
                        <button
                            key={p}
                            type="button"
                            onClick={() => onPageChange(p)}
                            style={{
                                ...pagebtnStyle,
                                background: p === page ? 'var(--accent-primary)' : 'rgba(255,255,255,0.04)',
                                color: p === page ? '#fff' : 'var(--text-primary)',
                                borderColor: p === page ? 'var(--accent-primary)' : 'var(--glass-border)',
                                fontWeight: p === page ? 700 : 400,
                            }}
                        >
                            {p}
                        </button>
                    )
            )}
            <button
                type="button"
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                style={{ ...pagebtnStyle, opacity: page >= totalPages ? 0.35 : 1 }}
            >
                {'>'}
            </button>
        </div>
    );
};

export default ReviewQueuePagination;
