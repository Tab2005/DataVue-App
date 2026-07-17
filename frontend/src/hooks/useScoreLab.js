import { useCallback, useEffect, useRef, useState } from 'react';

import {
    fetchMetaAndromedaScore,
    submitMetaAndromedaScore,
    uploadMetaAndromedaAsset,
} from '../services/metaAndromedaWorkflowService';
import { inferAssetType, TERMINAL } from '../components/MetaAndromeda/scoreLab/scoreLabShared';

const initialForm = {
    request_mode: 'auto',
    objective: 'purchase',
    placement_family: 'all',
    market: 'TW',
    primary_text: '',
    headline: '',
    cta: '',
};

export const useScoreLab = (t) => {
    const [selectedFile, setSelectedFile] = useState(null);
    const [localPreviewUrl, setLocalPreviewUrl] = useState(null);
    const [uploadedAsset, setUploadedAsset] = useState(null);
    const [scoreResult, setScoreResult] = useState(null);
    const [history, setHistory] = useState([]);
    const [loadingUpload, setLoadingUpload] = useState(false);
    const [loadingSubmit, setLoadingSubmit] = useState(false);
    const [polling, setPolling] = useState(false);
    const [error, setError] = useState(null);
    const [isDragActive, setIsDragActive] = useState(false);
    const [form, setForm] = useState(initialForm);
    const localPreviewRef = useRef(null);

    const revokeLocalPreview = useCallback(() => {
        if (localPreviewRef.current) {
            URL.revokeObjectURL(localPreviewRef.current);
            localPreviewRef.current = null;
        }
    }, []);

    const autoUpload = useCallback(async (file) => {
        const assetType = inferAssetType(file);
        if (!assetType) {
            setError(t('Unsupported file type.', '不支援的檔案格式。'));
            return;
        }
        setLoadingUpload(true);
        setError(null);
        try {
            const uploaded = await uploadMetaAndromedaAsset(file, assetType);
            setUploadedAsset(uploaded);
        } catch (err) {
            setError(err.message || t('Upload failed', '素材上傳失敗'));
        } finally {
            setLoadingUpload(false);
        }
    }, [t]);

    const handleFileSelect = useCallback(async (file) => {
        if (!file) return;
        revokeLocalPreview();
        const previewUrl = URL.createObjectURL(file);
        localPreviewRef.current = previewUrl;
        setSelectedFile(file);
        setLocalPreviewUrl(previewUrl);
        setUploadedAsset(null);
        await autoUpload(file);
    }, [autoUpload, revokeLocalPreview]);

    const clearSelectedAsset = useCallback(() => {
        revokeLocalPreview();
        setLocalPreviewUrl(null);
        setSelectedFile(null);
        setUploadedAsset(null);
    }, [revokeLocalPreview]);

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragActive(e.type === 'dragenter' || e.type === 'dragover');
    }, []);

    const handleDrop = useCallback(async (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragActive(false);
        const file = e.dataTransfer.files?.[0];
        if (file) await handleFileSelect(file);
    }, [handleFileSelect]);

    const handleSubmit = useCallback(async (e) => {
        e.preventDefault();
        if (!uploadedAsset) {
            setError(t('Upload an asset first.', '請先上傳素材。'));
            return;
        }
        setLoadingSubmit(true);
        setError(null);
        try {
            const result = await submitMetaAndromedaScore({
                ...form,
                asset_uri: uploadedAsset.asset_uri,
                asset_id: uploadedAsset.asset_id,
                asset_type: uploadedAsset.asset_type,
            });
            setScoreResult(result);
            setPolling(!TERMINAL.has(result.status));
            setHistory(prev => [result, ...prev].slice(0, 10));
        } catch (err) {
            setError(err.message || t('Submit failed', '送出評分失敗'));
        } finally {
            setLoadingSubmit(false);
        }
    }, [form, t, uploadedAsset]);

    const resetForm = useCallback(() => {
        revokeLocalPreview();
        setLocalPreviewUrl(null);
        setSelectedFile(null);
        setUploadedAsset(null);
        setScoreResult(null);
        setError(null);
        setPolling(false);
    }, [revokeLocalPreview]);

    useEffect(() => {
        if (!scoreResult?.score_event_id || TERMINAL.has(scoreResult?.status)) return undefined;

        const id = window.setInterval(async () => {
            try {
                const latest = await fetchMetaAndromedaScore(scoreResult.score_event_id);
                setScoreResult(latest);
                setHistory(prev => prev.map(h => h.score_event_id === latest.score_event_id ? latest : h));
                if (TERMINAL.has(latest.status)) {
                    setPolling(false);
                    window.clearInterval(id);
                }
            } catch (err) {
                setPolling(false);
                setError(err.message || t('Polling failed', '輪詢評分狀態失敗'));
                window.clearInterval(id);
            }
        }, 1800);

        return () => window.clearInterval(id);
    }, [scoreResult?.score_event_id, scoreResult?.status, t]);

    useEffect(() => () => revokeLocalPreview(), [revokeLocalPreview]);

    return {
        assetType: selectedFile ? inferAssetType(selectedFile) : null,
        autoUpload,
        clearSelectedAsset,
        error,
        form,
        handleDrag,
        handleDrop,
        handleFileSelect,
        handleSubmit,
        history,
        isDragActive,
        loadingSubmit,
        loadingUpload,
        localPreviewUrl,
        polling,
        resetForm,
        scoreResult,
        selectedFile,
        setForm,
        setHistory,
        setScoreResult,
        uploadedAsset,
    };
};
