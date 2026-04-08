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
            // For amounts >= 10, remove decimals. For smaller ones (like CPC), keep them if they are non-zero.
            // Matching AnalyticsKPICard threshold logic but in a table context.
            if (num >= 10 || Number.isInteger(num)) {
                return `$${num.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
            }
            return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        case 'percent':
            return `${num.toFixed(2)}%`;
        case 'decimal':
            return num.toFixed(2);
        case 'number':
        default:
            // Remove K/M abbreviations as requested, use full numbers with commas
            return num.toLocaleString();
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
            <td style={{ ...styles.nameCell, maxWidth: '350px' }} title={row[nameKey] || '-'}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                    {/* Thumbnail & Preview */}
                    {row.image_url && (
                        <div
                            style={{ position: 'relative', flexShrink: 0, marginTop: '2px' }}
                            onMouseEnter={(e) => {
                                const rect = e.currentTarget.getBoundingClientRect();
                                const container = document.getElementById('preview-img-container');
                                const img = document.getElementById('preview-img');
                                if (container && img) {
                                    container.style.display = 'block';
                                    img.src = row.image_url;
                                    container.style.top = `${rect.top}px`;
                                    container.style.left = `${rect.right + 10}px`;
                                }
                            }}
                            onMouseLeave={() => {
                                const container = document.getElementById('preview-img-container');
                                if (container) {
                                    container.style.display = 'none';
                                }
                            }}
                        >
                            <img
                                src={row.image_url}
                                alt="Ad"
                                style={{
                                    width: '40px',
                                    height: '40px',
                                    objectFit: 'cover',
                                    borderRadius: '4px',
                                    cursor: 'zoom-in',
                                    border: '1px solid rgba(255, 255, 255, 0.1)'
                                }}
                            />
                        </div>
                    )}
                    
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                        <div style={{ 
                            overflow: 'hidden', 
                            textOverflow: 'ellipsis', 
                            whiteSpace: 'nowrap'
                        }}>
                            {row[nameKey] || '-'}
                        </div>
                        {row.status && (
                            <div style={{ marginTop: '4px' }}>
                                <span style={styles.status(row.status === 'ACTIVE')}>
                                    {row.status === 'ACTIVE' ? (language === 'zh' ? '啟用' : 'Active') : row.status}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
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
