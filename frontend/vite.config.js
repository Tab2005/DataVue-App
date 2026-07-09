import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  // 強制把 react-markdown 預打包進 entry chunk，避免 lazy chunk 引用
  // 共享 chunk 時遭遇 hash 漂移導致 import 失敗（任務 2.3 follow-up）。
  optimizeDeps: {
    include: ['react-markdown', 'remark-gfm', 'rehype-raw'],
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setupTests.js',
    globals: true,
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
