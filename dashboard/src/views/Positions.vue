<template>
  <div class="positions">
    <div class="page-title">持仓列表</div>

    <div class="page-card">
      <el-table :data="store.positions" stripe v-loading="store.loading">
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
          <template #default="{ row }">${{ row.entry_price.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="当前价" width="120">
          <template #default="{ row }">${{ row.current_price.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="浮动盈亏" width="160">
          <template #default="{ row }">
            <span :class="pnlClass(row.unrealized_pnl)">
              ${{ row.unrealized_pnl.toFixed(2) }}
              ({{ row.unrealized_pnl_pct.toFixed(2) }}%)
            </span>
          </template>
        </el-table-column>
        <el-table-column label="止损" width="120">
          <template #default="{ row }">
            {{ row.stop_loss ? '$' + row.stop_loss.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="止盈" width="120">
          <template #default="{ row }">
            {{ row.take_profit ? '$' + row.take_profit.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="开仓时间" width="160">
          <template #default="{ row }">{{ fmtTime(row.opened_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openUpdateDialog(row)">设置止损/盈</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!store.loading && store.positions.length === 0" description="暂无持仓" />
    </div>

    <!-- 设置止损/止盈对话框 -->
    <el-dialog v-model="showUpdateDialog" title="设置止损/止盈" width="400px">
      <el-form :model="updateForm" label-width="100px">
        <el-form-item label="止损价格">
          <el-input-number
            v-model="updateForm.stop_loss"
            :min="0"
            :precision="2"
            style="width: 100%"
            placeholder="留空表示不设止损"
          />
        </el-form-item>
        <el-form-item label="止盈价格">
          <el-input-number
            v-model="updateForm.take_profit"
            :min="0"
            :precision="2"
            style="width: 100%"
            placeholder="留空表示不设止盈"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUpdateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUpdate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { positionApi, type Position } from '@/api'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const showUpdateDialog = ref(false)
const updateForm = ref({
  stop_loss: undefined as number | undefined,
  take_profit: undefined as number | undefined,
})
const updatePositionId = ref('')

function pnlClass(v: number) {
  return v >= 0 ? 'pnl-positive' : 'pnl-negative'
}

function fmtTime(ts: string) {
  return new Date(ts).toLocaleString('zh-CN')
}

function openUpdateDialog(position: Position) {
  updatePositionId.value = position.id
  updateForm.value = {
    stop_loss: position.stop_loss ?? undefined,
    take_profit: position.take_profit ?? undefined,
  }
  showUpdateDialog.value = true
}

async function saveUpdate() {
  await positionApi.update(updatePositionId.value, {
    stop_loss: updateForm.value.stop_loss ?? undefined,
    take_profit: updateForm.value.take_profit ?? undefined,
  })
  showUpdateDialog.value = false
  ElMessage.success('更新成功')
  if (store.currentAccountId) {
    await store.loadPositions(store.currentAccountId)
  }
}

onMounted(async () => {
  if (store.currentAccountId) {
    await store.loadPositions(store.currentAccountId)
  }
})
</script>

<style scoped>
.positions { max-width: 1400px; }
</style>
