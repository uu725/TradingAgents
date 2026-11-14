
import pandas as pd


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    # 按日期排序，保证从旧到新
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    if len(df) < 50:
        raise ValueError("至少需要50个交易日的数据")

    close = pd.to_numeric(df["close"], errors="raise")

    # 1. 简单移动平均线
    df["SMA_20"] = close.rolling(window=20).mean()
    df["SMA_50"] = close.rolling(window=50).mean()

    # 2. 指数移动平均线
    df["EMA_10"] = close.ewm(
    span=10, adjust=False
).mean()
    df["EMA_12"] = close.ewm(
        span=12, adjust=False
    ).mean()

    df["EMA_26"] = close.ewm(
        span=26, adjust=False
    ).mean()

    # 3. MACD
    df["MACD"] = df["EMA_12"] - df["EMA_26"]

    df["MACD_SIGNAL"] = df["MACD"].ewm(
        span=9, adjust=False
    ).mean()

    df["MACD_HIST"] = (
        df["MACD"] - df["MACD_SIGNAL"]
    )

    # 4. RSI（14日，Wilder平滑）
    period = 14
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = pd.Series(float("nan"), index=df.index)
    avg_loss = pd.Series(float("nan"), index=df.index)

    # 首个平均值采用14个价格变化的算术平均
    avg_gain.iloc[period] = gain.iloc[1:period + 1].mean()
    avg_loss.iloc[period] = loss.iloc[1:period + 1].mean()

    for i in range(period + 1, len(df)):
        avg_gain.iloc[i] = (
            avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]
        ) / period

        avg_loss.iloc[i] = (
            avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]
        ) / period

    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100 - 100 / (1 + rs)

    # 处理没有下跌或价格完全不变的情况
    rsi = rsi.mask(
        (avg_loss == 0) & (avg_gain > 0), 100
    )
    rsi = rsi.mask(
        (avg_loss == 0) & (avg_gain == 0), 50
    )

    df["RSI_14"] = rsi

    return df
