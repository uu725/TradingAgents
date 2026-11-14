
from collections import Counter

from redis.exceptions import RedisError
from sqlalchemy import select

from backend.core.database import SessionLocal
from backend.models.analysis import AnalysisTask
from backend.services.task_reconcile import reconcile_task


def main():
    # 创建数据库会话
    with SessionLocal() as db:

        # 查找未完成的任务，单次最多检查100条
        task_ids = db.scalars(
            select(AnalysisTask.task_id)
            .where(
                AnalysisTask.status.in_(
                    ["pending", "running"]
                )
            )
            .order_by(AnalysisTask.id.desc())
            .limit(100)
        ).all()

        print(f"待检查任务数量: {len(task_ids)}")

        stats = Counter()

        # 逐个对比 Redis 和 MySQL 状态
        for task_id in task_ids:

            try:
                result = reconcile_task(
                    task_id,
                    db
                )

                status = result["status"]
                stats[status] += 1

                print(
                    f"任务: {task_id}, "
                    f"检查结果: {result}"
                )

            except RedisError as exc:
                db.rollback()
                print(
                    f"Redis 连接异常: {type(exc).__name__}"
                )
                print("停止检查，避免错误更新任务")
                break

            except Exception as exc:
                db.rollback()
                stats["error"] += 1
                print(
                    f"任务 {task_id} 检查失败: "
                    f"{type(exc).__name__}: {exc}"
                )

        print("\n========== 检查结果 ==========")

        for status, count in stats.items():
            print(f"{status}: {count}")

        print("任务状态检查结束")


if __name__ == "__main__":
    main()
