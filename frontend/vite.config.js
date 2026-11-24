import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  // react-markdown 與其 unified / remark / rehype 生態系相依集中打包成單一 `markdown` chunk
  // （不能散落到多個共享 chunk，否則 lazy chunk 引用 shared chunk 遇到 hash 漂移會 import
  // 失敗 → 渲染壞掉）。Vite 8 起改用 Rolldown 的 codeSplitting（取代已棄用的 manualChunks）。
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            {
              name: 'markdown',
              test: /node_modules[\/](react-markdown|remark-gfm|rehype-raw|mdast|micromark|unist|hast|unified|bail|trough|vfile|character-entities)/,
            },
          ],
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
