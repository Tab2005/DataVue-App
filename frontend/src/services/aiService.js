/**
 * AI Service
 * Handles interactions with the backend AI endpoints.
 * 注意：串流端點（analyzeDataStream）因需要直接操作 ReadableStream，維持原生 fetch 實作。
 */

import apiClient from './apiClient';
import { getAuthToken } from '../utils/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const aiService = {
    /**
     * Test connection to AI Service
     */
    testConnection: async (apiKey = null) => {
        return apiClient.post('/ai/test-connection', { api_key: apiKey });
    },

    /**
     * Analyze Data Stream
     * 使用原生 fetch 以支援 SSE / ReadableStream 串流讀取。
     * @param {Object} data - The data to analyze
     * @param {string} context - Context string
     * @param {string} reportType - "ad_analysis" or "weekly_summary"
     * @param {string|null} apiKey - Optional BYOK
     * @param {function} onChunk - Callback for streaming chunks
     */
    analyzeDataStream: async (data, context, reportType = 'ad_analysis', apiKey = null, onChunk) => {
        try {
            const token = getAuthToken();
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
