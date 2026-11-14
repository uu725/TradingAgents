
from sqlalchemy import select
from rq.job import Job
from rq.exceptions import NoSuchJobError

from backend.models.analysis import AnalysisTask
from backend.core.redis_client import redis_client


def reconcile_task(task_id: str, db):
    # 1. 从 MySQL 查询任务
    task = db.scalar(
        select(AnalysisTask).where(
            AnalysisTask.task_id == task_id
        )
    )

    if task is None:
        return {"status": "not_found"}

    # 2. 已经结束的业务任务，不再修改
    if task.status not in ("pending", "running"):
        return {
            "status": "skipped",
            "db_status": task.status
        }

    # 3. 查询 Redis 中的 RQ 状态
    try:
        job = Job.fetch(
            task_id,
            connection=redis_client
        )
    except NoSuchJobError:
        # 任务可能过期，不能直接认定失败
        return {"status": "rq_job_missing"}

    rq_status = job.get_status(refresh=True)
    rq_status = getattr(rq_status, "value", rq_status)

    # 4. 只处理明确的失败状态
    if rq_status in ("failed", "stopped", "canceled"):
        task.status = "failed"
        task.error_message = (
            f"RQ任务状态为 {rq_status}，"
            "请查看 Worker 日志"
        )

        db.commit()

        return {
            "status": "reconciled",
            "db_status": "failed",
            "rq_status": rq_status
        }

    # 5. 仍在等待或运行的任务不修改
    return {
        "status": "unchanged",
        "db_status": task.status,
        "rq_status": rq_status
    }
