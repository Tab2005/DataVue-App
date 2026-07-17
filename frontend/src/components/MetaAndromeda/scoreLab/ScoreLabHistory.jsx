import { HistoryItem } from './scoreLabComponents';
import { btnSecStyle, panelStyle, titleSt } from './scoreLabShared';

const ScoreLabHistory = ({ history, isMobile, scoreResult, setHistory, setScoreResult, t }) => {
    if (history.length === 0) return null;

    return (
        <section style={{ ...panelStyle, marginTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h2 style={{ ...titleSt, margin: 0 }}>
                    {t('Session History', '本次 Session 評分記錄')}
                    <span style={{ marginLeft: '8px', color: 'var(--text-secondary)', fontWeight: 400, fontSize: '0.78rem' }}>
                        {t(`(${history.length} submissions, latest 10)`, `（共 ${history.length} 筆，最多保留 10 筆）`)}
                    </span>
                </h2>
                <button
                    type="button"
                    onClick={() => setHistory([])}
                    style={{ ...btnSecStyle, padding: '4px 10px', fontSize: '0.75rem' }}
                >
                    {t('Clear', '清除記錄')}
                </button>
            </div>
            <div style={{ display: 'grid', gap: '6px', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(280px, 1fr))' }}>
                {history.map(item => (
                    <HistoryItem
                        key={item.score_event_id}
                        item={item}
                        selected={scoreResult?.score_event_id === item.score_event_id}
                        onClick={() => setScoreResult(item)}
                    />
                ))}
            </div>
        </section>
    );
};

export default ScoreLabHistory;
