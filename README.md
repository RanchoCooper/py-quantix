# 加密货币期货量化交易系统

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

一个功能全面的加密货币期货量化交易系统，包含多种交易策略、风险管理和回测功能。该系统支持币安期货交易平台，具备自动交易和监控模式，适用于算法交易研究和实盘部署。

## 功能特性

- **多种交易策略**：
  - 趋势跟踪策略：使用移动平均线和动量指标识别市场趋势
  - 均值回归策略：基于布林带和RSI指标进行反向交易
  - 海龟交易策略：经典突破策略，基于唐奇安通道和ATR仓位管理
- **实时交易**：与币安期货API深度集成，支持实盘和测试网环境
- **风险管理**：灵活的仓位规模控制和杠杆设置，支持多币种独立配置
- **通知系统**：钉钉机器人集成，实时推送交易信号和系统状态
- **回测功能**：历史数据测试框架，支持策略性能评估和优化
- **日志记录**：基于Loguru的高级日志系统，支持多级别和文件输出
- **配置管理**：基于JSON的配置系统，支持多币种和策略的个性化配置
- **测试支持**：全面的单元测试和策略验证机制，确保系统稳定性

## 环境要求

- Python 3.7+
- pip (Python包管理器)
- 币安期货账户（实盘交易）或测试网账户（测试环境）
- 钉钉机器人（可选，用于通知）

## 安装步骤

1. 克隆代码仓库：
   ```bash
   git clone <repository-url>
   cd py-quantix
   ```

2. 创建虚拟环境（推荐）：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows系统使用: venv\Scripts\activate
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 验证安装：
   ```bash
   python -c "import numpy, pandas, requests; print('依赖安装成功')"
   ```

## 配置说明

1. 复制示例配置文件：
   ```bash
   cp config/config.example.json config/config.json
   ```

2. 编辑 `config/config.json` 文件，配置以下参数：

   ### 币安API设置
   - `api_key`: 币安期货API密钥
   - `api_secret`: 币安期货API密钥
   - `testnet`: 是否使用测试网（`true`为测试网，`false`为实盘）

   ### 交易设置
   - `symbols`: 交易对配置
     - `leverage`: 杠杆倍数
     - `position_size`: 仓位大小
     - `strategy`: 使用的策略名称
     - `strategy_params`: 策略特定参数

   ### 策略全局参数
   - 各策略的默认参数设置

   ### 通知设置
   - 钉钉机器人的webhook URL和密钥

   ### 日志设置
   - 日志级别和日志文件路径

## 使用方法

### 运行交易系统

```bash
python main.py
```

#### 运行模式
系统支持两种运行模式：
- **自动模式**（默认）：自动执行交易信号
- **监控模式**：仅发送通知，不执行实际交易

#### 命令行选项：
- `--config CONFIG`：配置文件路径（默认：config/config.json）
- `--once`：执行一次策略评估后退出
- `--interval INTERVAL`：评估间隔秒数（默认：3600）
- `--log-level {DEBUG,INFO,WARNING,ERROR}`：日志级别（默认：INFO）
- `--mode {auto,monitor}`：运行模式（默认：auto）

#### 示例命令：
```bash
# 使用默认配置运行自动交易模式
python main.py

# 使用自定义配置文件运行
python main.py --config config/my_config.json

# 以监控模式运行，每30分钟评估一次
python main.py --mode monitor --interval 1800

# 执行一次策略评估后退出
python main.py --once
```

### 回测运行

```bash
python backtest_example.py
```

此命令将对所有策略进行历史数据回测，并将结果输出到 `backtest_results.json` 文件。

#### 回测配置
回测脚本会根据配置文件中的参数进行测试，包括：
- 数据范围和时间周期
- 初始资金和手续费设置
- 各策略的参数配置

#### 回测结果
回测完成后，结果将保存在 `backtest_results.json` 文件中，包含：
- 策略收益率和夏普比率
- 最大回撤和胜率统计
- 交易次数和平均收益

### 测试运行

#### 运行单元测试：
```bash
python tests/test_unit.py
```

