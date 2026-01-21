/**
 * Source Groups Utility
 * 管理來源分組（預設 + 用戶自定義）
 * 依 GA4 Property 儲存，不同網站可有不同分組
 */

// 預設分組（不可刪除）
export const DEFAULT_SOURCE_GROUPS = [
    {
        key: 'group_facebook',
        label_zh: '📁 Facebook (集合)',
        label_en: '📁 Facebook (Group)',
        patterns: ['facebook', 'fb', 'meta.com'],
        isDefault: true
    },
    {
        key: 'group_google',
        label_zh: '📁 Google (集合)',
        label_en: '📁 Google (Group)',
        patterns: ['google', 'googleapis', 'goo.gl'],
        isDefault: true
    },
    {
        key: 'group_instagram',
        label_zh: '📁 Instagram (集合)',
        label_en: '📁 Instagram (Group)',
        patterns: ['instagram', 'ig', 'l.instagram'],
        isDefault: true
    },
    {
        key: 'group_line',
        label_zh: '📁 LINE (集合)',
        label_en: '📁 LINE (Group)',
        patterns: ['line', 'lin.ee'],
        isDefault: true
    },
    {
        key: 'group_threads',
        label_zh: '📁 Threads (集合)',
        label_en: '📁 Threads (Group)',
        patterns: ['threads', 'l.threads'],
        isDefault: true
    },
    {
        key: 'group_bing',
        label_zh: '📁 Bing (集合)',
        label_en: '📁 Bing (Group)',
        patterns: ['bing', 'cn.bing'],
        isDefault: true
    },
    {
        key: 'group_yahoo',
        label_zh: '📁 Yahoo (集合)',
        label_en: '📁 Yahoo (Group)',
        patterns: ['yahoo'],
        isDefault: true
    },
    {
        key: 'group_ai',
        label_zh: '🤖 AI 流量 (集合)',
        label_en: '🤖 AI Traffic (Group)',
        patterns: ['chatgpt', 'openai', 'gemini', 'claude', 'anthropic', 'copilot', 'perplexity', 'bard', 'you.com', 'phind', 'poe.com'],
        isDefault: true
    }
];

/**
 * 取得 LocalStorage Key（依 Property 區分）
 */
const getStorageKey = (propertyId) => {
    return `source_groups_${propertyId}`;
};

/**
 * 取得已儲存的預設分組覆寫
 * (用戶可以編輯預設分組，編輯結果會儲存在這裡)
 */
const getDefaultGroupOverrides = (propertyId) => {
    if (!propertyId) return {};
    try {
        const stored = localStorage.getItem(`source_groups_defaults_${propertyId}`);
        return stored ? JSON.parse(stored) : {};
    } catch (e) {
        console.error('Error reading default group overrides:', e);
        return {};
    }
};

/**
 * 儲存預設分組覆寫
 */
const saveDefaultGroupOverrides = (propertyId, overrides) => {
    if (!propertyId) return;
    try {
        localStorage.setItem(`source_groups_defaults_${propertyId}`, JSON.stringify(overrides));
    } catch (e) {
        console.error('Error saving default group overrides:', e);
    }
};

/**
 * 取得用戶自定義分組
 */
export const getCustomGroups = (propertyId) => {
    if (!propertyId) return [];

    try {
        const stored = localStorage.getItem(getStorageKey(propertyId));
        return stored ? JSON.parse(stored) : [];
    } catch (e) {
        console.error('Error reading custom source groups:', e);
        return [];
    }
};

/**
 * 儲存用戶自定義分組
 */
const saveCustomGroups = (propertyId, groups) => {
    if (!propertyId) return;

    try {
        localStorage.setItem(getStorageKey(propertyId), JSON.stringify(groups));
    } catch (e) {
        console.error('Error saving custom source groups:', e);
    }
};

/**
 * 取得所有分組（預設 + 自定義）
 * 預設分組會套用用戶的覆寫設定
 */
