<template>
  <div class="open-position">
    <div class="page-title">开仓</div>

    <div class="page-card" style="max-width: 600px">
      <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
        <el-form-item label="交易对" prop="symbol">
          <el-input v-model="form.symbol" placeholder="例如: BTCUSDT" />
        </el-form-item>
        <el-form-item label="方向" prop="side">
          <el-radio-group v-model="form.side">
            <el-radio-button value="long">做多 🔴</el-radio-button>
            <el-radio-button value="short">做空 🟢</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number
            v-model="form.quantity"
            :min="0.0001"
            :precision="4"
            :step="0.001"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="入场价格" prop="price">
          <el-input-number
            v-model="form.price"
            :min="0"
            :precision="2"
            :step="10"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="止损价格">
          <el-input-number
            v-model="form.stop_loss"
            :min="0"
            :precision="2"
            :step="10"
            style="width: 100%"
            placeholder="选填"
          />
        </el-form-item>
        <el-form-item label="止盈价格">
          <el-input-number
            v-model="form.take_profit"
            :min="0"
            :precision="2"
            :step="10"
            style="width: 100%"
            placeholder="选填"
          />
        </el-form-item>
        <el-form-item label="交易理由">
          <el-input
            v-model="form.reason"
            type="textarea"
            :rows="3"
            placeholder="选填，例如: 来自 analyzer 的买入信号"
          />
        </el-form-item>
      </el-form>

      <div class="form-actions">
        <el-button @click="resetForm">重置</el-button>
        <el-button type="primary" :loading="submitting" @click="submitOrder">
          提交订单（需飞书确认）
        </el-button>
      </div>
    </div>

    <!-- 待确认信号 -->
    <div class="page-card">
      <div class="page-title">待确认信号</div>
      <el-table :data="pendingSignals" stripe>
        <el-table-column prop="symbol" label="交易对" width="120" />
        <el-table-column label="方向" width="80">
          <template #default="{ row }">
            <el-tag :type="row.signal_type === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.signal_type === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="入场价" width="120">
          <template #default="{ row }">
            {{ row.entry_price ? '$' + row.entry_price.toFixed(2) : '-' }}
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
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pending' ? 'warning' : 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">{{ new Date(row.created_at).toLocaleString('zh-CN') }}</template>
        </el-table-column>
      </el-table>
      <el-empty v-if="pendingSignals.length === 0" description="暂无待确认信号" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { orderApi, signalApi, type Signal } from '@/api'
import { useAppStore } from '@/stores/app'

const store = useAppStore()
const formRef = ref()
const submitting = ref(false)
const pendingSignals = ref<Signal[]>([])

const form = ref({
  symbol: '',
  side: 'long',
  quantity: 0.001,
  price: 0,
  stop_loss: undefined as number | undefined,
  take_profit: undefined as number | undefined,
  reason: '',
})

const rules = {
  symbol: [{ required: true, message: '请输入交易对', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  price: [{ required: true, message: '请输入入场价格', trigger: 'blur' }],
}

function resetForm() {
  form.value = {
    symbol: '',
    side: 'long',
    quantity: 0.001,
    price: 0,
    stop_loss: undefined,
    take_profit: undefined,
    reason: '',
  }
  formRef.value?.resetFields()
}

async function submitOrder() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    if (!store.currentAccountId) {
      ElMessage.warning('请先选择账户')
      return
    }

    submitting.value = true
    try {
      const result = await orderApi.create({
        account_id: store.currentAccountId,
        symbol: form.value.symbol.toUpperCase(),
        side: 'buy',
        position_side: form.value.side as 'long' | 'short',
        quantity: form.value.quantity,
        price: form.value.price,
        stop_loss: form.value.stop_loss,
        take_profit: form.value.take_profit,
        source: 'manual',
        reason: form.value.reason,
      }) as any

      if (result.pending) {
        ElMessage.info('订单确认请求已发送到飞书，请等待确认')
      } else {
        ElMessage.success('开仓成功')
        await store.refresh(store.currentAccountId)
      }
      await loadPendingSignals()
    } finally {
      submitting.value = false
    }
  })
}

async function loadPendingSignals() {
  try {
    pendingSignals.value = await feishuApi.signals() as any
  } catch {}
}

import { feishuApi } from '@/api'

onMounted(async () => {
  await loadPendingSignals()
})
</script>

<style scoped>
.open-position { max-width: 900px; }

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
