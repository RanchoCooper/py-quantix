<template>
  <div class="close-position">
    <div class="page-title">平仓</div>

    <div class="page-card" style="max-width: 600px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="选择持仓">
          <el-select v-model="form.positionId" placeholder="请选择要平仓的持仓" @change="onPositionChange">
            <el-option
              v-for="pos in store.positions"
              :key="pos.id"
              :label="`${pos.symbol} ${pos.side === 'long' ? '多' : '空'} ${pos.quantity}`"
              :value="pos.id"
            />
          </el-select>
        </el-form-item>
        <template v-if="selectedPosition">
          <el-form-item label="交易对">
            <span>{{ selectedPosition.symbol }}</span>
          </el-form-item>
          <el-form-item label="方向">
            <el-tag :type="selectedPosition.side === 'long' ? 'danger' : 'success'" size="small">
              {{ selectedPosition.side === 'long' ? '做多' : '做空' }}
            </el-tag>
          </el-form-item>
          <el-form-item label="持仓数量">
            <span>{{ selectedPosition.quantity }}</span>
          </el-form-item>
          <el-form-item label="开仓价">
            <span>${{ selectedPosition.entry_price.toFixed(2) }}</span>
          </el-form-item>
          <el-form-item label="当前价">
            <span>${{ selectedPosition.current_price.toFixed(2) }}</span>
          </el-form-item>
          <el-form-item label="浮动盈亏">
            <span :class="pnlClass(selectedPosition.unrealized_pnl)">
              ${{ selectedPosition.unrealized_pnl.toFixed(2) }}
            </span>
          </el-form-item>
        </template>
        <el-form-item label="平仓数量">
          <el-input-number
            v-model="form.quantity"
            :min="0.0001"
            :max="selectedPosition?.quantity || 9999"
            :precision="4"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="平仓价格" prop="price">
          <el-input-number
            v-model="form.price"
            :min="0"
            :precision="2"
            :step="10"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <div class="form-actions">
        <el-button @click="form = { positionId: '', quantity: 0.001, price: 0 }">重置</el-button>
        <el-button
          type="danger"
          :loading="submitting"
          @click="submitClose"
        >
          确认平仓
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { positionApi, type Position } from '@/api'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const submitting = ref(false)
const form = ref({
  positionId: '',
  quantity: 0.001,
  price: 0,
})

const selectedPosition = computed<Position | null>(() =>
  store.positions.find((p) => p.id === form.value.positionId) || null
)

function pnlClass(v: number) {
  return v >= 0 ? 'pnl-positive' : 'pnl-negative'
}

function onPositionChange(posId: string) {
  const pos = store.positions.find((p) => p.id === posId)
  if (pos) {
    form.value.quantity = pos.quantity
    form.value.price = pos.current_price
  }
}

async function submitClose() {
  if (!form.value.positionId) {
    ElMessage.warning('请选择持仓')
    return
  }
  if (!form.value.price) {
    ElMessage.warning('请输入平仓价格')
    return
  }

  submitting.value = true
  try {
    const result = await positionApi.close(form.value.positionId, form.value.price) as any
    if (result.success) {
      ElMessage.success(
        `平仓成功，盈亏: $${(result.pnl as number).toFixed(2)}，手续费: $${(result.fee as number).toFixed(2)}`
      )
      if (store.currentAccountId) {
        await store.refresh(store.currentAccountId)
      }
      form.value = { positionId: '', quantity: 0.001, price: 0 }
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.close-position { max-width: 700px; }

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
