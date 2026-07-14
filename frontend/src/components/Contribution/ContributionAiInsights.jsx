import React, { useEffect, useRef, useState } from 'react';
import { FiCpu, FiRefreshCcw } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';

import { aiService } from '../../services/aiService';
import { saveAiSummary } from '../../services/contributionService';
import { ErrorPanel, secondaryButtonStyle, Section, t } from './ContributionShared';

const buildAiPayload = ({ snapshot, groups, reportedByGroup }) => {
    const results = snapshot?.results || {};
    const diagnostics = snapshot?.diagnostics || {};
    const config = snapshot?.config || {};
    const warnings = diagnostics.collinearity_warnings || [];
    const correlatedPairs = new Set();
    warnings.forEach((w) => {
        correlatedPairs.add(w.group_a);
        correlatedPairs.add(w.group_b);
    });
    const groupsData = results.groups || {};
    const groupRows = (groups || []).map((g) => {
        const data = groupsData[g.group_key] || {};
        const median = data.contribution_share?.median ?? 0;
        return {
            group_key: g.group_key,
            group_name: g.group_name,
            spend_share: data.spend_share ?? 0,
            reported_share: reportedByGroup?.[g.group_key] ?? 0,
            contribution_share_median: median,
            contribution_share_min: data.contribution_share?.min ?? 0,
            contribution_share_max: data.contribution_share?.max ?? 0,
            marginal_per_step_median: data.marginal?.per_step?.median ?? null,
            marginal_step: data.marginal?.step ?? null,
            doubtful: median <= 0.005 && correlatedPairs.has(g.group_key),
        };
    });
    return {
        groups: groupRows,
        diagnostics: {
            collinearity_warnings: warnings,
            // docs/27 任務 5.3：data_summary 內已含 ungrouped_spend_share，
            // 另把 data_quality_warnings（未分組花費等資料品質警告）一併帶上，
            // 讓 AI 白話解讀也能引用（prompt 既有「只引用 payload 內數字」規則已涵蓋）。
            data_quality_warnings: diagnostics.data_quality_warnings || [],
            holdout_r2_median: results.r2?.holdout?.median ?? null,
            poisson_ceiling_r2_holdout: diagnostics.poisson_ceiling_r2?.holdout ?? null,
            data_summary: diagnostics.data_summary || null,
        },
        config: {
            metric_key: config.metric_key || 'omni_purchase',
            n_restarts: config.n_restarts || null,
            holdout_days: config.holdout_days || null,
        },
    };
};

