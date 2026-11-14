from backend.services.market_guard import (
    validate_market_history,
    MarketDataUnavailable
)












from backend.services.market_guard import (
    validate_market_history,
    MarketDataUnavailable
)


import logging
from pathlib import Path

from dotenv import load_dotenv

# ==================================================
# 1. 加载环境变量
# ==================================================

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

from sqlalchemy import select

from backend.core.database import SessionLocal
from backend.models.analysis import AnalysisTask

from backend.services.local_market_setup import (
    build_local_graph_config
)

from backend.services.local_snapshot import (
    build_local_verified_snapshot
)

from tradingagents.graph.trading_graph import TradingAgentsGraph

logger = logging.getLogger(__name__)


# ==================================================
# 2. 执行真实股票分析任务
# ==================================================

def run_analysis_job(
    task_id: str,
    ticker: str,
    analysis_date: str
):
    # 每个 Worker 任务创建独立数据库会话
    db = SessionLocal()

    try:
        # ------------------------------------------
        # 第一步：查询 MySQL 中的任务
        # ------------------------------------------

        task = db.scalar(
            select(AnalysisTask).where(
                AnalysisTask.task_id == task_id
            )
        )

        if task is None:
            raise ValueError(f"任务不存在：{task_id}")

        # 更新为正在运行
        task.status = "running"
        db.commit()


        # 调用 DeepSeek 前检查历史数据
        validate_market_history(
            ticker,
            analysis_date,
            minimum_rows=200
        )




        # 调用 DeepSeek 前检查历史数据是否足够
        validate_market_history(
            ticker,
            analysis_date,
            minimum_rows=200
        )





        logger.warning(
            "开始分析股票：%s，日期：%s",
            ticker,
            analysis_date
        )

        # ------------------------------------------
        # 第二步：检查本地股票行情
        # ------------------------------------------

        snapshot = build_local_verified_snapshot(
            ticker,
            analysis_date,
            5
        )

        if "Latest OHLCV" not in snapshot:
            raise ValueError("本地行情预检查失败")

        logger.warning(
            "本地行情检查通过：%s %s",
            ticker,
            analysis_date
        )

        # ------------------------------------------
        # 第三步：加载本地数据源配置
        # ------------------------------------------

        config = build_local_graph_config()

        # 获取实际配置的数据源
        tool_vendors = config.get("tool_vendors", {})

        stock_vendor = tool_vendors.get(
            "get_stock_data"
        )

        indicator_vendor = tool_vendors.get(
            "get_indicators"
        )

        logger.warning(
            "股票行情数据源：%s",
            stock_vendor
        )

        logger.warning(
            "技术指标数据源：%s",
            indicator_vendor
        )

        # 检查是否正确使用 local_csv
        if (
            stock_vendor != "local_csv"
            or indicator_vendor != "local_csv"
        ):
            raise RuntimeError(
                "Worker 未正确加载本地数据源"
            )

        # ------------------------------------------
        # 第四步：创建 TradingAgentsGraph
        # ------------------------------------------

        # 注意：只创建一次 Graph
        graph = TradingAgentsGraph(
            selected_analysts=["market"],
            debug=False,
            config=config
        )

        logger.warning(
            "TradingAgentsGraph 创建成功"
        )

        # ------------------------------------------
        # 第五步：执行股票分析
        # ------------------------------------------

        state, decision = graph.propagate(
            ticker,
            analysis_date
        )

        logger.warning(
            "TradingAgents 分析执行结束"
        )

        # ------------------------------------------
        # 第六步：整理分析报告
        # ------------------------------------------

        report_parts = []

        report_fields = [
            ("market_report", "市场分析"),
            ("investment_plan", "研究结论"),
            ("trader_investment_plan", "交易计划"),
            ("final_trade_decision", "最终报告"),
        ]

        for key, title in report_fields:

            content = state.get(key)

            if content:
                report_parts.append(
                    f"## {title}\n{content}"
                )

        if not report_parts:
            raise ValueError(
                "TradingAgents 未生成分析报告"
            )

        full_report = "\n\n".join(report_parts)

        # ------------------------------------------
        # 第七步：检查报告的数据质量
        # ------------------------------------------

        unavailable_markers = [
            "DATA_UNAVAILABLE",
            "NO_DATA_AVAILABLE",
            "本次分析未获得任何市场数据",
            "未获取到任何市场数据",
        ]

        report_upper = full_report.upper()

        data_unavailable = any(
            marker.upper() in report_upper
            for marker in unavailable_markers
        )

        # 保存报告
        task.report = full_report

        if data_unavailable:

            task.status = "data_unavailable"
            task.decision = None
            task.error_message = (
                "分析报告包含行情数据缺失提示"
            )

            logger.warning(
                "股票 %s 分析报告存在数据缺失",
                ticker
            )

        else:

            task.status = "completed"
            task.decision = str(decision)[:30]
            task.error_message = None

            logger.warning(
                "股票 %s 分析完成：%s",
                ticker,
                task.decision
            )

        # ------------------------------------------
        # 第八步：保存到 MySQL
        # ------------------------------------------

        db.commit()

        logger.warning(
            "分析任务结果已保存到 MySQL：%s",
            task_id
        )

        return {
            "task_id": task_id,
            "status": task.status,
            "decision": task.decision
        }

    # ==============================================
    # 异常处理
    # ==============================================




    except MarketDataUnavailable as exc:
        db.rollback()

        task = db.scalar(
            select(AnalysisTask).where(
                AnalysisTask.task_id == task_id
            )
        )

        if task:
            task.status = "data_unavailable"
            task.decision = None
            task.error_message = str(exc)
            db.commit()

        logger.warning(
            "行情数据不足：%s",
            exc
        )

        return {
            "task_id": task_id,
            "status": "data_unavailable",
            "reason": str(exc)
        }


