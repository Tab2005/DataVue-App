import React from 'react';
import { useOutletContext } from 'react-router-dom';

import { MonitoringDashboard } from '../components/MetaAndromeda/MonitoringDashboard';
import { useMetaAndromedaMonitoring } from '../hooks/useMetaAndromedaMonitoring';

const MetaAndromedaMonitoring = () => {
    const { isMobile, language, selectedTeamId } = useOutletContext();
    const monitoring = useMetaAndromedaMonitoring({ language, selectedTeamId });

    return (
        <MonitoringDashboard
            isMobile={isMobile}
            language={language}
            monitoring={monitoring}
        />
    );
};

export default MetaAndromedaMonitoring;
