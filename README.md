# PyQuantX - 加密货币量化交易系统

[![Python Version](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个功能完善的加密货币量化交易系统，支持策略交易、市场分析、模拟交易和实时监控。

## 功能特性

### 核心功能
- **多模式运行**：支持监控模式（monitor）和市场分析模式（analyzer）
- **策略交易**：趋势跟踪、均值回归、海龟交易等多种策略
- **市场分析**：集成大语言模型（LLM）进行 K 线数据分析
- **模拟交易**：完整模拟交易系统，支持账户管理、持仓追踪、订单执行
- **实时监控**：自动评估交易信号，多渠道推送通知

### 技术架构
- **双 API 客户端**：支持 ccxt（多交易所）和 Binance 官方 API
- **异步引擎**：基于 asyncio 的异步执行，支持高并发
- **技术指标**：MA、ATR、布林带、RSI（Wilder 平滑）等

### 通知渠道
- **终端输出**：控制台实时显示交易信号
- **钉钉机器人**：群聊推送交易警报
- **飞书机器人**：富文本/卡片消息推送，支持订单确认

## 项目结构

```
py-quantix/
├── main.py                      # CLI 主程序入口
├── config/
│   ├── config.example.yaml      # 配置示例
│   └── settings.py              # Pydantic 配置管理
├── core/
│   ├── engine.py               # 交易引擎（工厂模式）
│   ├── analyzer_runner.py       # 市场分析运行器
│   ├── analyzer.py             # LLM 分析模块
│   └── components.py            # 交易引擎组件
├── data/
│   └── fetchers/
│       ├── market_fetcher.py   # ccxt 数据获取
│       └── binance_client.py   # Binance 官方 API
├── strategies/
│   ├── base_strategy.py        # 策略基类
│   ├── trend_following.py      # 趋势跟踪
│   ├── mean_reversion.py       # 均值回归
│   └── turtle_trading.py        # 海龟交易
├── notifications/
│   ├── base.py                # 通知器基类
│   ├── dingtalk.py             # 钉钉通知
│   └── feishu.py               # 飞书通知
├── paper_trading/              # 模拟交易模块
│   ├── api.py                  # FastAPI REST 接口
│   ├── service.py              # 业务逻辑层
│   ├── storage.py              # 数据库仓储层
│   ├── engine.py               # 模拟交易引擎
│   └── feishu_integration.py   # 飞书订单确认集成
└── utils/
    ├── config_manager.py       # 配置管理
    ├── data_formatter.py       # K线数据格式化
    └── indicators.py           # 技术指标计算
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

```bash
cp config/config.example.yaml config/config.yaml
```

编辑 `config.yaml`：

```yaml
run_mode: monitor                    # monitor / analyzer
signal_output:
  - console

exchange:
  api_client: ccxt                  # ccxt 或 binance
  api_key: your_api_key
  api_secret: your_api_secret
  testnet: true
  proxy:
    http: "http://127.0.0.1:8001"
    https: "http://127.0.0.1:8001"

trading:
  symbols:
    - symbol: BTCUSDT
      leverage: 10
      position_size: 0.001
      strategy: trend_following

notifications:
  feishu:
    webhook_url: https://open.feishu.cn/...

llm:
  enabled: false
  api_key: your_minimax_api_key
```

### 3. 运行

```bash
# 策略监控模式
python main.py --mode monitor

# LLM 市场分析模式
python main.py --mode analyzer --once

# 启动模拟交易 API
python paper_trading_cli.py
```

## 交易策略

### 趋势跟踪 (TrendFollowing)
- 移动平均线交叉 + 动量指标
- ATR 动态止损止盈

### 均值回归 (MeanReversion)
- 布林带识别超买超卖
- RSI 辅助判断

### 海龟交易 (TurtleTrading)
- 唐奇安通道突破
- ATR 仓位管理

## API 接口

### 模拟交易 API

启动服务后访问 `http://localhost:8000/docs` 查看完整接口文档。

```
# 账户管理
GET    /api/accounts              # 账户列表
POST   /api/accounts             # 创建账户
GET    /api/accounts/{id}        # 账户详情

# 持仓与订单
GET    /api/accounts/{id}/positions    # 持仓列表
POST   /api/orders                    # 创建订单
DELETE /api/positions/{id}            # 平仓

# LLM 分析
GET    /api/analyzer/config           # LLM 配置状态
POST   /api/analyzer/analyze         # 执行市场分析

# 实时数据
GET    /api/events/stream            # SSE 实时推送

# 健康检查
GET    /health                      # 服务状态
GET    /ready                       # 就绪检查

# 设置管理
GET    /api/settings                 # 获取配置
PUT    /api/settings                 # 更新配置
DELETE /api/settings                 # 重置配置
```

### API 示例

```bash
# 创建模拟账户
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "initial_balance": 10000, "leverage": 10}'

# 创建订单
curl -X POST http://localhost:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"account_id": "xxx", "symbol": "BTCUSDT", "side": "buy", "quantity": 0.001, "price": 50000}'
```

## 前端项目

基于 Vue 3 + Element Plus 的模拟交易管理后台。

### 技术栈

- **框架**：Vue 3 + Composition API
- **构建工具**：Vite
- **UI 组件**：Element Plus
- **状态管理**：Pinia
- **路由**：Vue Router
- **图表**：ECharts
- **HTTP 客户端**：Axios

### 项目结构

```
dashboard/
├── src/
│   ├── main.ts              # 应用入口
│   ├── App.vue              # 根组件
│   ├── api/
│   │   └── index.ts        # API 请求封装
│   ├── router/
│   │   └── index.ts        # 路由配置
│   ├── stores/
│   │   └── app.ts         # Pinia 状态管理
│   └── views/
│       ├── Dashboard.vue    # 主页/概览
│       ├── Positions.vue    # 持仓列表
│       ├── OpenPosition.vue # 开仓
│       ├── ClosePosition.vue # 平仓
│       ├── History.vue     # 历史订单
│       ├── Statistics.vue  # 统计分析
│       ├── RiskManagement.vue # 风险管理
│       ├── Settings.vue    # 系统设置
│       └── Analysis.vue   # LLM 市场分析
├── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### 运行前端

```bash
cd dashboard

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 功能页面

| 页面 | 说明 |
|------|------|
| Dashboard | 账户概览、权益曲线、持仓分布 |
| Positions | 当前持仓列表，支持止损止盈设置 |
| OpenPosition | 开仓下单界面 |
| ClosePosition | 平仓确认 |
| History | 历史订单查询 |
| Statistics | 账户统计、收益率分析 |
| RiskManagement | 风险指标监控 |
| Settings | LLM/通知/交易参数配置 |
| Analysis | LLM 市场分析界面 |

## 命令行参数

```bash
python main.py --help

Options:
  --config CONFIG                配置文件路径
  --mode {auto,monitor,analyzer} 运行模式
  --once                         运行一次后退出
  --interval INTERVAL            轮询间隔（秒）
  --log-level {DEBUG,INFO,WARN,ERROR}
```

## 技术指标

| 指标 | 说明 |
|------|------|
| MA | 移动平均线 |
| ATR | 平均真实波幅（Wilder 平滑） |
| RSI | 相对强弱指数（Wilder 平滑） |
| Bollinger | 布林带 |
| Donchian | 唐奇安通道 |

## 风险提示

⚠️ 加密货币交易具有高风险：

1. 仅使用可承受损失的资金
2. 充分回测后再实盘
3. 定期监控策略表现
4. 做好仓位管理

本系统仅供学习研究，不构成投资建议。
