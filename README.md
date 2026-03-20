# PyQuantX - 加密货币量化交易系统

[![Python Version](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个功能完善的加密货币合约量化交易系统，支持策略交易、市场分析、实时监控和回测。

## 功能特性

### 核心功能
- **多模式运行**：支持监控模式（monitor）和市场分析模式（analyser）
- **策略交易**：趋势跟踪、均值回归、海龟交易等多种策略
- **市场分析**：集成大语言模型（LLM）进行 K 线数据分析
- **实时监控**：自动评估交易信号，推送通知

### 通知渠道
- **终端输出**：控制台实时显示交易信号
- **钉钉机器人**：群聊推送交易警报
- **飞书机器人**：富文本/卡片消息推送

### 数据支持
- **K线数据**：支持多个交易对、多种时间周期
- **技术指标**：MA、ATR、布林带、RSI 等
- **数据格式化**：适合 LLM 分析的文本格式

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
# 运行模式: monitor (监控交易) / analyser (市场分析)
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
python main.py --mode analyser

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
| `analyser` | 获取 K 线 → LLM 分析 → 推送结果 | 市场分析、研究辅助 |

### 命令行参数

```bash
python main.py --help

Options:
  --config CONFIG       配置文件路径
  --mode {auto,monitor,analyser}  运行模式
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
│   └── config.yaml             # 实际配置
├── core/
│   ├── engine.py               # 交易引擎 + 工厂函数
│   ├── analyser_runner.py      # 市场分析器
│   ├── analyzer.py             # LLM 分析模块
│   ├── binance_client.py       # 币安 API 客户端
│   └── backtester.py           # 回测模块
├── strategies/
│   ├── base_strategy.py        # 策略基类
│   ├── trend_following.py      # 趋势跟踪
│   ├── mean_reversion.py       # 均值回归
│   └── turtle_trading.py       # 海龟交易
├── notifications/
│   ├── dingtalk.py             # 钉钉通知
│   └── feishu.py               # 飞书通知
└── utils/
    ├── config_manager.py        # 配置管理
    ├── data_formatter.py       # 数据格式化
    └── logger.py               # 日志工具
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

### 市场数据分析

```python
from core.binance_client import BinanceMarketData
from utils.data_formatter import DataFormatter
from core.analyzer import MarketAnalyzer

# 获取数据
fetcher = BinanceMarketData()
klines = fetcher.get_klines("BTCUSDT", "1h", 100)

# 格式化
formatter = DataFormatter()
formatted = formatter.format_for_analysis("BTCUSDT", klines, "1h")

# LLM 分析
analyzer = MarketAnalyzer()
result = analyzer.analyze("BTCUSDT", formatted)
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

## 风险提示

⚠️ 加密货币交易具有高风险，请确保：

1. 仅使用可承受损失的资金
2. 充分测试后再实盘
3. 理解每个策略的风险特征
4. 定期监控和调整策略参数

本系统仅供学习和研究，不构成投资建议。
