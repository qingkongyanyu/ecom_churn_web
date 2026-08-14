<!--
  StatTile.vue
  核心指标卡片：图标 + 标签 + 大数值 + 底部小字。
  大数值为等宽字体，hover 时边框发亮。
-->
<template>
  <div class="tile" :style="{ '--tile-accent': accent }">
    <div class="tile-head">
      <span class="tile-icon" :style="{ color: accent, borderColor: accent + '55', boxShadow: `0 0 10px ${accent}33` }">{{ icon }}</span>
      <span class="tile-label">{{ label }}</span>
    </div>
    <div class="tile-value num" :style="{ color: accent }">{{ value }}</div>
    <div class="tile-foot">{{ sub }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  value: { type: [String, Number], default: 0 },
  sub: { type: String, default: '' },
  icon: { type: String, default: '◆' },
  accent: { type: String, default: '#00d8ff' },
})
</script>

<style lang="scss" scoped>
.tile {
  background: linear-gradient(160deg, rgba(16, 38, 84, 0.55), rgba(9, 20, 46, 0.4));
  border: 1px solid rgba(0, 216, 255, 0.18);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;

  &:hover {
    transform: translateY(-2px);
    border-color: var(--border-strong);
    box-shadow: 0 6px 18px rgba(0, 216, 255, 0.18);
  }

  .tile-head {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .tile-icon {
    width: 22px;
    height: 22px;
    display: grid;
    place-items: center;
    font-size: 12px;
    border: 1px solid;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.02);
  }
  .tile-label {
    font-size: 13px;
    color: var(--ink-2);
    letter-spacing: 1px;
  }
  .tile-value {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.1;
    text-shadow: 0 0 14px var(--tile-accent);
    letter-spacing: 1px;
  }
  .tile-foot {
    font-size: 12px;
    color: var(--ink-3);
    letter-spacing: 0.5px;
  }
}
</style>
