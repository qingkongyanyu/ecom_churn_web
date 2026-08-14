// frontend-vue/src/utils/echarts.js
// ECharts 按需引入 + 科技暗色主题注册（全项目图表共用）
import * as echarts from 'echarts/core'
import { PieChart, BarChart, LineChart, GaugeChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  GraphicComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  PieChart,
  BarChart,
  LineChart,
  GaugeChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  GraphicComponent,
  CanvasRenderer,
])

// 科技暗色主题：深蓝 + 荧光青（与全局大屏主题保持一致）
echarts.registerTheme('tech-dark', {
  backgroundColor: 'transparent',
  color: ['#00d8ff', '#3d7bff', '#c7548c', '#c98200', '#8f7ad9', '#cf3d4d'],

  textStyle: { color: '#9fc6ec', fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif' },

  title: {
    textStyle: { color: '#e6f6ff', fontWeight: 600 },
    subtextStyle: { color: '#5f7fa8' },
  },

  legend: {
    textStyle: { color: '#9fc6ec', fontSize: 12 },
    itemWidth: 12,
    itemHeight: 8,
    itemGap: 18,
    inactiveColor: '#3a4a66',
  },

  tooltip: {
    backgroundColor: 'rgba(7, 15, 36, 0.95)',
    borderColor: 'rgba(0, 216, 255, 0.4)',
    borderWidth: 1,
    textStyle: { color: '#e6f6ff', fontSize: 12 },
    padding: [8, 12],
    extraCssText: 'box-shadow:0 0 12px rgba(0,216,255,0.25);border-radius:6px;',
  },

  axisLine: { lineStyle: { color: 'rgba(0,216,255,0.25)' } },
  axisTick: { lineStyle: { color: 'rgba(0,216,255,0.25)' } },
  axisLabel: { color: '#5f7fa8', fontSize: 11 },
  splitLine: { lineStyle: { color: 'rgba(0,216,255,0.07)' } },
  splitArea: { areaStyle: { color: 'rgba(0,216,255,0.02)' } },
})

export default echarts
