<!--
  Dashboard.vue —— 电商用户流失预测 · 数据可视化大屏（主视图）

  布局：
    ┌─────────────────────────────────────────────────────────┐
    │  顶栏：模型指标徽章  |  居中标题（流光装饰翼）  |  实时时钟   │
    ├──────────────┬──────────────────────────────┬───────────┤
    │ 左列          │         中列                 │ 右列       │
    │ · 核心运营指标 │ · 流失风险仪表盘（呼吸光晕）    │ · 渠道流失率 │
    │ · 设备占比     │ · 用户风险预测表单（实时推理）  │ · 特征相关性 │
    │ · 年龄段流失率 │                              │ · 训练监控   │
    ├──────────────┴──────────────────────────────┴───────────┤
    │  底部跑马灯：模型指标 + 经营洞察                          │
    └─────────────────────────────────────────────────────────┘
-->
<template>
  <div class="dash">
    <StarField />

    <div class="dash-inner">
      <!-- ============ 顶栏 ============ -->
      <header class="dash-header">
        <div class="h-left">
          <div class="chip"><i class="c-cyan"></i>准确率 <b class="num">{{ metrics.accuracy ? (metrics.accuracy * 100).toFixed(2) + '%' : '—' }}</b></div>
          <div class="chip"><i class="c-magenta"></i>AUC <b class="num">{{ metrics.auc ? metrics.auc.toFixed(3) : '—' }}</b></div>
        </div>

        <div class="h-center">
          <div class="title-row">
            <div class="wing"><i class="diamond"></i></div>
            <h1 class="title">电商用户流失预测<span class="title-sub">· 数据可视化大屏</span></h1>
            <div class="wing"><i class="diamond"></i></div>
          </div>
          <p class="tagline">ANN-MLP 深度学习模型 · 实时风险评估系统</p>
        </div>

        <div class="h-right">
          <Clock />
        </div>
      </header>

      <!-- ============ 主体 ============ -->
      <main class="dash-main">
        <!-- 左列 -->
        <div class="col col-left">
          <PanelBox title="核心运营指标" subtitle="总样本 500 条">
            <div class="kpi-grid">
              <StatTile label="用户总数" :value="overview.total_users ?? '—'" sub="ALL USERS" icon="◈" accent="#00d8ff" />
              <StatTile label="留存用户" :value="overview.retain_count ?? '—'" sub="RETAINED" icon="◉" accent="#00e676" />
              <StatTile label="流失用户" :value="overview.churn_count ?? '—'" sub="CHURNED" icon="◯" accent="#ff3d6e" />
              <StatTile label="流失率" :value="pct(overview.churn_rate)" sub="CHURN RATE" icon="◆" accent="#ffb300" />
            </div>
          </PanelBox>

          <PanelBox title="设备占比" subtitle="用户分布">
            <DonutChart
              :data="deviceData"
              center-label="用户数"
              :center-value="overview.total_users ?? 0"
            />
          </PanelBox>

          <PanelBox title="年龄段流失率" subtitle="流失率由高到低">
            <HBars :items="ageItems" />
          </PanelBox>
        </div>

        <!-- 中列 -->
        <div class="col col-center">
          <div class="hero">
            <RiskGauge :value="gauge.value" :color="gauge.color" :risk-text="gauge.riskText" />
          </div>

          <PanelBox title="用户风险预测" subtitle="ANN-MLP 实时推理" scrollable>
            <div v-if="hasPrediction" class="result-strip">
              <span class="rs-label">最近预测</span>
              <span class="rs-chip" :style="{ color: gauge.color, borderColor: gauge.color + '88', boxShadow: `0 0 10px ${gauge.color}44` }">
                {{ gauge.riskText }}
              </span>
              <span class="rs-val num" :style="{ color: gauge.color }">{{ (gauge.value * 100).toFixed(1) }}%</span>
              <span class="rs-hint">再次预测即更新仪表盘</span>
            </div>
            <PredictForm @predicted="onPredicted" @error="onError" />
          </PanelBox>
        </div>

        <!-- 右列 -->
        <div class="col col-right">
          <PanelBox title="渠道来源流失率" subtitle="按流失率排序">
            <HBars :items="sourceItems" />
          </PanelBox>

          <PanelBox title="特征相关性洞察" subtitle="数值特征 × 流失">
            <DivergingBars :items="correlations" :limit="8" />
          </PanelBox>

          <PanelBox title="模型训练监控" subtitle="BCE 损失曲线">
            <LossCurve v-if="lossTrain.length" :train="lossTrain" :val="lossVal" />
            <div v-else class="placeholder">尚未训练，请先运行 <code>python core/train.py</code></div>
          </PanelBox>
        </div>
      </main>

      <!-- ============ 底部跑马灯 ============ -->
      <footer class="dash-footer">
        <Ticker :items="tickerItems" />
      </footer>
    </div>

    <!-- 轻提示 -->
    <transition name="fade">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getDashboardData } from '@/api/request'