#### 验证策略导入：
```bash
python tests/test_strategies.py
```

#### 运行演示：
```bash
python demo.py
```

#### 测试钉钉通知：
```bash
python tests/test_dingtalk_message.py
```

#### 测试所有功能：
```bash
python -m pytest tests/
```

这些测试可以帮助验证系统各组件是否正常工作，特别是在修改代码后确保没有破坏现有功能。

## 项目结构

```
py-quantix/
├── backtest_example.py        # 回测实现
├── backtest_results.json      # 回测结果文件
├── config/
│   ├── config.example.json    # 示例配置文件
│   └── config.json            # 实际配置文件（不在仓库中）
├── core/
│   ├── __init__.py
│   ├── binance_client.py      # 币安期货API客户端
│   └── engine.py              # 主交易引擎
├── data/
│   └── __init__.py
├── demo.py                    # 系统演示
├── main.py                    # 程序入口
├── notifications/
│   ├── __init__.py
│   └── dingtalk.py            # 钉钉通知服务
├── README.md                  # 项目说明文件
├── requirements.txt           # Python依赖
├── strategies/
│   ├── __init__.py
│   ├── mean_reversion.py      # 均值回归策略
│   ├── trend_following.py     # 趋势跟踪策略
│   └── turtle_trading.py      # 海龟交易策略
├── SUMMARY.md                 # 项目摘要
└── utils/
    ├── __init__.py
    ├── config_manager.py      # 配置工具
    └── logger.py              # 日志工具
```

### 测试目录结构
```
tests/
├── __init__.py
├── test_dingtalk.py           # 钉钉通知测试
├── test_dingtalk_message.py   # 钉钉消息测试
├── test_modes.py              # 运行模式测试
├── test_multi_currency.py     # 多币种交易测试
├── test_strategies.py         # 策略导入/验证测试
└── test_unit.py               # 单元测试
```

## 交易策略

### 趋势跟踪策略
使用移动平均线和动量指标来识别并跟随市场趋势。
- **技术指标**：短期和长期移动平均线、ATR（平均真实波幅）、动量指标
- **入场信号**：短期均线上穿长期均线且动量为正时做多，反之则做空
- **出场信号**：短期均线下穿长期均线或止损止盈条件触发
- **风险管理**：基于ATR动态设置止损和止盈水平

### 均值回归策略
通过布林带和RSI指标识别超买/超卖状态，并针对极端价格波动进行反向交易。
- **技术指标**：布林带（移动平均线±标准差×倍数）、RSI（相对强弱指数）
- **入场信号**：价格突破布林带下轨且RSI<30时做多；价格突破布林带上轨且RSI>70时做空
- **出场信号**：价格回归到移动平均线附近或止损条件触发
- **风险管理**：固定比例仓位管理，严格控制单笔交易风险

### 海龟交易策略
经典的突破策略，基于唐奇安通道和ATR的仓位管理。
- **技术指标**：唐奇安通道（最高高价和最低低价）、ATR（平均真实波幅）
- **入场信号**：价格突破过去N天的最高价时做多，突破过去N天的最低价时做空
- **出场信号**：价格反向突破过去M天的最低价/最高价时平仓
- **风险管理**：基于ATR动态调整仓位大小，确保每笔交易风险一致

## 风险声明

交易加密货币及其衍生品具有重大风险，可能导致严重的财务损失。本系统仅供教育和研究目的，不构成任何投资建议。

### 重要提醒

1. **实盘交易风险**：在使用本系统进行实盘交易之前，请确保您完全理解其工作原理，并进行了充分的测试。
2. **资金管理**：请勿投入超出承受能力的资金，建议使用测试网环境进行充分验证后再考虑实盘交易。
3. **技术风险**：系统可能存在未发现的bug或错误，使用时请保持谨慎。
4. **市场风险**：加密货币市场波动极大，任何交易策略都无法保证盈利。

本系统作者不对因使用本系统而导致的任何损失负责。在决定使用本系统进行交易之前，请仔细考虑您的投资目标、经验水平和风险承受能力。
