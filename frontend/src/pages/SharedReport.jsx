// frontend/src/pages/SharedReport.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { reportService } from '../services/reportService';
import { WeeklyReportTemplate } from '../components/Reports';
import PageLoading from '../components/PageLoading';
import { FiAlertCircle, FiZap } from 'react-icons/fi';

const SharedReport = () => {
    const { token } = useParams();
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [language, setLanguage] = useState('zh'); // Default to zh for shared views

    useEffect(() => {
        const fetchSharedReport = async () => {
            if (!token) return;
            try {
                const res = await reportService.getSharedReport(token);
                setReport(res);
            } catch (err) {
                console.error('Failed to fetch shared report:', err);
                setError('無法載入此報表。可能連結已失效或不存在。');
            } finally {
                setLoading(false);
            }
        };
        fetchSharedReport();
    }, [token]);

    const t = (en, zh) => (language === 'zh' ? zh : en);

    if (loading) return <PageLoading />;

    if (error) {
        return (
            <div style={{ 
                height: '100vh', 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center',
                backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                padding: '20px',
                textAlign: 'center'
            }}>
                <FiAlertCircle size={64} color="#ef4444" style={{ marginBottom: '20px' }} />
                <h1 style={{ fontSize: '1.8rem', marginBottom: '12px' }}>{t('Report Not Found', '找不到此報表')}</h1>
                <p style={{ color: 'var(--text-secondary)', maxWidth: '400px' }}>{error}</p>
            </div>
        );
    }

    if (!report) return null;

    return (
        <div style={{ 
            minHeight: '100vh', 
            backgroundColor: 'var(--bg-primary)', 
            backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)',
            padding: '40px 20px',
            color: 'var(--text-primary)'
        }}>
            <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
                {/* Brand Header for Shared View */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px', paddingBottom: '20px', borderBottom: '1px solid var(--glass-border)' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <FiZap color="white" size={24} />
                    </div>
                    <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--text-primary)', letterSpacing: '1px' }}>DATAVUE</span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginLeft: 'auto' }}>
                        {t('Generated via AI Analytics', '由 AI 數據分析系統生成')}
                    </span>
                </div>

                <WeeklyReportTemplate
                    report={report}
                    isSharedView={true}
                    language={language}
                    // These won't be used in SharedView but passed for prop types
                    onUpdate={() => {}}
                    onGenerate={() => {}}
                    onGenerateAI={() => {}}
                    isGenerating={false}
                    isAnalyzing={false}
                />

                {/* Footer */}
                <div style={{ marginTop: '60px', textAlign: 'center', padding: '40px 0', borderTop: '1px solid var(--glass-border)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    © {new Date().getFullYear()} DataVue Analytics. {t('All rights reserved.', '保留所有權利。')}
                </div>
            </div>
        </div>
    );
};

export default SharedReport;
