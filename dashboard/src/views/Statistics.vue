<template>
  <div class="statistics">
    <div class="page-title">盈利统计</div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-cards" v-if="stats">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-label">总盈亏</div>
          <div class="stat-value" :class="pnlClass(stats.total_pnl)">
            ${{ stats.total_pnl.toFixed(2) }}
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-label">胜率</div>
          <div class="stat-value">{{ (stats.win_rate * 100).toFixed(1) }}%</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-label">盈亏比</div>
          <div class="stat-value">{{ stats.profit_factor.toFixed(2) }}</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-label">总交易次数</div>
          <div class="stat-value">{{ stats.total_trades }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <!-- 盈亏分布图 -->
      <el-col :span="16">
        <div class="page-card">
          <div class="page-title">每日盈亏</div>
          <div ref="dailyChartRef" style="height: 300px"></div>
        </div>
      </el-col>
      <!-- 盈亏分布 -->
      <el-col :span="8">
        <div class="page-card">
          <div class="page-title">盈亏分析</div>
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
              <span class="pnl-positive">${{ stats.avg_win.toFixed(2) }}</span>
            </div>
            <div class="stats-row">
              <span>平均亏损</span>
              <span class="pnl-negative">${{ stats.avg_loss.toFixed(2) }}</span>
            </div>
            <div class="stats-row">
              <span>最大单笔盈利</span>
              <span class="pnl-positive">${{ stats.largest_win.toFixed(2) }}</span>
            </div>
            <div class="stats-row">
              <span>最大单笔亏损</span>
              <span class="pnl-negative">${{ stats.largest_loss.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 每日统计表 -->
    <div class="page-card">
      <div class="page-title">每日统计</div>
      <el-table :data="dailyStats" stripe>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column label="开盘余额" width="120">
          <template #default="{ row }">${{ row.opening_balance.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="收盘余额" width="120">
          <template #default="{ row }">${{ row.closing_balance.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="日盈亏" width="140">
          <template #default="{ row }">
            <span :class="pnlClass(row.daily_pnl)">
              ${{ row.daily_pnl.toFixed(2) }}
              ({{ row.daily_pnl_pct.toFixed(2) }}%)
            </span>
          </template>
        </el-table-column>
        <el-table-column label="交易次数" width="100" prop="trade_count" />
        <el-table-column label="胜/负" width="100">
          <template #default="{ row }">
            {{ row.win_count }} / {{ row.lose_count }}
          </template>
        </el-table-column>
        <el-table-column label="胜率" width="80">
          <template #default="{ row }">{{ (row.win_rate * 100).toFixed(0) }}%</template>
        </el-table-column>
        <el-table-column label="最大盈利" width="120">
          <template #default="{ row }">
            <span class="pnl-positive">${{ row.largest_win.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="最大亏损" width="120">
          <template #default="{ row }">
            <span class="pnl-negative">${{ row.largest_loss.toFixed(2) }}</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-if="dailyTotal > pageSize"
        layout="prev, pager, next"
        :total="dailyTotal"
        :page-size="pageSize"
        v-model:current-page="currentPage"
        @current-change="loadDailyStats"
        style="margin-top: 16px; justify-content: center"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useAppStore } from '@/stores/app'
import { accountApi, type DailyStats } from '@/api'

const store = useAppStore()
const stats = ref(store.stats)
const dailyStats = ref<DailyStats[]>([])
const dailyTotal = ref(0)
const currentPage = ref(1)
const pageSize = 30
const dailyChartRef = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function pnlClass(v: number) {
  return v >= 0 ? 'pnl-positive' : 'pnl-negative'
}

async function loadDailyStats() {
  if (!store.currentAccountId) return
  const res = await accountApi.dailyStats(store.currentAccountId, currentPage.value, pageSize) as any
  dailyStats.value = res.items
  dailyTotal.value = res.total
  updateChart()
}

function updateChart() {
  if (!chart || dailyStats.value.length === 0) return
  const sorted = [...dailyStats.value].reverse()
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: sorted.map((d) => d.date) },
    yAxis: { type: 'value' },
    series: [
      {
        name: '日盈亏',
        type: 'bar',
        data: sorted.map((d) => ({
          value: d.daily_pnl,
          itemStyle: {
            color: d.daily_pnl >= 0 ? '#f56c6c' : '#67c23a',
          },
        })),
      },
    ],
  })
}

async function initChart() {
  await nextTick()
  if (dailyChartRef.value) {
    chart = echarts.init(dailyChartRef.value)
    updateChart()
  }
}

onMounted(async () => {
  if (store.currentAccountId) {
    stats.value = await accountApi.stats(store.currentAccountId) as any
  }
  await loadDailyStats()
  await initChart()
})

watch(() => store.currentAccountId, async (id) => {
  if (id) {
    stats.value = await accountApi.stats(id) as any
    await loadDailyStats()
  }
})
</script>

<style scoped>
.statistics { max-width: 1400px; }

.stat-cards { margin-bottom: 16px; }

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.stat-label { font-size: 13px; color: #999; margin-bottom: 8px; }

.stat-value { font-size: 22px; font-weight: 600; color: #333; }

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
