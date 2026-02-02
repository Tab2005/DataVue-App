/**
 * Content Groups Management Utilities
 * Similar to sourceGroups.js but for content type filtering
 */

// Rule types for content filtering
export const CONTENT_RULE_TYPES = [
    { key: 'contains', label_zh: '包含關鍵字', label_en: 'Contains Keyword' },
    { key: 'pathContains', label_zh: '路徑包含', label_en: 'Path Contains' },
    { key: 'startsWith', label_zh: '路徑開頭', label_en: 'Starts With' },
    { key: 'endsWith', label_zh: '路徑結尾', label_en: 'Ends With' },
    { key: 'equals', label_zh: '完全符合', label_en: 'Equals' }
];

// Default content groups (editable but not deletable)
export const DEFAULT_CONTENT_GROUPS = [
    {
        key: 'group_product',
        label_zh: '商品頁',
        label_en: 'Product Pages',
        isDefault: true,
        rules: [
            { type: 'startsWith', value: '/products/' },
            { type: 'startsWith', value: '/product/' },
            { type: 'startsWith', value: '/shop/' },
            { type: 'contains', value: 'product' },
            { type: 'contains', value: 'item' },
            { type: 'contains', value: '商品' }
        ]
    },
    {
        key: 'group_article',
        label_zh: '文章頁',
        label_en: 'Article Pages',
        isDefault: true,
        rules: [
            { type: 'startsWith', value: '/blog/' },
            { type: 'startsWith', value: '/article/' },
            { type: 'startsWith', value: '/articles/' },
            { type: 'startsWith', value: '/post/' },
            { type: 'startsWith', value: '/news/' },
            { type: 'contains', value: 'blog' },
            { type: 'contains', value: 'article' },
            { type: 'contains', value: '文章' }
        ]
    }
];

/**
 * Get localStorage key for content groups
 */
function getStorageKey(propertyId) {
    return `ga4_content_groups_${propertyId}`;
}

/**
 * Get default groups with any user modifications
 */
function getModifiedDefaultGroups(propertyId) {
    const storageKey = `ga4_content_groups_defaults_${propertyId}`;
    const stored = localStorage.getItem(storageKey);
    if (stored) {
        try {
            return JSON.parse(stored);
        } catch (e) {
            console.error('Error parsing modified default groups:', e);
        }
    }
    return DEFAULT_CONTENT_GROUPS;
}

/**
 * Save modified default group
 */
export function saveModifiedDefaultGroup(propertyId, group) {
    const storageKey = `ga4_content_groups_defaults_${propertyId}`;
    const defaults = getModifiedDefaultGroups(propertyId);
    const index = defaults.findIndex(g => g.key === group.key);
    if (index >= 0) {
        defaults[index] = { ...group, isDefault: true };
        localStorage.setItem(storageKey, JSON.stringify(defaults));
    }
}

/**
 * Get custom content groups from localStorage
 */
function getCustomGroups(propertyId) {
    const storageKey = getStorageKey(propertyId);
    const stored = localStorage.getItem(storageKey);
    if (stored) {
        try {
            return JSON.parse(stored);
        } catch (e) {
            console.error('Error parsing custom content groups:', e);
        }
    }
    return [];
}

/**
 * Get all content groups (defaults + custom)
 */
export function getAllContentGroups(propertyId) {
    const defaults = getModifiedDefaultGroups(propertyId);
    const custom = getCustomGroups(propertyId);
    return [...defaults, ...custom];
}

/**
 * Save a custom content group
 */
export function saveCustomContentGroup(propertyId, group) {
    // Check if it's a default group
    if (group.isDefault) {
        saveModifiedDefaultGroup(propertyId, group);
        return;
    }

    const custom = getCustomGroups(propertyId);
    const existingIndex = custom.findIndex(g => g.key === group.key);

    if (existingIndex >= 0) {
        // Update existing
        custom[existingIndex] = group;
    } else {
        // Add new with unique key
        const newGroup = {
            ...group,
            key: group.key || `custom_${Date.now()}`,
            isDefault: false
        };
        custom.push(newGroup);
    }

    localStorage.setItem(getStorageKey(propertyId), JSON.stringify(custom));
}

/**
 * Delete a custom content group
 */
export function deleteCustomContentGroup(propertyId, groupKey) {
    const custom = getCustomGroups(propertyId);
    const filtered = custom.filter(g => g.key !== groupKey);
    localStorage.setItem(getStorageKey(propertyId), JSON.stringify(filtered));
}

/**
 * Check if a group is a default group
 */
export function isDefaultContentGroup(groupKey) {
    return DEFAULT_CONTENT_GROUPS.some(g => g.key === groupKey);
}

/**
 * Check if a value matches a rule
 */
function matchesRule(value, rule) {
    const lowerValue = (value || '').toLowerCase();
    const lowerPattern = (rule.value || '').toLowerCase();

    switch (rule.type) {
        case 'contains':
        case 'pathContains':
            return lowerValue.includes(lowerPattern);
        case 'startsWith':
            return lowerValue.startsWith(lowerPattern);
        case 'endsWith':
            return lowerValue.endsWith(lowerPattern);
        case 'equals':
            return lowerValue === lowerPattern;
        default:
            return false;
    }
}

/**
 * Filter rows by content group rules
 */
export function filterByContentGroup(rows, group, dimension) {
    if (!group || !group.rules || group.rules.length === 0) {
        return rows;
    }

    return rows.filter(row => {
        const dimValue = row[dimension] || '';
        // Match if ANY rule matches (OR logic)
        return group.rules.some(rule => matchesRule(dimValue, rule));
    });
}

/**
 * Count matching rows for preview
 */
export function countMatchingRows(rows, group, dimension) {
    return filterByContentGroup(rows, group, dimension).length;
}
