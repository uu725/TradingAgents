
from pathlib import Path

import pandas as pd

from tradingagents.dataflows.errors import NoMarketDataError


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def get_local_stock_data(
    symbol: str,
    start_date: str,
    end_date: str
) -> str:

    ticker = symbol.strip().upper()

    print(
    f"[LOCAL_CSV] get_stock_data: {ticker}, "
    f"{start_date} -> {end_date}",
    flush=True
)

    # 当前只缓存了 AAPL
    if ticker != "AAPL":
        raise NoMarketDataError(
            symbol, ticker, "本地暂无该股票数据"
        )

    file_path = DATA_DIR / "aapl_ohlcv.csv"

    if not file_path.exists():
        raise NoMarketDataError(
            symbol, ticker, "行情文件不存在"
        )

    df = pd.read_csv(file_path)

    required = [
        "timestamp", "open", "high",
        "low", "close", "volume"
    ]

    if not set(required).issubset(df.columns):
        raise ValueError("行情数据缺少必要字段")

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)





    # 检查本地数据是否覆盖请求的历史起点
    available_start = df["timestamp"].min()
    available_end = df["timestamp"].max()

    if available_start > start:
        raise ValueError(
            f"历史行情不足：请求从 {start.date()} 开始，"
            f"本地数据仅从 {available_start.date()} 开始"
        )

    if available_end < end:
        raise ValueError(
            f"行情尚未覆盖请求结束日期：{end.date()}，"
            f"本地最新日期：{available_end.date()}"
        )






    if start > end:
        raise ValueError("开始日期不能晚于结束日期")

    # 只返回请求日期范围内的数据
    # 防止历史分析读取未来数据
    df = df[
        (df["timestamp"] >= start)
        & (df["timestamp"] <= end)
    ].copy()

    if df.empty:
        raise NoMarketDataError(
            symbol, ticker, "指定日期范围内没有行情"
        )

    if df[required].isna().any().any():
        raise ValueError("行情数据存在缺失值")

    df = df.sort_values("timestamp")

    df["timestamp"] = df["timestamp"].dt.strftime(
        "%Y-%m-%d"
    )

    return df[required].to_csv(index=False)
