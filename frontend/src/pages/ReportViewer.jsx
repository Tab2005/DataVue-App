// frontend/src/pages/ReportViewer.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import { FiChevronLeft, FiAlertCircle, FiSave, FiCheckCircle, FiShare2, FiCopy } from 'react-icons/fi';
import { reportService } from '../services/reportService';
import { ReportConfig, WeeklyReportTemplate } from '../components/Reports';
import PageLoading from '../components/PageLoading';
import { aiService } from '../services/aiService';

const ReportViewer = ({ mode = 'view' }) => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user, language, selectedTeamId } = useOutletContext();
    
    const [report, setReport] = useState(null);
    const [schedule, setSchedule] = useState(null);
    const [loading, setLoading] = useState(mode !== 'create');
    const [error, setError] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [showShareToast, setShowShareToast] = useState(false);

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

    const fetchSchedule = async () => {
        if (!id) return;
        setLoading(true);
        try {
            const res = await reportService.getSchedule(id);
            setSchedule(res);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch schedule:', err);
            setError(t('Failed to load schedule.', '載入排程失敗。'));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (mode === 'view' && id) {
            fetchReport();
        } else if (mode === 'edit-schedule' && id) {
            fetchSchedule();
        }
    }, [id, mode]);

    const handleSave = async (formData) => {
        setIsSaving(true);
        try {
            if (formData.is_automated) {
                if (mode === 'edit-schedule' && id) {
                    await reportService.updateSchedule(id, formData);
                } else {
                    await reportService.createSchedule(formData);
                }
                navigate('/reports');
                return;
            }
            
            // 下方為手動報表建立邏輯 (保持不變)
            const res = await reportService.create(formData);
            const newReport = res;
            setIsGenerating(true);
            try {
                await reportService.generate(newReport.id);
                navigate(`/reports/${newReport.id}`);
            } catch (err) {
                console.error('Initial generation failed:', err);
                navigate(`/reports/${newReport.id}`);
            }
        } catch (err) {
            console.error('Save failed:', err);
            alert(t('Failed to save.', '儲存失敗。'));
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
             // Calculate period based on date range
             const start = new Date(report.date_since);
             const end = new Date(report.date_until);
             const diffDays = Math.ceil(Math.abs(end - start) / (1000 * 60 * 60 * 24)) + 1;
             
             let period = 'weekly';
             let periodText = '週報';
             
             if (diffDays <= 1) {
                 period = 'daily';
                 periodText = '日報';
             } else if (diffDays > 14) {
                 period = 'monthly';
                 periodText = '月報';
             }

             let fullText = '';
             const context = `${periodText}分析：${report.ad_account_name}, 期間: ${report.date_since} ~ ${report.date_until}`;
             
             await aiService.analyzeDataStream(
                 report.report_data.summary,
                 context,
                 'weekly_summary',
                 null, // apiKey
                 (chunk) => {
                    fullText += chunk;
                    setReport(prev => ({ ...prev, ai_summary: fullText }));
                 },
                 null, // provider
                 null, // model
                 period,
                 report.module_type
             );
             
             // Final save to backend
             await handleUpdate({ ai_summary: fullText });
        } catch (err) {
            console.error('AI Analysis failed:', err);
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleCopyShareLink = () => {
        if (!report || !report.share_token) return;
        const shareUrl = `${window.location.origin}/reports/share/${report.share_token}`;
        navigator.clipboard.writeText(shareUrl);
        setShowShareToast(true);
        setTimeout(() => setShowShareToast(false), 3000);
    };

    if (loading) return <PageLoading />;

    return (
        <div style={{ padding: '24px 32px', maxWidth: '1400px', margin: '0 auto' }}>
            {/* Back Button */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
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
                        fontSize: '1rem',
                        padding: '8px 0'
                    }}
                    onMouseEnter={(e) => e.target.style.color = 'var(--text-primary)'}
                    onMouseLeave={(e) => e.target.style.color = 'var(--text-secondary)'}
                >
                    <FiChevronLeft /> {t('Back to List', '返回週報列表')}
                </button>

                {mode === 'view' && report && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {showShareToast && (
                            <span style={{ 
                                color: '#10b981', 
                                fontSize: '0.9rem', 
                                display: 'flex', 
                                alignItems: 'center', 
                                gap: '4px',
                                animation: 'fadeIn 0.3s ease'
                            }}>
                                <FiCheckCircle /> {t('Link Copied!', '分享連結已複製！')}
                            </span>
                        )}
                        <button
                            onClick={handleCopyShareLink}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                padding: '8px 16px',
                                borderRadius: '8px',
                                backgroundColor: 'var(--accent-primary)',
                                color: 'white',
                                border: 'none',
                                cursor: 'pointer',
                                fontWeight: '500',
                                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
                            }}
                        >
                            <FiShare2 /> {t('Share Report', '分享報表')}
                        </button>
                    </div>
                )}
            </div>

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

            {!error && (mode === 'create' || mode === 'edit-schedule') && (
                <ReportConfig
                   onSave={handleSave}
                   onCancel={() => navigate('/reports')}
                   language={language}
                   teamId={selectedTeamId}
                   initialEditData={schedule}
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
