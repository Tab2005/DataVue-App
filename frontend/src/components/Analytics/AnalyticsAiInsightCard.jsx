import React, { useEffect, useRef, useState } from 'react';
import { FiCheck, FiCpu, FiRefreshCcw, FiShare2 } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';

import { aiService } from '../../services/aiService';
import { analyticsAiService } from '../../services/analyticsAiService';

const inputStyle = {
    padding: '8px 12px',
    borderRadius: '8px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid var(--glass-border)',
    color: 'var(--text-primary)',
    fontSize: '0.85rem',
};

const secondaryButtonStyle = {
    ...inputStyle,
    cursor: 'pointer',
    fontWeight: 600,
};

const primaryButtonStyle = {
    display: 'flex', alignItems: 'center', gap: '6px',
    padding: '8px 16px', borderRadius: '8px',
    background: 'linear-gradient(135deg, #6366f1, #a855f7)',
    border: 'none', color: 'white',
    fontSize: '0.85rem', fontWeight: 'bold', cursor: 'pointer',
};

/**
 * 成效分析頁「AI 廣告分析」卡片（docs/58）。
 * 比照 GA4InsightsShared.jsx::AIInsightNote 的樣式與互動模式，但這裡沒有
 * GA4 那種「每次 GET 就自動 upsert 快照」的機制——點按鈕當下才建立一筆
 * 全新快照，AI 解讀完成後存回同一筆，分享連結一旦產生就永久凍結在
 * 分享當下的內容（重新解讀不影響已分享出去的連結）。
 */
