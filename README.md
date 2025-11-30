# 加密货币期货量化交易系统

一个功能全面的加密货币期货量化交易系统，包含多种交易策略、风险管理和回测功能。

## 功能特性

- **多种交易策略**：趋势跟踪、均值回归和海龟交易
- **实时交易**：与币安期货API集成
- **风险管理**：仓位规模和杠杆控制
- **通知系统**：钉钉集成告警
- **回测功能**：历史数据测试框架
- **日志记录**：完整的日志文件输出
- **配置管理**：基于JSON的配置系统
- **测试支持**：单元测试和策略验证

## 环境要求

- Python 3.7+
- pip (Python包管理器)

## 安装步骤

1. 克隆代码仓库：
   ```bash
   git clone <repository-url>
   cd py-futures-quant
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

## 配置说明

1. 复制示例配置文件：
   ```bash
   cp config/config.example.json config/config.json
   ```

2. 编辑 `config/config.json` 文件，填入：
   - 币安API密钥
   - 交易参数
   - 通知设置

## 使用方法

### 运行交易系统

```bash
python main.py
```

选项：
- `--config CONFIG`：配置文件路径（默认：config/config.json）
- `--once`：执行一次策略评估后退出
- `--interval INTERVAL`：评估间隔秒数（默认：3600）
- `--log-level {DEBUG,INFO,WARNING,ERROR}`：日志级别（默认：INFO）

### 回测运行

```bash
python backtest_example.py
```

此命令将对所有策略进行历史数据回测，并将结果输出到 `backtest_results.json` 文件。

### 测试运行

运行单元测试：
```bash
python test_unit.py
```

验证策略导入：
```bash
python test_strategies.py
```

运行演示：
```bash
python demo.py
```

测试钉钉通知：
```bash
python test_dingtalk_message.py
```

## 项目结构

```
py-futures-quant/
├── backtest_example.py     # 回测实现
├── config/
│   ├── config.example.json # 示例配置文件
│   └── config.json         # 实际配置文件（不在仓库中）
├── core/
│   ├── __init__.py
│   ├── binance_client.py   # 币安期货API客户端
│   └── engine.py           # 主交易引擎
├── data/
│   └── __init__.py
├── demo.py                 # 系统演示
├── logs/                   # 日志文件目录
├── main.py                 # 程序入口
├── notifications/
│   ├── __init__.py
│   └── dingtalk.py         # 钉钉通知服务
├── README.md               # 说明文件
├── requirements.txt        # Python依赖
├── strategies/
│   ├── __init__.py
│   ├── base.py             # 策略基类
│   ├── mean_reversion.py   # 均值回归策略
│   ├── trend_following.py  # 趋势跟踪策略
│   └── turtle_trading.py   # 海龟交易策略
├── SUMMARY.md              # 项目摘要
├── test_strategies.py      # 策略导入/验证测试
├── test_unit.py            # 单元测试
└── utils/
    ├── __init__.py
    ├── config_manager.py   # 配置工具
    └── logger.py           # 日志工具
```

## 交易策略

### 趋势跟踪策略
使用移动平均线和波动率通道来识别并跟随市场趋势。

### 均值回归策略
通过布林带和RSI指标识别超买/超卖状态，并针对极端价格波动进行反向交易。

### 海龟交易策略
经典的突破策略，基于唐奇安通道和ATR的仓位管理。

## 风险声明

交易加密货币及其衍生品具有重大亏损风险，并不适合所有投资者。高杠杆既可能为您带来收益，也可能造成损失。在决定交易加密货币期货之前，您应仔细考虑自己的投资目标、经验水平和风险承受能力。

过往表现并不代表未来结果。我们不是财务顾问，此系统仅用于教育目的。切勿投入超出承受能力的资金。
