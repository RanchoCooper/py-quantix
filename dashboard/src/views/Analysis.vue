<template>
  <div class="analysis-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>LLM 市场分析</h2>
      <p class="subtitle">基于大模型的多币种技术分析，支持一键生成交易信号</p>
    </div>

    <!-- 配置区 -->
    <el-card class="config-card">
      <el-form :model="form" label-width="120px">
        <el-row :gutter="20">
          <!-- 交易对选择 -->
          <el-col :span="24">
            <el-form-item label="交易对">
              <el-select
                v-model="form.symbols"
                multiple
                filterable
                allow-create
                default-first-option
                placeholder="选择或输入交易对，如 BTCUSDT"
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
          </el-col>

          <el-col :span="8">
            <el-form-item label="K线周期">
              <el-select v-model="form.timeframe" style="width: 100%">
                <el-option
                  v-for="tf in timeframes"
                  :key="tf.value"
                  :label="tf.label"
                  :value="tf.value"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="K线数量">
              <el-input-number
                v-model="form.limit"
                :min="10"
                :max="1000"
                :step="10"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="分析风格">
              <el-select v-model="form.style" style="width: 100%">
                <el-option
                  v-for="s in styleOptions"
                  :key="s"
                  :label="s"
                  :value="s"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <!-- 高级配置折叠 -->
          <el-col :span="24">
            <el-collapse>
              <el-collapse-item title="高级配置" name="advanced">
                <el-col :span="8">
                  <el-form-item label="API Key">
                    <el-input
                      v-model="form.llm_api_key"
                      type="password"
                      show-password
                      placeholder="留空则使用环境变量"
                      clearable
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="API URL">
                    <el-input
                      v-model="form.llm_base_url"
                      placeholder="留空使用默认 MiniMax"
                      clearable
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="模型">
                    <el-input
                      v-model="form.llm_model"
                      placeholder="留空使用默认模型"
                      clearable
                    />
                  </el-form-item>
                </el-col>
              </el-collapse-item>
            </el-collapse>
          </el-col>
        </el-row>

        <!-- 操作按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            :loading="analyzing"
            :disabled="analyzing || !form.symbols.length"
            size="large"
            @click="startAnalysis"
          >
            <el-icon v-if="!analyzing"><Cpu /></el-icon>
            {{ analyzing ? `分析中 (${completedCount}/${form.symbols.length})...` : '开始分析' }}
          </el-button>
          <el-button @click="resetForm" :disabled="analyzing">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- K线预览区 -->
    <div v-if="klinePreview.length > 0 && !analyzing" class="preview-section">
      <h3>数据预览</h3>
      <el-alert type="info" :closable="false" show-icon>
        已获取 {{ klinePreview.length }} 个交易对的 K 线数据，最新价格仅供参考
      </el-alert>
      <div class="preview-grid">
        <div v-for="item in klinePreview" :key="item.symbol" class="preview-item">
          <div class="symbol-name">{{ item.symbol }}</div>
          <div class="symbol-price">
            <span class="price">{{ formatPrice(item.klines[item.klines.length-1]?.close) }}</span>
            <span
              class="change"
              :class="getChangeClass(item)"
            >
              {{ formatChange(item) }}
            </span>
          </div>
          <div class="symbol-meta">
            K线数: {{ item.klines.length }} | {{ item.interval }}
          </div>
        </div>
      </div>
    </div>

    <!-- 分析结果区 -->
    <div v-if="results.length > 0 && !analyzing" class="results-section">
      <h3>分析报告</h3>

      <div v-if="errors && Object.keys(errors).length > 0" class="errors-section">
        <el-alert type="warning" title="部分分析失败">
          <template #default>
            <div v-for="(err, sym) in errors" :key="sym">
              {{ sym }}: {{ err }}
            </div>
          </template>
        </el-alert>
      </div>

      <div class="results-list">
        <el-card
          v-for="(result, index) in results"
          :key="result.symbol"
          class="result-card"
          :class="'trend-' + result.trend"
        >
          <template #header>
            <div class="result-header">
              <div class="result-title">
                <span class="symbol-badge" :class="'trend-' + result.trend">
                  {{ result.symbol }}
                </span>
                <el-tag :type="trendTagType(result.trend)" size="small">
                  {{ trendLabel(result.trend) }}
                </el-tag>
                <span class="kline-info">K线 {{ result.kline_count }} 根 | {{ result.interval }}</span>
              </div>
              <div class="result-actions">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click="createSignalFromResult(result)"
                >
                  生成信号
                </el-button>
                <el-button
                  size="small"
                  @click="toggleExpand(index)"
                >
                  {{ expandedIndex === index ? '收起' : '展开' }}
                </el-button>
              </div>
            </div>
          </template>

          <!-- 指标摘要 -->
          <div v-if="result.indicators && Object.keys(result.indicators).length > 0" class="indicators-row">
            <div class="indicator-item">
              <span class="label">最新价</span>
              <span class="value">{{ formatPrice(result.indicators.latest_price) }}</span>
            </div>
            <div class="indicator-item">
              <span class="label">MA5</span>
              <span class="value">{{ formatPrice(result.indicators.ma5) }}</span>
            </div>
            <div class="indicator-item">
              <span class="label">MA10</span>
              <span class="value">{{ formatPrice(result.indicators.ma10) }}</span>
            </div>
            <div class="indicator-item">
              <span class="label">MA20</span>
              <span class="value">{{ formatPrice(result.indicators.ma20) }}</span>
            </div>
            <div class="indicator-item">
              <span class="label">涨跌</span>
              <span
                class="value"
                :class="result.indicators.change_pct >= 0 ? 'positive' : 'negative'"
              >
                {{ result.indicators.change_pct >= 0 ? '+' : '' }}{{ result.indicators.change_pct }}%
              </span>
            </div>
            <div class="indicator-item">
              <span class="label">成交量变化</span>
              <span
                class="value"
                :class="result.indicators.volume_change >= 0 ? 'positive' : 'negative'"
              >
                {{ result.indicators.volume_change >= 0 ? '+' : '' }}{{ result.indicators.volume_change }}%
              </span>
            </div>
          </div>

          <!-- 完整分析文本 -->
          <div v-if="expandedIndex === index" class="analysis-content">
            <el-divider content-position="left">LLM 分析报告</el-divider>
            <div class="markdown-body">{{ result.raw_analysis }}</div>
          </div>

          <!-- 快速预览（折叠时显示摘要） -->
          <div v-else class="analysis-preview">
            <el-divider content-position="left">LLM 分析摘要</el-divider>
            <div class="markdown-body preview-text">
              {{ getPreviewText(result.raw_analysis) }}
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="!analyzing && results.length === 0 && klinePreview.length === 0"
      description="配置参数后点击「开始分析」"
    />

    <!-- 信号创建对话框 -->
    <el-dialog v-model="showSignalDialog" title="创建交易信号" width="500px">
      <el-form :model="signalForm" label-width="100px">
        <el-form-item label="交易对">
          <el-input :value="signalForm.symbol" disabled />
        </el-form-item>
        <el-form-item label="信号方向">
          <el-select v-model="signalForm.signal_type" style="width: 100%">
            <el-option label="看多 (Buy)" value="buy" />
            <el-option label="看空 (Sell)" value="sell" />
            <el-option label="观望 (Hold)" value="hold" />
          </el-select>
        </el-form-item>
        <el-form-item label="入场价格">
          <el-input-number
            v-model="signalForm.entry_price"
            :precision="4"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="止损价格">
          <el-input-number
            v-model="signalForm.stop_loss"
            :precision="4"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="止盈价格">
          <el-input-number
            v-model="signalForm.take_profit"
            :precision="4"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="时间周期">
          <el-select v-model="signalForm.timeframe" style="width: 100%">
            <el-option
              v-for="tf in timeframes"
              :key="tf.value"
              :label="tf.label"
              :value="tf.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分析依据">
          <el-input
            v-model="signalForm.reason"
            type="textarea"
            :rows="3"
            placeholder="简要说明分析依据..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSignalDialog = false">取消</el-button>
        <el-button type="primary" :loading="signalCreating" @click="submitSignal">
          创建信号
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu } from '@element-plus/icons-vue'
import { analysisApi } from '../api/index'

