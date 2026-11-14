
from copy import deepcopy

import tradingagents.agents.tools as agent_tools

from tradingagents.default_config import DEFAULT_CONFIG

from backend.services.local_vendor import register_local_vendor
from backend.services.local_snapshot import build_local_verified_snapshot


def build_local_graph_config():
    # 1. 注册本地股票行情与技术指标
    register_local_vendor()

    # 2. 将市场验证快照切换为本地实现
    agent_tools.build_verified_market_snapshot = (
        build_local_verified_snapshot
    )

    # 3. 创建独立配置，避免修改默认配置
    config = deepcopy(DEFAULT_CONFIG)

    config["data_vendors"]["core_stock_apis"] = "local_csv"
    config["data_vendors"]["technical_indicators"] = "local_csv"

    # 4. 确保工具级配置也使用本地数据
    config.setdefault("tool_vendors", {}).update({
        "get_stock_data": "local_csv",
        "get_indicators": "local_csv",
    })

    return config
