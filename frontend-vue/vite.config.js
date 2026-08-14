// frontend-vue/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 代理 /api 请求到后端 FastAPI 服务，解决跨域
      // 后端所有业务接口统一挂在 /api/* 下，这里原样转发、不做改写
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  build: {
    rollupOptions: {
      output: {
        // 将 echarts 拆分为独立 vendor 包，利于缓存与并行加载
        manualChunks: {
          echarts: ['echarts'],
        },
      },
    },
  },
})