const form = reactive({
  symbols: ['BTCUSDT', 'ETHUSDT'] as string[],
  timeframe: '1h',
  limit: 100,
  style: '基本面+技术面',
  llm_api_key: '',
  llm_base_url: '',
  llm_model: '',
})

const timeframes = ref<{ value: string; label: string }[]>([])
const popularSymbols = ref<{ value: string; label: string }[]>([])
const styleOptions = ref<string[]>([])

const analyzing = ref(false)
const completedCount = ref(0)
const klinePreview = ref<any[]>([])
const results = ref<any[]>([])
const errors = ref<Record<string, string>>({})
const expandedIndex = ref<number | null>(null)

// 信号创建
const showSignalDialog = ref(false)
const signalCreating = ref(false)
const signalForm = reactive({
  symbol: '',
  signal_type: 'buy',
  entry_price: 0,
  stop_loss: 0,
  take_profit: 0,
  timeframe: '1h',
  reason: '',
})

onMounted(async () => {
  await Promise.all([loadTimeframes(), loadPopularSymbols(), loadConfig()])
})

async function loadTimeframes() {
  try {
    const data = await analysisApi.getTimeframes()
    timeframes.value = data.options
  } catch {
    timeframes.value = [
      { value: '1m', label: '1 分钟' },
      { value: '5m', label: '5 分钟' },
      { value: '15m', label: '15 分钟' },
      { value: '30m', label: '30 分钟' },
      { value: '1h', label: '1 小时' },
      { value: '4h', label: '4 小时' },
      { value: '1d', label: '1 天' },
      { value: '1w', label: '1 周' },
    ]
  }
}

