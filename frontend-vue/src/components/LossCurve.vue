<!--
  LossCurve.vue —— 训练损失曲线（ECharts 双折线）
  - 训练(青) / 验证(洋红)，图例 + 端点数值，hover 十字线
-->
<template>
  <EChart :option="option" height="100%" style="min-height: 160px" />
</template>

<script setup>
import { computed } from 'vue'
import EChart from '@/components/EChart.vue'

const props = defineProps({
  train: { type: Array, default: () => [] },
  val: { type: Array, default: () => [] },
})

const option = computed(() => {
  const n = Math.min(props.train.length, props.val.length)
  const epochs = Array.from({ length: n }, (_, i) => i + 1)
  const train = props.train.slice(0, n)
  const val = props.val.slice(0, n)

  const lastEpoch = epochs.length ? epochs[epochs.length - 1] : 0

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#0d2247' } },
      formatter: (params) => {
        let s = `<b style="color:#00d8ff">Epoch ${params[0].axisValue}</b><br/>`
        for (const p of params) {
          s += `<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${p.color};margin-right:6px"></span>`
          s += `${p.seriesName} <b style="font-family:Consolas">${p.value.toFixed(4)}</b><br/>`
        }
        return s
      },
    },
    legend: { top: 0, right: 0 },
    grid: { left: 44, right: 16, top: 30, bottom: 22 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: epochs,
      axisLabel: { interval: Math.max(1, Math.floor(lastEpoch / 5)), formatter: '{value}' },
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitLine: { show: true },
    },
    series: [
      {
        name: '训练损失 Train',
        type: 'line',
        data: train,
        showSymbol: false,
        smooth: 0.2,
        lineStyle: { width: 2, color: '#00d8ff', shadowBlur: 6, shadowColor: '#00d8ff88' },
        itemStyle: { color: '#00d8ff' },
      },
      {
        name: '验证损失 Val',
        type: 'line',
        data: val,
        showSymbol: false,
        smooth: 0.2,
        lineStyle: { width: 2, color: '#c7548c', shadowBlur: 6, shadowColor: '#c7548c88' },
        itemStyle: { color: '#c7548c' },
      },
    ],
  }
})
</script>