const AnalyticsAiInsightCard = ({ language, buildPayload, contextLabel, disabled }) => {
    const t = (en, zh) => (language === 'zh' ? zh : en);

    const [aiContent, setAiContent] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [aiError, setAiError] = useState(null);
    const aiContentRef = useRef('');
    const [snapshotId, setSnapshotId] = useState(null);
    const [shareToken, setShareToken] = useState(null);
    const [isSharing, setIsSharing] = useState(false);
    const [shareError, setShareError] = useState(null);
    const [linkCopied, setLinkCopied] = useState(false);
    const [aiModel, setAiModel] = useState('');

    useEffect(() => {
        let cancelled = false;
        aiService.getSettings()
            .then((settings) => {
                if (!cancelled) setAiModel(settings?.ai_model || '');
            })
            .catch(() => {});
        return () => { cancelled = true; };
    }, []);

    const handleGenerate = async () => {
        if (isAnalyzing || disabled) return;
        setIsAnalyzing(true);
        setAiError(null);
        setAiContent('');
        aiContentRef.current = '';
        // 每次生成都是全新快照，先清掉舊的分享連結狀態，避免使用者以為
        // 目前顯示的分享連結是對應最新這次解讀的內容。
        setSnapshotId(null);
        setShareToken(null);
        setShareError(null);
        setLinkCopied(false);

        const built = buildPayload();
        if (!built) {
            setAiError(t('No data to analyze.', '目前沒有資料可以分析。'));
            setIsAnalyzing(false);
            return;
        }

        let newSnapshotId;
        try {
            const res = await analyticsAiService.createSnapshot(built);
            newSnapshotId = res.snapshot_id;
            setSnapshotId(newSnapshotId);
        } catch (err) {
            setAiError(err?.message || t('Failed to create snapshot.', '建立快照失敗，請重試。'));
            setIsAnalyzing(false);
            return;
        }

        try {
            await aiService.analyzeDataStream(
                built.payload,
                contextLabel,
                'analytics_table',
                null,
                (chunk) => {
                    aiContentRef.current += chunk;
                    setAiContent((prev) => prev + chunk);
                },
                null,
                null,
                'weekly',
                'fb_ads'
            );
        } catch (err) {
            setAiError(err?.message || t('AI analysis failed. Check AI key in settings.', 'AI 解讀失敗，請至設定頁確認 AI 金鑰。'));
            setIsAnalyzing(false);
            return;
        }
        setIsAnalyzing(false);
        setIsSaving(true);
        try {
            await analyticsAiService.saveAiSummary(newSnapshotId, aiContentRef.current);
        } catch (err) {
            setAiError(err?.message || t('AI summary generated but failed to save. Retry to persist.', 'AI 解讀已生成但儲存失敗，請重試以持久化。'));
        } finally {
            setIsSaving(false);
        }
    };

    const handleShare = async () => {
        if (isSharing || !snapshotId) return;
        setIsSharing(true);
        setShareError(null);
        setLinkCopied(false);
        try {
            const res = await analyticsAiService.createShareLink(snapshotId);
            setShareToken(res.share_token);
        } catch (err) {
            setShareError(err?.message || t('Failed to create share link.', '產生分享連結失敗，請重試。'));
        } finally {
            setIsSharing(false);
        }
    };

    const buildShareUrl = (token) => `${window.location.origin}/analytics/share/${token}`;

    const handleCopyLink = async () => {
        const url = buildShareUrl(shareToken);
        try {
            await navigator.clipboard.writeText(url);
            setLinkCopied(true);
            setTimeout(() => setLinkCopied(false), 2000);
        } catch {
            // clipboard API 可能因權限被拒；連結仍顯示在下方可手動選取複製。
        }
    };

    const hasContent = aiContent && aiContent.length > 0;
    const buttonLabel = hasContent ? t('Regenerate', '重新解讀') : t('Generate Insights', '開始 AI 解讀');
    const shareUrl = shareToken ? buildShareUrl(shareToken) : null;

    return (
        <div className="glass-panel" style={{ marginTop: '24px', padding: '20px', borderRadius: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '1.05rem' }}>
                        <FiCpu style={{ color: '#a855f7' }} />
                        <span style={{ background: 'linear-gradient(to right, #6366f1, #a855f7)', WebkitBackgroundClip: 'text', color: 'transparent' }}>
                            {t('AI Ad Analyst', 'AI 廣告分析')}
                        </span>
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '4px' }}>
                        {t('Analyzes the metrics you have selected above, using the rows currently shown in the table.', '針對上方已勾選的指標欄位，依表格目前顯示的資料進行分析。')}
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {hasContent && (
                        <button
                            type="button"
                            onClick={handleShare}
                            disabled={isSharing}
                            style={{ ...secondaryButtonStyle, display: 'flex', alignItems: 'center', gap: '6px', opacity: isSharing ? 0.5 : 1 }}
                        >
                            {isSharing ? <FiRefreshCcw className="spin" /> : <FiShare2 />}
                            {isSharing ? t('Creating link…', '產生連結中…') : t('Share Link', '產生分享連結')}
                        </button>
                    )}
                    <button
                        type="button"
                        onClick={handleGenerate}
                        disabled={isAnalyzing || isSaving || disabled}
                        style={{ ...primaryButtonStyle, opacity: isAnalyzing || isSaving || disabled ? 0.5 : 1 }}
                    >
                        {isAnalyzing || isSaving ? <FiRefreshCcw className="spin" /> : <FiCpu />}
                        {isAnalyzing ? t('Analyzing…', '解讀中…') : isSaving ? t('Saving…', '儲存中…') : buttonLabel}
                    </button>
                </div>
            </div>

            {aiError && (
                <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{aiError}</div>
            )}

            {shareError && (
                <div style={{ color: '#fca5a5', fontSize: '0.85rem', marginBottom: '10px' }}>{shareError}</div>
            )}

            {shareUrl && (
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        flexWrap: 'wrap',
                        background: 'rgba(34, 197, 94, 0.08)',
                        border: '1px solid rgba(34, 197, 94, 0.25)',
                        borderRadius: '10px',
                        padding: '10px 12px',
                        marginBottom: '10px',
                    }}
                >
                    <input
                        type="text"
                        readOnly
                        value={shareUrl}
                        onFocus={(e) => e.target.select()}
                        style={{ ...inputStyle, flex: 1, minWidth: '200px', fontSize: '0.8rem' }}
                    />
                    <button type="button" onClick={handleCopyLink} style={{ ...secondaryButtonStyle, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {linkCopied ? <FiCheck /> : <FiShare2 />}
                        {linkCopied ? t('Copied', '已複製') : t('Copy', '複製')}
                    </button>
                </div>
            )}

            <div
                style={{
                    background: 'rgba(59, 130, 246, 0.05)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: '12px',
                    padding: '16px 18px',
                    minHeight: '80px',
                    color: 'var(--text-primary)',
                    lineHeight: 1.7,
                }}
            >
                {hasContent ? (
                    <div className="report-ai-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                            {aiContent}
                        </ReactMarkdown>
                    </div>
                ) : (
                    <div style={{ color: 'var(--text-tertiary)', textAlign: 'center', padding: '16px', fontSize: '0.85rem' }}>
                        {isAnalyzing
                            ? t('AI is analyzing your data…', 'AI 正在分析您的數據…')
                            : disabled
                                ? t('Select at least one metric to enable AI analysis.', '請先勾選至少一個指標欄位才能使用 AI 解讀。')
                                : t('No AI summary yet. Click "Generate Insights".', '尚無 AI 解讀，點選「開始 AI 解讀」。')}
                    </div>
                )}
            </div>

            <div style={{ marginTop: '10px', fontSize: '0.74rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
                {aiModel
                    ? t(
                        `Disclaimer: AI insights are for reference only (model: ${aiModel}). The numbers above are the source of truth.`,
                        `免責聲明：AI 解讀僅供參考（模型：${aiModel}），實際數字請以上方表格為準。`
                    )
                    : t(
                        'Disclaimer: AI insights are for reference only. The numbers above are the source of truth.',
                        '免責聲明：AI 解讀僅供參考，實際數字請以上方表格為準。'
                    )}
            </div>
        </div>
    );
};

export default AnalyticsAiInsightCard;
