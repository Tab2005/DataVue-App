// frontend/src/components/Settings/LineBindingCard.jsx
import React, { useState, useEffect } from 'react';
import { FiMessageSquare, FiCopy, FiCheckCircle, FiRefreshCw, FiExternalLink } from 'react-icons/fi';
import { lineService } from '../../services/lineService';

const LineBindingCard = ({ language }) => {
    const [status, setStatus] = useState({ is_linked: false });
    const [bindingData, setBindingData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);

    const t = (en, zh) => (language === 'zh' ? zh : en);

    const fetchStatus = async () => {
        try {
            const res = await lineService.getStatus();
            setStatus(res);
        } catch (err) {
            console.error('Failed to fetch LINE status:', err);
        }
    };

    const handleGetCode = async () => {
        setLoading(true);
        try {
            const res = await lineService.getBindingCode();
            setBindingData(res);
        } catch (err) {
            console.error('Failed to get binding code:', err);
        } finally {
            setLoading(false);
        }
    };

    const copyCode = () => {
        if (!bindingData) return;
        navigator.clipboard.writeText(bindingData.code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    // 輪詢狀態 (如果正在等待綁定)
    useEffect(() => {
        let interval;
        if (bindingData && !status.is_linked) {
            interval = setInterval(async () => {
                const res = await lineService.getStatus();
                if (res.is_linked) {
                    setStatus(res);
                    setBindingData(null);
                    clearInterval(interval);
                }
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [bindingData, status.is_linked]);

    return (
        <div style={{ 
            backgroundColor: 'var(--bg-secondary)', 
            borderRadius: '16px', 
            padding: '24px',
            border: '1px solid var(--glass-border)',
            marginTop: '20px'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <div style={{ 
                    backgroundColor: status.is_linked ? '#06c755' : 'rgba(255,255,255,0.05)', 
                    padding: '10px', 
                    borderRadius: '12px' 
                }}>
                    <FiMessageSquare size={24} color={status.is_linked ? 'white' : 'var(--text-tertiary)'} />
                </div>
                <div>
                    <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>{t('LINE Notification Bot', 'LINE 通知選單')}</h3>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {status.is_linked 
                            ? t('Linked Successfully', '連結狀態：已串聯') 
                            : t('Receive automated reports via LINE', '透過 LINE 接收自動化週報通知')}
                    </p>
                </div>
            </div>

            {status.is_linked ? (
                <div style={{ backgroundColor: 'rgba(6, 199, 85, 0.1)', border: '1px solid rgba(6, 199, 85, 0.3)', borderRadius: '12px', padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <FiCheckCircle color="#06c755" size={20} />
                    <span style={{ color: '#06c755', fontWeight: '500' }}>{t('Service active', '通知服務已啟用')}</span>
                    <button 
                        onClick={fetchStatus}
                        style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: 'pointer' }}
                    >
                        <FiRefreshCw size={14} />
                    </button>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {!bindingData ? (
                        <button 
                            onClick={handleGetCode}
                            disabled={loading}
                            style={{ 
                                padding: '12px', 
                                backgroundColor: 'var(--accent-primary)', 
                                color: 'white', 
                                border: 'none', 
                                borderRadius: '10px', 
                                fontWeight: 'bold', 
                                cursor: 'pointer'
                            }}
                        >
                            {loading ? t('Loading...', '產生中...') : t('Link LINE Account', '現在開始綁定 LINE 帳號')}
                        </button>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                            <div style={{ textAlign: 'center', padding: '20px', backgroundColor: 'var(--bg-primary)', borderRadius: '12px', border: '1px dashed var(--glass-border)' }}>
                                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                                    {t('1. Scan QR Code to add our Bot', '1. 第一步：掃描 QR Code 加入 DataVue 官方帳號')}
                                </p>
                                <div style={{ width: '120px', height: '120px', margin: '0 auto', backgroundColor: 'white', borderRadius: '8px', padding: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                     {/* 這裡未來放入您的機器人實體 QR Code URL */}
                                     <div style={{ textAlign: 'center', color: '#666' }}>
                                        <FiMessageSquare size={48} color="#06c755" />
                                        <div style={{ fontSize: '0.6rem' }}>Scan QR</div>
                                     </div>
                                </div>
                            </div>

                            <div style={{ backgroundColor: 'var(--bg-primary)', padding: '16px', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                                    {t('2. Send this 6-digit code to the bot', '2. 第二步：在對話框中輸入並發送以下 6 位數代碼')}
                                </p>
                                <div style={{ display: 'flex', gap: '12px' }}>
                                    <div style={{ 
                                        flex: 1, 
                                        backgroundColor: 'var(--bg-secondary)', 
                                        padding: '12px', 
                                        borderRadius: '8px', 
                                        textAlign: 'center', 
                                        fontSize: '1.5rem', 
                                        fontWeight: 'bold', 
                                        letterSpacing: '4px', 
                                        color: 'var(--accent-primary)' 
                                    }}>
                                        {bindingData.code}
                                    </div>
                                    <button 
                                        onClick={copyCode}
                                        style={{ width: '48px', backgroundColor: 'var(--bg-hover)', border: 'none', borderRadius: '8px', cursor: 'pointer', color: copied ? '#06c755' : 'white' }}
                                    >
                                        {copied ? <FiCheckCircle size={20} /> : <FiCopy size={20} />}
                                    </button>
                                </div>
                                <p style={{ fontSize: '0.75rem', color: '#ef4444', marginTop: '12px', textAlign: 'center' }}>
                                    {t('Expires in 10 minutes', '驗證碼將在 10 分鐘內過期')}
                                </p>
                            </div>
                        </div>
                    )}
                </div>
            )}
            
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--glass-border)', fontSize: '0.8rem', color: 'var(--text-tertiary)' }}>
                <p style={{ margin: '0 0 4px 0' }}>{t('Instructions:', '使用說明：')}</p>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                    <li>{t('You must add the bot as a friend to receive messages.', '您必須先將機器人加入好友，否則無法收到推播內容。')}</li>
                    <li>{t('Each schedule can individually toggle LINE notifications.', '綁定後，您可以在各個自動排程中勾選是否開啟 LINE 通知。')}</li>
                </ul>
            </div>
        </div>
    );
};

export default LineBindingCard;
