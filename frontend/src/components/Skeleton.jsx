import React from 'react';
import './Skeleton.css';

/**
 * Base Skeleton component for creating animated loading placeholders
 * 
 * Props:
 * - width: width of the skeleton (default: '100%')
 * - height: height of the skeleton (default: '1rem')
 * - borderRadius: border radius (default: '4px')
 * - className: additional CSS classes
 * - variant: 'text' | 'circular' | 'rectangular' (default: 'text')
 */
const Skeleton = ({
    width = '100%',
    height = '1rem',
    borderRadius,
    className = '',
    variant = 'text',
    style = {}
}) => {
    const getVariantStyles = () => {
        switch (variant) {
            case 'circular':
                return { borderRadius: '50%' };
            case 'rectangular':
                return { borderRadius: '8px' };
            case 'text':
            default:
                return { borderRadius: borderRadius || '4px' };
        }
    };

    return (
        <div
            className={`skeleton ${className}`}
            style={{
                width,
                height,
                ...getVariantStyles(),
                ...style
            }}
        />
    );
};

/**
 * Skeleton for KPI cards on Dashboard
 */
export const SkeletonCard = () => (
    <div className="skeleton-card">
        <Skeleton width="60%" height="0.9rem" style={{ marginBottom: '12px' }} />
        <Skeleton width="80%" height="2rem" style={{ marginBottom: '8px' }} />
        <Skeleton width="50%" height="0.8rem" />
    </div>
);

/**
 * Skeleton for Dashboard chart area
 */
export const SkeletonChart = () => (
    <div className="skeleton-chart">
        <div className="skeleton-chart-bars">
            {[...Array(7)].map((_, i) => (
                <div key={i} className="skeleton-bar" style={{ height: `${30 + Math.random() * 50}%` }} />
            ))}
        </div>
        <Skeleton width="100%" height="20px" style={{ marginTop: '16px' }} />
    </div>
);

/**
 * Skeleton for data table rows
 */
export const SkeletonTable = ({ rows = 5, columns = 6 }) => (
    <div className="skeleton-table">
        {/* Header */}
        <div className="skeleton-table-header">
            {[...Array(columns)].map((_, i) => (
                <Skeleton key={i} width={i === 0 ? '150px' : '80px'} height="1rem" />
            ))}
        </div>
        {/* Rows */}
        {[...Array(rows)].map((_, rowIndex) => (
            <div key={rowIndex} className="skeleton-table-row">
                {[...Array(columns)].map((_, colIndex) => (
                    <Skeleton
                        key={colIndex}
                        width={colIndex === 0 ? '120px' : '60px'}
                        height="0.9rem"
                    />
                ))}
            </div>
        ))}
    </div>
);

/**
 * Full page skeleton for Dashboard
 */
export const DashboardSkeleton = () => (
    <div className="dashboard-skeleton">
        {/* KPI Cards Grid */}
        <div className="skeleton-kpi-grid">
            {[...Array(8)].map((_, i) => (
                <SkeletonCard key={i} />
            ))}
        </div>

        {/* Chart Area */}
        <div className="skeleton-section">
            <Skeleton width="200px" height="1.5rem" style={{ marginBottom: '16px' }} />
            <SkeletonChart />
        </div>
    </div>
);

/**
 * Skeleton for Analytics page
 */
export const AnalyticsSkeleton = () => (
    <div className="analytics-skeleton">
        {/* Control Panel */}
        <div className="skeleton-controls">
            <Skeleton width="150px" height="36px" borderRadius="8px" />
            <Skeleton width="200px" height="36px" borderRadius="8px" />
            <Skeleton width="120px" height="36px" borderRadius="8px" />
        </div>

        {/* Data Table */}
        <SkeletonTable rows={8} columns={7} />
    </div>
);

export default Skeleton;
