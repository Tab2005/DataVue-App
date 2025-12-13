import React, { useState } from 'react';
import { FiX, FiUsers } from 'react-icons/fi';
import { TeamService } from '../services/teamService';

const CreateTeamModal = ({ isOpen, onClose, onTeamCreated, language }) => {
    const [teamName, setTeamName] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const newTeam = await TeamService.createTeam(teamName);
            onTeamCreated(newTeam);
            onClose();
        } catch (err) {
            console.error(err);
            setError(err.message || 'Failed to create team');
        } finally {
            setLoading(false);
        }
    };

    const t = {
        title: language === 'zh' ? '建立新團隊' : 'Create New Team',
        label: language === 'zh' ? '團隊名稱' : 'Team Name',
        placeholder: language === 'zh' ? '例如: 行銷部 A 組' : 'e.g. Marketing Team A',
        cancel: language === 'zh' ? '取消' : 'Cancel',
        submit: language === 'zh' ? '建立' : 'Create',
        creating: language === 'zh' ? '建立中...' : 'Creating...',
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
                width: '400px',
                padding: '24px',
                borderRadius: '12px',
                border: '1px solid var(--glass-border)',
                position: 'relative'
            }}>
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute', top: '16px', right: '16px',
                        background: 'transparent', border: 'none',
                        color: 'var(--text-secondary)', cursor: 'pointer'
                    }}
                >
                    <FiX size={24} />
                </button>

                <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px', fontSize: '1.5rem' }}>
                    <FiUsers />
                    {t.title}
                </h2>

                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                            {t.label}
                        </label>
                        <input
                            type="text"
                            value={teamName}
                            onChange={(e) => setTeamName(e.target.value)}
                            placeholder={t.placeholder}
                            style={{
                                width: '100%',
                                padding: '10px',
                                borderRadius: '6px',
                                border: '1px solid var(--glass-border)',
                                background: 'rgba(255,255,255,0.05)',
                                color: 'white',
                                fontSize: '1rem',
                                outline: 'none'
                            }}
                            required
                        />
                    </div>

                    {error && (
                        <div style={{ color: '#ef4444', marginBottom: '16px', fontSize: '0.9rem' }}>
                            {error}
                        </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                        <button
                            type="button"
                            onClick={onClose}
                            style={{
                                padding: '8px 16px',
                                borderRadius: '6px',
                                background: 'transparent',
                                border: '1px solid var(--glass-border)',
                                color: 'var(--text-secondary)',
                                cursor: 'pointer'
                            }}
                        >
                            {t.cancel}
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            style={{
                                padding: '8px 24px',
                                borderRadius: '6px',
                                background: 'var(--accent-primary)',
                                border: 'none',
                                color: 'white',
                                cursor: loading ? 'not-allowed' : 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            {loading ? t.creating : t.submit}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreateTeamModal;
