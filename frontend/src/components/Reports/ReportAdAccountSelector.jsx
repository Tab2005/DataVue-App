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
                    border: '1px solid var(--glass-border)',
                    borderRadius: '10px',
                    color: selectedAccount ? 'var(--text-primary)' : 'var(--text-tertiary)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'all 0.2s'
                }}
            >
                <div>
                    {selectedAccount 
                        ? `${selectedAccount.name} (${selectedAccount.id})` 
                        : t('Select an Ad Account...', '請選擇廣告帳號...')}
                </div>
                <div style={{ 
                    transition: 'transform 0.2s', 
                    transform: isOpen ? 'rotate(180deg)' : 'rotate(0)' 
                }}>
                    <FiSearch />
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
                    boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                    zIndex: 100,
                    overflow: 'hidden',
                    animation: 'fadeIn 0.2s ease-out'
                }}>
                    {/* Search inside dropdown */}
                    <div style={{ 
                        padding: '10px', 
                        borderBottom: '1px solid var(--glass-border)',
                        backgroundColor: 'rgba(255,255,255,0.03)'
                    }}>
                        <input
                            autoFocus
                            type="text"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder={t('Search...', '搜尋...')}
                            style={{
                                width: '100%',
                                padding: '8px 12px',
                                backgroundColor: 'var(--bg-primary)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                color: 'var(--text-primary)',
                                fontSize: '0.9rem',
                                outline: 'none'
                            }}
                        />
                    </div>

                    {/* Options List */}
                    <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                        {filteredAccounts.map(acc => (
                            <div
                                key={acc.id}
                                onClick={() => {
                                    onSelect(acc.id, acc.name);
                                    setIsOpen(false);
                                }}
                                style={{
                                    padding: '12px 16px',
                                    cursor: 'pointer',
                                    borderBottom: '1px solid rgba(255,255,255,0.02)',
                                    backgroundColor: acc.id === selectedId ? 'rgba(45, 136, 255, 0.1)' : 'transparent',
                                    transition: 'background 0.2s'
                                }}
                                onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.05)'}
                                onMouseLeave={(e) => e.target.style.backgroundColor = acc.id === selectedId ? 'rgba(45, 136, 255, 0.1)' : 'transparent'}
                            >
                                <div style={{ 
                                    color: acc.id === selectedId ? 'var(--accent-primary)' : 'var(--text-primary)',
                                    fontWeight: acc.id === selectedId ? 'bold' : 'normal',
                                    fontSize: '0.9rem'
                                }}>
                                    {acc.name}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                                    ID: {acc.id}
                                </div>
                            </div>
                        ))}
                        {filteredAccounts.length === 0 && (
                            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                                {t('No results.', '沒有相符的帳號')}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ReportAdAccountSelector;
