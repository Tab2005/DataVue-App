import React from 'react';
import { useOutletContext } from 'react-router-dom';

import ReleaseOverviewContent from '../components/MetaAndromeda/release/ReleaseOverviewContent';
import { infoPanelStyle, panelStyle } from '../components/MetaAndromeda/release/releaseShared';
import { useModuleAccess } from '../hooks/usePermission';
import { useMetaAndromedaRelease } from '../hooks/useMetaAndromedaRelease';

const MetaAndromedaRelease = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const { hasAccess, loading: loadingModuleAccess } = useModuleAccess('meta_andromeda', selectedTeamId);
    const t = (en, zh) => (language === 'en' ? en : zh);
    const releaseState = useMetaAndromedaRelease({ hasAccess, t });

    if (loadingModuleAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <div style={panelStyle}>{t('Checking workspace access...', '正在檢查工作區模組權限...')}</div>
            </div>
        );
    }

    if (!hasAccess) {
        return (
            <div style={{ padding: isMobile ? '16px' : '24px' }}>
                <div style={infoPanelStyle}>
                    {t(
                        'You do not have access to Meta Andromeda in this workspace.',
                        '你目前沒有此工作區的 Meta Andromeda 模組存取權限。'
                    )}
                </div>
            </div>
        );
    }

    return (
        <ReleaseOverviewContent
            {...releaseState}
            isMobile={isMobile}
            t={t}
        />
    );
};

export default MetaAndromedaRelease;
