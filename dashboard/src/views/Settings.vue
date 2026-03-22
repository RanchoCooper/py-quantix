<template>
  <div class="settings-container">
    <div class="page-header">
      <h2>设置</h2>
      <p class="subtitle">系统配置，页面设置优先级高于 config.yaml</p>
    </div>

    <el-tabs v-model="activeTab" class="settings-tabs">
      <!-- 运行设置 -->
      <el-tab-pane label="运行" name="run">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>运行设置</span>
              <el-tag size="small" type="info">{{ form.run.run_mode }}</el-tag>
            </div>
          </template>

          <el-form :model="form.run" label-width="140px" @submit.prevent>
            <el-form-item label="运行模式">
              <el-select v-model="form.run.run_mode" style="width: 100%">
                <el-option value="monitor" label="monitor - 监控交易" />
                <el-option value="analyzer" label="analyzer - 市场分析" />
              </el-select>
              <span class="form-hint">monitor: 评估策略信号并发送通知<br>analyzer: LLM分析K线数据后推送</span>
            </el-form-item>

            <el-form-item label="信号输出">
              <el-checkbox-group v-model="form.run.signal_output">
                <el-checkbox label="console">终端</el-checkbox>
                <el-checkbox label="dingtalk">钉钉</el-checkbox>
                <el-checkbox label="feishu">飞书</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 交易所配置 -->
      <el-tab-pane label="交易所" name="exchange">
        <el-card>
          <template #header>
            <span>交易所配置</span>
          </template>

          <el-form :model="form.exchange" label-width="140px" @submit.prevent>
            <el-form-item label="API 客户端">
              <el-select v-model="form.exchange.api_client" style="width: 100%">
                <el-option value="ccxt" label="ccxt - 多交易所支持" />
                <el-option value="binance" label="binance - 官方API" />
              </el-select>
            </el-form-item>

            <el-form-item label="市场类型">
              <el-select v-model="form.exchange.mode" style="width: 100%">
                <el-option value="spot" label="现货" />
                <el-option value="futures" label="合约" />
                <el-option value="swap" label="永续" />
              </el-select>
            </el-form-item>

            <el-form-item label="使用 Testnet">
              <el-switch v-model="form.exchange.testnet" />
              <span class="form-hint">开启后从测试网络获取数据/下单</span>
            </el-form-item>

            <el-divider content-position="left">代理配置</el-divider>

            <el-form-item label="HTTP 代理">
              <el-input
                v-model="form.exchange.proxy.http"
                placeholder="http://127.0.0.1:8080"
                clearable
              />
            </el-form-item>

            <el-form-item label="HTTPS 代理">
              <el-input
                v-model="form.exchange.proxy.https"
                placeholder="http://127.0.0.1:8080"
                clearable
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 币安凭证 -->
      <el-tab-pane label="币安凭证" name="binance">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>币安凭证</span>
              <el-tag size="small" type="warning">敏感信息</el-tag>
            </div>
          </template>

          <el-alert type="warning" :closable="false" show-icon style="margin-bottom: 16px">
            API 密钥用于访问币安账户，请妥善保管，切勿泄露给他人
          </el-alert>

          <el-form :model="form.binance" label-width="140px" @submit.prevent>
            <el-form-item label="API Key">
              <el-input
                v-model="form.binance.api_key"
                type="password"
                show-password
                placeholder="输入 API Key（留空保持已保存的值）"
                clearable
              />
              <span class="form-hint">
                <el-tag v-if="form.binance.api_key_configured" type="success" size="small">已配置</el-tag>
                <el-tag v-else type="info" size="small">未配置</el-tag>
              </span>
            </el-form-item>

            <el-form-item label="API Secret">
              <el-input
                v-model="form.binance.api_secret"
                type="password"
                show-password
                placeholder="输入 API Secret（留空保持已保存的值）"
                clearable
              />
              <span class="form-hint">
                <el-tag v-if="form.binance.api_secret_configured" type="success" size="small">已配置</el-tag>
                <el-tag v-else type="info" size="small">未配置</el-tag>
              </span>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 策略参数 -->
      <el-tab-pane label="策略" name="strategies">
        <el-card>
          <template #header>
            <span>策略参数配置</span>
          </template>

          <el-form :model="form.strategies" label-width="160px" @submit.prevent>
            <el-divider content-position="left">趋势跟随策略</el-divider>

            <el-form-item label="移动平均周期">
              <el-input-number
                v-model="form.strategies.trend_following.period"
                :min="1"
                :max="100"
              />
              <span class="form-hint">短期均线周期</span>
            </el-form-item>

            <el-form-item label="倍数">
              <el-input-number
                v-model="form.strategies.trend_following.multiplier"
                :min="0.1"
                :max="10"
                :step="0.1"
                :precision="1"
              />
              <span class="form-hint">均线倍数</span>
            </el-form-item>

            <el-divider content-position="left">均值回归策略</el-divider>

            <el-form-item label="移动平均周期">
              <el-input-number
                v-model="form.strategies.mean_reversion.period"
                :min="1"
                :max="100"
              />
              <span class="form-hint">布林带周期</span>
            </el-form-item>

            <el-form-item label="标准差倍数">
              <el-input-number
                v-model="form.strategies.mean_reversion.std_dev_multiplier"
                :min="0.5"
                :max="5"
                :step="0.1"
                :precision="1"
              />
              <span class="form-hint">布林带标准差倍数</span>
            </el-form-item>

            <el-divider content-position="left">海龟交易策略</el-divider>

            <el-form-item label="入场周期">
              <el-input-number
                v-model="form.strategies.turtle_trading.entry_period"
                :min="1"
                :max="100"
              />
              <span class="form-hint">唐奇安通道周期</span>
            </el-form-item>

            <el-form-item label="出场周期">
              <el-input-number
                v-model="form.strategies.turtle_trading.exit_period"
                :min="1"
                :max="100"
              />
            </el-form-item>

            <el-form-item label="ATR 周期">
              <el-input-number
                v-model="form.strategies.turtle_trading.atr_period"
                :min="1"
                :max="100"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 通知配置 -->
      <el-tab-pane label="通知" name="notifications">
        <el-card>
          <template #header>
            <span>通知配置</span>
          </template>

          <el-form :model="form.notifications" label-width="140px" @submit.prevent>
            <el-divider content-position="left">钉钉</el-divider>

            <el-form-item label="启用钉钉">
              <el-switch v-model="form.notifications.dingtalk.enabled" />
            </el-form-item>

            <el-form-item label="Webhook URL">
              <el-input
                v-model="form.notifications.dingtalk.webhook_url"
                placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
                clearable
              />
            </el-form-item>

            <el-form-item label="签名密钥">
              <el-input
                v-model="form.notifications.dingtalk.secret"
                type="password"
                show-password
                placeholder="钉钉签名密钥"
                clearable
              />
            </el-form-item>

            <el-divider content-position="left">飞书</el-divider>

            <el-form-item label="启用飞书">
              <el-switch v-model="form.notifications.feishu.enabled" />
            </el-form-item>

            <el-form-item label="Webhook URL">
              <el-input
                v-model="form.notifications.feishu.webhook_url"
                placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
                clearable
              />
            </el-form-item>

            <el-form-item label="模板 ID">
              <el-input
                v-model="form.notifications.feishu.template_id"
                placeholder="消息模板 ID"
                clearable
              />
            </el-form-item>

            <el-form-item label="模板版本">
              <el-input
                v-model="form.notifications.feishu.template_version"
                placeholder="1.0.0"
                clearable
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 日志配置 -->
      <el-tab-pane label="日志" name="logging">
        <el-card>
          <template #header>
            <span>日志配置</span>
          </template>

          <el-form :model="form.logging" label-width="140px" @submit.prevent>
            <el-form-item label="日志级别">
              <el-select v-model="form.logging.level" style="width: 100%">
                <el-option value="DEBUG" label="DEBUG - 调试" />
                <el-option value="INFO" label="INFO - 信息" />
                <el-option value="WARNING" label="WARNING - 警告" />
                <el-option value="ERROR" label="ERROR - 错误" />
              </el-select>
            </el-form-item>

            <el-form-item label="日志文件">
              <el-input
                v-model="form.logging.file"
                placeholder="logs/trading.log"
                clearable
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- LLM 分析 -->
      <el-tab-pane label="LLM" name="llm">
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

            <el-divider content-position="left">代理配置</el-divider>

            <el-form-item label="HTTP 代理">
              <el-input
                v-model="form.llm.proxy.http"
                placeholder="http://127.0.0.1:8080"
                clearable
              />
            </el-form-item>

            <el-form-item label="HTTPS 代理">
              <el-input
                v-model="form.llm.proxy.https"
                placeholder="http://127.0.0.1:8080"
                clearable
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 市场数据 -->
      <el-tab-pane label="市场数据" name="market_data">
        <el-card>
          <template #header>
            <span>市场数据配置</span>
          </template>

          <el-form :model="form.market_data" label-width="140px" @submit.prevent>
            <el-form-item label="K 线周期">
              <el-select v-model="form.market_data.interval" style="width: 100%">
                <el-option value="1m" label="1 分钟" />
                <el-option value="5m" label="5 分钟" />
                <el-option value="15m" label="15 分钟" />
                <el-option value="30m" label="30 分钟" />
                <el-option value="1h" label="1 小时" />
                <el-option value="4h" label="4 小时" />
                <el-option value="1d" label="1 天" />
                <el-option value="1w" label="1 周" />
              </el-select>
            </el-form-item>

            <el-form-item label="K 线数量">
              <el-input-number
                v-model="form.market_data.limit"
                :min="10"
                :max="1000"
                :step="10"
              />
              <span class="form-hint">每次获取的K线数量 (10-1000)</span>
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

