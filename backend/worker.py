
from rq import SimpleWorker
from rq.timeouts import TimerDeathPenalty

from backend.core.queue import analysis_queue


# Windows 专用的开发测试 Worker
class WindowsSimpleWorker(SimpleWorker):
    death_penalty_class = TimerDeathPenalty


if __name__ == "__main__":
    worker = WindowsSimpleWorker(
        [analysis_queue],
        connection=analysis_queue.connection
    )

    print("Worker 已启动，正在监听 analysis 队列")

    worker.work()
