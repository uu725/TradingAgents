
from datetime import date
from uuid import uuid4
from unittest.mock import patch

from sqlalchemy import select

from backend.core.database import SessionLocal
from backend.models.analysis import AnalysisTask
from backend.tasks.analysis_task import run_analysis_job


def main():
    # 1. 生成测试任务 ID
    task_id = str(uuid4())

    # 2. 在 MySQL 创建测试任务
    with SessionLocal() as db:
        task = AnalysisTask(
            task_id=task_id,
            ticker="AAPL",
            analysis_date=date(2026, 11, 10),
            status="pending"
        )

        db.add(task)
        db.commit()

    print("测试任务已创建:", task_id)

    # 3. 执行真实任务函数
    # 用 mock 禁止初始化 TradingAgentsGraph
    # 保证测试不调用 DeepSeek
    with patch(
        "backend.tasks.analysis_task.TradingAgentsGraph",
        side_effect=AssertionError(
            "测试不允许初始化 TradingAgentsGraph"
        )
    ):
        result = run_analysis_job(
            task_id,
            "AAPL",
            "2026-11-10"
        )

    print("任务返回结果:", result)

    # 4. 从 MySQL 查询任务最终状态
    with SessionLocal() as db:
        task = db.scalar(
            select(AnalysisTask).where(
                AnalysisTask.task_id == task_id
            )
        )

        assert task is not None

        print("MySQL 任务状态:", task.status)
        print("错误原因:", task.error_message)

        # 5. 验证数据不足状态
        assert task.status == "data_unavailable"
        assert task.decision is None
        assert "历史数据不足" in (
            task.error_message or ""
        )

    assert result["status"] == "data_unavailable"

    print("\n数据质量保护测试全部通过！")
    print("DeepSeek 模型未被调用")


if __name__ == "__main__":
    main()