async function loadPopularSymbols() {
  try {
    const data = await analysisApi.getPopularSymbols()
    popularSymbols.value = data.symbols
  } catch {
    popularSymbols.value = [
      { value: 'BTCUSDT', label: 'BTC/USDT' },
      { value: 'ETHUSDT', label: 'ETH/USDT' },
      { value: 'BNBUSDT', label: 'BNB/USDT' },
      { value: 'SOLUSDT', label: 'SOL/USDT' },
    ]
  }
}

async function loadConfig() {
  try {
    const data = await analysisApi.getConfig()
    styleOptions.value = data.style_options
    if (data.style_options.length > 0 && !styleOptions.value.includes(form.style)) {
      form.style = data.style_options[0]
    }
  } catch {
    styleOptions.value = ['基本面+技术面', '纯技术面', '波段交易', '趋势跟踪', '均值回归']
  }
}

async function startAnalysis() {
  if (!form.symbols.length) {
    ElMessage.warning('请至少选择一个交易对')
    return
  }

  analyzing.value = true
  completedCount.value = 0
  klinePreview.value = []
  results.value = []
  errors.value = {}

  try {
    const response = await analysisApi.analyze({
      symbols: form.symbols,
      timeframe: form.timeframe,
      limit: form.limit,
      style: form.style,
      llm_api_key: form.llm_api_key || undefined,
      llm_base_url: form.llm_base_url || undefined,
      llm_model: form.llm_model || undefined,
    })

    results.value = response.results || []
    errors.value = response.errors || {}

    if (results.value.length > 0) {
      // 尝试获取 K 线预览
      try {
        const klines = await analysisApi.fetchKlines({
          symbols: form.symbols,
          timeframe: form.timeframe,
          limit: 20,
        })
        klinePreview.value = klines
      } catch {
        // 预览失败不影响主流程
      }
      ElMessage.success(`分析完成：${results.value.length} 个交易对`)
    } else {
      ElMessage.warning('分析未返回结果，请检查 API Key 配置')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '分析失败')
  } finally {
    analyzing.value = false
  }
}

function resetForm() {
  form.symbols = ['BTCUSDT', 'ETHUSDT']
  form.timeframe = '1h'
  form.limit = 100
  form.style = '基本面+技术面'
  form.llm_api_key = ''
  form.llm_base_url = ''
  form.llm_model = ''
  klinePreview.value = []
  results.value = []
  errors.value = {}
  expandedIndex.value = null
}

function toggleExpand(index: number) {
  expandedIndex.value = expandedIndex.value === index ? null : index
}

function trendLabel(trend: string): string {
  const map: Record<string, string> = { bull: '看多', bear: '看空', neutral: '中性' }
  return map[trend] || trend
}

function trendTagType(trend: string): string {
  const map: Record<string, string> = { bull: 'danger', bear: 'success', neutral: 'warning' }
  return map[trend] || 'info'
}

