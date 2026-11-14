
import tradingagents.agents.tools as agent_tools

from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.router import route_to_vendor

from backend.services.local_market_setup import (
    build_local_graph_config
)


# 注册 Worker 将要使用的数据源
config = build_local_graph_config()
set_config(config)

# 测试股票行情
stock = route_to_vendor(
    "get_stock_data",
    "AAPL",
    "2026-11-09",
    "2026-11-10"
)

assert "348.51" in stock
print("1. 本地股票行情：通过")


# 测试技术指标
indicator = route_to_vendor(
    "get_indicators",
    "AAPL",
    "rsi",
    "2026-11-10",
    5
)

assert "55.8914" in indicator
print("2. 本地 RSI 指标：通过")


# 测试市场验证快照工具
snapshot = agent_tools.get_verified_market_snapshot.func(
    "AAPL",
    "2026-11-10",
    5,
    trade_date="2026-11-10"
)

assert "348.5100" in snapshot
assert "337.2667" in snapshot

print("3. 本地市场验证快照：通过")
print("\nWorker 数据源集成测试全部通过！")
