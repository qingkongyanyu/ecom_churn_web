<!--
  HBars.vue —— 横向条形图（流失率高低，ECharts）
  - 顺序编码：单一青色阶，值越高颜色越深
  - hover 浮层显示样本数 / 流失数
-->
<template>
  <EChart :option="option" height="100%" style="min-height: 170px" />
</template>

<script setup>
import { computed } from 'vue'
import EChart from '@/components/EChart.vue'

const props = defineProps({
  items: { type: Array, default: () => [] }, // [{ label, rate, count, churn }]
  sort: { type: Boolean, default: true },
})

const RAMP = ['#37f4ff', '#00d8ff', '#00b0e0', '#0088c6', '#0060a8', '#004088']

function colorFor(rate) {
  const idx = Math.max(0, Math.min(5, Math.round(rate * 5)))
  return RAMP[idx]
}

const option = computed(() => {
  const arr = [...props.items]
  if (props.sort) arr.sort((a, b) => b.rate - a.rate)
  // 从上到下显示流失率由高到低
  const rows = arr.slice().reverse()

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const it = rows[params[0].dataIndex]
        return (
          `<b style="color:#00d8ff">${it.label}</b><br/>` +
          `流失率 ${(it.rate * 100).toFixed(1)}%<br/>` +
          `样本数 ${it.count} 人 · 流失 ${it.churn} 人`
        )
      },
    },
    grid: { left: 62, right: 44, top: 6, bottom: 18 },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { formatter: '{value}%' },
      splitLine: { show: true },
    },
    yAxis: {
      type: 'category',
      data: rows.map((r) => r.label),
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        barWidth: 11,
        data: rows.map((r) => ({
          value: +(r.rate * 100).toFixed(2),
          itemStyle: {
            color: colorFor(r.rate),
            borderRadius: [0, 4, 4, 0],
            shadowBlur: 8,
            shadowColor: colorFor(r.rate) + '88',
          },
        })),
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          color: '#9fc6ec',
          fontSize: 11,
          fontWeight: 600,
          fontFamily: 'Consolas, monospace',
        },
      },
    ],
  }
})
</script>
