
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.services.task_reconcile import reconcile_task


def make_task(status="running"):
    return SimpleNamespace(
        task_id="test-001",
        status=status,
        error_message=None
    )


# 测试1：RQ 失败时修复 MySQL
def test_reconcile_failed_job():
    task = make_task()
    db = MagicMock()
    db.scalar.return_value = task

    fake_job = MagicMock()
    fake_job.get_status.return_value = "failed"

    with patch(
        "backend.services.task_reconcile.Job.fetch",
        return_value=fake_job
    ):
        result = reconcile_task("test-001", db)

    assert result["status"] == "reconciled"
    assert task.status == "failed"
    assert "failed" in task.error_message
    db.commit.assert_called_once()


# 测试2：正在执行的任务不应修改
def test_reconcile_running_job():
    task = make_task()
    db = MagicMock()
    db.scalar.return_value = task

    fake_job = MagicMock()
    fake_job.get_status.return_value = "started"

    with patch(
        "backend.services.task_reconcile.Job.fetch",
        return_value=fake_job
    ):
        result = reconcile_task("test-001", db)

    assert result["status"] == "unchanged"
    assert task.status == "running"
    db.commit.assert_not_called()


# 测试3：已完成任务不能被覆盖
def test_reconcile_completed_task():
    task = make_task("completed")
    db = MagicMock()
    db.scalar.return_value = task

    result = reconcile_task("test-001", db)

    assert result["status"] == "skipped"
    assert task.status == "completed"
    db.commit.assert_not_called()
