<!--
  DivergingBars.vue —— 特征 × 流失 相关性发散条形图（ECharts）
  - 正相关（推高流失）= 风险红；负相关（保护留存）= 荧光青
  - 0 为中性轴线；hover 浮层显示流失/留存均值对比
-->
<template>
  <EChart :option="option" height="100%" style="min-height: 200px" />
</template>

<script setup>
import { computed } from 'vue'
import EChart from '@/components/EChart.vue'

const props = defineProps({
  items: { type: Array, default: () => [] }, // [{ feature, label, corr, mean_retain, mean_churn }]
  limit: { type: Number, default: 8 },
})

const option = computed(() => {
  const sorted = [...props.items]
    .sort((a, b) => Math.abs(b.corr) - Math.abs(a.corr))
    .slice(0, props.limit)
  // 从上到下显示 |corr| 由高到低
  const rows = sorted.slice().reverse()

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const it = rows[params[0].dataIndex]
        const fmt = (v) => (v === undefined || v === null ? '—' : Number(v).toLocaleString())
        return (
          `<b style="color:#00d8ff">${it.label}</b><br/>` +
          `相关性 <b>${it.corr >= 0 ? '+' : ''}${it.corr.toFixed(3)}</b><br/>` +
          `留存均值 ${fmt(it.mean_retain)}<br/>` +
          `流失均值 ${fmt(it.mean_churn)}`
        )
      },
    },
    grid: { left: 74, right: 50, top: 6, bottom: 18 },
    xAxis: {
      type: 'value',
      min: -1,
      max: 1,
      axisLabel: { formatter: (v) => v.toFixed(1) },
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
          value: r.corr,
          itemStyle: {
            color:
              r.corr >= 0
                ? {
                    type: 'linear',
                    x: 0, y: 0, x2: 1, y2: 0,
                    colorStops: [
                      { offset: 0, color: 'rgba(255,61,110,0.25)' },
                      { offset: 1, color: '#ff3d6e' },
                    ],
                  }
                : {
                    type: 'linear',
                    x: 0, y: 0, x2: 1, y2: 0,
                    colorStops: [
                      { offset: 0, color: '#00d8ff' },
                      { offset: 1, color: 'rgba(0,216,255,0.25)' },
                    ],
                  },
            borderRadius:
              r.corr >= 0 ? [0, 4, 4, 0] : [4, 0, 0, 4],
            shadowBlur: 8,
            shadowColor: r.corr >= 0 ? 'rgba(255,61,110,0.5)' : 'rgba(0,216,255,0.5)',
          },
        })),
        label: {
          show: true,
          position: 'right',
          formatter: (p) => (p.value >= 0 ? '+' : '') + p.value.toFixed(2),
          color: '#9fc6ec',
          fontSize: 11,
          fontFamily: 'Consolas, monospace',
        },
      },
    ],
  }
})
</script>
