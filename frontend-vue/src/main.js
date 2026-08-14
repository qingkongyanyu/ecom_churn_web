// frontend-vue/src/main.js
import { createApp } from 'vue'
import App from './App.vue'
// 全局主题样式只在这里导入一次（组件内直接使用 CSS 变量）
import '@/style/global.scss'

createApp(App).mount('#app')
