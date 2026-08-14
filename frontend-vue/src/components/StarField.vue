<!--
  StarField.vue
  动态星空粒子背景：Canvas 绘制缓慢漂移的星辰 + 偶发流星，
  外加两层 CSS 星云光晕。整体克制、不抢图表（透明度较低）。
-->
<template>
  <div class="starfield" aria-hidden="true">
    <div class="nebula nebula-1"></div>
    <div class="nebula nebula-2"></div>
    <canvas ref="canvasEl"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const canvasEl = ref(null)
let ctx = null
let rafId = 0
let stars = []
let meteors = []
let w = 0
let h = 0
let dpr = 1

function resize() {
  const canvas = canvasEl.value
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  w = canvas.clientWidth
  h = canvas.clientHeight
  canvas.width = w * dpr
  canvas.height = h * dpr
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  initStars()
}

function initStars() {
  const count = Math.min(160, Math.floor((w * h) / 9000))
  stars = Array.from({ length: count }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    r: Math.random() * 1.3 + 0.3,
    baseA: Math.random() * 0.4 + 0.15,
    speed: Math.random() * 0.12 + 0.03, // 缓慢下移
    twinkle: Math.random() * Math.PI * 2, // 闪烁相位
    twinkleSpeed: Math.random() * 0.02 + 0.005,
    cyan: Math.random() < 0.35, // 部分星辰偏青
  }))
}

function spawnMeteor() {
  meteors.push({
    x: Math.random() * w * 0.9,
    y: Math.random() * h * 0.3,
    len: Math.random() * 90 + 60,
    speed: Math.random() * 6 + 4,
    life: 1,
    vx: -0.55, // 左上 → 右下
    vy: 0.4,
  })
}

function draw() {
  ctx.clearRect(0, 0, w, h)

  // 星辰
  for (const s of stars) {
    s.twinkle += s.twinkleSpeed
    const alpha = s.baseA * (0.6 + 0.4 * Math.sin(s.twinkle))
    ctx.beginPath()
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2)
    ctx.fillStyle = s.cyan
      ? `rgba(120, 235, 255, ${alpha})`
      : `rgba(200, 225, 255, ${alpha})`
    ctx.fill()

    // 缓慢漂移，触底回顶
    s.y += s.speed
    if (s.y > h + 2) s.y = -2
  }

  // 流星
  meteors = meteors.filter((m) => m.life > 0 && m.x > -m.len && m.y < h + 40)
  for (const m of meteors) {
    m.x += m.vx * m.speed
    m.y += m.vy * m.speed
    m.life -= 0.012
    const grad = ctx.createLinearGradient(m.x, m.y, m.x + m.len * m.vx, m.y + m.len * m.vy)
    grad.addColorStop(0, `rgba(0, 216, 255, ${0.5 * m.life})`)
    grad.addColorStop(1, 'rgba(0, 216, 255, 0)')
    ctx.strokeStyle = grad
    ctx.lineWidth = 1.4
    ctx.beginPath()
    ctx.moveTo(m.x, m.y)
    ctx.lineTo(m.x + m.len * m.vx, m.y + m.len * m.vy)
    ctx.stroke()
  }

  rafId = requestAnimationFrame(draw)
}

function loop() {
  draw()
  // 平均每 6 秒划一颗流星
  if (Math.random() < 1 / 360) spawnMeteor()
}

onMounted(() => {
  ctx = canvasEl.value.getContext('2d')
  resize()
  window.addEventListener('resize', resize)
  loop()
})

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  window.removeEventListener('resize', resize)
})
</script>

<style lang="scss" scoped>
.starfield {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;

  canvas {
    width: 100%;
    height: 100%;
    display: block;
  }

  .nebula {
    position: absolute;
    border-radius: 50%;
    filter: blur(90px);
    pointer-events: none;
  }
  .nebula-1 {
    width: 60vw;
    height: 60vw;
    left: -18vw;
    top: -22vw;
    background: var(--bg-nebula-1);
    animation: floaty 18s ease-in-out infinite;
  }
  .nebula-2 {
    width: 46vw;
    height: 46vw;
    right: -12vw;
    bottom: -18vw;
    background: var(--bg-nebula-2);
    animation: floaty 22s ease-in-out infinite reverse;
  }
}
</style>
