/**
 * AnalyticsTableRow Component
 * 
 * Memoized table row for Analytics data table.
 * Optimized to prevent unnecessary re-renders when other rows change.
 */
import React, { memo, useCallback } from 'react';

/**
 * Format value based on type
 */
const formatValue = (val, format) => {
    if (val === null || val === undefined || val === '' || (typeof val === 'number' && isNaN(val))) {
        return '-';
    }

    const num = parseFloat(val);
    if (isNaN(num)) return val; // Return as-is for strings

    switch (format) {
        case 'currency':
            return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        case 'percent':
            return `${num.toFixed(2)}%`;
        case 'decimal':
            return num.toFixed(2);
        case 'number':
        default:
            return num >= 1000000
                ? `${(num / 1000000).toFixed(1)}M`
                : num >= 1000
                    ? `${(num / 1000).toFixed(1)}K`
                    : num.toLocaleString();
    }
};

const AnalyticsTableRow = memo(function AnalyticsTableRow({
    row,
    columns,
    isSelected,
    onToggleSelect,
    rowIndex,
    nameKey = 'name',
    showCheckbox = true,
    language = 'zh'
}) {
    const handleCheckboxChange = useCallback(() => {
        onToggleSelect(row.id || row[nameKey]);
    }, [row, nameKey, onToggleSelect]);

    const styles = {
        row: {
            backgroundColor: isSelected
                ? 'rgba(59, 130, 246, 0.1)'
                : rowIndex % 2 === 0
                    ? 'transparent'
                    : 'rgba(255, 255, 255, 0.02)',
            transition: 'background-color 0.15s',
        },
        cell: {
            padding: '12px 16px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            fontSize: '0.875rem',
            color: 'var(--text-primary)',
        },
        nameCell: {
            padding: '12px 16px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            fontSize: '0.875rem',
            fontWeight: '500',
            color: 'var(--text-primary)',
            maxWidth: '250px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
        },
        checkbox: {
            width: '16px',
            height: '16px',
            cursor: 'pointer',
            accentColor: '#3b82f6',
        },
        status: (active) => ({
            display: 'inline-block',
            padding: '2px 8px',
            borderRadius: '4px',
            fontSize: '0.7rem',
            backgroundColor: active ? 'rgba(16, 185, 129, 0.2)' : 'rgba(156, 163, 175, 0.2)',
            color: active ? '#10b981' : '#9ca3af',
        })
    };

    return (
        <tr
            style={styles.row}
            onMouseOver={(e) => {
                if (!isSelected) {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                }
            }}
            onMouseOut={(e) => {
                if (!isSelected) {
                    e.currentTarget.style.backgroundColor = rowIndex % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.02)';
                }
            }}
        >
            {/* Checkbox column */}
            {showCheckbox && (
                <td style={{ ...styles.cell, width: '40px', textAlign: 'center' }}>
                    <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={handleCheckboxChange}
                        style={styles.checkbox}
                    />
                </td>
            )}

            {/* Name column */}
            <td style={styles.nameCell} title={row[nameKey] || '-'}>
                {row[nameKey] || '-'}
                {row.status && (
                    <span style={{ marginLeft: '8px', ...styles.status(row.status === 'ACTIVE') }}>
                        {row.status === 'ACTIVE' ? (language === 'zh' ? '啟用' : 'Active') : row.status}
                    </span>
                )}
            </td>

            {/* Data columns */}
            {columns.map((col) => (
                <td key={col.key} style={{ ...styles.cell, textAlign: 'right' }}>
                    {formatValue(row[col.key], col.format)}
                </td>
            ))}
        </tr>
    );
}, (prevProps, nextProps) => {
    // Custom comparison for memo - only re-render if relevant props changed
    return (
        prevProps.row === nextProps.row &&
        prevProps.isSelected === nextProps.isSelected &&
        prevProps.columns === nextProps.columns &&
        prevProps.rowIndex === nextProps.rowIndex
    );
});

export default AnalyticsTableRow;