export const getAllSourceGroups = (propertyId) => {
    const overrides = getDefaultGroupOverrides(propertyId);
    const customGroups = getCustomGroups(propertyId);

    // 合併預設分組與覆寫設定
    const mergedDefaults = DEFAULT_SOURCE_GROUPS.map(group => {
        if (overrides[group.key]) {
            return {
                ...group,
                ...overrides[group.key],
                isDefault: true, // 強制保持 isDefault 標記
                key: group.key   // 強制保持原始 key
            };
        }
        return group;
    });

    return [...mergedDefaults, ...customGroups];
};

/**
 * 新增自定義分組
 * @returns 新建的分組完整物件
 */
export const addCustomGroup = (propertyId, name, nameEn, patterns) => {
    if (!propertyId || !name || !patterns || patterns.length === 0) {
        throw new Error('Invalid group data');
    }

    const customGroups = getCustomGroups(propertyId);

    // 產生唯一 key
    const key = `custom_${Date.now()}`;

    const newGroup = {
        key,
        label_zh: `⭐ ${name}`,
        label_en: `⭐ ${nameEn || name}`,
        patterns: patterns.map(p => p.trim().toLowerCase()).filter(Boolean),
        isDefault: false,
        createdAt: new Date().toISOString()
    };

    customGroups.push(newGroup);
    saveCustomGroups(propertyId, customGroups);

    return newGroup;
};

/**
 * 更新分組（支援自定義與預設分組）
 * 預設分組的編輯會儲存為覆寫
 */
export const updateCustomGroup = (propertyId, key, name, nameEn, patterns) => {
    if (!propertyId || !key || !name || !patterns) {
        throw new Error('Invalid group data');
    }

    const isDefault = DEFAULT_SOURCE_GROUPS.some(g => g.key === key);

    if (isDefault) {
        // 預設分組：儲存為覆寫
        const overrides = getDefaultGroupOverrides(propertyId);
        overrides[key] = {
            label_zh: `📁 ${name}`,
            label_en: `📁 ${nameEn || name} (Group)`,
            patterns: patterns.map(p => p.trim().toLowerCase()).filter(Boolean),
            updatedAt: new Date().toISOString()
        };
        saveDefaultGroupOverrides(propertyId, overrides);
        return { ...DEFAULT_SOURCE_GROUPS.find(g => g.key === key), ...overrides[key], isDefault: true };
    }

    // 自定義分組：原有邏輯
    const customGroups = getCustomGroups(propertyId);
    const index = customGroups.findIndex(g => g.key === key);

    if (index === -1) {
        throw new Error('Group not found');
    }

    customGroups[index] = {
        ...customGroups[index],
        label_zh: `⭐ ${name}`,
        label_en: `⭐ ${nameEn || name}`,
        patterns: patterns.map(p => p.trim().toLowerCase()).filter(Boolean),
        updatedAt: new Date().toISOString()
    };

    saveCustomGroups(propertyId, customGroups);
    return customGroups[index];
};

/**
 * 刪除自定義分組
 */
export const deleteCustomGroup = (propertyId, key) => {
    if (!propertyId || !key) return false;

    // 不允許刪除預設分組
    if (DEFAULT_SOURCE_GROUPS.some(g => g.key === key)) {
        throw new Error('Cannot delete default groups');
    }

    const customGroups = getCustomGroups(propertyId);
    const filtered = customGroups.filter(g => g.key !== key);

    if (filtered.length === customGroups.length) {
        return false; // 沒有找到要刪除的分組
    }

    saveCustomGroups(propertyId, filtered);
    return true;
};

/**
 * 檢查分組是否為預設分組
 */
export const isDefaultGroup = (key) => {
    return DEFAULT_SOURCE_GROUPS.some(g => g.key === key);
};

/**
 * 重置預設分組到原始狀態（移除用戶覆寫）
 */
export const resetDefaultGroup = (propertyId, key) => {
    if (!propertyId || !key) return false;
    if (!isDefaultGroup(key)) return false;

    const overrides = getDefaultGroupOverrides(propertyId);
    if (overrides[key]) {
        delete overrides[key];
        saveDefaultGroupOverrides(propertyId, overrides);
        return true;
    }
    return false;
};
