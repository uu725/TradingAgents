
import os
from pathlib import Path

import redis
from dotenv import load_dotenv

# 加载项目根目录中的 .env 文件
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# 创建 Redis 客户端
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD"),
    db=int(os.getenv("REDIS_DB", "0")),
    decode_responses=False,
    socket_connect_timeout=5,
    socket_timeout=500
)
