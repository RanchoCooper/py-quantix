<template>
  <div class="risk-management">
    <div class="page-title">仓位管理</div>

    <template v-if="store.currentAccount">
      <!-- 风险指标 -->
      <el-row :gutter="16" class="stat-cards">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">账户余额</div>
            <div class="stat-value">${{ store.currentAccount.balance.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">可用资金</div>
            <div class="stat-value">${{ store.currentAccount.available_balance.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">冻结保证金</div>
            <div class="stat-value">${{ store.currentAccount.frozen_margin.toFixed(2) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">杠杆倍数</div>
            <div class="stat-value">{{ store.currentAccount.leverage }}x</div>
          </div>
        </el-col>
      </el-row>

      <!-- 风险仪表 -->
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="page-card">
            <div class="page-title">仓位分布</div>
            <div ref="pieChartRef" style="height: 280px"></div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="page-card">
            <div class="page-title">账户风险</div>
            <div class="risk-items">
              <div class="risk-item">
                <span class="risk-label">保证金使用率</span>
                <el-progress
                  :percentage="marginUsedPct"
                  :color="marginUsedColor"
                  :stroke-width="12"
                />
                <span class="risk-value">{{ marginUsedPct.toFixed(1) }}%</span>
              </div>
              <div class="risk-item">
                <span class="risk-label">当前持仓数</span>
                <el-progress
                  :percentage="positionCountPct"
                  :color="positionCountColor"
                  :stroke-width="12"
                />
                <span class="risk-value">{{ store.positions.length }} 个</span>
              </div>
              <div class="risk-item">
                <span class="risk-label">浮动盈亏</span>
                <div :class="pnlClass(stats?.open_position_pnl || 0)">
                  ${{ (stats?.open_position_pnl || 0).toFixed(2) }}
                </div>
              </div>
              <div class="risk-item">
                <span class="risk-label">胜率</span>
                <el-progress
                  :percentage="(stats?.win_rate || 0) * 100"
                  :color="winRateColor"
                  :stroke-width="12"
                />
                <span class="risk-value">{{ ((stats?.win_rate || 0) * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 账户配置 -->
      <div class="page-card" style="max-width: 600px">
        <div class="page-title">账户配置</div>
        <el-form :model="accountForm" label-width="120px">
          <el-form-item label="账户名称">
            <el-input v-model="accountForm.name" />
          </el-form-item>
          <el-form-item label="杠杆倍数">
            <el-input-number v-model="accountForm.leverage" :min="1" :max="125" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveAccount">保存配置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { accountApi, type AccountStats } from '@/api'

const store = useAppStore()
const stats = ref<AccountStats | null>(null)
const pieChartRef = ref<HTMLDivElement>()
let pieChart: echarts.ECharts | null = null

const accountForm = ref({
  name: '',
  leverage: 10,
})

const marginUsedPct = computed(() => {
  if (!store.currentAccount) return 0
  const total = store.currentAccount.balance + store.currentAccount.frozen_margin
  return total > 0 ? (store.currentAccount.frozen_margin / total) * 100 : 0
})

const marginUsedColor = computed(() => {
  const p = marginUsedPct.value
  if (p < 30) return '#67c23a'
  if (p < 60) return '#e6a23c'
  return '#f56c6c'
})

const positionCountPct = computed(() => {
  // 假设最多10个持仓作为上限
  return Math.min((store.positions.length / 10) * 100, 100)
})

const positionCountColor = computed(() => {
  const p = positionCountPct.value
  if (p < 30) return '#67c23a'
  if (p < 70) return '#e6a23c'
  return '#f56c6c'
})

const winRateColor = computed(() => {
  const r = stats.value?.win_rate || 0
  if (r >= 0.5) return '#67c23a'
  if (r >= 0.3) return '#e6a23c'
  return '#f56c6c'
})

function pnlClass(v: number) {
  return v >= 0 ? 'pnl-positive' : 'pnl-negative'
}

async function saveAccount() {
  if (!store.currentAccountId) return
  await accountApi.update(store.currentAccountId, {
    name: accountForm.value.name,
    leverage: accountForm.value.leverage,
  })
  ElMessage.success('配置已保存')
  await store.loadAccounts()
}

function updatePieChart() {
  if (!pieChart || store.positions.length === 0) return

  const long = store.positions.filter((p) => p.side === 'long')
  const short = store.positions.filter((p) => p.side === 'short')

  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        name: '持仓分布',
        type: 'pie',
        radius: ['40%', '70%'],
        data: [
          { value: long.length, name: `多头 (${long.length})`, itemStyle: { color: '#67c23a' } },
          { value: short.length, name: `空头 (${short.length})`, itemStyle: { color: '#f56c6c' } },
        ],
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' },
        },
      },
    ],
  })
}

async function initPieChart() {
  await nextTick()
  if (pieChartRef.value) {
    pieChart = echarts.init(pieChartRef.value)
    updatePieChart()
  }
}

onMounted(async () => {
  if (store.currentAccount) {
    accountForm.value = {
      name: store.currentAccount.name,
      leverage: store.currentAccount.leverage,
    }
    stats.value = await accountApi.stats(store.currentAccount.id) as any
  }
  await initPieChart()
})

watch(() => store.positions, () => {
  updatePieChart()
}, { deep: true })
</script>

<style scoped>
.risk-management { max-width: 1200px; }

.stat-cards { margin-bottom: 16px; }

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.stat-label { font-size: 13px; color: #999; margin-bottom: 8px; }

.stat-value { font-size: 22px; font-weight: 600; color: #333; }

.risk-items { display: flex; flex-direction: column; gap: 20px; }

.risk-item {
  display: grid;
  grid-template-columns: 120px 1fr 80px;
  align-items: center;
  gap: 12px;
}

.risk-label { font-size: 14px; color: #666; }
.risk-value { font-size: 14px; font-weight: 600; text-align: right; }
</style>