const activeTab = ref('run')
const saving = ref(false)

// 表单数据结构 - 与 config.yaml 配置项对应
const form = reactive({
  run: {
    run_mode: 'monitor',
    signal_output: ['console'],
  },
  exchange: {
    api_client: 'ccxt',
    testnet: true,
    mode: 'futures',
    proxy: {
      http: '',
      https: '',
    },
  },
  binance: {
    api_key: '',
    api_key_configured: false,
    api_secret: '',
    api_secret_configured: false,
  },
  trading: {
    confirm_via_feishu: false,
  },
  strategies: {
    trend_following: {
      period: 25,
      multiplier: 1,
    },
    mean_reversion: {
      period: 30,
      std_dev_multiplier: 3,
    },
    turtle_trading: {
      entry_period: 20,
      exit_period: 10,
      atr_period: 15,
    },
  },
  notifications: {
    dingtalk: {
      webhook_url: '',
      secret: '',
      enabled: false,
    },
    feishu: {
      webhook_url: '',
      template_id: '',
      template_version: '',
      enabled: true,
    },
  },
  logging: {
    level: 'INFO',
    file: 'logs/trading.log',
  },
  llm: {
    enabled: false,
    api_key: '',
    api_key_configured: false,
    base_url: 'https://api.minimax.chat/v1',
    model: 'Claude Opus-4.6',
    style: '基本面+技术面',
    style_options: ['基本面+技术面', '纯技术面', '波段交易', '趋势跟踪', '均值回归'],
    proxy: {
      http: '',
      https: '',
    },
  },
  market_data: {
    interval: '1h',
    limit: 100,
  },
  system: {
    db_path: '',
    api_port: 8000,
  },
})

