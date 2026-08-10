// frontend/src/hooks/useGA4ChannelsTab.jsx (docs/33 第 7 波：GA4Insights.jsx 組合層瘦身)
import { useState } from 'react';

import { ga4InsightsService } from '../services/ga4InsightsService';

export const useGA4ChannelsTab = ({ t }) => {
    const [channelsDays, setChannelsDays] = useState(7);
    const [channelsDimension, setChannelsDimension] = useState('default_channel_group');
    const [channelsSnapshot, setChannelsSnapshot] = useState(null);
    const [channelsLoading, setChannelsLoading] = useState(false);
    const [channelsError, setChannelsError] = useState('');

    const loadChannels = async (pid, days, dimension = channelsDimension) => {
        if (!pid) return;
        setChannelsLoading(true);
        setChannelsError('');
        try {
            setChannelsSnapshot(await ga4InsightsService.getChannels(pid, days, dimension));
        } catch (err) {
            setChannelsError(err.message || t('Failed to load channel comparison.', '載入渠道對照失敗。'));
        } finally {
            setChannelsLoading(false);
        }
    };

    const ensureLoaded = (pid) => {
        if (!pid || channelsSnapshot) return;
        loadChannels(pid, channelsDays);
    };

    const reset = () => {
        setChannelsSnapshot(null);
    };

    return {
        channelsDays, setChannelsDays,
        channelsDimension, setChannelsDimension,
        channelsSnapshot, channelsLoading, channelsError,
        loadChannels,
        ensureLoaded,
        reset,
    };
};

export default useGA4ChannelsTab;