import StarField from '@/components/StarField.vue'
import Clock from '@/components/Clock.vue'
import PanelBox from '@/components/PanelBox.vue'
import StatTile from '@/components/StatTile.vue'
import DonutChart from '@/components/DonutChart.vue'
import HBars from '@/components/HBars.vue'
import DivergingBars from '@/components/DivergingBars.vue'
import RiskGauge from '@/components/RiskGauge.vue'
import LossCurve from '@/components/LossCurve.vue'
import Ticker from '@/components/Ticker.vue'
import PredictForm from '@/components/PredictForm.vue'

// ---------- 状态 ----------
const overview = reactive({ total_users: null, retain_count: null, churn_count: null, churn_rate: null })
const dimensions = ref([]) // [{ dimension, label, items: [{value,count,churn,rate}] }]
const correlations = ref([])
const insights = ref([])
const metrics = reactive({})

// 中心仪表盘
const gauge = reactive({
  value: 0,
  color: '#00d8ff',
  riskText: '数据集基线流失率',
})
const hasPrediction = ref(false)
const toast = ref('')

// 后端返回的颜色 key -> 大屏状态色
const COLOR_MAP = {
  green: '#00e676',
  orange: '#ffb300',
  red: '#ff3d6e',
}

const pct = (v) => (v === null || v === undefined ? '—' : (v * 100).toFixed(1) + '%')

// ---------- 数据加载 ----------
onMounted(async () => {
  try {
    const d = await getDashboardData()
    Object.assign(overview, d.overview)
    dimensions.value = d.dimensions
    correlations.value = d.correlations
    insights.value = d.insights
    Object.assign(metrics, d.metrics)
    // 中心仪表盘默认展示数据集基线流失率
    gauge.value = d.overview.churn_rate
    gauge.color = '#00d8ff'
    gauge.riskText = '数据集基线流失率'
  } catch (e) {
    onError('统计数据加载失败：' + e.message)
  }
})

// ---------- 维度数据派生 ----------
function dimByName(name) {
  return dimensions.value.find((x) => x.dimension === name)
}

const deviceData = computed(() => {
  const d = dimByName('device')
  return d ? d.items.map((i) => ({ label: i.value, value: i.count })) : []
})

const ageItems = computed(() => {
  const d = dimByName('age_range')
  return d ? d.items.map((i) => ({ label: i.value, rate: i.rate, count: i.count, churn: i.churn })) : []
})

const sourceItems = computed(() => {
  const d = dimByName('source')
  return d ? d.items.map((i) => ({ label: i.value, rate: i.rate, count: i.count, churn: i.churn })) : []
})

const lossTrain = computed(() => metrics.loss_curve?.train || [])
const lossVal = computed(() => metrics.loss_curve?.val || [])

// ---------- 跑马灯内容 ----------
const tickerItems = computed(() => {
  const list = []
  if (metrics.accuracy != null) {
    list.push({ kind: 'model', text: `模型准确率 ${(metrics.accuracy * 100).toFixed(2)}% · AUC ${metrics.auc?.toFixed(3)} · 最佳轮次 Epoch ${metrics.best_epoch}` })
  }
  insights.value.forEach((ins) => {
    const rate = ins.rate != null ? `，流失率 ${(ins.rate * 100).toFixed(1)}%` : ''
    list.push({ kind: ins.kind, text: `${ins.title}｜${ins.desc}${rate}` })
  })
  return list
})

// ---------- 预测回调 ----------
function onPredicted(res) {
  gauge.value = res.prob
  gauge.color = COLOR_MAP[res.color] || '#00d8ff'
  gauge.riskText = res.riskLevel
  hasPrediction.value = true
}

// ---------- 轻提示 ----------
let toastTimer = null
function onError(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 3000)
}
</script>

<style lang="scss" scoped>
.dash {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 100vh;
  overflow: auto;
  background:
    radial-gradient(1200px 600px at 50% -10%, rgba(20, 60, 160, 0.18), transparent 60%),
    var(--bg-page);
}

.dash-inner {
  position: relative;
  z-index: 1;
  height: 100vh;
  min-height: 720px;
  display: flex;
  flex-direction: column;
}

