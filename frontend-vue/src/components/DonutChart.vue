<!--
  DonutChart.vue —— 设备占比环形图（ECharts）
  - 分类色按固定顺序分配（已验证 CVD 安全）
  - 中心显示总量，下方图例，hover 浮层显示数量/占比
-->
<template>
  <EChart :option="option" height="100%" style="min-height: 180px" />
</template>

<script setup>
import { computed } from 'vue'
import EChart from '@/components/EChart.vue'

const props = defineProps({
  data: { type: Array, default: () => [] }, // [{ label, value }]
  centerLabel: { type: String, default: '总量' },
  centerValue: { type: [String, Number], default: 0 },
})

// 分类色固定顺序（暗色面板验证通过）
const CAT = ['#00a2b5', '#3d7bff', '#c7548c', '#c98200', '#8f7ad9', '#cf3d4d']

const option = computed(() => {
  const total = props.data.reduce((s, d) => s + Number(d.value || 0), 0)
  const pieData = props.data.map((d, i) => ({
    name: d.label,
    value: Number(d.value || 0),
    itemStyle: { color: CAT[i % CAT.length] },
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) =>
        `<b style="color:#00d8ff">${p.name}</b><br/>` +
        `用户数 ${p.value} 人（${p.percent}%）`,
    },
    legend: {
      bottom: 0,
      icon: 'roundRect',
    },
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '34%',
        style: {
          text: String(props.centerValue || total),
          fill: '#e6f6ff',
          fontSize: 28,
          fontWeight: 700,
          fontFamily: 'Consolas, monospace',
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '48%',
        style: {
          text: props.centerLabel,
          fill: '#5f7fa8',
          fontSize: 12,
          letterSpacing: 2,
        },
      },
    ],
    series: [
      {
        type: 'pie',
        radius: ['48%', '70%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        label: { show: false },
        labelLine: { show: false },
        itemStyle: {
          borderColor: '#0a1736',
          borderWidth: 2,
        },
        emphasis: {
          scaleSize: 6,
          itemStyle: {
            shadowBlur: 14,
            shadowColor: 'rgba(0,216,255,0.6)',
          },
        },
        data: pieData,
      },
    ],
  }
})
</script>