onMounted(async () => {
  try {
    const data = await settingsApi.get()
    if (data.run) {
      form.run.run_mode = data.run.run_mode || 'monitor'
      form.run.signal_output = data.run.signal_output || ['console']
    }
    if (data.exchange) {
      form.exchange.api_client = data.exchange.api_client || 'ccxt'
      form.exchange.testnet = data.exchange.testnet ?? true
      form.exchange.mode = data.exchange.mode || 'futures'
      if (data.exchange.proxy) {
        form.exchange.proxy.http = data.exchange.proxy.http || ''
        form.exchange.proxy.https = data.exchange.proxy.https || ''
      }
    }
    if (data.binance) {
      form.binance.api_key_configured = data.binance.api_key_configured ?? false
      form.binance.api_secret_configured = data.binance.api_secret_configured ?? false
    }
    if (data.trading) {
      form.trading.confirm_via_feishu = data.trading.confirm_via_feishu ?? false
    }
    if (data.strategies) {
      if (data.strategies.trend_following) {
        form.strategies.trend_following.period = data.strategies.trend_following.period ?? 25
        form.strategies.trend_following.multiplier = data.strategies.trend_following.multiplier ?? 1
      }
      if (data.strategies.mean_reversion) {
        form.strategies.mean_reversion.period = data.strategies.mean_reversion.period ?? 30
        form.strategies.mean_reversion.std_dev_multiplier = data.strategies.mean_reversion.std_dev_multiplier ?? 3
      }
      if (data.strategies.turtle_trading) {
        form.strategies.turtle_trading.entry_period = data.strategies.turtle_trading.entry_period ?? 20
        form.strategies.turtle_trading.exit_period = data.strategies.turtle_trading.exit_period ?? 10
        form.strategies.turtle_trading.atr_period = data.strategies.turtle_trading.atr_period ?? 15
      }
    }
    if (data.notifications) {
      if (data.notifications.dingtalk) {
        form.notifications.dingtalk.webhook_url = data.notifications.dingtalk.webhook_url || ''
        form.notifications.dingtalk.secret = data.notifications.dingtalk.secret || ''
        form.notifications.dingtalk.enabled = data.notifications.dingtalk.enabled ?? false
      }
      if (data.notifications.feishu) {
        form.notifications.feishu.webhook_url = data.notifications.feishu.webhook_url || ''
        form.notifications.feishu.template_id = data.notifications.feishu.template_id || ''
        form.notifications.feishu.template_version = data.notifications.feishu.template_version || ''
        form.notifications.feishu.enabled = data.notifications.feishu.enabled ?? true
      }
    }
    if (data.logging) {
      form.logging.level = data.logging.level || 'INFO'
      form.logging.file = data.logging.file || 'logs/trading.log'
    }
    if (data.llm) {
      form.llm.enabled = data.llm.enabled ?? false
      form.llm.api_key_configured = data.llm.api_key_configured ?? false
      form.llm.base_url = data.llm.base_url || 'https://api.minimax.chat/v1'
      form.llm.model = data.llm.model || 'Claude Opus-4.6'
      form.llm.style = data.llm.style || '基本面+技术面'
      if (data.llm.proxy) {
        form.llm.proxy.http = data.llm.proxy.http || ''
        form.llm.proxy.https = data.llm.proxy.https || ''
      }
    }
    if (data.market_data) {
      form.market_data.interval = data.market_data.interval || '1h'
      form.market_data.limit = data.market_data.limit ?? 100
    }
    if (data.system) {
      form.system.db_path = data.system.db_path || ''
      form.system.api_port = data.system.api_port ?? 8000
    }
  } catch (e: any) {
    ElMessage.warning('无法加载设置，使用默认值')
  }
})

