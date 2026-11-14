
from unittest.mock import Mock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from backend.services import market_cache


@pytest.fixture
def cache_environment(monkeypatch, tmp_path):
    # 创建临时 CSV 文件，不影响真实行情
    data_file = tmp_path / "aapl_ohlcv.csv"
    data_file.write_text(
        "timestamp,close\n2026-11-10,348.51\n",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        market_cache,
        "DATA_FILE",
        data_file
    )

    # 模拟 Redis
    fake_redis = Mock()
    monkeypatch.setattr(
        market_cache,
        "redis_client",
        fake_redis
    )

    # 模拟本地行情读取函数
    fake_local = Mock(
        return_value="timestamp,close\n2026-11-10,348.51\n"
    )
    monkeypatch.setattr(
        market_cache,
        "get_local_stock_data",
        fake_local
    )

    return fake_redis, fake_local


# 测试1：Redis 缓存命中
def test_cache_hit(cache_environment):
    fake_redis, fake_local = cache_environment

    fake_redis.get.return_value = b"cached data"

    result = market_cache.get_cached_stock_data(
        "AAPL", "2026-11-03", "2026-11-10"
    )

    assert result == "cached data"
    fake_local.assert_not_called()
    fake_redis.setex.assert_not_called()


# 测试2：缓存未命中，读取本地并保存
def test_cache_miss(cache_environment):
    fake_redis, fake_local = cache_environment

    fake_redis.get.return_value = None

    result = market_cache.get_cached_stock_data(
        "AAPL", "2026-11-03", "2026-11-10"
    )

    assert "348.51" in result
    fake_local.assert_called_once()
    fake_redis.setex.assert_called_once()

    # 检查 TTL 是否为3600秒
    args = fake_redis.setex.call_args.args
    assert args[1] == 3600
    assert args[2] == result


# 测试3：Redis 故障时回退到本地 CSV
def test_redis_failure(cache_environment):
    fake_redis, fake_local = cache_environment

    fake_redis.get.side_effect = RedisConnectionError(
        "Redis connection failed"
    )
    fake_redis.setex.side_effect = RedisConnectionError(
        "Redis connection failed"
    )

    result = market_cache.get_cached_stock_data(
        "AAPL", "2026-11-03", "2026-11-10"
    )

    assert "348.51" in result
    fake_local.assert_called_once()


# 测试4：本地行情异常时不能缓存
def test_invalid_data_not_cached(cache_environment):
    fake_redis, fake_local = cache_environment

    fake_redis.get.return_value = None
    fake_local.side_effect = ValueError("历史行情不足")

    with pytest.raises(
        ValueError,
        match="历史行情不足"
    ):
        market_cache.get_cached_stock_data(
            "AAPL", "2025-04-01", "2026-11-10"
        )

    fake_redis.setex.assert_not_called()
