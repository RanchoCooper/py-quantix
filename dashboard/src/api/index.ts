import axios from 'axios'
import type { AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 响应拦截器：自动解包 data
api.interceptors.response.use(
  <T = any>(response: AxiosResponse<T>) => response.data as T,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

// ==================== 类型定义 ====================

export interface Account {
  id: string
  name: string
  initial_balance: number
  balance: number
  frozen_margin: number
  available_balance: number
  total_pnl: number
  total_pnl_pct: number
  leverage: number
  created_at: string
  updated_at: string
}

export interface Position {
  id: string
  account_id: string
  symbol: string
  side: 'long' | 'short'
  quantity: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  stop_loss: number | null
  take_profit: number | null
  opened_at: string
  updated_at: string
}

export interface Order {
  id: string
  account_id: string
  symbol: string
  side: 'buy' | 'sell'
  position_side: 'long' | 'short' | null
  order_type: 'market' | 'limit'
  quantity: number
  price: number | null
  filled_price: number | null
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  position_id: string | null
  signal_id: string | null
  fee: number
  pnl: number | null
  source: 'manual' | 'feishu' | 'analyzer'
  reason: string | null
  created_at: string
  filled_at: string | null
}

export interface Signal {
  id: string
  symbol: string
  timeframe: string | null
  signal_type: 'buy' | 'sell' | 'hold'
  reason: string | null
  entry_price: number | null
  stop_loss: number | null
  take_profit: number | null
  status: 'pending' | 'confirmed' | 'rejected' | 'expired'
  created_at: string
  confirmed_at: string | null
}

export interface AccountStats {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  total_pnl: number
  total_pnl_pct: number
  avg_win: number
  avg_loss: number
  profit_factor: number
  largest_win: number
  largest_loss: number
  current_positions: number
  open_position_pnl: number
}

export interface DailyStats {
  id: string
  account_id: string
  date: string
  opening_balance: number
  closing_balance: number
  daily_pnl: number
  daily_pnl_pct: number
  trade_count: number
  win_count: number
  lose_count: number
  largest_win: number
  largest_loss: number
  win_rate: number
}

export interface EquityPoint {
  date: string
  balance: number
  daily_pnl: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ==================== API 方法 ====================

// 账户
export const accountApi = {
  list: () => api.get<Account[]>('/accounts'),
  create: (data: { name: string; initial_balance: number; leverage: number }) =>
    api.post<Account>('/accounts', data),
  get: (id: string) => api.get<Account>(`/accounts/${id}`),
  update: (id: string, data: { name?: string; leverage?: number }) =>
    api.put<Account>(`/accounts/${id}`, data),
  delete: (id: string) => api.delete(`/accounts/${id}`),
  stats: (id: string) => api.get<AccountStats>(`/accounts/${id}/stats`),
  equityCurve: (id: string, days?: number) =>
    api.get<EquityPoint[]>(`/accounts/${id}/equity-curve`, { params: { days } }),
  dailyStats: (id: string, page = 1, pageSize = 30) =>
    api.get<PaginatedResponse<DailyStats>>(`/accounts/${id}/stats/daily`, {
      params: { page, page_size: pageSize },
    }),
}

// 持仓
export const positionApi = {
  list: (accountId: string) =>
    api.get<Position[]>(`/accounts/${accountId}/positions`),
  update: (id: string, data: { stop_loss?: number; take_profit?: number }) =>
    api.put<Position>(`/positions/${id}`, data),
  close: (id: string, exitPrice: number) =>
    api.delete(`/positions/${id}`, { params: { exit_price: exitPrice } }),
}

// 订单
export const orderApi = {
  list: (
    accountId: string,
    params?: { page?: number; page_size?: number; symbol?: string; side?: string; status?: string }
  ) =>
    api.get<PaginatedResponse<Order>>(`/accounts/${accountId}/orders`, { params }),
  create: (data: {
    account_id: string
    symbol: string
    side: 'buy' | 'sell'
    position_side?: 'long' | 'short'
    quantity: number
    price: number
    stop_loss?: number
    take_profit?: number
    source?: string
    signal_id?: string
    reason?: string
    position_id?: string
  }) => api.post('/orders', data),
  pending: () => api.get<Order[]>('/orders/pending'),
}

// 飞书
export const feishuApi = {
  signals: () => api.get<Signal[]>('/feishu/signals'),
}

// 信号
export const signalApi = {
  create: (data: {
    symbol: string
    signal_type: string
    timeframe?: string
    reason?: string
    entry_price?: number
    stop_loss?: number
    take_profit?: number
  }) => api.post<Signal>('/signals', data),
}

// 价格更新
export const priceApi = {
  update: (accountId: string, prices: Record<string, number>) =>
    api.post('/prices/update', prices, { params: { account_id: accountId } }),
}

// 分析相关
export interface KLineDataPoint {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface SymbolKLineResponse {
  symbol: string
  interval: string
  klines: KLineDataPoint[]
  fetched_at: string
}

export interface AnalysisResult {
  symbol: string
  timestamp: string
  interval: string
  trend: 'bull' | 'bear' | 'neutral'
  kline_count: number
  raw_analysis: string
  indicators: Record<string, any>
}

export interface AnalysisResponse {
  timestamp: string
  results: AnalysisResult[]
  errors: Record<string, string>
}

export interface LLMConfig {
  configured: boolean
  model: string | null
  base_url: string | null
  style_options: string[]
}

export interface TimeframeOption {
  value: string
  label: string
}

export interface PopularSymbol {
  value: string
  label: string
}

export const analysisApi = {
  getConfig: (): Promise<LLMConfig> => api.get('/analyzer/config'),
  getTimeframes: (): Promise<{ options: TimeframeOption[] }> => api.get('/analyzer/timeframes'),
  getPopularSymbols: (): Promise<{ symbols: PopularSymbol[] }> => api.get('/analyzer/symbols/popular'),
  fetchKlines: (data: { symbols: string[]; timeframe: string; limit: number }): Promise<SymbolKLineResponse[]> =>
    api.post('/analyzer/klines', data),
  analyze: (data: {
    symbols: string[]
    timeframe: string
    limit: number
    style: string
    llm_api_key?: string
    llm_base_url?: string
    llm_model?: string
  }): Promise<AnalysisResponse> => api.post('/analyzer/analyze', data),
  createSignal: (data: {
    symbol: string
    signal_type: string
    timeframe?: string
    reason?: string
    entry_price?: number
    stop_loss?: number
    take_profit?: number
  }): Promise<Signal> => api.post('/signals', data),
}

// 设置相关 - 与 config.yaml 配置项对应
export interface ProxySettings {
  http: string
  https: string
}

export interface RunSettings {
  run_mode: string
  signal_output: string[]
}

export interface ExchangeSettings {
  api_client: string
  testnet: boolean
  mode: string
  proxy: ProxySettings
}

export interface BinanceSettings {
  api_key?: string
  api_key_configured: boolean
  api_secret?: string
  api_secret_configured: boolean
}

export interface StrategyParams {
  period: number | undefined
  multiplier: number | undefined
  std_dev_multiplier: number | undefined
  entry_period: number | undefined
  exit_period: number | undefined
  atr_period: number | undefined
}

export interface StrategiesSettings {
  trend_following: StrategyParams
  mean_reversion: StrategyParams
  turtle_trading: StrategyParams
}

export interface DingtalkSettings {
  webhook_url: string
  secret: string
  enabled: boolean
}

export interface FeishuSettings {
  webhook_url: string
  template_id: string
  template_version: string
  enabled: boolean
}

export interface NotificationSettings {
  dingtalk: DingtalkSettings
  feishu: FeishuSettings
}

export interface LoggingSettings {
  level: string
  file: string
}

export interface LLMSettings {
  enabled: boolean
  api_key?: string
  api_key_configured: boolean
  base_url: string
  model: string
  style: string
  style_options: string[]
  proxy: ProxySettings
}

export interface MarketDataSettings {
  interval: string
  limit: number
}

export interface SystemSettings {
  db_path: string
  api_port: number
}

export interface TradingSettings {
  confirm_via_feishu: boolean
}

export interface AppSettings {
  run: RunSettings
  exchange: ExchangeSettings
  binance: BinanceSettings
  trading: TradingSettings
  strategies: StrategiesSettings
  notifications: NotificationSettings
  logging: LoggingSettings
  llm: LLMSettings
  market_data: MarketDataSettings
  system: SystemSettings
}

export const settingsApi = {
  get: (): Promise<AppSettings> => api.get('/settings'),
  getDefaults: (): Promise<AppSettings> => api.get('/settings/defaults'),
  update: (data: Partial<AppSettings>): Promise<AppSettings> =>
    api.put('/settings', data),
  reset: (): Promise<AppSettings> => api.delete('/settings'),
}

export default api
