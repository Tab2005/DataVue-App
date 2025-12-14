import React, { useState, useEffect } from 'react';
import { TeamService } from '../services/teamService';
import { FiCheckSquare, FiSquare, FiSave, FiAlertCircle } from 'react-icons/fi';

const AdAccountSelector = ({ teamId, initialSelected, language, styles, teamName }) => {
    const [allAccounts, setAllAccounts] = useState([]);
    const [selectedIds, setSelectedIds] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState(null);

    // Parse initialSelected (JSON string or null)
    useEffect(() => {
        if (initialSelected) {
            try {
                const parsed = JSON.parse(initialSelected);
                if (Array.isArray(parsed)) {
                    setSelectedIds(parsed);
                } else {
                    setSelectedIds([]);
                }
            } catch (e) {
                console.error("Failed to parse visible_ad_account_ids", e);
                setSelectedIds([]);
            }
        } else {
            // New logic: Default to Empty (none selected) as per backend strict mode
            setSelectedIds([]);
        }
    }, [initialSelected, teamId]);

    // Fetch All Available Accounts
    useEffect(() => {
        const fetchAccounts = async () => {
            setLoading(true);
            try {
                const accts = await TeamService.getAllAdAccounts(teamId);
                setAllAccounts(accts);
            } catch (err) {
                console.error("Failed to fetch ad accounts", err);
                setError(language === 'zh' ? '無法載入廣告帳號列表' : 'Failed to load ad accounts');
            } finally {
                setLoading(false);
            }
        };
        fetchAccounts();
    }, [teamId]);

    const handleToggle = (id) => {
        if (selectedIds.includes(id)) {
            setSelectedIds(selectedIds.filter(sid => sid !== id));
        } else {
            setSelectedIds([...selectedIds, id]);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setSuccessMsg(null);
        setError(null);
        try {
            await TeamService.updateAdAccounts(teamId, selectedIds);
            setSuccessMsg(language === 'zh' ? '權限設定已更新' : 'Permissions updated');

            // Reload page or notify parent?
            // Since context updates might be complex, a simple success message is good enough.
            // But ideally we should reload the team content.
            // window.location.reload(); // Aggressive but ensures global state sync
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleSelectAll = () => {
        if (selectedIds.length === allAccounts.length) {
            setSelectedIds([]);
        } else {
            setSelectedIds(allAccounts.map(a => a.id));
        }
    };

    return (
        <div>
            {/* Status and Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        type="button"
                        onClick={handleSelectAll}
                        style={{
                            padding: '8px 12px',
                            fontSize: '0.875rem',
                            borderRadius: '8px',
                            border: '1px solid var(--glass-border)',
                            backgroundColor: 'rgba(255,255,255,0.05)',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer'
                        }}
                    >
                        {selectedIds.length === allAccounts.length ? (language === 'zh' ? '取消全選' : 'Deselect All') : (language === 'zh' ? '全選' : 'Select All')}
                    </button>
                </div>

                <button
                    onClick={handleSave}
                    disabled={saving}
                    style={{
                        ...styles.buttonPrimary,
                        padding: '10px 24px',
                        fontSize: '0.875rem'
                    }}
                >
                    {saving ? (language === 'zh' ? '儲存中...' : 'Saving...') : (language === 'zh' ? '儲存設定' : 'Save Settings')}
                </button>
            </div>

            {successMsg && (
                <div style={{
                    marginBottom: '16px', padding: '12px', borderRadius: '8px',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)', color: '#22c55e', border: '1px solid rgba(34, 197, 94, 0.2)'
                }}>
                    {successMsg}
                </div>
            )}

            {error && (
                <div style={{
                    marginBottom: '16px', padding: '12px', borderRadius: '8px',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.2)'
                }}>
                    <FiAlertCircle style={{ marginRight: '8px', verticalAlign: 'text-bottom' }} />
                    {error}
                </div>
            )}

            {/* List */}
            {loading ? (
                <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '24px' }}>Loading accounts...</div>
            ) : (
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
                    gap: '12px',
                    maxHeight: '400px',
                    overflowY: 'auto',
                    paddingRight: '4px' // for scrollbar
                }}>
                    {allAccounts.map(acc => (
                        <div
                            key={acc.id}
                            onClick={() => handleToggle(acc.id)}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                padding: '12px',
                                borderRadius: '12px',
                                backgroundColor: selectedIds.includes(acc.id) ? 'rgba(37, 99, 235, 0.1)' : 'rgba(255,255,255,0.03)',
                                border: selectedIds.includes(acc.id) ? '1px solid #3b82f6' : '1px solid var(--glass-border)',
                                cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                        >
                            <div style={{ color: selectedIds.includes(acc.id) ? '#3b82f6' : 'var(--text-secondary)' }}>
                                {selectedIds.includes(acc.id) ? <FiCheckSquare size={20} /> : <FiSquare size={20} />}
                            </div>
                            <div style={{ overflow: 'hidden' }}>
                                <div style={{ fontWeight: '500', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {acc.name}
                                </div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                    {acc.id}
                                </div>
                            </div>
                        </div>
                    ))}
                    {allAccounts.length === 0 && (
                        <div style={{ gridColumn: '1/-1', color: 'var(--text-secondary)', textAlign: 'center' }}>
                            {language === 'zh' ? '沒有可用的廣告帳號' : 'No ad accounts found.'}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default AdAccountSelector;
