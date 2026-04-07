// frontend/src/pages/ReportViewer.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import { FiChevronLeft, FiAlertCircle, FiSave, FiCheckCircle } from 'react-icons/fi';
import { reportService } from '../services/reportService';
import { ReportConfig, WeeklyReportTemplate } from '../components/Reports';
import PageLoading from '../components/PageLoading';
import { aiService } from '../services/aiService';

const ReportViewer = ({ mode = 'view' }) => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user, language, selectedTeamId } = useOutletContext();
    
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(mode === 'view');
    const [error, setError] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const t = (en, zh) => (language === 'zh' ? zh : en);

    const fetchReport = async () => {
        if (!id) return;
        setLoading(true);
        try {
            const res = await reportService.get(id);
            setReport(res);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch report:', err);
            setError(t('Failed to load report.', '載入週報失敗。'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (mode === 'view' && id) {
            fetchReport();
        }
    }, [id, mode]);

    const handleCreate = async (formData) => {
        setIsSaving(true);
        try {
            const res = await reportService.create(formData);
            const newReport = res;
            // After create, immediately trigger generation
            setIsGenerating(true);
            try {
                await reportService.generate(newReport.id);
                navigate(`/reports/${newReport.id}`);
            } catch (err) {
                console.error('Initial generation failed:', err);
                navigate(`/reports/${newReport.id}`); // Still navigate to see the draft
            }
        } catch (err) {
            console.error('Create failed:', err);
            alert(t('Failed to create report.', '建立週報失敗。'));
        } finally {
            setIsSaving(false);
            setIsGenerating(false);
        }
    };

    const handleGenerate = async () => {
        if (!report) return;
        setIsGenerating(true);
        try {
            const res = await reportService.generate(report.id);
            setReport(res);
        } catch (err) {
            console.error('Generation failed:', err);
            alert(t('Failed to fetch data from Facebook.', '抓取資料失敗。'));
        } finally {
            setIsGenerating(false);
        }
    };

    const handleUpdate = async (payload) => {
        if (!report) return;
        try {
            const res = await reportService.update(report.id, payload);
            setReport(res);
        } catch (err) {
            console.error('Update failed:', err);
        }
    };

    const handleGenerateAI = async () => {
        if (!report || !report.report_data) return;
        setIsAnalyzing(true);
        try {
             // Reuse existing aiService.analyzeDataStream
             // We'll collect the stream and update the report once done
             let fullText = '';
             const context = `${t('Weekly Report for', '週報分析：')} ${report.ad_account_name}, ${t('Period', '期間')}: ${report.date_since} ~ ${report.date_until}`;
             
             await aiService.analyzeDataStream(
                 report.report_data.summary,
                 context,
                 'weekly_summary',
                 null, // apiKey
                 (chunk) => {
                    fullText += chunk;
                    // Update local state for real-time preview
                    setReport(prev => ({ ...prev, ai_summary: fullText }));
                 }
             );
             
             // Final save to backend
             await handleUpdate({ ai_summary: fullText });
        } catch (err) {
            console.error('AI Analysis failed:', err);
        } finally {
            setIsAnalyzing(false);
        }
    };

    if (loading) return <PageLoading />;

    return (
        <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
            {/* Back Button */}
            <button
                onClick={() => navigate('/reports')}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: 'var(--text-secondary)',
                    cursor: 'pointer',
                    marginBottom: '24px',
                    fontSize: '1rem',
                    padding: '8px 0'
                }}
                onMouseEnter={(e) => e.target.style.color = 'var(--text-primary)'}
                onMouseLeave={(e) => e.target.style.color = 'var(--text-secondary)'}
            >
                <FiChevronLeft /> {t('Back to List', '返回週報列表')}
            </button>

            {error && (
                <div style={{
                    padding: '24px',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    borderRadius: '16px',
                    color: '#ef4444',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    textAlign: 'center',
                    flexDirection: 'column'
                }}>
                    <FiAlertCircle size={48} />
                    <h2 style={{ margin: '8px 0' }}>{error}</h2>
                    <button
                        onClick={() => navigate('/reports')}
                        style={{ backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '10px 24px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
                        {t('Go Back', '回到列表')}
                    </button>
                </div>
            )}

            {!error && mode === 'create' && (
                <ReportConfig
                   onSave={handleCreate}
                   onCancel={() => navigate('/reports')}
                   language={language}
                   teamId={selectedTeamId}
                />
            )}

            {!error && mode === 'view' && report && (
                <WeeklyReportTemplate
                    report={report}
                    onUpdate={handleUpdate}
                    onGenerate={handleGenerate}
                    onGenerateAI={handleGenerateAI}
                    isGenerating={isGenerating}
                    isAnalyzing={isAnalyzing}
                    language={language}
                />
            )}
        </div>
    );
};

export default ReportViewer;
