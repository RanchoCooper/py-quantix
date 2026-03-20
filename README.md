# PyQuantX - 加密货币量化交易系统

[![Python Version](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个功能完善的加密货币合约量化交易系统，支持策略交易、市场分析、实时监控和回测。

## 功能特性

### 核心功能
- **多模式运行**：支持监控模式（monitor）和市场分析模式（analyzer）
- **策略交易**：趋势跟踪、均值回归、海龟交易等多种策略
- **市场分析**：集成大语言模型（LLM）进行 K 线数据分析
- **实时监控**：自动评估交易信号，推送通知
- **异步引擎**：基于 asyncio 的异步策略执行引擎
- **数据持久化**：K线数据本地缓存和文件存储

### 通知渠道
- **终端输出**：控制台实时显示交易信号
- **钉钉机器人**：群聊推送交易警报
- **飞书机器人**：富文本/卡片消息推送

### 数据支持
- **多交易所支持**：基于 ccxt 支持 Binance、OKX、Bybit 等
- **K线数据**：支持多个交易对、多种时间周期
- **实时行情**：ticker、order_book、funding_rate
- **技术指标**：MA、ATR、布林带、RSI、EMA、SMA 等

## 环境要求

- Python 3.8+
- 币安合约账户（测试网/实盘）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

复制示例配置并编辑：

```bash
cp config/config.example.yaml config/config.yaml
```

编辑 `config.yaml`：

```yaml
# 运行模式: monitor (监控交易) / analyzer (市场分析)
run_mode: monitor

# 信号输出: console, dingtalk, feishu (可多选)
signal_output:
  - console
  - feishu

binance:
  api_key: your_api_key
  api_secret: your_api_secret
  testnet: true

trading:
  symbols:
    - symbol: BTCUSDT
      leverage: 10
      position_size: 0.001
      strategy: trend_following

notifications:
  dingtalk:
    webhook_url: https://oapi.dingtalk.com/robot/send?access_token=xxx
    secret: xxx
  feishu:
    webhook_url: https://open.feishu.cn/open-apis/bot/v2/hook/xxx
    secret: xxx

llm:
  enabled: true
  api_key: your_minimax_api_key
  model: "Claude Opus-4.6"
```

### 3. 运行系统

```bash
# 默认从配置文件读取模式
python main.py

# 覆盖为监控模式（不执行交易，只发通知）
python main.py --mode monitor

# 覆盖为分析模式（LLM 分析 + 推送）
python main.py --mode analyzer

# 运行一次后退出
python main.py --once

# 自定义轮询间隔（秒）
python main.py --interval 1800
```

## 使用说明

### 运行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `monitor` | 评估策略信号，发送通知 | 策略监控、信号推送 |
| `analyzer` | 获取 K 线 → LLM 分析 → 推送结果 | 市场分析、研究辅助 |

### 命令行参数

```bash
python main.py --help

Options:
  --config CONFIG       配置文件路径
  --mode {auto,monitor,analyzer}  运行模式
  --once               运行一次后退出
  --interval INTERVAL  轮询间隔（秒）
  --log-level LEVEL    日志级别
```

### 配置文件

支持 YAML 和 JSON 格式，关键配置项：

```yaml
run_mode: monitor          # 运行模式
signal_output: [console]   # 输出渠道

binance:                   # 币安 API
trading:                   # 交易配置
notifications:              # 通知渠道
llm:                       # LLM 分析配置
market_data:               # K线数据配置
```

## 项目结构

```
py-quantix/
├── main.py                      # 程序入口
├── config/
│   ├── config.example.yaml      # 配置示例
│   ├── config.yaml              # 实际配置
│   └── settings.py              # pydantic 配置管理
├── core/
│   ├── engine.py                # 交易引擎 + 工厂函数
│   ├── strategy_engine.py       # 异步策略引擎
│   ├── analyzer_runner.py       # 市场分析器
│   ├── analyzer.py              # LLM 分析模块
│   ├── binance_client.py       # 币安 API 客户端
│   └── backtester.py            # 回测模块
├── data/                        # 数据层 (新增)
│   ├── fetchers/
│   │   └── market_fetcher.py    # ccxt 市场数据获取
│   └── storage/
│       └── candle_store.py     # K线数据存储
├── strategy/                    # 策略模块 (新增)
│   ├── models.py                # Signal, Position 数据结构
│   └── utils.py                 # 仓位/止损止盈计算工具
├── strategies/
│   ├── base_strategy.py         # 策略基类
│   ├── trend_following.py       # 趋势跟踪
│   ├── mean_reversion.py        # 均值回归
│   └── turtle_trading.py        # 海龟交易
├── notifications/
│   ├── dingtalk.py              # 钉钉通知
│   └── feishu.py                # 飞书通知
└── utils/
    ├── config_manager.py        # 配置管理 (兼容)
    ├── data_formatter.py        # 数据格式化
    └── logger.py                # 日志工具
```

## 交易策略

### 趋势跟踪策略 (TrendFollowing)
- 基于移动平均线交叉 + 动量指标
- 入场：短均线金叉且动量为正
- 止损止盈：基于 ATR 动态计算

### 均值回归策略 (MeanReversion)
- 基于布林带识别超买超卖
- 入场：价格突破布林带上下轨
- 风险管理：固定比例仓位

### 海龟交易策略 (TurtleTrading)
- 基于唐奇安通道突破
- 入场：价格突破 N 日最高/最低
- 仓位管理：基于 ATR 动态调整

## API 集成

### 新版数据获取 (基于 ccxt)

```python
import asyncio
from data.fetchers import MarketFetcher
from data.storage import CandleStore

async def main():
    # 初始化数据获取器
    fetcher = MarketFetcher(exchange_id="binance", testnet=True)

    # 获取 K 线数据
    candles = await fetcher.fetch_ohlcv("BTC/USDT:USDT", "1h", limit=100)
    print(f"获取到 {len(candles)} 根 K 线")

    # 获取实时行情
    ticker = await fetcher.fetch_ticker("BTC/USDT:USDT")
    print(f"当前价格: {ticker['last']}")

    # 获取账户余额
    balance = await fetcher.fetch_balance()
    print(f"USDT 余额: {balance['USDT']}")

    # 初始化数据存储
    store = CandleStore(data_path="./data/storage")
    store.add_candles("BTC/USDT:USDT", "1h", candles)

    # 保存到文件
    store.save_to_file("BTC/USDT:USDT", "1h")

    # 获取 DataFrame
    df = store.get_candles_dataframe("BTC/USDT:USDT", "1h")
    print(df.tail())

asyncio.run(main())
```

### 策略工具函数

```python
from strategy.utils import (
    calculate_position_size,
    calculate_stop_loss,
    calculate_take_profit,
    calculate_pnl,
    calculate_atr,
)

# 仓位计算
size = calculate_position_size(balance=10000, price=50000, risk_pct=0.02)
print(f"建议仓位: {size} BTC")

# 止损止盈
stop_loss = calculate_stop_loss(entry_price=50000, side="long", risk_pct=0.01)
take_profit = calculate_take_profit(entry_price=50000, side="long", reward_pct=0.02)
print(f"止损: {stop_loss}, 止盈: {take_profit}")

# 盈亏计算
pnl = calculate_pnl(entry_price=50000, current_price=55000, side="long", amount=0.1)
print(f"盈亏: {pnl} USDT")
```

### 信号与持仓

```python
from strategy.models import Signal, SignalType, Position

# 创建信号
signal = Signal(
    signal_type=SignalType.BUY,
    symbol="BTC/USDT:USDT",
    price=50000,
    amount=0.1,
    stop_loss=49000,
    take_profit=52000,
    reason="趋势突破"
)

# 创建持仓
position = Position(
    symbol="BTC/USDT:USDT",
    side="long",
    amount=0.1,
    entry_price=50000
)
```

### 异步策略引擎

```python
import asyncio
from core.strategy_engine import StrategyEngine
from strategies.trend_following import TrendFollowingStrategy

async def main():
    # 创建引擎
    engine = StrategyEngine(
        exchange_id="binance",
        testnet=True,
        data_path="./data/storage"
    )

    # 添加策略
    strategy = TrendFollowingStrategy(
        name="my_strategy",
        symbol="BTC/USDT:USDT",
        timeframe="1h",
        period=14,
        multiplier=2
    )
    engine.add_strategy(strategy)

    # 设置信号回调
    async def on_signal(signal):
        print(f"收到信号: {signal}")

    engine.on_signal = on_signal

    # 初始化并启动
    await engine.initialize()
    await engine.start()

    # 运行一段时间后停止
    await asyncio.sleep(3600)
    await engine.stop()

asyncio.run(main())
```

### 通知发送

```python
from notifications.feishu import FeishuNotifier
from notifications.dingtalk import DingTalkNotifier

# 飞书通知
feishu = FeishuNotifier(webhook_url="xxx", secret="xxx")
feishu.send_analysis_report("BTCUSDT", analysis_result, "bull")

# 钉钉通知
dingtalk = DingTalkNotifier(webhook_url="xxx", secret="xxx")
dingtalk.send_trade_notification("BTCUSDT", "buy", 50000.0)
```

### 配置管理 (pydantic-settings)

```python
from config import get_settings, Settings

# 从 YAML 加载
settings = get_settings(config_path="config/config.yaml")

# 访问配置
print(settings.exchange.api_key)
print(settings.trading.symbols)
print(settings.data.timeframes)

# 或直接使用环境变量
# EXCHANGE_API_KEY=xxx python script.py
```

## 风险提示

⚠️ 加密货币交易具有高风险，请确保：

1. 仅使用可承受损失的资金
2. 充分测试后再实盘
3. 理解每个策略的风险特征
4. 定期监控和调整策略参数

本系统仅供学习和研究，不构成投资建议。
