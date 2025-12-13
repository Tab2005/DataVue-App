import React, { useState } from 'react';
import { FiX, FiLink, FiCopy } from 'react-icons/fi';
import { TeamService } from '../services/teamService';

const InviteModal = ({ isOpen, onClose, teamId, language }) => {
    const [inviteData, setInviteData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [copied, setCopied] = useState(false);

    if (!isOpen) return null;

    const handleGenerate = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await TeamService.createInviteLink(teamId);
            setInviteData(data);
        } catch (err) {
            setError(err.message || (language === 'en' ? 'Failed' : '發生錯誤'));
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = () => {
        if (inviteData?.invite_url) {
            navigator.clipboard.writeText(inviteData.invite_url);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    // Auto generate on open if not exists? Maybe wait for user action.
    // Let's require button click for now to avoid spamming tokens.

    const t = {
        title: language === 'en' ? 'Invite Member' : '邀請成員',
        desc: language === 'en' ? 'Generate a link valid for 24 hours. Share it to invite members.' : '產生一個 24 小時有效的邀請連結，將此連結傳給成員即可。',
        generate: language === 'en' ? 'Generate Link' : '產生連結',
        generating: language === 'en' ? 'Generating...' : '產生中...',
        copy: language === 'en' ? 'Copy Link' : '複製連結',
        copied: language === 'en' ? 'Copied!' : '已複製！',
        expires: language === 'en' ? 'Expires at' : '過期時間',
        close: language === 'en' ? 'Close' : '關閉'
    };

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1100, backdropFilter: 'blur(5px)'
        }}>
            <div className="glass-panel" style={{
                background: 'var(--bg-secondary)',
                width: '450px',
                padding: '24px',
                borderRadius: '12px',
                border: '1px solid var(--glass-border)',
                position: 'relative'
            }}>
                <button onClick={onClose} style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <FiX size={24} />
                </button>

                <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px', fontSize: '1.4rem' }}>
                    <FiLink /> {t.title}
                </h2>

                <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: 1.5 }}>
                    {t.desc}
                </p>

                {!inviteData ? (
                    <div style={{ textAlign: 'center' }}>
                        <button
                            onClick={handleGenerate}
                            disabled={loading}
                            style={{
                                padding: '10px 24px',
                                borderRadius: '8px',
                                background: 'var(--accent-primary)',
                                border: 'none',
                                color: 'white',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            {loading ? t.generating : t.generate}
                        </button>
                        {error && <p style={{ color: '#ef4444', marginTop: '12px' }}>{error}</p>}
                    </div>
                ) : (
                    <div style={{ background: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '8px', border: '1px solid var(--glass-border)' }}>

                        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
                            <input
                                readOnly
                                value={inviteData.invite_url}
                                style={{
                                    flex: 1,
                                    background: 'var(--bg-primary)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'var(--text-primary)',
                                    padding: '8px',
                                    borderRadius: '4px',
                                    outline: 'none'
                                }}
                            />
                            <button
                                onClick={handleCopy}
                                style={{
                                    background: copied ? '#10b981' : 'var(--bg-hover)',
                                    border: '1px solid var(--glass-border)',
                                    color: 'white',
                                    padding: '8px 12px',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '4px'
                                }}
                            >
                                <FiCopy /> {copied ? t.copied : t.copy}
                            </button>
                        </div>

                        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                            {t.expires}: {new Date(inviteData.expires_at + 'Z').toLocaleString()}
                        </div>

                        <div style={{ marginTop: '16px', textAlign: 'right' }}>
                            <button onClick={() => setInviteData(null)} style={{ background: 'transparent', border: 'none', color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.9rem' }}>
                                {language === 'en' ? 'Generate New...' : '產生新的...'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InviteModal;
