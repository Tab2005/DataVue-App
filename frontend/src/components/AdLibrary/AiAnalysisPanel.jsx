/**
 * 行銷活動 AI 分析側邊面板（docs/75）
 *
 * - 有舊結果：直接顯示；資料重新抓取後（context_hash 改變）提示可重新分析
 * - 沒有結果：顯示預估資料量與模型，按「開始分析」後串流顯示
 * - 未設定 AI API Key：引導到設定頁
 * 模型輸出以 ReactMarkdown + remark-gfm 渲染，不啟用 raw HTML。
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FiCpu, FiRefreshCw, FiX } from 'react-icons/fi';

import { getAiAnalysis, streamAiAnalysis } from '../../services/adLibraryService';
import { formatNumber, t } from './labels';

// 表格放進可橫向捲動的容器；數字不在中間斷行，長網址等文字段落才允許任意斷行
const REPORT_STYLES = `
.adlib-ai-report p, .adlib-ai-report li { overflow-wrap: anywhere; }
.adlib-ai-report .adlib-ai-table { overflow-x: auto; margin: 0.6rem 0 0.8rem; }
.adlib-ai-report .adlib-ai-table table { width: auto; min-width: 100%; margin: 0; }
.adlib-ai-report th { white-space: nowrap; }
.adlib-ai-report td { overflow-wrap: normal; word-break: normal; min-width: 3.5em; }
`;

const MARKDOWN_COMPONENTS = {
    // eslint-disable-next-line no-unused-vars
    table: ({ node, ...props }) => (
        <div className="adlib-ai-table"><table {...props} /></div>
    ),
};

const formatTime = (s) => (s ? new Date(`${s}Z`).toLocaleString('zh-TW') : '—');

const AiAnalysisPanel = ({ accountId, campaign, language, onClose }) => {
    const [meta, setMeta] = useState(null);
    const [error, setError] = useState(null);
    const [streamText, setStreamText] = useState('');
    const [streaming, setStreaming] = useState(false);
    const controllerRef = useRef(null);

    const loadMeta = useCallback(() => {
        setError(null);
        return getAiAnalysis({ accountId, campaignId: campaign.campaign_id })
            .then(setMeta)
            .catch((err) => setError(err.message));
    }, [accountId, campaign.campaign_id]);

    useEffect(() => {
        setMeta(null);
        setStreamText('');
        loadMeta();
        return () => controllerRef.current?.abort();
    }, [loadMeta]);

    useEffect(() => {
        const onKey = (e) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [onClose]);

    const handleStart = async () => {
        setError(null);
        setStreamText('');
        setStreaming(true);
        const controller = new AbortController();
        controllerRef.current = controller;
        try {
            await streamAiAnalysis({
                accountId, campaignId: campaign.campaign_id, onChunk: setStreamText, signal: controller.signal,
            });
            await loadMeta();
            setStreamText('');
        } catch (err) {
            if (err.name !== 'AbortError') setError(err.message);
        } finally {
            setStreaming(false);
        }
    };

    const analysis = meta?.analysis;
    const content = streaming || streamText ? streamText : analysis?.content;
    const noKey = meta && !meta.has_api_key;

    return (
        <div role="dialog" aria-modal="true" aria-label={t(language, 'AI analysis', 'AI 分析')}
             style={{ position: 'fixed', inset: 0, zIndex: 1000, display: 'flex', justifyContent: 'flex-end' }}>
            <div onClick={onClose} style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)' }} />
            <aside style={{
                position: 'relative', width: 'min(760px, 100%)', height: '100%', background: 'var(--bg-primary)',
                borderLeft: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column',
            }}>
                <header style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderBottom: '1px solid var(--glass-border)' }}>
                    <FiCpu style={{ color: 'var(--accent-primary)', flexShrink: 0 }} />
                    <div style={{ minWidth: 0, flex: 1 }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{t(language, 'AI analysis', 'AI 分析')}</div>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)', overflowWrap: 'anywhere' }}>
                            {campaign.name || campaign.campaign_id}
                        </div>
                    </div>
                    <button type="button" className="adlib-btn" onClick={onClose} aria-label={t(language, 'Close', '關閉')}>
                        <FiX size={16} />
                    </button>
                </header>

                <div style={{ padding: 16, overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {error && (
                        <div role="alert" style={{ color: 'var(--text-error)', border: '1px solid var(--text-error)', borderRadius: 8, padding: '10px 12px', fontSize: '0.88rem' }}>
                            {error}
                        </div>
                    )}

                    {!meta && !error && <div style={{ color: 'var(--text-muted)' }}>{t(language, 'Loading…', '載入中…')}</div>}

                    {noKey && (
                        <div role="status" style={{ border: '1px solid var(--glass-border)', borderRadius: 8, padding: '12px 14px', fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                            {t(language,
                                'AI analysis uses your own OpenRouter API key. Add it under Settings → OpenRouter, then come back.',
                                'AI 分析會使用你自己的 OpenRouter API Key。請先到「設定 → OpenRouter」填入，再回來分析。')}
                        </div>
                    )}

                    {meta && (
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                            <span className="adlib-badge">{t(language, 'Model', '模型')}：{analysis && !streaming ? analysis.model : meta.model}</span>
                            <span className="adlib-badge">
                                {t(language, `~${formatNumber(meta.context_chars)} characters of data`, `資料約 ${formatNumber(meta.context_chars)} 字元`)}
                            </span>
                            <span>{t(language, 'Data fetched', '資料抓取於')} {formatTime(meta.data_fetched_at)}</span>
                            {analysis && !streaming && (
                                <span>· {t(language, 'Analyzed', '分析於')} {formatTime(analysis.created_at)}</span>
                            )}
                        </div>
                    )}

                    {meta && analysis && !streaming && meta.is_stale && (
                        <div role="status" style={{ border: '1px solid var(--accent-primary)', borderRadius: 8, padding: '10px 12px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            {t(language, 'The data has been refreshed since this analysis. You can run it again.', '這份分析之後資料已重新抓取，可以重新分析。')}
                        </div>
                    )}
                    {meta && analysis?.status === 'failed' && !streaming && (
                        <div role="status" style={{ border: '1px solid var(--text-error)', borderRadius: 8, padding: '10px 12px', fontSize: '0.85rem', color: 'var(--text-error)' }}>
                            {t(language, 'The last analysis did not finish. Below is what was received.', '上次分析沒有完成，以下為已收到的部分。')}
                        </div>
                    )}

                    {meta && !noKey && (
                        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                            <button type="button" className="adlib-btn adlib-btn-primary" onClick={handleStart} disabled={streaming}>
                                <FiRefreshCw size={14} className={streaming ? 'spin' : undefined} />
                                {streaming
                                    ? t(language, 'Analyzing…', '分析中…')
                                    : analysis ? t(language, 'Analyze again', '重新分析') : t(language, 'Start analysis', '開始分析')}
                            </button>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                {t(language, 'Uses your OpenRouter API key.', '會使用你的 OpenRouter API Key 計費。')}
                            </span>
                        </div>
                    )}

                    {content ? (
                        <div className="report-ai-content adlib-ai-report" style={{ color: 'var(--text-primary)', lineHeight: 1.7 }}>
                            <style>{REPORT_STYLES}</style>
                            <ReactMarkdown remarkPlugins={[remarkGfm]} components={MARKDOWN_COMPONENTS}>{content}</ReactMarkdown>
                        </div>
                    ) : (
                        meta && !noKey && !streaming && (
                            <div style={{ color: 'var(--text-muted)', fontSize: '0.88rem', lineHeight: 1.6 }}>
                                {t(language,
                                    'No analysis yet. The AI reviews this campaign’s structure, copy and media tests, and dynamic creative results, then suggests next steps.',
                                    '尚未分析。AI 會檢視這個行銷活動的結構、文案與素材測試、動態素材元件成效，並提出下一步建議。')}
                            </div>
                        )
                    )}
                </div>
            </aside>
        </div>
    );
};

export default AiAnalysisPanel;
