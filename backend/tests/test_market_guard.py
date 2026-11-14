
import pandas as pd
import pytest

from backend.services import market_guard


# 创建独立的模拟行情，不依赖真实 CSV
@pytest.fixture
def fake_history(tmp_path, monkeypatch):
    dates = pd.bdate_range(
        end="2026-11-10",
        periods=61
    )

    df = pd.DataFrame({
        "timestamp": dates,
        "open": [100.0] * 61,
        "high": [105.0] * 61,
        "low": [95.0] * 61,
        "close": [102.0] * 61,
        "volume": [1000000] * 61,
    })

    file_path = tmp_path / "aapl_ohlcv.csv"
    df.to_csv(file_path, index=False)

    # 测试时使用模拟文件，不修改真实数据
    monkeypatch.setattr(
        market_guard,
        "DATA_FILE",
        file_path
    )

    return file_path


# 测试1：61天数据满足50天要求
def test_history_50_days(fake_history):
    result = market_guard.validate_market_history(
        "AAPL",
        "2026-11-10",
        minimum_rows=50
    )

    assert result["status"] == "valid"
    assert result["rows"] == 61


# 测试2：61天数据不满足200天要求
def test_history_200_days(fake_history):
    with pytest.raises(
        market_guard.MarketDataUnavailable,
        match="历史数据不足"
    ):
        market_guard.validate_market_history(
            "AAPL",
            "2026-11-10",
            minimum_rows=200
        )


# 测试3：不支持的股票应拒绝分析
def test_unsupported_ticker(fake_history):
    with pytest.raises(
        market_guard.MarketDataUnavailable,
        match="暂不支持股票"
    ):
        market_guard.validate_market_history(
            "MSFT",
            "2026-11-10",
            minimum_rows=50
        )