const AiInsightsCard = ({
    language,
    snapshot,
    groups,
    reportedByGroup,
    accountName,
    onAiSummarySaved,
}) => {
    const existing = snapshot?.ai_summary || '';
    const [aiContent, setAiContent] = useState(existing);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [aiError, setAiError] = useState(null);
    // 儲存時需讀取最新串流內容：與 setAiContent 同步雙寫，避免 setState 閉包舊值
    const aiContentRef = useRef(existing);

    // 切換快照時重置內容
    useEffect(() => {
        setAiContent(existing);
        aiContentRef.current = existing;
        setAiError(null);
    }, [snapshot?.snapshot_id, existing]);

    if (!snapshot || snapshot.status !== 'completed' || !snapshot.results) {
        return null;
    }

    const handleGenerate = async () => {
        if (isAnalyzing) return;
        setIsAnalyzing(true);
        setAiError(null);
        setAiContent('');
        aiContentRef.current = '';
        const payload = buildAiPayload({ snapshot, groups, reportedByGroup });
        const accountLabel = accountName || snapshot.account_id;
        const context = t(
            language,
            `Account: ${accountLabel} (${snapshot.account_id}); Period: ${snapshot.date_start} ~ ${snapshot.date_end}; Groups: ${groups.length}.`,
            `帳戶：${accountLabel}（${snapshot.account_id}）· 期間：${snapshot.date_start} ~ ${snapshot.date_end} · 群組數：${groups.length}`
        );
        try {
            await aiService.analyzeDataStream(
                payload,
                context,
                'contribution_analysis',
                null,
                (chunk) => {
                    aiContentRef.current = aiContentRef.current + chunk;
                    setAiContent((prev) => prev + chunk);
                },
                null,
                null,
                'weekly',
                'fb_ads'
            );
        } catch (err) {
            setAiError(
                err?.message ||
                t(language, 'AI analysis failed. Check AI key in settings.', 'AI 解讀失敗，請至設定頁確認 AI 金鑰。')
            );
            setIsAnalyzing(false);
            return;
        }
        setIsAnalyzing(false);

        // 串流完成 → 持久化（讀 ref 確保拿到最新內容，不靠閉包舊值）
        setIsSaving(true);
        try {
            const saved = await saveAiSummary({
                snapshotId: snapshot.snapshot_id,
                aiSummary: aiContentRef.current,
            });
            if (onAiSummarySaved) onAiSummarySaved(saved);
        } catch (err) {
            setAiError(
                err?.message ||
                t(language, 'AI summary generated but failed to save. Retry to persist.', 'AI 解讀已生成但儲存失敗，請重試以持久化。')
            );
        } finally {
            setIsSaving(false);
        }
    };

    const hasContent = aiContent && aiContent.length > 0;
    const buttonLabel = hasContent
        ? t(language, 'Regenerate', '重新解讀')
        : t(language, 'Generate Insights', '開始 AI 解讀');

    return (
        <Section
            title={t(language, 'AI Plain-Language Insights', 'AI 白話解讀')}
            subtitle={t(
                language,
                'Translates the numbers above into a quick read for non-statisticians. Generated by AI; the charts above remain the source of truth.',
                '把上方數字翻成白話文，給不懂統計的主管快速掌握重點。AI 生成，上方圖表仍是事實來源。'
            )}
        >
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
                <button
                    type="button"
                    onClick={handleGenerate}
                    disabled={isAnalyzing || isSaving}
                    style={{
                        ...secondaryButtonStyle,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        opacity: isAnalyzing || isSaving ? 0.5 : 1,
                    }}
                >
                    {isAnalyzing || isSaving ? <FiRefreshCcw className="spin" /> : <FiCpu />}
                    {isAnalyzing
                        ? t(language, 'Analyzing…', '解讀中…')
                        : isSaving
                            ? t(language, 'Saving…', '儲存中…')
                            : buttonLabel}
                </button>
            </div>

            {aiError && <ErrorPanel message={aiError} />}

            <div
                style={{
                    background: 'rgba(59, 130, 246, 0.05)',
                    border: '1px solid rgba(59, 130, 246, 0.2)',
                    borderRadius: '12px',
                    padding: '20px 22px',
                    minHeight: '100px',
                    color: 'var(--text-primary)',
                    lineHeight: 1.7,
                }}
            >
                {hasContent ? (
                    <div className="report-ai-content">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeRaw]}
                        >
                            {aiContent}
                        </ReactMarkdown>
                    </div>
                ) : (
                    <div
                        style={{
                            color: 'var(--text-tertiary)',
                            textAlign: 'center',
                            padding: '20px',
                            fontSize: '0.85rem',
                        }}
                    >
                        {isAnalyzing
                            ? t(language, 'AI is analyzing your data…', 'AI 正在分析您的數據…')
                            : t(
                                language,
                                'No AI summary yet. Click "Generate Insights" to ask AI to translate the results.',
                                '尚無 AI 解讀。點選「開始 AI 解讀」讓 AI 翻譯結果。'
                            )}
                    </div>
                )}
            </div>

            <div
                style={{
                    marginTop: '10px',
                    fontSize: '0.74rem',
                    color: 'var(--text-tertiary)',
                    lineHeight: 1.5,
                }}
            >
                {t(
                    language,
                    'Disclaimer: AI insights are for reference only. The charts and numbers above are the source of truth.',
                    '免責聲明：AI 解讀僅供參考，數字仍以上方圖表為準。'
                )}
            </div>
        </Section>
    );
};

export default AiInsightsCard;
