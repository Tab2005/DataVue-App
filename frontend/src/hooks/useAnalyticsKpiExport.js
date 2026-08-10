// frontend/src/hooks/useAnalyticsKpiExport.js (docs/33 第 7 波：Analytics.jsx 組合層瘦身)
import { useRef, useState } from 'react';
import html2canvas from 'html2canvas';

export const useAnalyticsKpiExport = () => {
    const kpiRef = useRef(null);
    const [showKpiMenu, setShowKpiMenu] = useState(false);

    const handleExportImage = async () => {
        if (!kpiRef.current) return;

        try {
            const canvas = await html2canvas(kpiRef.current, {
                backgroundColor: '#18191a', // Match theme background
                scale: 2, // High resolution
                useCORS: true // Allow cross-origin images
            });

            // Generate Filename: YYYYMMDD_Random3
            const now = new Date();
            const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
            const randomStr = Math.floor(Math.random() * 900 + 100).toString();
            const filename = `${dateStr}_${randomStr}.png`;

            const link = document.createElement('a');
            link.download = filename;
            link.href = canvas.toDataURL();
            link.click();

            setShowKpiMenu(false);
        } catch (err) {
            console.error("Export failed", err);
        }
    };

    return { kpiRef, showKpiMenu, setShowKpiMenu, handleExportImage };
};

export default useAnalyticsKpiExport;
