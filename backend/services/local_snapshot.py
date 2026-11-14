
from pathlib import Path

import pandas as pd

from backend.services.indicators import calculate_indicators
from tradingagents.dataflows.errors import NoMarketDataError


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "aapl_ohlcv.csv"
)


def build_local_verified_snapshot(



    symbol: str,
    as_of_date: str,
    look_back_days: int = 30
) -> str:


    print(
        f"[LOCAL_CSV] get_verified_market_snapshot: "
        f"{symbol}, {as_of_date}",
        flush=True
    )


    ticker = symbol.strip().upper()
    end = pd.Timestamp(as_of_date)

    # 第一版只支持 AAPL
    if ticker != "AAPL":
        raise NoMarketDataError(
            symbol, ticker, "本地暂不支持该股票"
        )

    if not DATA_FILE.exists():
        raise NoMarketDataError(
            symbol, ticker, "本地行情文件不存在"
        )

    # 读取本地行情
    df = pd.read_csv(DATA_FILE)

    required = [
        "timestamp", "open", "high",
        "low", "close", "volume"
    ]

    if not set(required).issubset(df.columns):
        raise ValueError("行情缺少必要字段")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="raise"
    )

    for col in required[1:]:
        df[col] = pd.to_numeric(
            df[col], errors="raise"
        )

    if df.empty or df[required].isna().any().any():
        raise ValueError("行情存在空值")

    if df["timestamp"].duplicated().any():
        raise ValueError("行情日期重复")

    if (
        (df[["open", "high", "low", "close"]] <= 0)
        .any().any()
        or (df["volume"] < 0).any()
    ):
        raise ValueError("行情存在非法价格或成交量")

    if (
        (df["high"] < df[["open", "low", "close"]].max(axis=1)).any()
        or (df["low"] > df[["open", "high", "close"]].min(axis=1)).any()
    ):
        raise ValueError("OHLC 价格关系不合理")

    # 严格避免读取分析日期之后的数据
    df = df[df["timestamp"] <= end]
    df = df.sort_values("timestamp")

    if df.empty or df.iloc[-1]["timestamp"] != end:
        raise NoMarketDataError(
            symbol, ticker,
            "当前测试要求缓存包含目标交易日"
        )

    if len(df) < 50:
        raise NoMarketDataError(
            symbol, ticker, "少于50个交易日"
        )

    # 使用已有的 pandas 指标计算模块
    result = calculate_indicators(df)
    latest = result.iloc[-1]

    # TradingAgents 名称 → 本地指标
    indicator_map = {
        "close_10_ema": "EMA_10",
        "close_50_sma": "SMA_50",
        "rsi": "RSI_14",
        "macd": "MACD",
        "macds": "MACD_SIGNAL",
        "macdh": "MACD_HIST",
        "boll": "SMA_20",
    }

    lines = [
        f"## Local market data snapshot for {ticker}",
        "",
        "Source: Alpha Vantage daily OHLCV, local CSV",
        "Prices are unadjusted.",
        "Data was locally validated, not independently verified.",
        f"Analysis date: {as_of_date}",
        f"Historical rows: {len(result)}",
        "",
        "### Latest OHLCV",
        "| Field | Value |",
        "|---|---:|",
    ]

    for field in ["open", "high", "low", "close", "volume"]:
        lines.append(
            f"| {field} | {latest[field]:.4f} |"
        )

    lines.extend([
        "",
        "### Technical indicators",
        "| Indicator | Value |",
        "|---|---:|",
    ])

    for name, column in indicator_map.items():
        value = latest[column]

        if pd.isna(value):
            value_text = "N/A"
        else:
            value_text = f"{value:.4f}"

        lines.append(f"| {name} | {value_text} |")

    # 数据不足或尚未实现的指标，不得编造
    lines.append("| close_200_sma | N/A (need 200 rows) |")

    for name in ["boll_ub", "boll_lb", "atr", "vwma"]:
        lines.append(
            f"| {name} | N/A (not calculated) |"
        )

    # 最近若干交易日收盘价
    count = max(1, min(int(look_back_days), 30))

    lines.extend([
        "",
        "### Recent closes",
        "| Date | Close |",
        "|---|---:|",
    ])

    for _, row in result.tail(count).iterrows():
        day = row["timestamp"].strftime("%Y-%m-%d")
        lines.append(
            f"| {day} | {row['close']:.4f} |"
        )

    lines.extend([
        "",
        "Do not estimate unavailable indicators.",
        "Do not claim independent data verification.",
    ])

    return "\n".join(lines)
