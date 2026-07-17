import { useEffect, useRef, useState } from 'react';

export const useGscSearchAppearance = ({ apiUrl, selectedSite, activeDateRange, activeTab }) => {
    const [searchAppearanceData, setSearchAppearanceData] = useState(null);
    const [searchAppearanceLoading, setSearchAppearanceLoading] = useState(false);
    const [searchAppearanceError, setSearchAppearanceError] = useState(null);
    const cacheRef = useRef({});

    useEffect(() => {
        if (activeTab !== 'searchAppearance') return;
        if (!selectedSite || !activeDateRange.start || !activeDateRange.end) return;

        const cacheKey = `${selectedSite}-${activeDateRange.start}-${activeDateRange.end}`;
        const cached = cacheRef.current[cacheKey];
        if (cached) {
            setSearchAppearanceData(cached);
            setSearchAppearanceError(null);
            return;
        }

        let cancelled = false;

        (async () => {
            setSearchAppearanceLoading(true);
            setSearchAppearanceError(null);
            try {
                const resp = await fetch(
                    `${apiUrl}/api/gsc/search-appearance-summary?site_url=${encodeURIComponent(selectedSite)}&start_date=${activeDateRange.start}&end_date=${activeDateRange.end}`,
                    { headers: { 'Authorization': `Bearer ${localStorage.getItem('google_token')}` } }
                );
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.error || data.detail || 'Failed to fetch search appearance summary');
                if (cancelled) return;
                cacheRef.current[cacheKey] = data;
                setSearchAppearanceData(data);
            } catch (err) {
                if (!cancelled) {
                    console.error('Failed to fetch GSC search appearance summary:', err);
                    setSearchAppearanceError(err.message);
                }
            } finally {
                if (!cancelled) setSearchAppearanceLoading(false);
            }
        })();

        return () => { cancelled = true; };
    }, [activeTab, selectedSite, activeDateRange, apiUrl]);

    return { searchAppearanceData, searchAppearanceLoading, searchAppearanceError };
};
