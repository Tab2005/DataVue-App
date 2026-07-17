import React from 'react';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';

const AdminPagination = ({ page, totalPages, setPage, styles, t }) => {
    if (totalPages <= 1) return null;

    return (
        <div style={styles.pagination}>
            <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                style={{ ...styles.pageBtn, opacity: page === 1 ? 0.5 : 1 }}
            >
                <FaChevronLeft /> {t.prev}
            </button>
            <span>{t.page} {page} / {totalPages}</span>
            <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                style={{ ...styles.pageBtn, opacity: page === totalPages ? 0.5 : 1 }}
            >
                {t.next} <FaChevronRight />
            </button>
        </div>
    );
};

export default AdminPagination;
