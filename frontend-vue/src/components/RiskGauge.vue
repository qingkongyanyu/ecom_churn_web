<!--
  RiskGauge.vue —— 中心流失风险仪表盘（ECharts Gauge）
  - 240° 弧形进度，按流失概率填充，颜色随风险等级变化
  - 数值呼吸光晕（CSS）+ 单层装饰环，保留大屏科技感
-->
<template>
  <div class="gauge" :style="{ '--gauge-color': color }">
    <i class="ring"></i>
    <EChart :option="option" height="100%" style="min-height: 260px" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import EChart from '@/components/EChart.vue'

const props = defineProps({
  value: { type: Number, default: 0.5 },
  color: { type: String, default: '#00d8ff' },
  riskText: { type: String, default: '' },
})

function clamp01(v) {
  return Math.max(0, Math.min(1, Number(v) || 0))
}

const option = computed(() => {
  const val = clamp01(props.value) * 100
  return {
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30, // 240° 弧（顶部开口，缺口在底部）
        min: 0,
        max: 100,
        radius: '92%',
        center: ['50%', '56%'],
        pointer: { show: false },
        progress: {
          show: true,
          width: 16,
          roundCap: true,
          itemStyle: {
            color: props.color,
            shadowColor: props.color,
            shadowBlur: 16,
          },
        },
        axisLine: {
          lineStyle: { width: 16, color: [[1, 'rgba(120,170,230,0.14)']] },
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          distance: 22,
          color: '#5f7fa8',
          fontSize: 10,
          fontFamily: 'Consolas, monospace',
          formatter: (v) => (v % 25 === 0 ? v : ''),
        },
        anchor: { show: false },
        title: {
          show: true,
          offsetCenter: [0, '40%'],
          color: '#9fc6ec',
          fontSize: 14,
          letterSpacing: 3,
          formatter: props.riskText || '流失风险概率',
        },
        detail: {
          valueAnimation: true,
          formatter: (v) => v.toFixed(1) + '%',
          color: props.color,
          fontSize: 46,
          fontWeight: 700,
          fontFamily: 'Consolas, monospace',
          offsetCenter: [0, '-6%'],
        },
        data: [{ value: +val.toFixed(2) }],
      },
    ],
  }
})
</script>

<style lang="scss" scoped>
.gauge {
  position: relative;
  width: 100%;
  height: 100%;

  .ring {
    position: absolute;
    left: 50%;
    top: 52%;
    width: 82%;
    max-width: 340px;
    aspect-ratio: 1;
    transform: translate(-50%, -50%);
    border: 1px dashed rgba(0, 216, 255, 0.35);
    border-radius: 50%;
    pointer-events: none;
    animation: spin 40s linear infinite;

    &::before,
    &::after {
      content: '';
      position: absolute;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--cyan);
      box-shadow: 0 0 10px var(--cyan);
    }
    &::before {
      top: -4px;
      left: 50%;
      transform: translateX(-50%);
    }
    &::after {
      bottom: 12%;
      right: 4%;
      width: 5px;
      height: 5px;
      opacity: 0.7;
    }
  }

  /* 数值呼吸光晕 */
  :deep(.echart-wrap canvas) {
    animation: breathe 4s ease-in-out infinite;
    filter: drop-shadow(0 0 16px var(--gauge-color));
  }
}
</style>
