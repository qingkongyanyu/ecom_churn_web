<!--
  PredictForm.vue
  大屏预测表单（紧凑两列布局）：
    - 5 个分类下拉 + 13 个数值输入
    - 「随机示例」一键填充演示数据
    - 调用 /predict 接口，emit predicted 事件驱动中心仪表盘
-->
<template>
  <form class="pform" @submit.prevent="handlePredict">
    <div class="fields">
      <div v-for="f in formFields" :key="f.key" class="fg">
        <label class="fl">{{ f.label }}<span v-if="f.required" class="req">*</span></label>

        <select
          v-if="f.type === 'select'"
          v-model="formData[f.key]"
          class="fc"
          :required="f.required"
        >
          <option value="" disabled>请选择</option>
          <option v-for="opt in f.options" :key="opt" :value="opt">{{ opt }}</option>
        </select>

        <input
          v-else
          v-model.number="formData[f.key]"
          type="number"
          class="fc num"
          :placeholder="f.placeholder || '0'"
          :required="f.required"
          :min="f.min"
          :max="f.max"
          step="any"
        />
      </div>
    </div>

    <div class="actions">
      <button type="button" class="btn ghost" @click="fillRandom" title="随机生成一份示例用户数据">⚡ 随机示例</button>
      <button type="submit" class="btn primary" :disabled="loading">
        {{ loading ? '⏳ 计算中…' : '🔮 开始预测' }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { predictChurn } from '@/api/request'

const emit = defineEmits(['predicted', 'error'])

// ---------- 字段配置（与后端 UserData 完全一致） ----------
const formFields = [
  { key: 'gender', label: '性别', type: 'select', required: true, options: ['F', 'M'] },
  { key: 'age_range', label: '年龄段', type: 'select', required: true, options: ['<18', '18-24', '25-34', '35-44', '45-54', '55+'] },
  { key: 'device', label: '设备', type: 'select', required: true, options: ['Mobile', 'PC', 'Tablet'] },
  { key: 'operative_system', label: '操作系统', type: 'select', required: true, options: ['Windows', 'Linux', 'macOS', 'Android', 'iOS'] },
  { key: 'source', label: '渠道来源', type: 'select', required: true, options: ['Ads', 'Search', 'Social', 'Direct', 'Email', 'Referral'] },
  { key: 'new_user', label: '是否新用户', type: 'number', required: true, min: 0, max: 1 },
  { key: 'register_days', label: '注册天数', type: 'number', required: true, min: 0 },
  { key: 'member_level', label: '会员等级', type: 'number', required: true, min: 0, max: 4 },
  { key: 'total_pages_visited', label: '累计访问页数', type: 'number', required: true, min: 0 },
  { key: 'active_days_30d', label: '近30天活跃天数', type: 'number', required: true, min: 0, max: 30 },
  { key: 'days_since_last_login', label: '距上次登录(天)', type: 'number', required: true, min: 0 },
  { key: 'cart_total', label: '加购件数', type: 'number', required: true, min: 0 },
  { key: 'fav_total', label: '收藏件数', type: 'number', required: true, min: 0 },
  { key: 'last_buy_days', label: '距上次下单(天)', type: 'number', required: true, min: 0 },
  { key: 'buy_freq', label: '下单总次数', type: 'number', required: true, min: 0 },
  { key: 'total_spend', label: '累计消费(元)', type: 'number', required: true, min: 0 },
  { key: 'avg_order_amount', label: '平均客单价(元)', type: 'number', required: true, min: 0 },
  { key: 'refund_cnt', label: '退款次数', type: 'number', required: true, min: 0 },
]

// ---------- 表单数据 ----------
const formData = reactive({})
formFields.forEach((f) => {
  formData[f.key] = f.type === 'select' ? '' : 0
})

const loading = ref(false)

// ---------- 随机示例 ----------
function rnd(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}
function fillRandom() {
  formFields.forEach((f) => {
    if (f.type === 'select') {
      formData[f.key] = f.options[rnd(0, f.options.length - 1)]
    } else {
      const ranges = {
        new_user: () => rnd(0, 1),
        register_days: () => rnd(10, 800),
        member_level: () => rnd(0, 4),
        total_pages_visited: () => rnd(5, 220),
        active_days_30d: () => rnd(0, 30),
        days_since_last_login: () => rnd(0, 80),
        cart_total: () => rnd(0, 45),
        fav_total: () => rnd(0, 35),
        last_buy_days: () => rnd(0, 150),
        buy_freq: () => rnd(0, 70),
        total_spend: () => +(rnd(50, 24000) + Math.random()).toFixed(2),
        avg_order_amount: () => +(rnd(40, 1400) + Math.random()).toFixed(2),
        refund_cnt: () => rnd(0, 6),
      }
      formData[f.key] = (ranges[f.key] || (() => 0))()
    }
  })
}

// ---------- 预测 ----------
const handlePredict = async () => {
  for (const f of formFields) {
    if (f.type === 'select' && !formData[f.key]) {
      emit('error', `请选择${f.label}`)
      return
    }
    if (f.type === 'number' && (formData[f.key] === '' || isNaN(formData[f.key]))) {
      emit('error', `请输入有效的${f.label}`)
      return
    }
  }

  loading.value = true
  try {
    const payload = { ...formData }
    formFields.forEach((f) => {
      if (f.type === 'number') payload[f.key] = Number(payload[f.key])
    })
    const res = await predictChurn(payload)
    emit('predicted', {
      prob: res.churn_prob,
      riskLevel: res.risk_level,
      color: res.color,
    })
  } catch (err) {
    emit('error', err.message)
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.pform {
  .fields {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px 14px;
  }

  .fg {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;

    .fl {
      font-size: 12px;
      color: var(--ink-2);
      letter-spacing: 0.5px;
      .req {
        color: var(--status-critical);
        margin-left: 2px;
      }
    }

    .fc {
      width: 100%;
      height: 32px;
      padding: 4px 10px;
      background: rgba(5, 12, 30, 0.65);
      border: 1px solid rgba(0, 216, 255, 0.22);
      border-radius: 6px;
      color: var(--ink-1);
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
      appearance: none;

      &:focus {
        border-color: var(--border-strong);
        box-shadow: 0 0 0 3px rgba(0, 216, 255, 0.15);
      }
      &::-webkit-outer-spin-button,
      &::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
      }
    }
    select.fc {
      cursor: pointer;
      option {
        background: var(--surface-solid);
        color: var(--ink-1);
      }
    }
  }

  .actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;

    .btn {
      flex: 1;
      height: 40px;
      border: none;
      border-radius: 8px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      letter-spacing: 1px;
      transition: transform 0.15s, box-shadow 0.2s, opacity 0.2s;
      &:active {
        transform: scale(0.98);
      }
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }
    .primary {
      background: linear-gradient(120deg, var(--cyan), var(--blue));
      color: #04101f;
      box-shadow: 0 0 18px rgba(0, 216, 255, 0.4);
      &:hover:not(:disabled) {
        box-shadow: 0 0 28px rgba(0, 216, 255, 0.6);
        transform: translateY(-1px);
      }
    }
    .ghost {
      background: transparent;
      border: 1px solid rgba(0, 216, 255, 0.4);
      color: var(--cyan);
      &:hover:not(:disabled) {
        background: rgba(0, 216, 255, 0.1);
        box-shadow: var(--glow-cyan-sm);
      }
    }
  }
}
</style>
