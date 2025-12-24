/**
 * AI Service
 * Handles interactions with the backend AI endpoints.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const aiService = {
    /**
     * Test connection to AI Service
     */
    testConnection: async (apiKey = null) => {
        try {
            const token = localStorage.getItem('google_token');
            const res = await fetch(`${API_URL}/ai/test-connection`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ api_key: apiKey })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Connection failed');
            }

            return await res.json();
        } catch (error) {
            console.error('AI Test Failed:', error);
            throw error;
        }
    },

    /**
     * Analyze Data Stream
     * @param {Object} data - The data to analyze
     * @param {string} context - Context string
     * @param {string} reportType - "ad_analysis" or "weekly_summary"
     * @param {string|null} apiKey - Optional BYOK
     * @param {function} onChunk - Callback for streaming chunks
     */
    analyzeDataStream: async (data, context, reportType = 'ad_analysis', apiKey = null, onChunk) => {
        try {
            const token = localStorage.getItem('google_token');
            const res = await fetch(`${API_URL}/ai/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    data,
                    context,
                    api_key: apiKey,
                    report_type: reportType
                })
            });

            if (!res.ok) {
                throw new Error(`Analysis failed: ${res.statusText}`);
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                onChunk(chunk);
            }

        } catch (error) {
            console.error('Analysis Stream Error:', error);
            throw error;
        }
    }
};
