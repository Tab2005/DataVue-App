import React, { useState, useEffect } from 'react';
import { CONTENT_RULE_TYPES, isDefaultContentGroup } from '../utils/contentGroups';

/**
 * Modal for editing content type groups
 * Similar to SourceGroupModal but with rule-based filtering
 */
const ContentGroupModal = ({
    isOpen,
    onClose,
    onSave,
    onDelete,
    group,
    language,
    previewData,
    dimension
}) => {
    const t = (zh, en) => language === 'zh' ? zh : en;

    const [label_zh, setLabelZh] = useState('');
    const [label_en, setLabelEn] = useState('');
    const [rules, setRules] = useState([]);
    const [matchCount, setMatchCount] = useState(0);

    // Initialize form when group changes
    useEffect(() => {
        if (group) {
            setLabelZh(group.label_zh || '');
            setLabelEn(group.label_en || '');
            setRules(group.rules || [{ type: 'contains', value: '' }]);
        } else {
            // New group defaults
            setLabelZh('');
            setLabelEn('');
            setRules([{ type: 'contains', value: '' }]);
        }
    }, [group]);

    // Calculate match count for preview
    useEffect(() => {
        if (previewData && rules.length > 0) {
            const count = previewData.filter(row => {
                const dimValue = (row[dimension] || '').toLowerCase();
                return rules.some(rule => {
                    const pattern = (rule.value || '').toLowerCase();
                    if (!pattern) return false;
                    switch (rule.type) {
                        case 'contains': return dimValue.includes(pattern);
                        case 'startsWith': return dimValue.startsWith(pattern);
                        case 'endsWith': return dimValue.endsWith(pattern);
                        case 'equals': return dimValue === pattern;
                        default: return false;
                    }
                });
            }).length;
            setMatchCount(count);
        } else {
            setMatchCount(0);
        }
    }, [rules, previewData, dimension]);

    const handleAddRule = () => {
        setRules([...rules, { type: 'contains', value: '' }]);
    };

    const handleRemoveRule = (index) => {
        if (rules.length > 1) {
            setRules(rules.filter((_, i) => i !== index));
        }
    };

    const handleRuleChange = (index, field, value) => {
        const newRules = [...rules];
        newRules[index] = { ...newRules[index], [field]: value };
        setRules(newRules);
    };

    const handleSave = () => {
        if (!label_zh.trim() && !label_en.trim()) {
            alert(t('請輸入分組名稱', 'Please enter a group name'));
            return;
        }
        if (rules.every(r => !r.value.trim())) {
            alert(t('請至少輸入一個規則', 'Please enter at least one rule'));
            return;
        }

        const updatedGroup = {
            ...(group || {}),
            key: group?.key || `custom_${Date.now()}`,
            label_zh: label_zh.trim() || label_en.trim(),
            label_en: label_en.trim() || label_zh.trim(),
            rules: rules.filter(r => r.value.trim()),
            isDefault: group?.isDefault || false
        };

        onSave(updatedGroup);
        onClose();
    };

    const handleDelete = () => {
        if (window.confirm(t('確定要刪除此分組嗎？', 'Are you sure you want to delete this group?'))) {
            onDelete(group.key);
            onClose();
        }
    };

    if (!isOpen) return null;

    const isDefault = group?.isDefault || false;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
        }}>
            <div style={{
                background: 'var(--bg-primary, #1a1a2e)',
                borderRadius: '16px',
                padding: '24px',
                width: '90%',
                maxWidth: '500px',
                maxHeight: '80vh',
                overflow: 'auto',
                border: '1px solid var(--glass-border, rgba(255,255,255,0.1))'
            }}>
                {/* Header */}
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '20px'
                }}>
                    <h3 style={{ margin: 0, color: 'var(--text-primary, #fff)' }}>
                        {group ? t('編輯內容分組', 'Edit Content Group') : t('新增內容分組', 'Add Content Group')}
                    </h3>
                    <button
                        onClick={onClose}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-secondary)',
                            fontSize: '24px',
                            cursor: 'pointer'
                        }}
                    >
                        ×
                    </button>
                </div>

                {/* Group Name */}
                <div style={{ marginBottom: '16px' }}>
                    <label style={{
                        display: 'block',
                        marginBottom: '8px',
                        fontSize: '13px',
                        fontWeight: 600,
                        color: 'var(--text-secondary)'
                    }}>
                        {t('分組名稱（中文）', 'Group Name (Chinese)')}
                    </label>
                    <input
                        type="text"
                        value={label_zh}
                        onChange={(e) => setLabelZh(e.target.value)}
                        placeholder={t('例如: 商品頁', 'e.g., Product Pages')}
                        style={{
                            width: '100%',
                            padding: '10px 12px',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: 'var(--text-primary)',
                            fontSize: '14px'
                        }}
                    />
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <label style={{
                        display: 'block',
                        marginBottom: '8px',
                        fontSize: '13px',
                        fontWeight: 600,
                        color: 'var(--text-secondary)'
                    }}>
                        {t('分組名稱（英文）', 'Group Name (English)')}
                    </label>
                    <input
                        type="text"
                        value={label_en}
                        onChange={(e) => setLabelEn(e.target.value)}
                        placeholder="e.g., Product Pages"
                        style={{
                            width: '100%',
                            padding: '10px 12px',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            background: 'rgba(255, 255, 255, 0.05)',
                            color: 'var(--text-primary)',
                            fontSize: '14px'
                        }}
                    />
                </div>

                {/* Rules */}
                <div style={{ marginBottom: '16px' }}>
                    <label style={{
                        display: 'block',
                        marginBottom: '12px',
                        fontSize: '13px',
                        fontWeight: 600,
                        color: 'var(--text-secondary)'
                    }}>
                        📋 {t('篩選規則（符合任一條件）', 'Filter Rules (match any)')}
                    </label>

                    {rules.map((rule, index) => (
                        <div key={index} style={{
                            display: 'flex',
                            gap: '8px',
                            marginBottom: '8px',
                            alignItems: 'center'
                        }}>
                            <select
                                value={rule.type}
                                onChange={(e) => handleRuleChange(index, 'type', e.target.value)}
                                style={{
                                    width: '120px',
                                    padding: '10px 8px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    color: 'var(--text-primary)',
                                    fontSize: '13px'
                                }}
                            >
                                {CONTENT_RULE_TYPES.map(type => (
                                    <option key={type.key} value={type.key} style={{ color: 'black' }}>
                                        {language === 'zh' ? type.label_zh : type.label_en}
                                    </option>
                                ))}
                            </select>

                            <input
                                type="text"
                                value={rule.value}
                                onChange={(e) => handleRuleChange(index, 'value', e.target.value)}
                                placeholder={rule.type === 'startsWith' ? '/products/' : t('關鍵字', 'keyword')}
                                style={{
                                    flex: 1,
                                    padding: '10px 12px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    color: 'var(--text-primary)',
                                    fontSize: '14px'
                                }}
                            />

                            <button
                                onClick={() => handleRemoveRule(index)}
                                disabled={rules.length === 1}
                                style={{
                                    padding: '10px 12px',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    background: 'rgba(255, 255, 255, 0.05)',
                                    color: rules.length === 1 ? 'var(--text-disabled)' : '#ea4335',
                                    cursor: rules.length === 1 ? 'not-allowed' : 'pointer',
                                    fontSize: '14px'
                                }}
                            >
                                🗑️
                            </button>
                        </div>
                    ))}

                    <button
                        onClick={handleAddRule}
                        style={{
                            width: '100%',
                            padding: '10px',
                            border: '1px dashed var(--glass-border)',
                            borderRadius: '8px',
                            background: 'transparent',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer',
                            fontSize: '14px',
                            marginTop: '8px'
                        }}
                    >
                        ➕ {t('新增規則', 'Add Rule')}
                    </button>
                </div>

                {/* Preview */}
                <div style={{
                    padding: '12px',
                    background: 'rgba(52, 168, 83, 0.1)',
                    borderRadius: '8px',
                    marginBottom: '20px',
                    border: '1px solid rgba(52, 168, 83, 0.2)'
                }}>
                    <span style={{ color: '#34a853', fontSize: '14px' }}>
                        📊 {t(`預覽: 符合 ${matchCount} 個頁面`, `Preview: Matches ${matchCount} pages`)}
                    </span>
                </div>

                {/* Actions */}
                <div style={{
                    display: 'flex',
                    gap: '12px',
                    justifyContent: 'flex-end'
                }}>
                    {group && !isDefault && (
                        <button
                            onClick={handleDelete}
                            style={{
                                padding: '10px 20px',
                                border: '1px solid #ea4335',
                                borderRadius: '8px',
                                background: 'transparent',
                                color: '#ea4335',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            🗑️ {t('刪除', 'Delete')}
                        </button>
                    )}
                    <button
                        onClick={onClose}
                        style={{
                            padding: '10px 20px',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            background: 'transparent',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer',
                            fontSize: '14px'
                        }}
                    >
                        {t('取消', 'Cancel')}
                    </button>
                    <button
                        onClick={handleSave}
                        style={{
                            padding: '10px 20px',
                            border: 'none',
                            borderRadius: '8px',
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            cursor: 'pointer',
                            fontSize: '14px',
                            fontWeight: 600
                        }}
                    >
                        💾 {t('儲存', 'Save')}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ContentGroupModal;
