
from pathlib import Path

import pandas as pd

from backend.services.indicators import calculate_indicators


# 读取之前保存的行情
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
input_file = DATA_DIR / "aapl_ohlcv.csv"

df = pd.read_csv(input_file)

# 计算技术指标
result = calculate_indicators(df)

# 保存计算结果
output_file = DATA_DIR / "aapl_indicators.csv"
result.to_csv(output_file, index=False)

# 查看最近5个交易日的指标
columns = [
    "timestamp",
    "close",
    "SMA_20",
    "SMA_50",
    "RSI_14",
    "MACD",
    "MACD_SIGNAL",
]

print("技术指标计算完成！")
print(result[columns].tail(5).to_string(index=False))
print("结果保存位置：", output_file)
