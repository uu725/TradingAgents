
from redis.exceptions import RedisError

from backend.core.redis_client import redis_client
from backend.services.local_stock import get_local_stock_data
from backend.services.market_guard import DATA_FILE


def get_cached_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    ttl: int = 3600
):
    symbol = symbol.strip().upper()

    # 用文件修改时间区分不同版本的数据
    file_version = (
        DATA_FILE.stat().st_mtime_ns
        if DATA_FILE.exists()
        else 0
    )

    cache_key = (
        f"market:stock:{symbol}:"
        f"{start_date}:{end_date}:{file_version}"
    )

    # 1. 优先读取 Redis
    try:
        cached_data = redis_client.get(cache_key)

        if cached_data is not None:
            print("[REDIS] CACHE HIT")

            if isinstance(cached_data, bytes):
                return cached_data.decode("utf-8")

            return cached_data

    except RedisError as exc:
        print(f"[REDIS] 读取失败，回退本地数据: {exc}")

    # 2. Redis 没有数据，读取本地 CSV
    print("[REDIS] CACHE MISS")

    data = get_local_stock_data(
        symbol,
        start_date,
        end_date
    )

    # 3. 将有效结果存入 Redis
    try:
        redis_client.setex(
            cache_key,
            ttl,
            data
        )

        print("[REDIS] CACHE SAVED")

    except RedisError as exc:
        print(f"[REDIS] 写入失败: {exc}")

    return data
