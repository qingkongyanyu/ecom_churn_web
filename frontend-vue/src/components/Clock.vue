<!--
  Clock.vue
  大屏实时时钟：HH:MM:SS + 中文日期，每秒刷新。
-->
<template>
  <div class="clock">
    <div class="time num">{{ time }}</div>
    <div class="date">{{ date }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const WEEK = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const time = ref('--:--:--')
const date = ref('')

let timer = null
function tick() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  time.value = `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
  date.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${WEEK[d.getDay()]}`
}

onMounted(() => {
  tick()
  timer = setInterval(tick, 1000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<style lang="scss" scoped>
.clock {
  text-align: right;
  .time {
    font-size: 26px;
    font-weight: 700;
    color: var(--cyan);
    text-shadow: var(--glow-cyan-sm);
    letter-spacing: 2px;
  }
  .date {
    font-size: 13px;
    color: var(--ink-3);
    letter-spacing: 1px;
    margin-top: 2px;
  }
}
</style>
