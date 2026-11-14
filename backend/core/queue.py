
from rq import Queue

from backend.core.redis_client import redis_client

# 创建股票分析任务队列
analysis_queue = Queue(
    name="analysis",
    connection=redis_client,
    default_timeout=600
)
