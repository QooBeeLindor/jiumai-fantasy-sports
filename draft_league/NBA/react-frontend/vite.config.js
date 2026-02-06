import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/NBA/draftleague/',  // ⭐ 添加这行！子目录路径
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5003',  // ✅ 已经是5003，不用改
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
