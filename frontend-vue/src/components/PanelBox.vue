<!--
  PanelBox.vue
  大屏通用面板容器：
    - 青色发光描边 + 四角括弧装饰
    - 顶部一条流光反复扫过（线条流光扫边）
    - 内部一缕极淡的纵向扫描线（不抢内容）
    - 标题栏带发光小圆点与分隔线
-->
<template>
  <section class="panel">
    <i class="corner tl"></i>
    <i class="corner tr"></i>
    <i class="corner bl"></i>
    <i class="corner br"></i>

    <header v-if="title" class="panel-head">
      <span class="dot" :style="titleColor ? { background: titleColor, boxShadow: `0 0 8px ${titleColor}` } : {}"></span>
      <h3 class="title">{{ title }}</h3>
      <span v-if="subtitle" class="sub">{{ subtitle }}</span>
      <span class="line"></span>
    </header>

    <div class="panel-body" :class="{ scroll: scrollable }">
      <slot></slot>
    </div>

    <!-- 顶部流光 -->
    <div class="flow"></div>
    <!-- 纵向扫描线 -->
    <div class="scan"></div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  titleColor: { type: String, default: '' },
  scrollable: { type: Boolean, default: false },
})
</script>

<style lang="scss" scoped>
.panel {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 16px rgba(0, 216, 255, 0.12), inset 0 0 30px rgba(0, 216, 255, 0.03);

  &:hover {
    box-shadow: 0 0 24px rgba(0, 216, 255, 0.2), inset 0 0 34px rgba(0, 216, 255, 0.05);
  }

  /* 四角括弧 */
  .corner {
    position: absolute;
    width: 16px;
    height: 16px;
    border-color: var(--border-strong);
    border-style: solid;
    z-index: 2;
    pointer-events: none;
  }
  .tl { top: -1px; left: -1px; border-width: 2px 0 0 2px; border-radius: 6px 0 0 0; }
  .tr { top: -1px; right: -1px; border-width: 2px 2px 0 0; border-radius: 0 6px 0 0; }
  .bl { bottom: -1px; left: -1px; border-width: 0 0 2px 2px; border-radius: 0 0 0 6px; }
  .br { bottom: -1px; right: -1px; border-width: 0 2px 2px 0; border-radius: 0 0 6px 0; }

  /* 顶部流光 */
  .flow {
    position: absolute;
    top: 0;
    left: 0;
    width: 33%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(0, 216, 255, 0.9), transparent);
    filter: drop-shadow(0 0 4px var(--cyan));
    z-index: 2;
    animation: sweep 4.5s ease-in-out infinite;
    pointer-events: none;
  }

  /* 纵向扫描线（极淡） */
  .scan {
    position: absolute;
    left: 0;
    width: 100%;
    height: 22%;
    background: linear-gradient(180deg, transparent, rgba(0, 216, 255, 0.045), transparent);
    animation: scanline 7s linear infinite;
    pointer-events: none;
    z-index: 1;
  }
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px 10px;
  border-bottom: 1px solid rgba(0, 216, 255, 0.12);

  .dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--cyan);
    box-shadow: 0 0 8px var(--cyan);
    flex: none;
  }
  .title {
    font-size: 15px;
    font-weight: 600;
    color: var(--ink-1);
    letter-spacing: 1px;
    white-space: nowrap;
  }
  .sub {
    font-size: 12px;
    color: var(--ink-3);
    white-space: nowrap;
  }
  .line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
    margin-left: 4px;
  }
}

.panel-body {
  flex: 1;
  padding: 14px 16px;
  min-height: 0;
  position: relative;
  z-index: 1;
  &.scroll {
    overflow-y: auto;
    overflow-x: hidden;
  }
}
</style>