/* ---------- 顶栏 ---------- */
.dash-header {
  flex: none;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  padding: 16px 20px 12px;
  gap: 16px;

  .h-left {
    display: flex;
    gap: 10px;
    .chip {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: var(--ink-2);
      padding: 5px 12px;
      border: 1px solid rgba(0, 216, 255, 0.2);
      border-radius: 999px;
      background: rgba(9, 22, 52, 0.5);
      b {
        color: var(--ink-1);
        font-size: 14px;
      }
      i {
        width: 8px;
        height: 8px;
        border-radius: 50%;
      }
      .c-cyan { background: var(--cyan); box-shadow: 0 0 8px var(--cyan); }
      .c-magenta { background: var(--cat-magenta); box-shadow: 0 0 8px var(--cat-magenta); }
    }
  }

  .h-center {
    text-align: center;
    .title-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 14px;
    }
    .title {
      font-size: 30px;
      font-weight: 700;
      letter-spacing: 4px;
      background: linear-gradient(90deg, #7be9ff, #00d8ff 45%, #3d7bff);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      filter: drop-shadow(0 0 12px rgba(0, 216, 255, 0.35));
      white-space: nowrap;
      .title-sub {
        font-size: 18px;
        font-weight: 500;
        letter-spacing: 3px;
        margin-left: 6px;
      }
    }
    .wing {
      width: 120px;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--cyan));
      position: relative;
      &:last-child {
        background: linear-gradient(90deg, var(--cyan), transparent);
      }
      .diamond {
        position: absolute;
        top: -3px;
        width: 6px;
        height: 6px;
        background: var(--cyan);
        transform: rotate(45deg);
        box-shadow: 0 0 8px var(--cyan);
      }
      &:first-child .diamond { right: -2px; }
      &:last-child .diamond { left: -2px; }
    }
    .tagline {
      margin-top: 6px;
      font-size: 12px;
      color: var(--ink-3);
      letter-spacing: 3px;
    }
  }

  .h-right {
    display: flex;
    justify-content: flex-end;
  }
}

/* ---------- 主体 ---------- */
.dash-main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1.12fr 1fr;
  gap: 14px;
  padding: 0 20px 12px;
}

.col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;

  :deep(.panel) {
    flex: 1;
    min-height: 0;
  }
}

.col-center {
  .hero {
    flex: 1.25;
    min-height: 0;
    display: grid;
    place-items: center;
    position: relative;

    &::after {
      /* 中心图形外层呼吸光圈 */
      content: '';
      position: absolute;
      width: 72%;
      aspect-ratio: 1;
      border-radius: 50%;
      border: 1px solid rgba(0, 216, 255, 0.18);
      animation: breathe 5s ease-in-out infinite;
      pointer-events: none;
    }
  }
  :deep(.panel) {
    flex: 1;
    min-height: 0;
  }
}

/* KPI 网格 */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  height: 100%;
}

/* 结果条 */
.result-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding: 8px 12px;
  border: 1px solid rgba(0, 216, 255, 0.16);
  border-radius: 8px;
  background: rgba(0, 216, 255, 0.04);
  font-size: 13px;

  .rs-label {
    color: var(--ink-3);
    letter-spacing: 1px;
  }
  .rs-chip {
    padding: 2px 10px;
    border: 1px solid;
    border-radius: 999px;
    font-weight: 600;
    font-size: 13px;
  }
  .rs-val {
    font-size: 18px;
    font-weight: 700;
  }
  .rs-hint {
    margin-left: auto;
    font-size: 11px;
    color: var(--ink-3);
  }
}

.placeholder {
  display: grid;
  place-items: center;
  height: 100%;
  color: var(--ink-3);
  font-size: 13px;
  code {
    color: var(--cyan);
    background: rgba(0, 216, 255, 0.08);
    padding: 1px 6px;
    border-radius: 4px;
  }
}

/* ---------- 底部 ---------- */
.dash-footer {
  flex: none;
  padding: 0 20px 16px;
}

/* ---------- 轻提示 ---------- */
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 60;
  padding: 10px 22px;
  background: rgba(255, 61, 110, 0.14);
  border: 1px solid rgba(255, 61, 110, 0.5);
  color: #ff9db4;
  border-radius: 8px;
  font-size: 14px;
  box-shadow: 0 0 20px rgba(255, 61, 110, 0.3);
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ---------- 响应式 ---------- */
@media (max-width: 1380px) {
  .dash-inner {
    height: auto;
    min-height: 100vh;
  }
  .dash-main {
    grid-template-columns: 1fr;
  }
  .col {
    min-height: 0;
  }
}
@media (max-width: 760px) {
  .dash-header {
    grid-template-columns: 1fr auto;
    .h-left {
      display: none;
    }
    .title {
      font-size: 22px;
    }
    .wing {
      display: none;
    }
  }
  .kpi-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
