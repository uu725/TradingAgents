
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.tasks.analysis_task import run_analysis_job
from backend.services.market_guard import MarketDataUnavailable


# 测试1：模拟 DeepSeek 执行失败
def test_worker_analysis_failed():

    # 模拟 MySQL 中的任务
    task = SimpleNamespace(
        task_id="test-001",
        status="pending",
        decision=None,
        report=None,
        error_message=None
    )

    # 模拟数据库会话
    fake_db = MagicMock()
    fake_db.scalar.return_value = task

    config = {
        "tool_vendors": {
            "get_stock_data": "local_csv",
            "get_indicators": "local_csv"
        }
    }

    with (
        patch(
            "backend.tasks.analysis_task.SessionLocal",
            return_value=fake_db
        ),
        patch(
            "backend.tasks.analysis_task.validate_market_history"
        ),
        patch(
            "backend.tasks.analysis_task.build_local_verified_snapshot",
            return_value="Latest OHLCV"
        ),
        patch(
            "backend.tasks.analysis_task.build_local_graph_config",
            return_value=config
        ),
        patch(
            "backend.tasks.analysis_task.TradingAgentsGraph",
            side_effect=RuntimeError("模拟 DeepSeek 调用失败")
        )
    ):
        with pytest.raises(RuntimeError, match="模拟 DeepSeek 调用失败"):
            run_analysis_job(
                "test-001",
                "AAPL",
                "2026-11-10"
            )

    # 检查异常处理结果
    assert task.status == "failed"
    assert task.error_message is not None

    fake_db.rollback.assert_called_once()
    assert fake_db.commit.call_count == 2
    fake_db.close.assert_called_once()


# 测试2：历史行情不足时不调用模型
def test_worker_data_unavailable():

    task = SimpleNamespace(
        task_id="test-002",
        status="pending",
        decision=None,
        report=None,
        error_message=None
    )

    fake_db = MagicMock()
    fake_db.scalar.return_value = task

    with (
        patch(
            "backend.tasks.analysis_task.SessionLocal",
            return_value=fake_db
        ),
        patch(
            "backend.tasks.analysis_task.validate_market_history",
            side_effect=MarketDataUnavailable("历史数据不足")
        ),
        patch(
            "backend.tasks.analysis_task.TradingAgentsGraph"
        ) as mock_graph
    ):

        result = run_analysis_job(
            "test-002",
            "AAPL",
            "2026-11-10"
        )

    assert result["status"] == "data_unavailable"
    assert task.status == "data_unavailable"
    assert task.decision is None
    assert "历史数据不足" in task.error_message

    # 验证未创建 Graph
    mock_graph.assert_not_called()

    fake_db.close.assert_called_once()
