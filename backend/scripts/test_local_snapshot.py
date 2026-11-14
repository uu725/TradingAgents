
import tradingagents.agents.tools as agent_tools

from backend.services.local_snapshot import (
    build_local_verified_snapshot
)


# 仅在当前测试进程中替换快照实现
agent_tools.build_verified_market_snapshot = (
    build_local_verified_snapshot
)

# 调用 TradingAgents 原有的验证快照工具
result = agent_tools.get_verified_market_snapshot.func(
    "AAPL",
    "2026-11-10",
    5,
    trade_date="2026-11-10"
)

print(result)

assert "2026-11-10" in result
assert "348.5100" in result
assert "55.8914" in result
assert "close_200_sma" in result

print("\n本地市场验证快照测试通过！")
