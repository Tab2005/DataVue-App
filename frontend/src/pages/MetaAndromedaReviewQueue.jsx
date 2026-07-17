import { useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';

import ReviewQueueDetail from '../components/MetaAndromeda/reviewQueue/ReviewQueueDetail';
import ReviewQueueList from '../components/MetaAndromeda/reviewQueue/ReviewQueueList';
import {
    errorPanelStyle,
    panelStyle,
    queueScrollCss,
    selectStyle,
} from '../components/MetaAndromeda/reviewQueue/reviewQueueShared';
import { useModuleAccess } from '../hooks/usePermission';
import { useReviewQueue } from '../hooks/useReviewQueue';

const MetaAndromedaReviewQueue = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('meta_andromeda', selectedTeamId);
    const t = useCallback((en, zh) => (language === 'en' ? en : zh), [language]);
    const queue = useReviewQueue(t);

    if (accessLoading) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <section style={panelStyle}>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                    <div style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>{t('Checking access...', '正在確認權限...')}</div>
                </section>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <section style={panelStyle}>
                    <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
                    <div style={errorPanelStyle}>{t('No access to Meta Andromeda in this workspace.', '此工作區無 Meta Andromeda 存取權限。')}</div>
                </section>
            </div>
        );
    }

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <style>{queueScrollCss}</style>
            <HeaderFilters isMobile={isMobile} queue={queue} t={t} />
            {queue.error ? <div style={errorPanelStyle}>{queue.error}</div> : null}

            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '0.9fr 1.1fr', gap: '16px' }}>
                <ReviewQueueList {...queue} t={t} />
                <ReviewQueueDetail
                    detail={queue.detail}
                    isMobile={isMobile}
                    language={language}
                    loadingDetail={queue.loadingDetail}
                    t={t}
                />
            </div>
        </div>
    );
};

const HeaderFilters = ({ isMobile, queue, t }) => {
    const {
        observationFilter,
        roasBandFilter,
        scoringEngineFilter,
        sourceFilter,
        statusFilter,
    } = queue.filters;

    return (
        <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: isMobile ? 'flex-start' : 'center',
            flexDirection: isMobile ? 'column' : 'row',
            gap: '16px',
            marginBottom: '20px',
        }}>
            <div>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>Meta Andromeda</div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Evaluation Records', '評估紀錄')}</h1>
            </div>

            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                <select value={sourceFilter} onChange={(e) => queue.setSourceFilter(e.target.value)} style={selectStyle}>
                    <option value="all">{t('All Sources', '全部來源')}</option>
                    <option value="analytics">{t('Analytics Import', '成效分析匯入')}</option>
                    <option value="score_lab">{t('Score Lab', '評分工作台')}</option>
                </select>
                <select value={statusFilter} onChange={(e) => queue.setStatusFilter(e.target.value)} style={selectStyle}>
                    <option value="all">{t('All Statuses', '全部狀態')}</option>
                    <option value="completed">{t('Completed', '已完成')}</option>
                    <option value="queued">{t('Queued', '排隊中')}</option>
                    <option value="failed">{t('Failed', '失敗')}</option>
                </select>
                <select value={roasBandFilter} onChange={(e) => queue.setRoasBandFilter(e.target.value)} style={selectStyle}>
                    <option value="all">{t('All Scores', '全部評分')}</option>
                    <option value="high">{t('High', '高')}</option>
                    <option value="mid">{t('Mid', '中')}</option>
                    <option value="low">{t('Low', '低')}</option>
                </select>
                <select value={observationFilter} onChange={(e) => queue.setObservationFilter(e.target.value)} style={selectStyle}>
                    <option value="all">{t('All Records', '全部紀錄')}</option>
                    <option value="matched">{t('Matched', '已匹配成效')}</option>
                    <option value="unmatched">{t('Not Matched', '尚未匹配')}</option>
                </select>
                <select value={scoringEngineFilter} onChange={(e) => queue.setScoringEngineFilter(e.target.value)} style={selectStyle}>
                    <option value="all">{t('All Engines', '全部引擎')}</option>
                    <option value="ai">{t('AI Model', 'AI 模型')}</option>
                    <option value="heuristic">{t('Heuristic', '啟發式引擎')}</option>
                </select>
            </div>
        </div>
    );
};

export default MetaAndromedaReviewQueue;