async function saveSettings() {
  saving.value = true
  try {
    const payload: Record<string, any> = {}

    // 运行设置
    payload.run = {
      run_mode: form.run.run_mode,
      signal_output: form.run.signal_output,
    }

    // 交易所设置
    payload.exchange = {
      api_client: form.exchange.api_client,
      testnet: form.exchange.testnet,
      mode: form.exchange.mode,
      proxy: {
        http: form.exchange.proxy.http,
        https: form.exchange.proxy.https,
      },
    }

    // 币安凭证（只发送非空值）
    if (form.binance.api_key) {
      payload.binance = { api_key: form.binance.api_key }
    }
    if (form.binance.api_secret) {
      payload.binance = payload.binance || {}
      payload.binance.api_secret = form.binance.api_secret
    }

    // 交易设置
    payload.trading = {
      confirm_via_feishu: form.trading.confirm_via_feishu,
    }

    // 策略设置
    payload.strategies = {
      trend_following: {
        period: form.strategies.trend_following.period,
        multiplier: form.strategies.trend_following.multiplier,
      },
      mean_reversion: {
        period: form.strategies.mean_reversion.period,
        std_dev_multiplier: form.strategies.mean_reversion.std_dev_multiplier,
      },
      turtle_trading: {
        entry_period: form.strategies.turtle_trading.entry_period,
        exit_period: form.strategies.turtle_trading.exit_period,
        atr_period: form.strategies.turtle_trading.atr_period,
      },
    }

    // 通知设置
    payload.notifications = {
      dingtalk: {
        webhook_url: form.notifications.dingtalk.webhook_url,
        secret: form.notifications.dingtalk.secret,
        enabled: form.notifications.dingtalk.enabled,
      },
      feishu: {
        webhook_url: form.notifications.feishu.webhook_url,
        template_id: form.notifications.feishu.template_id,
        template_version: form.notifications.feishu.template_version,
        enabled: form.notifications.feishu.enabled,
      },
    }

    // 日志设置
    payload.logging = {
      level: form.logging.level,
      file: form.logging.file,
    }

    // LLM 设置
    const llmPayload: Record<string, any> = {
      enabled: form.llm.enabled,
      base_url: form.llm.base_url,
      model: form.llm.model,
      style: form.llm.style,
      proxy: {
        http: form.llm.proxy.http,
        https: form.llm.proxy.https,
      },
    }
    if (form.llm.api_key) {
      llmPayload.api_key = form.llm.api_key
    }
    payload.llm = llmPayload

    // 市场数据设置
    payload.market_data = {
      interval: form.market_data.interval,
      limit: form.market_data.limit,
    }

    await settingsApi.update(payload)
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
    // 重新加载数据
    if (data.run) {
      form.run.run_mode = data.run.run_mode
      form.run.signal_output = data.run.signal_output
    }
    if (data.exchange) {
      form.exchange.api_client = data.exchange.api_client
      form.exchange.testnet = data.exchange.testnet
      form.exchange.mode = data.exchange.mode
      if (data.exchange.proxy) {
        form.exchange.proxy.http = data.exchange.proxy.http
        form.exchange.proxy.https = data.exchange.proxy.https
      }
    }
    form.binance.api_key = ''
    form.binance.api_secret = ''
    if (data.binance) {
      form.binance.api_key_configured = data.binance.api_key_configured
      form.binance.api_secret_configured = data.binance.api_secret_configured
    }
    if (data.strategies) {
      if (data.strategies.trend_following) {
        form.strategies.trend_following.period = data.strategies.trend_following.period ?? 25
        form.strategies.trend_following.multiplier = data.strategies.trend_following.multiplier ?? 1
      }
      if (data.strategies.mean_reversion) {
        form.strategies.mean_reversion.period = data.strategies.mean_reversion.period ?? 30
        form.strategies.mean_reversion.std_dev_multiplier = data.strategies.mean_reversion.std_dev_multiplier ?? 3
      }
      if (data.strategies.turtle_trading) {
        form.strategies.turtle_trading.entry_period = data.strategies.turtle_trading.entry_period ?? 20
        form.strategies.turtle_trading.exit_period = data.strategies.turtle_trading.exit_period ?? 10
        form.strategies.turtle_trading.atr_period = data.strategies.turtle_trading.atr_period ?? 15
      }
    }
    if (data.notifications) {
      if (data.notifications.dingtalk) {
        form.notifications.dingtalk = data.notifications.dingtalk
      }
      if (data.notifications.feishu) {
        form.notifications.feishu = data.notifications.feishu
      }
    }
    if (data.logging) {
      form.logging = data.logging
    }
    form.llm.api_key = ''
    if (data.llm) {
      form.llm.enabled = data.llm.enabled
      form.llm.api_key_configured = data.llm.api_key_configured
      form.llm.base_url = data.llm.base_url
      form.llm.model = data.llm.model
      form.llm.style = data.llm.style
      if (data.llm.proxy) {
        form.llm.proxy = data.llm.proxy
      }
    }
    if (data.market_data) {
      form.market_data = data.market_data
    }
    if (data.system) {
      form.system = data.system
    }
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
  max-width: 900px;
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
  line-height: 1.4;
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
