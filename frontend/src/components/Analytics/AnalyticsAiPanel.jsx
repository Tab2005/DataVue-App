import React from 'react';
import { FiCpu, FiX, FiZap } from 'react-icons/fi';

const AnalyticsAiPanel = ({
    aiError,
    analysisResult,
    handleStartAnalysis,
    isAnalyzing,
    isMobile,
    language,
    setShowAiPanel,
    showAiPanel,
}) => (
    <>
            {/* AI Analyst Slide-over Panel */}
            <div style={{
                position: 'fixed',
                top: 0,
                right: showAiPanel ? 0 : '-500px', // Slide in/out
                width: isMobile ? '100%' : '500px',
                height: '100vh',
                backgroundColor: 'var(--bg-secondary)',
                boxShadow: showAiPanel ? '-4px 0 20px rgba(0,0,0,0.5)' : 'none',
                transition: 'right 0.3s ease',
                zIndex: 2000,
                display: 'flex',
                flexDirection: 'column',
                borderLeft: '1px solid var(--glass-border)'
            }}>
                {/* Header */}
                <div style={{
                    padding: '16px',
                    borderBottom: '1px solid var(--glass-border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: 'var(--bg-primary)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '1.1rem' }}>
                        <FiCpu style={{ color: '#a855f7' }} />
                        <span style={{ background: 'linear-gradient(to right, #6366f1, #a855f7)', WebkitBackgroundClip: 'text', color: 'transparent' }}>
                            {language === 'zh' ? 'AI 廣告分析師' : 'AI Ad Analyst'}
                        </span>
                    </div>
                    <button
                        onClick={() => setShowAiPanel(false)}
                        style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '1.2rem' }}
                    >
                        <FiX />
                    </button>
                </div>

                {/* Content */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>

                    {!isAnalyzing && !analysisResult && !aiError && (
                        <div style={{ textAlign: 'center', marginTop: '40px', color: 'var(--text-secondary)' }}>
                            <div style={{ fontSize: '3rem', marginBottom: '16px', opacity: 0.5 }}>🤖</div>
                            <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px' }}>
                                {language === 'zh' ? '準備好分析您的數據了嗎？' : 'Ready to analyze your data?'}
                            </h3>
                            <p style={{ fontSize: '0.9rem', maxWidth: '80%', margin: '0 auto 24px' }}>
                                {language === 'zh'
                                    ? 'AI 將會讀取您當前選取的報表數據（前 20 筆），並提供見解與優化建議。'
                                    : 'AI will read your current report data (top 20 rows) and provide insights and optimization suggestions.'}
                            </p>
                            <button
                                onClick={handleStartAnalysis}
                                style={{
                                    padding: '10px 24px',
                                    background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                    border: 'none',
                                    borderRadius: '8px',
                                    color: 'white',
                                    fontWeight: 'bold',
                                    cursor: 'pointer',
                                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                                    boxShadow: '0 4px 12px rgba(168, 85, 247, 0.4)'
                                }}
                            >
                                <FiZap />
                                {language === 'zh' ? '開始分析' : 'Start Analysis'}
                            </button>
                        </div>
                    )}

                    {
                        isAnalyzing && (
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '60px' }}>
                                <div className="spinner" style={{
                                    width: '40px', height: '40px',
                                    border: '3px solid rgba(168, 85, 247, 0.3)',
                                    borderTop: '3px solid #a855f7',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite'
                                }}></div>
                                <p style={{ marginTop: '16px', color: 'var(--text-secondary)', animation: 'pulse 1.5s infinite' }}>
                                    {language === 'zh' ? 'AI 正在思考中...' : 'AI is thinking...'}
                                </p>
                                {analysisResult && (
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '8px' }}>
                                        {language === 'zh' ? '正在接收分析結果...' : 'Receiving insights...'}
                                    </div>
                                )}
                            </div>
                        )
                    }

                    {
                        aiError && (
                            <div style={{
                                padding: '16px',
                                background: 'rgba(239, 68, 68, 0.1)',
                                border: '1px solid #ef4444',
                                borderRadius: '8px',
                                color: '#ef4444'
                            }}>
                                <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>Analysis Failed</div>
                                <div style={{ fontSize: '0.9rem' }}>{aiError}</div>
                                <button
                                    onClick={handleStartAnalysis}
                                    style={{
                                        marginTop: '12px',
                                        padding: '6px 12px',
                                        background: '#ef4444',
                                        color: 'white',
                                        border: 'none',
                                        borderRadius: '4px',
                                        cursor: 'pointer',
                                        fontSize: '0.85rem'
                                    }}
                                >
                                    {language === 'zh' ? '重試' : 'Retry'}
                                </button>
                            </div>
                        )
                    }

                    {
                        analysisResult && (
                            <div className="markdown-content" style={{
                                lineHeight: '1.6',
                                fontSize: '0.95rem',
                                color: 'var(--text-primary)',
                                whiteSpace: 'pre-wrap'
                            }}>
                                {/* Simple render for now, replace with ReactMarkdown later if needed */}
                                {analysisResult}
                            </div>
                        )
                    }

                    {/* Bottom Padding */}
                    <div style={{ height: '50px' }}></div>
                </div>
            </div>

            {/* Backdrop */}
            {
                showAiPanel && (
                    <div
                        onClick={() => setShowAiPanel(false)}
                        style={{
                            position: 'fixed',
                            top: 0, left: 0, right: 0, bottom: 0,
                            background: 'rgba(0,0,0,0.5)',
                            zIndex: 1999,
                            backdropFilter: 'blur(2px)'
                        }}
                    />
                )
            }
    </>
);

export default AnalyticsAiPanel;
