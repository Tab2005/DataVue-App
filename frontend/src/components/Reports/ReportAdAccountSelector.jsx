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
    const [isOpen, setIsOpen] = useState(false);

    const t = (en, zh) => (language === 'zh' ? zh : en);

    const selectedAccount = accounts.find(a => a.id === selectedId);

    useEffect(() => {
        const fetchAccounts = async () => {
            setLoading(true);
            try {
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
        <div style={{ padding: '12px', color: 'var(--text-secondary)' }}>
            <FiLoader className="spin" /> {t('Loading accounts...', '正在載入帳號...')}
        </div>
    );

    if (error) return (
        <div style={{ padding: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px' }}>
            <FiAlertCircle /> {error}
        </div>
    );

    return (
        <div style={{ position: 'relative' }}>
            {/* Custom Dropdown Trigger */}
            <div 
                onClick={() => setIsOpen(!isOpen)}
                style={{
                    padding: '12px 16px',
                    backgroundColor: 'var(--bg-primary)',
                    border: isOpen ? '1px solid var(--accent-primary)' : '1px solid var(--glass-border)',
                    borderRadius: '10px',
                    color: selectedAccount ? 'var(--text-primary)' : 'var(--text-tertiary)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'all 0.2s',
                    boxShadow: isOpen ? '0 0 0 2px rgba(45, 136, 255, 0.2)' : 'none'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
                    <div style={{ 
                        width: '8px', 
                        height: '8px', 
                        borderRadius: '50%', 
                        backgroundColor: selectedAccount ? '#10b981' : 'var(--text-tertiary)',
                        flexShrink: 0
                    }} />
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: selectedAccount ? '600' : 'normal' }}>
                        {selectedAccount 
                            ? `${selectedAccount.name}` 
                            : t('Select an Ad Account...', '請選擇廣告帳號...')}
                    </div>
                </div>
                <div style={{ 
                    transition: 'transform 0.2s', 
                    transform: isOpen ? 'rotate(180deg)' : 'rotate(0)',
                    color: isOpen ? 'var(--accent-primary)' : 'var(--text-tertiary)'
                }}>
                    <FiChevronDown />
                </div>
            </div>

            {/* Dropdown Menu */}
            {isOpen && (
                <div style={{
                    position: 'absolute',
                    top: 'calc(100% + 8px)',
                    left: 0,
                    right: 0,
                    backgroundColor: 'var(--bg-secondary)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '12px',
                    boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
                    zIndex: 1000,
                    overflow: 'visible',
                    animation: 'fadeInUp 0.2s ease-out'
                }}>
                    {/* Search inside dropdown */}
                    <div style={{ 
                        padding: '12px', 
                        borderBottom: '1px solid var(--glass-border)',
                        backgroundColor: 'rgba(255,255,255,0.02)'
                    }}>
                        <div style={{ position: 'relative' }}>
                            <FiSearch style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)' }} />
                            <input
                                autoFocus
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder={t('Search...', '搜尋廣告帳號名稱或 ID...')}
                                style={{
                                    width: '100%',
                                    padding: '10px 10px 10px 38px',
                                    backgroundColor: 'var(--bg-primary)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    color: 'var(--text-primary)',
                                    fontSize: '0.9rem',
                                    outline: 'none'
                                }}
                            />
                        </div>
                    </div>

                    {/* Options List */}
                    <div style={{ maxHeight: '300px', overflowY: 'auto', padding: '6px' }}>
                        {filteredAccounts.map(acc => (
                            <div
                                key={acc.id}
                                onClick={() => {
                                    onSelect(acc.id, acc.name);
                                    setIsOpen(false);
                                }}
                                style={{
                                    padding: '10px 14px',
                                    cursor: 'pointer',
                                    borderRadius: '8px',
                                    marginBottom: '2px',
                                    backgroundColor: acc.id === selectedId ? 'rgba(45, 136, 255, 0.15)' : 'transparent',
                                    transition: 'all 0.15s'
                                }}
                                onMouseEnter={(e) => {
                                    if (acc.id !== selectedId) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)';
                                }}
                                onMouseLeave={(e) => {
                                    if (acc.id !== selectedId) e.currentTarget.style.backgroundColor = 'transparent';
                                }}
                            >
                                <div style={{ 
                                    color: acc.id === selectedId ? 'var(--accent-primary)' : 'var(--text-primary)',
                                    fontWeight: acc.id === selectedId ? '600' : '500',
                                    fontSize: '0.95rem',
                                    marginBottom: '2px'
                                }}>
                                    {acc.name}
                                </div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', display: 'flex', justifyContent: 'space-between' }}>
                                    <span>ID: {acc.id}</span>
                                    {acc.id === selectedId && <FiCheckCircle color="var(--accent-primary)" style={{ marginLeft: '4px' }} />}
                                </div>
                            </div>
                        ))}
                        {filteredAccounts.length === 0 && (
                            <div style={{ padding: '30px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                                <FiSearch size={24} style={{ marginBottom: '8px', opacity: 0.3 }} />
                                <div>{t('No results found.', '找不到相符的帳號')}</div>
                            </div>
                        )}
                    </div>
                </div>
            )}
            
            {/* Click outside to close (Optional but recommended) */}
            {isOpen && (
                <div 
                    style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 999 }} 
                    onClick={() => setIsOpen(false)}
                />
            )}
        </div>
    );
};

export default ReportAdAccountSelector;
