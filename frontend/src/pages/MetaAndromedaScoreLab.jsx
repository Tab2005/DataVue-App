import { useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';

import { AccessScreen } from '../components/MetaAndromeda/scoreLab/scoreLabComponents';
import ScoreLabForm from '../components/MetaAndromeda/scoreLab/ScoreLabForm';
import ScoreLabHistory from '../components/MetaAndromeda/scoreLab/ScoreLabHistory';
import ScoreLabResult from '../components/MetaAndromeda/scoreLab/ScoreLabResult';
import {
    errorPanelStyle,
    scoreLabScrollCss,
} from '../components/MetaAndromeda/scoreLab/scoreLabShared';
import { useModuleAccess } from '../hooks/usePermission';
import { useScoreLab } from '../hooks/useScoreLab';

const MetaAndromedaScoreLab = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: accessLoading } = useModuleAccess('meta_andromeda', selectedTeamId);
    const t = useCallback((en, zh) => (language === 'en' ? en : zh), [language]);
    const lang = language === 'en' ? 'en' : 'zh';
    const lab = useScoreLab(t);

    if (accessLoading) return <AccessScreen isMobile={isMobile} t={t} loading />;
    if (!hasAccess) return <AccessScreen isMobile={isMobile} t={t} />;

    return (
        <div style={{ padding: isMobile ? '16px' : '24px' }}>
            <style>{scoreLabScrollCss}</style>

            <div style={{ marginBottom: '20px' }}>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700, marginBottom: '8px' }}>Meta Andromeda</div>
                <h1 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('Score Lab', '評分工作台')}</h1>
            </div>

            {lab.error && <div style={errorPanelStyle}>{lab.error}</div>}

            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: '16px' }}>
                <ScoreLabForm lab={lab} lang={lang} t={t} />
                <ScoreLabResult lab={lab} lang={lang} t={t} />
            </div>

            <ScoreLabHistory
                history={lab.history}
                isMobile={isMobile}
                scoreResult={lab.scoreResult}
                setHistory={lab.setHistory}
                setScoreResult={lab.setScoreResult}
                t={t}
            />
        </div>
    );
};

export default MetaAndromedaScoreLab;