function formatPrice(val?: number): string {
  if (!val) return '-'
  return val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })
}

function formatChange(item: any): string {
  const klines = item.klines
  if (klines.length < 2) return '-'
  const latest = klines[klines.length - 1]
  const prev = klines[klines.length - 2]
  if (!latest?.close || !prev?.close) return '-'
  const change = ((latest.close - prev.close) / prev.close * 100).toFixed(2)
  return `${change >= '0' ? '+' : ''}${change}%`
}

function getChangeClass(item: any): string {
  const klines = item.klines
  if (klines.length < 2) return ''
  const latest = klines[klines.length - 1]
  const prev = klines[klines.length - 2]
  if (!latest?.close || !prev?.close) return ''
  return latest.close >= prev.close ? 'positive' : 'negative'
}

function getPreviewText(text: string): string {
  if (!text) return ''
  // 取前200字作为预览
  const first = text.split('\n').slice(0, 5).join(' | ')
  return first.length > 200 ? first.slice(0, 200) + '...' : first
}

function createSignalFromResult(result: any) {
  signalForm.symbol = result.symbol
  signalForm.signal_type = result.trend === 'bull' ? 'buy' : result.trend === 'bear' ? 'sell' : 'hold'
  signalForm.timeframe = result.interval
  signalForm.entry_price = result.indicators?.latest_price || 0
  signalForm.reason = `[LLM分析 ${result.interval}] ${getPreviewText(result.raw_analysis)}`
  showSignalDialog.value = true
}

async function submitSignal() {
  signalCreating.value = true
  try {
    await analysisApi.createSignal({
      symbol: signalForm.symbol,
      signal_type: signalForm.signal_type,
      entry_price: signalForm.entry_price || undefined,
      stop_loss: signalForm.stop_loss || undefined,
      take_profit: signalForm.take_profit || undefined,
      timeframe: signalForm.timeframe,
      reason: signalForm.reason || undefined,
    })
    ElMessage.success('信号创建成功')
    showSignalDialog.value = false
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '创建失败')
  } finally {
    signalCreating.value = false
  }
}
</script>

<style scoped>
.analysis-container {
  padding: 20px;
  max-width: 1200px;
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

.config-card {
  margin-bottom: 20px;
}

.preview-section {
  margin-bottom: 24px;
}

.preview-section h3,
.results-section h3 {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.preview-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #ebeef5;
}

.symbol-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.symbol-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 4px;
}

.price {
  font-size: 16px;
  font-weight: 600;
}

.change {
  font-size: 12px;
}

.change.positive { color: #f56c6c; }
.change.negative { color: #67c23a; }

.symbol-meta {
  font-size: 11px;
  color: #909399;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  border-left: 4px solid #909399;
}

.result-card.trend-bull { border-left-color: #f56c6c; }
.result-card.trend-bear { border-left-color: #67c23a; }
.result-card.trend-neutral { border-left-color: #e6a23c; }

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.symbol-badge {
  font-weight: 700;
  font-size: 16px;
  padding: 2px 10px;
  border-radius: 4px;
  background: #ecf5ff;
  color: #409eff;
}

.symbol-badge.trend-bull { background: #fef0f0; color: #f56c6c; }
.symbol-badge.trend-bear { background: #f0f9eb; color: #67c23a; }
.symbol-badge.trend-neutral { background: #fdf6ec; color: #e6a23c; }

.kline-info {
  font-size: 12px;
  color: #909399;
}

.result-actions {
  display: flex;
  gap: 8px;
}

.indicators-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 8px;
}

.indicator-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.indicator-item .label {
  font-size: 11px;
  color: #909399;
}

.indicator-item .value {
  font-size: 14px;
  font-weight: 600;
}

.indicator-item .value.positive { color: #f56c6c; }
.indicator-item .value.negative { color: #67c23a; }

.analysis-content,
.analysis-preview {
  margin-top: 8px;
}

.preview-text {
  color: #606266;
  font-size: 13px;
}

.markdown-body {
  font-size: 14px;
  line-height: 1.7;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
}

.errors-section {
  margin-bottom: 16px;
}

.positive { color: #f56c6c; }
.negative { color: #67c23a; }
</style>
