<template>
  <div class="history">
    <div class="page-title">历史订单</div>

    <!-- 筛选 -->
    <div class="page-card">
      <el-form :inline="true" :model="filters" class="filters">
        <el-form-item label="交易对">
          <el-input v-model="filters.symbol" placeholder="例如: BTCUSDT" clearable />
        </el-form-item>
        <el-form-item label="方向">
          <el-select v-model="filters.side" placeholder="全部" clearable>
            <el-option label="买入" value="buy" />
            <el-option label="卖出" value="sell" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable>
            <el-option label="待确认" value="pending" />
            <el-option label="已成交" value="filled" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadOrders">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="orders" stripe v-loading="loading">
        <el-table-column prop="symbol" label="交易对" width="120" />
        <el-table-column label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.side === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.side === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="持仓方向" width="80">
          <template #default="{ row }">
            {{ row.position_side === 'long' ? '多' : row.position_side === 'short' ? '空' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="数量" width="100">
          <template #default="{ row }">{{ row.quantity }}</template>
        </el-table-column>
        <el-table-column label="委托价" width="120">
          <template #default="{ row }">
            {{ row.price ? '$' + row.price.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="成交价" width="120">
          <template #default="{ row }">
            {{ row.filled_price ? '$' + row.filled_price.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="手续费" width="100">
          <template #default="{ row }">${{ row.fee.toFixed(4) }}</template>
        </el-table-column>
        <el-table-column label="盈亏" width="120">
          <template #default="{ row }">
            <span v-if="row.pnl !== null" :class="pnlClass(row.pnl)">
              ${{ row.pnl.toFixed(2) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="80">
          <template #default="{ row }">{{ row.source }}</template>
        </el-table-column>
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ fmtTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        layout="prev, pager, next, total"
        :total="total"
        :page-size="pageSize"
        v-model:current-page="currentPage"
        @current-change="loadOrders"
        style="margin-top: 16px; justify-content: center"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAppStore } from '@/stores/app'
import { orderApi, type Order } from '@/api'

const store = useAppStore()
const orders = ref<Order[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 20
const loading = ref(false)
const filters = ref({
  symbol: '',
  side: '',
  status: '',
})

function statusTag(status: string) {
  const map: Record<string, string> = {
    pending: 'warning',
    filled: 'success',
    cancelled: 'info',
    rejected: 'danger',
  }
  return map[status] || 'info'
}

function pnlClass(v: number) {
  return v >= 0 ? 'pnl-positive' : 'pnl-negative'
}

function fmtTime(ts: string) {
  return new Date(ts).toLocaleString('zh-CN')
}

function resetFilters() {
  filters.value = { symbol: '', side: '', status: '' }
  currentPage.value = 1
  loadOrders()
}

async function loadOrders() {
  if (!store.currentAccountId) return
  loading.value = true
  try {
    const res = await orderApi.list(store.currentAccountId, {
      page: currentPage.value,
      page_size: pageSize,
      symbol: filters.value.symbol || undefined,
      side: filters.value.side || undefined,
      status: filters.value.status || undefined,
    }) as any
    orders.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (store.currentAccountId) loadOrders()
})

watch(() => store.currentAccountId, () => {
  if (store.currentAccountId) loadOrders()
})
</script>

<style scoped>
.history { max-width: 1400px; }
.filters { margin-bottom: 16px; }
</style>
