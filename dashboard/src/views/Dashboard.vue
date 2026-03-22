<template>
  <div class="dashboard">
    <div class="page-title">账户总览</div>

    <!-- 账户选择提示 -->
    <el-alert
      v-if="!store.currentAccount"
      title="请先创建模拟账户"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    />

    <template v-else>
      <!-- 账户基本信息 -->
      <el-row :gutter="16" class="stat-cards">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">账户余额</div>
            <div class="stat-value">${{ fmt(store.currentAccount.balance) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">可用资金</div>
            <div class="stat-value">${{ fmt(store.currentAccount.available_balance) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">冻结保证金</div>
            <div class="stat-value">${{ fmt(store.currentAccount.frozen_margin) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">总盈亏</div>
            <div class="stat-value" :class="pnlClass(store.currentAccount.total_pnl)">
              ${{ fmt(store.currentAccount.total_pnl) }}
              ({{ store.currentAccount.total_pnl_pct.toFixed(2) }}%)
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16" class="stat-cards">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">胜率</div>
            <div class="stat-value">{{ stats ? (stats.win_rate * 100).toFixed(1) : 0 }}%</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">总交易次数</div>
            <div class="stat-value">{{ stats?.total_trades || 0 }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">当前持仓</div>
            <div class="stat-value">{{ stats?.current_positions || 0 }} 个</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">浮动盈亏</div>
            <div class="stat-value" :class="pnlClass(stats?.open_position_pnl || 0)">
              ${{ fmt(stats?.open_position_pnl || 0) }}
            </div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="16">
          <div class="page-card">
            <div class="page-title">权益曲线</div>
            <div ref="chartRef" style="height: 300px"></div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="page-card">
            <div class="page-title">交易统计</div>
            <div class="stats-list" v-if="stats">
              <div class="stats-row">
                <span>盈利次数</span>
                <span class="pnl-positive">{{ stats.winning_trades }}</span>
              </div>
              <div class="stats-row">
                <span>亏损次数</span>
                <span class="pnl-negative">{{ stats.losing_trades }}</span>
              </div>
              <div class="stats-row">
                <span>平均盈利</span>
                <span class="pnl-positive">${{ fmt(stats.avg_win) }}</span>
              </div>
              <div class="stats-row">
                <span>平均亏损</span>
                <span class="pnl-negative">${{ fmt(stats.avg_loss) }}</span>
              </div>
              <div class="stats-row">
                <span>盈亏比</span>
                <span>{{ stats.profit_factor.toFixed(2) }}</span>
              </div>
              <div class="stats-row">
                <span>最大单笔盈利</span>
                <span class="pnl-positive">${{ fmt(stats.largest_win) }}</span>
              </div>
              <div class="stats-row">
                <span>最大单笔亏损</span>
                <span class="pnl-negative">${{ fmt(stats.largest_loss) }}</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 当前持仓 -->
      <div class="page-card">
        <div class="page-title">当前持仓</div>
        <el-table :data="store.positions" stripe>
          <el-table-column prop="symbol" label="交易对" width="120" />
          <el-table-column label="方向" width="80">
            <template #default="{ row }">
              <el-tag :type="row.side === 'long' ? 'danger' : 'success'" size="small">
                {{ row.side === 'long' ? '做多' : '做空' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100">
            <template #default="{ row }">{{ row.quantity }}</template>
          </el-table-column>
          <el-table-column label="开仓价" width="120">
            <template #default="{ row }">${{ fmt(row.entry_price) }}</template>
          </el-table-column>
          <el-table-column label="当前价" width="120">
            <template #default="{ row }">${{ fmt(row.current_price) }}</template>
          </el-table-column>
          <el-table-column label="浮动盈亏" width="140">
            <template #default="{ row }">
              <span :class="pnlClass(row.unrealized_pnl)">
                ${{ fmt(row.unrealized_pnl) }}
                ({{ row.unrealized_pnl_pct.toFixed(2) }}%)
              </span>
            </template>
          </el-table-column>
          <el-table-column label="止损/止盈" width="180">
            <template #default="{ row }">
              {{ row.stop_loss ? '$' + fmt(row.stop_loss) : '-' }} /
              {{ row.take_profit ? '$' + fmt(row.take_profit) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="开仓时间" min-width="160">
            <template #default="{ row }">{{ fmtTime(row.opened_at) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-if="store.positions.length === 0" description="暂无持仓" />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'
import { accountApi, type EquityPoint } from '@/api'

const store = useAppStore()
const stats = ref(store.stats)
const chartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null
let sseSource: EventSource | null = null

function fmt(v: number) {
  return v.toFixed(2)
}

function pnlClass(v: number) {
  return v >= 0 ? 'pnl-positive' : 'pnl-negative'
}

function fmtTime(ts: string) {
  return new Date(ts).toLocaleString('zh-CN')
}

async function loadEquityCurve() {
  if (!store.currentAccountId) return
  const data = await accountApi.equityCurve(store.currentAccountId, 90) as any
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: {
      type: 'category',
      data: data.map((d: EquityPoint) => d.date),
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: '权益',
        type: 'line',
        data: data.map((d: EquityPoint) => d.balance),
        smooth: true,
        lineStyle: { width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64,158,255,0.3)' },
            { offset: 1, color: 'rgba(64,158,255,0.05)' },
          ]),
        },
      },
    ],
  })
}

async function initChart() {
  await nextTick()
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    await loadEquityCurve()
  }
}

async function loadAll() {
  if (!store.currentAccountId) return
  await store.refresh(store.currentAccountId)
  stats.value = store.stats
  await loadEquityCurve()
}

function connectSSE() {
  sseSource = new EventSource('/api/events/stream')
  sseSource.onmessage = async (e) => {
    try {
      const event = JSON.parse(e.data)
      if (event.event === 'prices_updated' || event.event === 'position_opened' || event.event === 'position_closed') {
        await loadAll()
      }
    } catch {}
  }
}

onMounted(async () => {
  await loadAll()
  await initChart()
  connectSSE()
})

onUnmounted(() => {
  sseSource?.close()
  chart?.dispose()
})

watch(() => store.currentAccountId, async () => {
  await loadAll()
  await initChart()
})
</script>

<style scoped>
.dashboard { max-width: 1400px; }

.stat-cards { margin-bottom: 16px; }

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.stats-list { display: flex; flex-direction: column; gap: 12px; }

.stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.stats-row:last-child { border-bottom: none; }
</style>
