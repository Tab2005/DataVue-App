// frontend/src/components/Reports/ReportGA4PropertySelector.jsx
import React, { useState, useEffect } from 'react';
import { ga4Service } from '../../services/ga4Service';
import { FiSearch, FiAlertCircle, FiLoader, FiChevronDown, FiCheckCircle } from 'react-icons/fi';

/**
 * 報表專用的 GA4 屬性選擇器 (單選模式)
 */
const ReportGA4PropertySelector = ({ selectedId, onSelect, language }) => {
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [isOpen, setIsOpen] = useState(false);

    const t = (en, zh) => (language === 'zh' ? zh : en);

    const selectedProperty = properties.find(p => p.property_id === selectedId);

    useEffect(() => {
        const fetchProperties = async () => {
            setLoading(true);
            try {
                const propertyList = await ga4Service.getProperties();
                setProperties(propertyList || []);
            } catch (err) {
                console.error("Failed to fetch GA4 properties for reports", err);
                setError(t('Failed to load GA4 properties', '無法載入 GA4 資源'));
            } finally {
                setLoading(false);
            }
        };
        fetchProperties();
    }, []);

    const filteredProperties = properties.filter(prop => 
        (prop.display_name || '').toLowerCase().includes(searchTerm.toLowerCase()) || 
        prop.property_id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return (
        <div style={{ padding: '12px', color: 'var(--text-secondary)' }}>
            <FiLoader className="spin" /> {t('Loading properties...', '正在載入資源...')}
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
                    color: selectedProperty ? 'var(--text-primary)' : 'var(--text-tertiary)',
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
                        backgroundColor: selectedProperty ? '#10b981' : 'var(--text-tertiary)',
                        flexShrink: 0
                    }} />
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: selectedProperty ? '600' : 'normal' }}>
                        {selectedProperty 
                            ? `${selectedProperty.display_name}` 
                            : t('Select a GA4 Property...', '請選擇 GA4 資源...')}
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
                                placeholder={t('Search...', '搜尋 GA4 資源名稱或 ID...')}
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
                        {filteredProperties.map(prop => (
                            <div
                                key={prop.property_id}
                                onClick={() => {
                                    onSelect(prop.property_id, prop.display_name);
                                    setIsOpen(false);
                                }}
                                style={{
                                    padding: '10px 14px',
                                    cursor: 'pointer',
                                    borderRadius: '8px',
                                    marginBottom: '2px',
                                    backgroundColor: prop.property_id === selectedId ? 'rgba(45, 136, 255, 0.15)' : 'transparent',
                                    transition: 'all 0.15s'
                                }}
                                onMouseEnter={(e) => {
                                    if (prop.property_id !== selectedId) e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.05)';
                                }}
                                onMouseLeave={(e) => {
                                    if (prop.property_id !== selectedId) e.currentTarget.style.backgroundColor = 'transparent';
                                }}
                            >
                                <div style={{ 
                                    color: prop.property_id === selectedId ? 'var(--accent-primary)' : 'var(--text-primary)',
                                    fontWeight: prop.property_id === selectedId ? '600' : '500',
                                    fontSize: '0.95rem',
                                    marginBottom: '2px'
                                }}>
                                    {prop.display_name}
                                </div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', display: 'flex', justifyContent: 'space-between' }}>
                                    <span>ID: {prop.property_id}</span>
                                    {prop.property_id === selectedId && <FiCheckCircle color="var(--accent-primary)" style={{ marginLeft: '4px' }} />}
                                </div>
                            </div>
                        ))}
                        {filteredProperties.length === 0 && (
                            <div style={{ padding: '30px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                                <FiSearch size={24} style={{ marginBottom: '8px', opacity: 0.3 }} />
                                <div>{t('No results found.', '找不到相符的資源')}</div>
                            </div>
                        )}
                    </div>
                </div>
            )}
            
            {/* Click outside to close */}
            {isOpen && (
                <div 
                    style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 999 }} 
                    onClick={() => setIsOpen(false)}
                />
            )}
        </div>
    );
};

export default ReportGA4PropertySelector;
