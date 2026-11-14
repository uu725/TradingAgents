
from copy import deepcopy

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.router import route_to_vendor

from backend.services.local_vendor import register_local_vendor


# 1. 注册本地指标数据源
register_local_vendor()

# 2. 修改数据源配置
config = deepcopy(DEFAULT_CONFIG)

config["data_vendors"]["core_stock_apis"] = "local_csv"

config["data_vendors"]["technical_indicators"] = "local_csv"

set_config(config)

# 3. 测试指标路由
for indicator in ["rsi", "macd", "close_50_sma"]:
    print(f"\n正在测试：{indicator}")

    result = route_to_vendor(
        "get_indicators",
        "AAPL",
        indicator,
        "2026-11-10",
        7
    )

    print(result)

print("\n开始测试本地股票行情...")

result = route_to_vendor(
    "get_stock_data",
    "AAPL",
    "2026-11-03",
    "2026-11-10"
)

print(result)

# 检查返回内容
assert "2026-11-10" in result
assert "timestamp,open,high,low,close,volume" in result

# 检查没有返回请求日期之后的数据
assert "2026-11-11" not in result

print("本地行情路由测试通过！")