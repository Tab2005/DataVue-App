// frontend/src/components/Reports/ReportAdAccountSelector.jsx
import React, { useState, useEffect } from 'react';
import { TeamService } from '../../services/teamService';
import { FiCheck, FiSearch, FiAlertCircle, FiLoader } from 'react-icons/fi';

/**
 * 報表專用的廣告帳號選擇器 (單選模式)
 * 移除「儲存」與「權限設定」邏輯，專注於精靈流程中的帳號選取。
 */
const ReportAdAccountSelector = ({ teamId, selectedId, onSelect, language }) => {
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const t = (en, zh) => (language === 'zh' ? zh : en);

    useEffect(() => {
        const fetchAccounts = async () => {
            if (!teamId) return;
            setLoading(true);
            try {
                // 使用 TeamService.getAllAdAccounts 並帶入當前團隊 ID
                const data = await TeamService.getAllAdAccounts(teamId);
                setAccounts(data || []);
            } catch (err) {
                console.error("Failed to fetch ad accounts for reports", err);
                setError(t('Failed to load ad accounts', '無法載入廣告帳號'));
            } finally {
                setLoading(false);
            }
        };
        fetchAccounts();
    }, [teamId]);

    const filteredAccounts = accounts.filter(acc => 
        acc.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
        acc.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return (
        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
            <FiLoader className="spin" /> {t('Loading accounts...', '正在載入帳號...')}
        </div>
    );

    if (error) return (
        <div style={{ padding: '16px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FiAlertCircle /> {error}
        </div>
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* Search Input */}
            <div style={{ position: 'relative' }}>
                <FiSearch style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
                <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder={t('Search accounts...', '搜尋廣告帳號...')}
                    style={{
                        width: '100%',
                        padding: '10px 10px 10px 38px',
                        backgroundColor: 'var(--bg-primary)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '10px',
                        color: 'var(--text-primary)',
                        fontSize: '0.9rem'
                    }}
                />
            </div>

            {/* Account List Grid */}
            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', 
                gap: '10px', 
                maxHeight: '320px', 
                overflowY: 'auto',
                padding: '4px'
            }}>
                {filteredAccounts.map(acc => {
                    const isSelected = acc.id === selectedId;
                    return (
                        <div
                            key={acc.id}
                            onClick={() => onSelect(acc.id, acc.name)}
                            style={{
                                padding: '12px',
                                borderRadius: '12px',
                                backgroundColor: isSelected ? 'rgba(45, 136, 255, 0.15)' : 'var(--bg-primary)',
                                border: isSelected ? '1.5px solid var(--accent-primary)' : '1px solid var(--glass-border)',
                                cursor: 'pointer',
                                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                position: 'relative',
                                overflow: 'hidden'
                            }}
                        >
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{ 
                                    fontWeight: '600', 
                                    fontSize: '0.95rem',
                                    color: isSelected ? 'var(--text-primary)' : 'var(--text-primary)',
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis'
                                }}>
                                    {acc.name}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                                    ID: {acc.id}
                                </div>
                            </div>
                            {isSelected && (
                                <div style={{ 
                                    width: '24px', 
                                    height: '24px', 
                                    borderRadius: '50%', 
                                    backgroundColor: 'var(--accent-primary)', 
                                    display: 'flex', 
                                    alignItems: 'center', 
                                    justifyContent: 'center',
                                    color: 'white',
                                    flexShrink: 0,
                                    marginLeft: '8px'
                                }}>
                                    <FiCheck size={14} />
                                </div>
                            )}
                        </div>
                    );
                })}
                {filteredAccounts.length === 0 && accounts.length > 0 && (
                    <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '20px', color: 'var(--text-tertiary)' }}>
                        {t('No accounts match your search', '找不到相符的帳號')}
                    </div>
                )}
                {accounts.length === 0 && (
                    <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '20px', color: 'var(--text-tertiary)' }}>
                        {t('No FB accounts found linked to this team.', '此團隊尚未串接 FB 廣告帳號。')}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReportAdAccountSelector;
