import React, { useState, useRef } from 'react';
import { FiX, FiCpu, FiPrinter } from 'react-icons/fi';
import { aiService } from '../../services/aiService';
import ReactMarkdown from 'react-markdown';
import { METRIC_GROUPS } from '../../constants/analyticsConfig';

/**
 * ReportModal Component
 * 
 * Displays a preview of the dashboard report and allows generating AI summary.
 * Uses browser's native print function for PDF export to ensure full Chinese support.
 */
const ReportModal = ({
    isOpen,
    onClose,
    data,
    dateRange,
    selectedMetrics,
    summaryData,
    language = 'zh',
    user
}) => {
    const [aiSummary, setAiSummary] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const contentRef = useRef(null);

    // If not open, don't render
    if (!isOpen) return null;

    const handleGenerateSummary = async () => {
        setIsGenerating(true);
        setAiSummary('');
        try {
            const context = `
            Report Type: Weekly Performance Summary
            Date Range: ${dateRange.since} to ${dateRange.until}
            Metrics Focus: ${Array.from(selectedMetrics).join(', ')}
            Language: ${language === 'zh' ? 'Traditional Chinese' : 'English'}
            `;

            const summaryStats = {
                period: dateRange,
                kpis: summaryData,
                rows: data.slice(0, 30)
            };

            await aiService.analyzeDataStream(
                summaryStats,
                context,
                'weekly_summary',
                null,
                (chunk) => setAiSummary(prev => prev + chunk)
            );
        } catch (err) {
            console.error(err);
        } finally {
            setIsGenerating(false);
        }
    };

    // Helper to format metric values
    const getFormattedValue = (val, format) => {
        if (val === undefined || val === null || isNaN(val)) return '-';
        if (format === 'currency') return `$${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
        if (format === 'percent') return `${val.toFixed(2)}%`;
        if (format === 'decimal') return val.toFixed(2);
        return val.toLocaleString();
    };

    // Use browser's native print function
    const handlePrint = () => {
        window.print();
    };

    return (
        <div className="report-modal-overlay" style={{
            position: 'fixed', inset: 0, zIndex: 3000,
            background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)',
            display: 'flex', justifyContent: 'center', alignItems: 'center'
        }}>
            {/* Print Styles - Comprehensive CSS for PDF output */}
            <style>{`
                @media print {
                    /* Page Setup - Landscape for wide tables */
                    @page {
                        size: A4 landscape;
                        margin: 10mm;
                    }

                    /* CRITICAL: Reset html and body to prevent blank pages */
                    html, body {
                        height: auto !important;
                        min-height: 0 !important;
                        max-height: none !important;
                        overflow: visible !important;
                        margin: 0 !important;
                        padding: 0 !important;
                    }

                    /* Reset React root containers */
                    #root, #app, .App, [data-reactroot] {
                        height: auto !important;
                        min-height: 0 !important;
                        max-height: none !important;
                        overflow: visible !important;
                        position: static !important;
                    }

                    /* Hide everything except the report */
                    body * {
                        visibility: hidden;
                    }

                    /* Show report content */
                    .report-modal-overlay,
                    .report-modal-overlay * {
                        visibility: visible;
                    }

                    /* Reset overlay positioning - CRITICAL for no blank pages */
                    .report-modal-overlay {
                        position: absolute !important;
                        left: 0 !important;
                        top: 0 !important;
                        width: 100% !important;
                        height: auto !important;
                        min-height: 0 !important;
                        max-height: none !important;
                        background: white !important;
                        display: block !important;
                        overflow: visible !important;
                        padding: 0 !important;
                        margin: 0 !important;
                    }

                    /* Reset modal container - CRITICAL for no blank pages */
                    .report-modal {
                        position: static !important;
                        width: 100% !important;
                        height: auto !important;
                        min-height: 0 !important;
                        max-height: none !important;
                        background: white !important;
                        color: black !important;
                        box-shadow: none !important;
                        border: none !important;
                        border-radius: 0 !important;
                        overflow: visible !important;
                        display: block !important;
                        padding: 0 !important;
                        margin: 0 !important;
                    }

                    /* Hide modal header (buttons) */
                    .no-print {
                        display: none !important;
                    }

                    /* Reset content area - CRITICAL for no blank pages */
                    .report-content {
                        overflow: visible !important;
                        padding: 10px !important;
                        background: white !important;
                        color: black !important;
                        height: auto !important;
                        min-height: 0 !important;
                        max-height: none !important;
                        flex: none !important;
                    }

                    /* Typography */
                    h1, h2, h3, h4, h5, h6, p, span, div, td, th {
                        color: black !important;
                        font-family: "Microsoft JhengHei", "Noto Sans TC", Arial, sans-serif !important;
                    }

                    h1 {
                        font-size: 22px !important;
                        margin-bottom: 8px !important;
                    }

                    h3 {
                        font-size: 14px !important;
                        margin-bottom: 10px !important;
                        color: #333 !important;
                        border-left-color: #333 !important;
                    }

                    /* KPI Cards Grid */
                    .kpi-grid {
                        display: grid !important;
                        grid-template-columns: repeat(4, 1fr) !important;
                        gap: 10px !important;
                        margin-bottom: 20px !important;
                    }

                    .kpi-card {
                        border: 1px solid #ccc !important;
                        background: #f9f9f9 !important;
                        padding: 10px !important;
                        border-radius: 6px !important;
                        break-inside: avoid !important;
                        page-break-inside: avoid !important;
                    }

                    .kpi-card .label {
                        font-size: 10px !important;
                        color: #555 !important;
                    }

                    .kpi-card .value {
                        font-size: 16px !important;
                        font-weight: bold !important;
                        color: #000 !important;
                    }

                    /* Table Styles */
                    table {
                        width: 100% !important;
                        border-collapse: collapse !important;
                        font-size: 7px !important;
                        page-break-inside: auto !important;
                        table-layout: fixed !important;
                    }

                    thead {
                        display: table-header-group !important;
                    }

                    tr {
                        page-break-inside: avoid !important;
                        page-break-after: auto !important;
                    }

                    th {
                        background-color: #e9e9e9 !important;
                        color: black !important;
                        font-weight: bold !important;
                        padding: 4px 2px !important;
                        border: 1px solid #bbb !important;
                        text-align: center !important;
                        /* Rotate header text for better fit */
                        writing-mode: vertical-rl !important;
                        text-orientation: mixed !important;
                        height: 80px !important;
                        white-space: nowrap !important;
                        vertical-align: bottom !important;
                        font-size: 8px !important;
                    }

                    /* First column (Name) should NOT be rotated */
                    th:first-child {
                        writing-mode: horizontal-tb !important;
                        height: auto !important;
                        min-width: 100px !important;
                        vertical-align: middle !important;
                    }

                    td {
                        padding: 3px 2px !important;
                        border: 1px solid #ddd !important;
                        color: black !important;
                        font-size: 7px !important;
                        text-align: center !important;
                    }

                    td:first-child {
                        text-align: left !important;
                        min-width: 100px !important;
                    }

                    /* AI Summary */
                    .ai-summary {
                        background: #f5f5f5 !important;
                        border: 1px solid #ddd !important;
                        padding: 15px !important;
                        margin-bottom: 20px !important;
                        border-radius: 6px !important;
                    }

                    .markdown-body {
                        font-size: 11px !important;
                        line-height: 1.5 !important;
                    }
                }
            `}</style>

            <div className="report-modal glass-panel" style={{
                background: '#18191a',
                color: '#e4e6eb',
                width: '900px',
                height: '90vh',
                borderRadius: '16px',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                boxShadow: '0 20px 50px rgba(0,0,0,0.7)',
                border: '1px solid rgba(255,255,255,0.1)'
            }}>
                {/* Header - Hidden during print */}
                <div className="no-print" style={{
                    padding: '16px 24px',
                    borderBottom: '1px solid rgba(255,255,255,0.1)',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    background: 'rgba(255,255,255,0.05)'
                }}>
                    <h2 style={{ fontSize: '1.2rem', margin: 0, display: 'flex', alignItems: 'center', gap: '8px', color: '#e4e6eb' }}>
                        📄 {language === 'zh' ? '報表預覽' : 'Report Preview'}
                    </h2>
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <button
                            onClick={handleGenerateSummary}
                            disabled={isGenerating}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '6px',
                                padding: '8px 16px', borderRadius: '6px',
                                background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                color: 'white', border: 'none', cursor: 'pointer',
                                opacity: isGenerating ? 0.7 : 1,
                                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
                            }}
                        >
                            <FiCpu />
                            {isGenerating ? (language === 'zh' ? '生成中...' : 'Generating...') : (language === 'zh' ? 'AI 總結' : 'AI Summary')}
                        </button>
                        <button
                            onClick={handlePrint}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '6px',
                                padding: '8px 16px', borderRadius: '6px',
                                background: '#3b82f6',
                                color: 'white', border: 'none', cursor: 'pointer'
                            }}
                        >
                            <FiPrinter />
                            {language === 'zh' ? '列印 / 儲存 PDF' : 'Print / Save PDF'}
                        </button>
                        <button
                            onClick={onClose}
                            style={{
                                background: 'transparent', border: 'none',
                                color: '#b0b3b8', cursor: 'pointer', fontSize: '1.5rem',
                                display: 'flex', alignItems: 'center'
                            }}
                        >
                            <FiX />
                        </button>
                    </div>
                </div>

                {/* Content Area */}
                <div className="report-content" ref={contentRef} style={{ flex: 1, overflowY: 'auto', padding: '40px', background: '#18191a' }}>

                    {/* Report Header */}
                    <div style={{ marginBottom: '30px', borderBottom: '2px solid rgba(255,255,255,0.1)', paddingBottom: '20px' }}>
                        <h1 style={{ fontSize: '2rem', marginBottom: '10px', color: '#e4e6eb' }}>Facebook Ads Performance Report</h1>
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: '#b0b3b8' }}>
                            <div>
                                <div><strong>Date Range:</strong> {dateRange.since} ~ {dateRange.until}</div>
                                <div><strong>Generated By:</strong> {user?.name || 'User'}</div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div><strong>Generated On:</strong> {new Date().toLocaleDateString()}</div>
                            </div>
                        </div>
                    </div>

                    {/* KPI Cards Section */}
                    {summaryData && (
                        <div style={{ marginBottom: '40px' }}>
                            <h3 style={{ color: '#fbbf24', marginBottom: '16px', borderLeft: '4px solid #fbbf24', paddingLeft: '12px' }}>
                                {language === 'zh' ? '關鍵指標 (Key Metrics)' : 'Key Metrics'}
                            </h3>
                            <div className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
                                {METRIC_GROUPS.map(group => {
                                    const activeMetrics = group.metrics.filter(m => selectedMetrics.has(`${group.id}:${m.key}`) || selectedMetrics.has(m.key));
                                    return activeMetrics.map(m => (
                                        <div key={m.key} className="kpi-card" style={{
                                            padding: '16px',
                                            borderRadius: '12px',
                                            background: 'rgba(255,255,255,0.05)',
                                            border: '1px solid rgba(255,255,255,0.1)'
                                        }}>
                                            <div className="label" style={{ fontSize: '0.85rem', color: '#b0b3b8', marginBottom: '8px' }}>
                                                {language === 'zh' ? m.label_zh : m.label_en}
                                            </div>
                                            <div className="value" style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#e4e6eb' }}>
                                                {getFormattedValue(summaryData[m.key], m.format)}
                                            </div>
                                        </div>
                                    ));
                                })}
                            </div>
                        </div>
                    )}

                    {/* AI Summary Section */}
                    {(aiSummary || isGenerating) && (
                        <div className="ai-summary" style={{ marginBottom: '40px', padding: '24px', background: 'rgba(99, 102, 241, 0.1)', borderRadius: '12px', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
                            <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: '#a855f7' }}>
                                🤖 AI Performance Summary
                            </h3>
                            {isGenerating && !aiSummary && <div style={{ color: '#b0b3b8', fontStyle: 'italic' }}>AI is analyzing your data...</div>}
                            <div className="markdown-body" style={{ lineHeight: '1.6', color: '#e4e6eb' }}>
                                <ReactMarkdown>{aiSummary}</ReactMarkdown>
                            </div>
                        </div>
                    )}

                    {/* Data Table */}
                    <div style={{ marginBottom: '20px' }}>
                        <h3 style={{ color: '#e4e6eb', marginBottom: '16px', borderLeft: '4px solid #3b82f6', paddingLeft: '12px' }}>
                            {language === 'zh' ? '成效數據 (Performance Data)' : 'Performance Data'}
                        </h3>
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem', color: '#e4e6eb', minWidth: '800px' }}>
                                <thead>
                                    <tr style={{ background: 'rgba(255,255,255,0.1)', borderBottom: '2px solid rgba(255,255,255,0.2)' }}>
                                        <th style={{ padding: '12px', textAlign: 'left', color: '#e4e6eb' }}>Name</th>
                                        {METRIC_GROUPS.flatMap(group =>
                                            group.metrics.filter(m => selectedMetrics.has(`${group.id}:${m.key}`) || selectedMetrics.has(m.key))
                                        ).map(m => (
                                            <th key={m.key} style={{ padding: '12px', textAlign: 'right', color: '#e4e6eb', whiteSpace: 'nowrap' }}>
                                                {language === 'zh' ? m.label_zh : m.label_en}
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {data.map((row, idx) => (
                                        <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                            <td style={{ padding: '10px' }}>{row.name || row.campaign_name || row.adset_name}</td>
                                            {METRIC_GROUPS.flatMap(group =>
                                                group.metrics.filter(m => selectedMetrics.has(`${group.id}:${m.key}`) || selectedMetrics.has(m.key))
                                            ).map(m => (
                                                <td key={m.key} style={{ padding: '10px', textAlign: 'right' }}>
                                                    {getFormattedValue(row[m.key], m.format)}
                                                </td>
                                            ))}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ReportModal;
