import { DATE_PRESETS } from './constants';

// Helper function to format date to YYYY-MM-DD (local time)
export const formatDate = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
};

// Helper function to calculate date range from preset (aligned with GA4)
export const getDateRangeFromPreset = (presetKey) => {
    const today = new Date();
    const preset = DATE_PRESETS.find(p => p.key === presetKey);

    if (!preset) {
        // Default fallback
        const start = new Date();
        start.setDate(today.getDate() - 30);
        return { start: formatDate(start), end: formatDate(today) };
    }

    // Today
    if (preset.isToday) {
        return { start: formatDate(today), end: formatDate(today) };
    }

    // Yesterday
    if (preset.isYesterday) {
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        return { start: formatDate(yesterday), end: formatDate(yesterday) };
    }

    // This Week (Monday to today)
    if (preset.isThisWeek) {
        const dayOfWeek = today.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        const monday = new Date(today);
        monday.setDate(monday.getDate() - daysToMonday);
        return { start: formatDate(monday), end: formatDate(today) };
    }

    // Last Week (Last Monday to Last Sunday)
    if (preset.isLastWeek) {
        const dayOfWeek = today.getDay();
        const daysToLastSunday = dayOfWeek === 0 ? 7 : dayOfWeek;
        const lastSunday = new Date(today);
        lastSunday.setDate(lastSunday.getDate() - daysToLastSunday);
        const lastMonday = new Date(lastSunday);
        lastMonday.setDate(lastMonday.getDate() - 6);
        return { start: formatDate(lastMonday), end: formatDate(lastSunday) };
    }

    // This Month (1st to last day of current month)
    if (preset.isThisMonth) {
        const firstOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
        const lastOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        return { start: formatDate(firstOfMonth), end: formatDate(lastOfMonth) };
    }

    // Last Month (1st to last day of previous month)
    if (preset.isLastMonth) {
        const firstOfLastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
        const lastOfLastMonth = new Date(today.getFullYear(), today.getMonth(), 0);
        return { start: formatDate(firstOfLastMonth), end: formatDate(lastOfLastMonth) };
    }

    // Custom or null days - return current range or default
    if (preset.days === null) {
        const start = new Date();
        start.setDate(today.getDate() - 30);
        return { start: formatDate(start), end: formatDate(today) };
    }

    // For "last X days" presets (complete days, not including today)
    // e.g., "Last 7 days" = 7 complete days before today = (today-7) to (today-1)
    const end = new Date(today);
    end.setDate(today.getDate() - 1);  // Yesterday
    const start = new Date(today);
    start.setDate(today.getDate() - preset.days);  // X days before today
    return { start: formatDate(start), end: formatDate(end) };
};


// Helper: Extract main keyword for grouping (first significant word)
export const extractGroupKey = (query) => {
    if (!query) return '';
    // Remove common suffixes/prefixes and get the main topic
    const words = query.trim().toLowerCase().split(/\s+/);
    // Get first 2 significant words for grouping
    const significantWords = words.filter(w => w.length > 1).slice(0, 2);
    return significantWords.join(' ') || query;
};

// Helper: Detect primary language of a string
export const detectLanguage = (str) => {
    const chineseChars = (str.match(/[\u4e00-\u9fa5]/g) || []).length;
    const englishChars = (str.match(/[a-zA-Z]/g) || []).length;

    if (chineseChars > englishChars) return 'chinese';
    if (englishChars > chineseChars) return 'english';
    return 'mixed';
};

// Helper: N-gram similarity (better for Chinese)
export const ngramSimilarity = (str1, str2, n = 2) => {
    const s1 = str1.toLowerCase().replace(/\s+/g, '');
    const s2 = str2.toLowerCase().replace(/\s+/g, '');

    if (s1.length < n || s2.length < n) {
        // Fallback to character overlap for very short strings
        const chars1 = new Set(s1.split(''));
        const chars2 = new Set(s2.split(''));
        const intersection = [...chars1].filter(c => chars2.has(c));
        const union = new Set([...chars1, ...chars2]);
        return union.size > 0 ? intersection.length / union.size : 0;
    }

    const getNgrams = (s) => {
        const ngrams = new Set();
        for (let i = 0; i <= s.length - n; i++) {
            ngrams.add(s.substring(i, i + n));
        }
        return ngrams;
    };

    const ngrams1 = getNgrams(s1);
    const ngrams2 = getNgrams(s2);
    const intersection = [...ngrams1].filter(ng => ngrams2.has(ng));
    const union = new Set([...ngrams1, ...ngrams2]);

    return union.size > 0 ? intersection.length / union.size : 0;
};

// Helper: Word-split similarity (better for English)
export const wordSimilarity = (str1, str2) => {
    const s1 = str1.toLowerCase();
    const s2 = str2.toLowerCase();

    const words1 = new Set(s1.split(/\s+/).filter(w => w.length > 0));
    const words2 = new Set(s2.split(/\s+/).filter(w => w.length > 0));
    const intersection = [...words1].filter(w => words2.has(w));
    const union = new Set([...words1, ...words2]);

    return union.size > 0 ? intersection.length / union.size : 0;
};

// Helper: Adaptive similarity - uses optimal algorithm based on language
export const getSimilarity = (str1, str2) => {
    const s1 = str1.toLowerCase();
    const s2 = str2.toLowerCase();

    // Quick check: if one contains the other, they're highly similar
    if (s1.includes(s2) || s2.includes(s1)) return 0.8;

    const lang1 = detectLanguage(str1);
    const lang2 = detectLanguage(str2);

    // Both Chinese → use N-gram (optimal for Chinese)
    if (lang1 === 'chinese' && lang2 === 'chinese') {
        return ngramSimilarity(str1, str2);
    }

    // Both English → use word-split (optimal for English)
    if (lang1 === 'english' && lang2 === 'english') {
        return wordSimilarity(str1, str2);
    }

    // Mixed languages → average of both methods
    return (ngramSimilarity(str1, str2) + wordSimilarity(str1, str2)) / 2;
};

// Helper: Extract a readable title from URL path
export const getTitleFromUrl = (url) => {
    if (!url) return '';
    try {
        // Decode URL-encoded characters
        const decoded = decodeURIComponent(url);
        // Get the last path segment
        const path = decoded.replace(/^https?:\/\/[^/]+/, '');
        const segments = path.split('/').filter(s => s.length > 0);
        const lastSegment = segments[segments.length - 1] || '';

        // Remove file extension if any
        const withoutExt = lastSegment.replace(/\.(html?|php|aspx?)$/i, '');

        // Convert slug format to title case (handles both - and _ separators)
        const title = withoutExt
            .replace(/[-_]/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());

        return title || path;
    } catch {
        // Fallback: just use the URL
        return url.replace(/^https?:\/\/[^/]+/, '');
    }
};

export const escapeCSV = (value) => {
    if (value === null || value === undefined) return '';
    const result = String(value).replace(/"/g, '""');
    return result.includes('"') || result.includes(',') || result.includes('\n')
        ? `"${result}"`
        : result;
};

export const downloadCSV = (rows, filename) => {
    const csvContent = '\uFEFF' + rows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