#-----------------------------------------------------------



    except MarketDataUnavailable as exc:
        db.rollback()

        task = db.scalar(
            select(AnalysisTask).where(
                AnalysisTask.task_id == task_id
            )
        )

        if task is not None:
            task.status = "data_unavailable"
            task.decision = None
            task.error_message = str(exc)
            db.commit()

        logger.warning(
            "历史行情数据不足：%s",
            exc
        )

        return {
            "task_id": task_id,
            "status": "data_unavailable",
            "reason": str(exc)
        }











    except Exception:

        db.rollback()

        logger.exception(
            "股票分析任务失败：%s",
            task_id
        )

        try:
            failed_task = db.scalar(
                select(AnalysisTask).where(
                    AnalysisTask.task_id == task_id
                )
            )

            if failed_task is not None:

                failed_task.status = "failed"

                failed_task.error_message = (
                    "股票分析执行失败，请查看 Worker 日志"
                )

                db.commit()

        except Exception:

            db.rollback()

            logger.exception(
                "任务失败状态保存失败：%s",
                task_id
            )

        raise

    # ==============================================
    # 关闭数据库连接
    # ==============================================

    finally:
        db.close()


# ==================================================
# 3. Worker 数据源诊断函数
# ==================================================

def check_worker_data_source():

    from tradingagents.dataflows.config import (
        run_config
    )

    from tradingagents.dataflows.router import (
        get_vendor,
        route_to_vendor
    )

    # 加载本地数据源配置
    config = build_local_graph_config()

    # 在 TradingAgents 配置上下文中测试
    with run_config(config):

        stock_vendor = get_vendor(
            "core_stock_apis",
            "get_stock_data"
        )

        indicator_vendor = get_vendor(
            "technical_indicators",
            "get_indicators"
        )

        print(
            "股票行情数据源:",
            stock_vendor,
            flush=True
        )

        print(
            "技术指标数据源:",
            indicator_vendor,
            flush=True
        )

        if (
            stock_vendor != "local_csv"
            or indicator_vendor != "local_csv"
        ):
            raise RuntimeError(
                "Worker 未正确加载本地数据源"
            )

        # 测试本地股票行情
        stock_data = route_to_vendor(
            "get_stock_data",
            "AAPL",
            "2026-11-09",
            "2026-11-10"
        )

        # 测试本地 RSI
        indicator_data = route_to_vendor(
            "get_indicators",
            "AAPL",
            "rsi",
            "2026-11-10",
            5
        )

    if "348.51" not in stock_data:
        raise RuntimeError(
            "本地股票行情数据异常"
        )

    if "55.8914" not in indicator_data:
        raise RuntimeError(
            "本地 RSI 指标数据异常"
        )

    return {
        "stock_vendor": stock_vendor,
        "indicator_vendor": indicator_vendor,
        "status": "ok"
    }
