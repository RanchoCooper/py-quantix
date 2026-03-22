<template>
  <div class="settings-container">
    <div class="page-header">
      <h2>设置</h2>
      <p class="subtitle">系统配置，页面设置优先级高于 config.yaml</p>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- LLM 设置 -->
      <el-tab-pane label="LLM 分析" name="llm">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>LLM 分析配置</span>
              <el-tag size="small" :type="form.llm.enabled ? 'success' : 'info'">
                {{ form.llm.enabled ? '已启用' : '未启用' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="form.llm" label-width="140px" @submit.prevent>
            <el-form-item label="启用 LLM">
              <el-switch v-model="form.llm.enabled" />
              <span class="form-hint">启用后可在分析页面使用大模型分析 K 线</span>
            </el-form-item>

            <el-form-item label="API Key">
              <el-input
                v-model="form.llm.api_key"
                type="password"
                show-password
                placeholder="输入 MiniMax API Key（留空保持已保存的值）"
                clearable
              />
              <span class="form-hint">
                <el-tag v-if="form.llm.api_key_configured" type="success" size="small">已配置</el-tag>
                <el-tag v-else type="info" size="small">未配置</el-tag>
              </span>
            </el-form-item>

            <el-form-item label="API 地址">
              <el-input
                v-model="form.llm.base_url"
                placeholder="https://api.minimax.chat/v1"
                clearable
              />
            </el-form-item>

            <el-form-item label="模型名称">
              <el-input
                v-model="form.llm.model"
                placeholder="Claude Opus-4.6"
                clearable
              />
            </el-form-item>

            <el-form-item label="分析风格">
              <el-select v-model="form.llm.style" style="width: 100%">
                <el-option
                  v-for="s in form.llm.style_options"
                  :key="s"
                  :label="s"
                  :value="s"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 通知设置 -->
      <el-tab-pane label="通知" name="notifications">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>通知配置</span>
              <el-tag size="small" :type="form.notifications.enabled ? 'success' : 'info'">
                {{ form.notifications.enabled ? '已启用' : '已禁用' }}
              </el-tag>
            </div>
          </template>

          <el-form :model="form.notifications" label-width="140px" @submit.prevent>
            <el-form-item label="启用通知">
              <el-switch v-model="form.notifications.enabled" />
            </el-form-item>

            <el-divider content-position="left">飞书配置</el-divider>

            <el-form-item label="Webhook URL">
              <el-input
                v-model="form.notifications.feishu_webhook"
                placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
                clearable
              />
            </el-form-item>

            <el-form-item label="签名密钥">
              <el-input
                v-model="form.notifications.feishu_secret"
                type="password"
                show-password
                placeholder="飞书签名密钥（可选）"
                clearable
              />
            </el-form-item>

            <el-divider content-position="left">通知类型</el-divider>

            <el-form-item label="交易通知">
              <el-switch v-model="form.notifications.notify_on_trade" />
              <span class="form-hint">开仓/平仓时发送通知</span>
            </el-form-item>

            <el-form-item label="错误通知">
              <el-switch v-model="form.notifications.notify_on_error" />
              <span class="form-hint">系统异常时发送通知</span>
            </el-form-item>

            <el-form-item label="每日报告">
              <el-switch v-model="form.notifications.notify_on_daily" />
              <span class="form-hint">每日发送账户盈亏报告</span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 交易设置 -->
      <el-tab-pane label="交易" name="trading">
        <el-card>
          <template #header>
            <span>交易配置</span>
          </template>

          <el-form :model="form.trading" label-width="140px" @submit.prevent>
            <el-form-item label="默认杠杆">
              <el-input-number
                v-model="form.trading.default_leverage"
                :min="1"
                :max="125"
                :step="1"
              />
              <span class="form-hint">1-125 倍</span>
            </el-form-item>

            <el-form-item label="手续费率">
              <el-input-number
                v-model="form.trading.default_fee_rate"
                :min="0"
                :max="0.01"
                :precision="4"
                :step="0.0001"
              />
              <span class="form-hint">双向手续费率，如 0.0004 = 0.04%</span>
            </el-form-item>

            <el-form-item label="飞书确认下单">
              <el-switch v-model="form.trading.confirm_via_feishu" />
              <span class="form-hint">开启后每次下单需在飞书确认</span>
            </el-form-item>

            <el-form-item label="默认交易对">
              <el-select
                v-model="form.trading.default_symbols"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入交易对"
                style="width: 100%"
              >
                <el-option
                  v-for="sym in popularSymbols"
                  :key="sym.value"
                  :label="sym.label"
                  :value="sym.value"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 市场数据 -->
      <el-tab-pane label="市场数据" name="market">
        <el-card>
          <template #header>
            <span>市场数据配置</span>
          </template>

          <el-form :model="form.market" label-width="140px" @submit.prevent>
            <el-form-item label="默认 K 线周期">
              <el-select v-model="form.market.default_timeframe" style="width: 100%">
                <el-option
                  v-for="tf in timeframes"
                  :key="tf.value"
                  :label="tf.label"
                  :value="tf.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="使用 Testnet">
              <el-switch v-model="form.market.testnet" />
              <span class="form-hint">开启后从币安测试网络获取数据</span>
            </el-form-item>

            <el-form-item label="交易对列表">
              <el-select
                v-model="form.market.symbols"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入交易对"
                style="width: 100%"
              >
                <el-option
                  v-for="sym in popularSymbols"
                  :key="sym.value"
                  :label="sym.label"
                  :value="sym.value"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 系统 -->
      <el-tab-pane label="系统" name="system">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="数据库路径">
              {{ form.system.db_path || '使用默认路径' }}
            </el-descriptions-item>
            <el-descriptions-item label="API 端口">
              {{ form.system.api_port }}
            </el-descriptions-item>
          </el-descriptions>

          <el-alert
            type="info"
            :closable="false"
            show-icon
            style="margin-top: 16px"
          >
            <template #title>
              关于页面设置
            </template>
            页面设置存储在内存中，服务重启后会重置为 config.yaml 默认值。
            如需永久保存，请修改 config.yaml 文件。
          </el-alert>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 底部操作栏 -->
    <div class="settings-actions">
      <el-button @click="resetToDefaults" :loading="saving">
        重置为默认值
      </el-button>
      <el-button type="primary" @click="saveSettings" :loading="saving">
        保存设置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi } from '../api/index'

const activeTab = ref('llm')
const saving = ref(false)

const popularSymbols = [
  { value: 'BTCUSDT', label: 'BTC/USDT' },
  { value: 'ETHUSDT', label: 'ETH/USDT' },
  { value: 'BNBUSDT', label: 'BNB/USDT' },
  { value: 'SOLUSDT', label: 'SOL/USDT' },
  { value: 'XRPUSDT', label: 'XRP/USDT' },
  { value: 'ADAUSDT', label: 'ADA/USDT' },
  { value: 'DOGEUSDT', label: 'DOGE/USDT' },
  { value: 'AVAXUSDT', label: 'AVAX/USDT' },
  { value: 'DOTUSDT', label: 'DOT/USDT' },
  { value: 'LINKUSDT', label: 'LINK/USDT' },
  { value: 'LTCUSDT', label: 'LTC/USDT' },
  { value: 'MATICUSDT', label: 'MATIC/USDT' },
]

const timeframes = [
  { value: '1m', label: '1 分钟' },
  { value: '5m', label: '5 分钟' },
  { value: '15m', label: '15 分钟' },
  { value: '30m', label: '30 分钟' },
  { value: '1h', label: '1 小时' },
  { value: '4h', label: '4 小时' },
  { value: '1d', label: '1 天' },
]

const form = reactive({
  llm: {
    enabled: false,
    api_key: '',
    api_key_configured: false,
    base_url: 'https://api.minimax.chat/v1',
    model: 'Claude Opus-4.6',
    style: '基本面+技术面',
    style_options: ['基本面+技术面', '纯技术面', '波段交易', '趋势跟踪', '均值回归'],
  },
  notifications: {
    enabled: true,
    feishu_webhook: '',
    feishu_secret: '',
    notify_on_trade: true,
    notify_on_error: true,
    notify_on_daily: true,
  },
  trading: {
    default_leverage: 10,
    default_fee_rate: 0.0004,
    confirm_via_feishu: false,
    default_symbols: ['BTCUSDT', 'ETHUSDT'],
  },
  market: {
    default_timeframe: '1h',
    testnet: true,
    symbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT'],
  },
  system: {
    db_path: '',
    api_port: 8000,
  },
})

onMounted(async () => {
  try {
    const data = await settingsApi.get()
    if (data.llm) {
      // api_key 永不清空，仅更新其他字段
      const { api_key: _ek, ...restLlm } = data.llm
      Object.assign(form.llm, restLlm)
      if (data.llm.api_key_configured !== undefined) {
        form.llm.api_key_configured = data.llm.api_key_configured
      }
    }
    if (data.notifications) {
      Object.assign(form.notifications, data.notifications)
    }
    if (data.trading) {
      Object.assign(form.trading, data.trading)
    }
    if (data.market) {
      Object.assign(form.market, data.market)
    }
    if (data.system) {
      Object.assign(form.system, data.system)
    }
  } catch (e: any) {
    ElMessage.warning('无法加载设置，使用默认值')
  }
})

async function saveSettings() {
  saving.value = true
  try {
    // 仅发送非空 api_key，避免覆盖已保存的值
    const llmPayload: Record<string, any> = { ...form.llm }
    if (!llmPayload.api_key) {
      delete llmPayload.api_key
    }
    delete llmPayload.api_key_configured
    delete llmPayload.style_options
    await settingsApi.update({
      llm: llmPayload as any,
      notifications: form.notifications,
      trading: form.trading,
      market: form.market,
    })
    ElMessage.success('设置已保存')
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function resetToDefaults() {
  saving.value = true
  try {
    const data = await settingsApi.reset()
    if (data.llm) Object.assign(form.llm, data.llm)
    if (data.notifications) Object.assign(form.notifications, data.notifications)
    if (data.trading) Object.assign(form.trading, data.trading)
    if (data.market) Object.assign(form.market, data.market)
    if (data.system) Object.assign(form.system, data.system)
    ElMessage.success('已重置为 config.yaml 默认值')
  } catch (e: any) {
    ElMessage.error(e?.message || '重置失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
  max-width: 800px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.settings-tabs {
  margin-bottom: 80px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form-hint {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}

.settings-actions {
  position: fixed;
  bottom: 0;
  left: 200px;
  right: 0;
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  z-index: 100;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}
</style>
