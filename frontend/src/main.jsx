import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import './index.css'
import App from './App.jsx'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 請求失敗自動重試 1 次（排除 4xx 錯誤）
      retry: (failureCount, error) => {
        if (error?.statusCode >= 400 && error?.statusCode < 500) return false;
        return failureCount < 1;
      },
      // 視窗重新聚焦時重新取得（若資料超過 5 分鐘）
      staleTime: 5 * 60 * 1000,
      // 快取保留 10 分鐘
      gcTime: 10 * 60 * 1000,
    },
    mutations: {
      // 突變失敗不自動重試
      retry: false,
    },
  },
});

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  </StrictMode>,
)
