import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  // 強制把 react-markdown + 插件預打包進 entry chunk（不能拆出共享 chunk，
  // 否則 lazy chunk 引用 shared chunk 時遇到 hash 漂移會 import 失敗 → 渲染壞掉）。
  // 做法：用 manualChunks 把 react-markdown 與所有 plugin 歸到 entry chunk（空字串函式
  // 會回傳 undefined → Vite 把它放進 entry chunk），同時 optimizeDeps 預熱依賴。
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (
            id.includes('node_modules/react-markdown') ||
            id.includes('node_modules/remark-gfm') ||
            id.includes('node_modules/rehype-raw') ||
            id.includes('node_modules/mdast') ||
            id.includes('node_modules/micromark') ||
            id.includes('node_modules/unist') ||
            id.includes('node_modules/hast') ||
            id.includes('node_modules/unified') ||
            id.includes('node_modules/bail') ||
            id.includes('node_modules/trough') ||
            id.includes('node_modules/vfile') ||
            id.includes('node_modules/character-entities')
          ) {
            return ''; // → merge into entry chunk
          }
        },
      },
    },
  },
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
