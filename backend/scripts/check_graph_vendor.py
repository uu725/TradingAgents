
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.dataflows.config import run_config
from tradingagents.dataflows.router import get_vendor

from backend.services.local_market_setup import (
    build_local_graph_config
)


# 1. 获取本地数据源配置
config = build_local_graph_config()

# 2. 创建 TradingAgentsGraph
# 不执行 propagate，因此不会运行股票分析
graph = TradingAgentsGraph(
    selected_analysts=["market"],
    debug=False,
    config=config
)

# 3. 查看 Graph 保存的配置
print("Graph 股票数据配置:")
print(graph.config["data_vendors"]["core_stock_apis"])

print("Graph 技术指标配置:")
print(graph.config["data_vendors"]["technical_indicators"])

# 4. 检查真正使用的数据源
with run_config(graph.config):
    stock_vendor = get_vendor(
        "core_stock_apis",
        "get_stock_data"
    )

    indicator_vendor = get_vendor(
        "technical_indicators",
        "get_indicators"
    )

print("实际行情路由:", stock_vendor)
print("实际指标路由:", indicator_vendor)

# 5. 验证
assert stock_vendor == "local_csv"
assert indicator_vendor == "local_csv"

print("\nGraph 数据源配置测试通过！")
