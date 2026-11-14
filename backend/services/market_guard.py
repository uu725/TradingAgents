
from pathlib import Path

import pandas as pd


class MarketDataUnavailable(Exception):
    """股票行情不足或不可用"""
    pass


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "aapl_ohlcv.csv"
)


def validate_market_history(
    ticker: str,
    analysis_date: str,
    minimum_rows: int = 200
):
    # 当前本地缓存只支持 AAPL
    if ticker.upper() != "AAPL":
        raise MarketDataUnavailable(
            f"暂不支持股票：{ticker}"
        )

    if not DATA_FILE.exists():
        raise MarketDataUnavailable(
            "本地行情文件不存在"
        )

    df = pd.read_csv(DATA_FILE)

    if "timestamp" not in df.columns:
        raise MarketDataUnavailable(
            "行情缺少 timestamp 字段"
        )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    end = pd.Timestamp(analysis_date)

    # 不允许使用未来数据
    df = df[df["timestamp"] <= end]

    if df.empty:
        raise MarketDataUnavailable(
            "分析日期之前没有行情数据"
        )

    df = df.sort_values("timestamp")

    if df["timestamp"].iloc[-1] != end:
        raise MarketDataUnavailable(
            "本地行情不包含目标交易日"
        )

    if len(df) < minimum_rows:
        raise MarketDataUnavailable(
            f"历史数据不足：需要至少 {minimum_rows} "
            f"个交易日，实际只有 {len(df)} 个"
        )

    return {
        "ticker": ticker,
        "rows": len(df),
        "status": "valid"
    }
