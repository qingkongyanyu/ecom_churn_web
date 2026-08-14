<!--
  EChart.vue
  通用 ECharts 封装：初始化 / 更新 option / 窗口自适应 / 卸载销毁。
  全项目图表统一走这里，保证生命周期与主题一致。
-->
<template>
  <div ref="el" class="echart-wrap" :style="{ height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import echarts from '@/utils/echarts'

const props = defineProps({
  option: { type: Object, default: () => ({}) },
  theme: { type: String, default: 'tech-dark' },
  height: { type: String, default: '100%' },
})

const el = ref(null)
let chart = null

function resize() {
  chart && chart.resize()
}

onMounted(() => {
  chart = echarts.init(el.value, props.theme)
  chart.setOption(props.option)
  window.addEventListener('resize', resize)
  // 容器尺寸变化（如面板 flex 变化）也自适应
  if (typeof ResizeObserver !== 'undefined') {
    chart.__ro = new ResizeObserver(() => resize())
    chart.__ro.observe(el.value)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  if (chart) {
    chart.__ro && chart.__ro.disconnect()
    chart.dispose()
    chart = null
  }
})

watch(
  () => props.option,
  (opt) => {
    if (chart) chart.setOption(opt)
  },
  { deep: true }
)
</script>

<style lang="scss" scoped>
.echart-wrap {
  width: 100%;
  min-height: 140px;
}
</style>
