/**
 * 廣告文案庫小縮圖（docs/74）：已落地素材走 /media/{asset_id}（需帶授權），
 * 未落地者退回 FB CDN 原網址（可能已過期，載入失敗時顯示佔位圖）。
 */
import React, { useEffect, useState } from 'react';
import { FiImage, FiPlay } from 'react-icons/fi';

import { fetchMediaBlobUrl } from '../../services/adLibraryService';

const Thumb = ({ thumbnail, size = 64 }) => {
    const [src, setSrc] = useState(null);
    const [failed, setFailed] = useState(false);

    useEffect(() => {
        setSrc(null);
        setFailed(false);
        if (!thumbnail?.asset_id) return undefined;
        const controller = new AbortController();
        let objectUrl = null;
        fetchMediaBlobUrl(thumbnail.asset_id, controller.signal)
            .then((url) => { objectUrl = url; setSrc(url); })
            .catch((err) => { if (err.name !== 'AbortError') setFailed(true); });
        return () => {
            controller.abort();
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [thumbnail?.asset_id]);

    const displaySrc = src || (!thumbnail?.asset_id && thumbnail?.fb_url) || null;
    return (
        <div className="adlib-ad-thumb" style={{ width: size, height: size, position: 'relative' }}>
            {displaySrc && !failed
                ? <img src={displaySrc} alt="" loading="lazy" onError={() => setFailed(true)} />
                : <FiImage size={Math.max(16, size / 3)} />}
            {thumbnail?.kind === 'video_thumbnail' && (
                <span style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
                    <span style={{ background: 'rgba(0,0,0,0.55)', borderRadius: '50%', padding: 6, display: 'flex' }}>
                        <FiPlay size={Math.max(10, size / 6)} color="#fff" />
                    </span>
                </span>
            )}
        </div>
    );
};

export default Thumb;
