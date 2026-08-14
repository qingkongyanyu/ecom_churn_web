// frontend-vue/src/api/request.js
import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api', // 由 Vite 代理转发到后端 8000 端口
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器：统一处理错误
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    console.error('API 请求错误:', msg)
    return Promise.reject(new Error(msg))
  }
)

// ---------- 大屏数据接口 ----------
/** 获取大屏聚合统计（一次返回 overview/dimensions/correlations/insights/metrics） */
export function getDashboardData() {
  return request.get('/dashboard')
}

/** 调用流失预测接口 */
export function predictChurn(payload) {
  return request.post('/predict', payload)
}

export default request
