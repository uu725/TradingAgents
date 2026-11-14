
from copy import deepcopy
from io import StringIO
from pathlib import Path

import pandas as pd

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.router import route_to_vendor


config = deepcopy(DEFAULT_CONFIG)
config["data_vendors"]["core_stock_apis"] = "alpha_vantage"
set_config(config)

print("开始获取 AAPL 历史行情...")

result = route_to_vendor(
    "get_stock_data",
    "AAPL",
    "2026-08-17",
    "2026-11-10"
)

if (
    not result.strip()
    or result.startswith("DATA_UNAVAILABLE")
    or result.startswith("NO_DATA_AVAILABLE")
):
    raise RuntimeError("股票行情不可用：" + result[:300])

# 将 CSV 字符串转换成 DataFrame
df = pd.read_csv(StringIO(result))

required = [
    "timestamp", "open", "high",
    "low", "close", "volume"
]

if not set(required).issubset(df.columns):
    raise ValueError("缺少必要的 OHLCV 字段")

df["timestamp"] = pd.to_datetime(df["timestamp"])

for col in required[1:]:
    df[col] = pd.to_numeric(df[col], errors="raise")

if df.empty or df[required].isna().any().any():
    raise ValueError("行情数据为空或存在缺失值")

if df["timestamp"].duplicated().any():
    raise ValueError("存在重复交易日期")

if (
    (df["high"] < df[["open", "close", "low"]].max(axis=1)).any()
    or (df["low"] > df[["open", "close", "high"]].min(axis=1)).any()
    or (df["volume"] < 0).any()
):
    raise ValueError("行情数据存在不合理数值")

df = df.sort_values("timestamp")

if df["timestamp"].max() != pd.Timestamp("2026-11-10"):
    raise ValueError("缺少目标交易日的行情")

# 保存本地 CSV
output = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "aapl_ohlcv.csv"
)
output.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(output, index=False)

print("数据校验通过")
print("交易日数量：", len(df))
print("最早日期：", df["timestamp"].min().date())
print("最新日期：", df["timestamp"].max().date())
print("数据已保存：", output)
