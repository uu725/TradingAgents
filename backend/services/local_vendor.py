from backend.services.market_cache import get_cached_stock_data

from pathlib import Path

import pandas as pd

from tradingagents.dataflows import router
from tradingagents.dataflows.errors import NoMarketDataError

from backend.services.indicators import calculate_indicators

from backend.services.local_stock import get_local_stock_data

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# TradingAgents 指标名称 → 本地计算列名
INDICATOR_MAP = {
    "close_50_sma": "SMA_50",
    "close_10_ema": "EMA_10",
    "rsi": "RSI_14",
    "macd": "MACD",
    "macds": "MACD_SIGNAL",
    "macdh": "MACD_HIST",
    "boll": "SMA_20",
}


def get_local_indicator(
    symbol: str,
    indicator: str,
    as_of_date: str,
    look_back_days: int = 30
) -> str:
    ticker = symbol.upper().strip()
    indicator = indicator.lower().strip()

    print(
    f"[LOCAL_CSV] get_indicators: "
    f"{ticker}, {indicator}, {as_of_date}",
    flush=True
)

    # 第一版只支持已下载的 AAPL 数据
    if ticker != "AAPL":
        raise NoMarketDataError(
            symbol, ticker, "本地暂无该股票行情"
        )

    if indicator not in INDICATOR_MAP:
        raise NoMarketDataError(
            symbol, ticker, f"本地暂不支持 {indicator}"
        )

    file = DATA_DIR / "aapl_ohlcv.csv"

    if not file.exists():
        raise NoMarketDataError(
            symbol, ticker, "本地行情文件不存在"
        )

    df = pd.read_csv(file)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 防止使用分析日期之后的数据
    end = pd.Timestamp(as_of_date)

    df = df[df["timestamp"] <= end]

    if df.empty:
        raise NoMarketDataError(
            symbol, ticker, "分析日期之前没有行情"
        )

    # 先用历史数据计算指标，再截取展示窗口
    result = calculate_indicators(df)

    column = INDICATOR_MAP[indicator]
    start = end - pd.Timedelta(days=look_back_days)

    result = result[
        (result["timestamp"] >= start)
        & (result["timestamp"] <= end)
    ]

    result = result[
        ["timestamp", column]
    ].dropna()

    if result.empty:
        raise NoMarketDataError(
            symbol, ticker, "指标数据不足"
        )

    lines = [
        f"## {indicator.upper()} ({ticker})",
        "Source: local Alpha Vantage daily OHLCV",
        "Note: local calculation; historical warm-up may affect values.",
    ]

    for _, row in result.iterrows():
        date = row["timestamp"].strftime("%Y-%m-%d")
        value = row[column]
        lines.append(f"{date}: {value:.4f}")

    return "\n".join(lines)


def register_local_vendor():
    # 注册本地技术指标
    router.VENDOR_METHODS["get_indicators"][
        "local_csv"
    ] = get_local_indicator

    # 注册本地 OHLCV 行情
router.VENDOR_METHODS["get_stock_data"]["local_csv"] = get_cached_stock_data