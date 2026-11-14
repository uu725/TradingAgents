
from tradingagents.agents.tools import (
    get_stock_data,
    get_indicators,
    get_verified_market_snapshot
)

from tradingagents.dataflows.config import run_config

from backend.services.local_market_setup import (
    build_local_graph_config
)


# 1. 加载本地数据源配置
config = build_local_graph_config()

print("开始测试 TradingAgents 真实工具...")

with run_config(config):

    # 2. 测试真实的股票行情工具
    stock = get_stock_data.func(
        "AAPL",
        "2026-11-03",
        "2026-11-10",
        trade_date="2026-11-10"
    )

    assert "348.51" in stock
    assert "DATA_UNAVAILABLE" not in stock
    print("1. get_stock_data：通过")

    # 3. 测试真实的技术指标工具
    indicator = get_indicators.func(
        "AAPL",
        "rsi",
        "2026-11-10",
        5,
        trade_date="2026-11-10"
    )

    assert "55.8914" in indicator
    assert "DATA_UNAVAILABLE" not in indicator
    print("2. get_indicators：通过")

    # 4. 测试市场验证快照工具
    snapshot = get_verified_market_snapshot.func(
        "AAPL",
        "2026-11-10",
        5,
        trade_date="2026-11-10"
    )

    assert "348.5100" in snapshot
    assert "337.2667" in snapshot
    assert "DATA_UNAVAILABLE" not in snapshot

    print("3. get_verified_market_snapshot：通过")


print("\nTradingAgents 三个实际工具测试全部通过！")
