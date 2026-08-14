<!--
  Ticker.vue
  底部信息跑马灯：模型指标 + 经营洞察无缝横向滚动。
  内容克隆一份实现无缝循环；hover 暂停。
-->
<template>
  <div class="ticker">
    <div class="badge">运营洞察</div>
    <div class="track" @mouseenter="paused = true" @mouseleave="paused = false">
      <div class="content" :class="{ paused }">
        <span v-for="(item, i) in doubled" :key="i" class="item">
          <i class="ic" :class="'k-' + item.kind">{{ iconOf(item.kind) }}</i>
          <span class="txt">{{ item.text }}</span>
          <span class="sep">✦</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] }, // [{ kind, text }]
})

const paused = defineModel({ type: Boolean, default: false })
const doubled = computed(() => {
  const a = props.items.map((it) => ({ ...it }))
  const b = props.items.map((it) => ({ ...it }))
  return [...a, ...b]
})

function iconOf(kind) {
  return { up: '▲', down: '▼', info: '◇', model: '▣' }[kind] || '◇'
}
</script>

<style lang="scss" scoped>
.ticker {
  display: flex;
  align-items: center;
  gap: 14px;
  height: 44px;
  padding: 0 18px;
  background: linear-gradient(90deg, rgba(9, 22, 52, 0.85), rgba(5, 12, 30, 0.85));
  border: 1px solid rgba(0, 216, 255, 0.2);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 0 16px rgba(0, 216, 255, 0.08);

  .badge {
    flex: none;
    font-size: 12px;
    color: #061018;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
    background: linear-gradient(120deg, var(--cyan), var(--blue));
    box-shadow: var(--glow-cyan-sm);
    letter-spacing: 2px;
  }

  .track {
    flex: 1;
    overflow: hidden;
    mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent);
    -webkit-mask-image: linear-gradient(90deg, transparent, #000 4%, #000 96%, transparent);
  }
  .content {
    display: flex;
    align-items: center;
    gap: 8px;
    width: max-content;
    animation: ticker 40s linear infinite;
    &.paused {
      animation-play-state: paused;
    }
  }
  .item {
    display: flex;
    align-items: center;
    gap: 7px;
    white-space: nowrap;
    font-size: 13px;
    color: var(--ink-2);
    .ic {
      font-style: normal;
      color: var(--cyan);
      font-size: 11px;
      text-shadow: var(--glow-cyan-sm);
    }
    .k-up { color: var(--status-critical); }
    .k-down { color: var(--status-good); }
    .k-info { color: var(--cyan); }
    .k-model { color: var(--cat-amber); }
    .txt {
      color: var(--ink-2);
    }
    .sep {
      color: var(--ink-3);
      font-size: 9px;
      margin: 0 10px;
    }
  }
}
</style>
