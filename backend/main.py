from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError
from rq.job import Job

from backend.core.queue import analysis_queue
from backend.core.redis_client import redis_client
from backend.tasks.demo_task import demo_task



import logging
from datetime import date
from uuid import uuid4

from dotenv import load_dotenv

# 加载 .env 中的 DeepSeek 配置
load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.analysis import AnalysisTask

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph


app = FastAPI(title="TradingAgents 智能股票分析系统")
logger = logging.getLogger(__name__)


# 请求参数模型
class AnalysisRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=16)
    analysis_date: date


# 1. 健康检查接口
@app.get("/health")
def health():
    return {"status": "ok"}


# 2. 股票分析接口
@app.post("/api/v1/analyses/run")
def analyze_stock(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    ticker = request.ticker.upper()
    task_id = str(uuid4())

    # 第一步：创建任务记录
    task = AnalysisTask(
        task_id=task_id,
        ticker=ticker,
        analysis_date=request.analysis_date,
        status="running"
    )

    db.add(task)
    db.commit()

    try:
        # 第二步：调用 TradingAgents
        config = DEFAULT_CONFIG.copy()

        graph = TradingAgentsGraph(
            selected_analysts=["market"],
            debug=False,
            config=config
        )

        state, decision = graph.propagate(
            ticker,
            request.analysis_date.isoformat()
        )

        # 第三步：整理分析报告
        report_parts = []

        for key, title in [
            ("market_report", "市场分析"),
            ("investment_plan", "研究结论"),
            ("trader_investment_plan", "交易计划"),
            ("final_trade_decision", "最终报告"),
        ]:
            content = state.get(key)
            if content:
                report_parts.append(
                    f"## {title}\n{content}"
                )

        # 第四步：更新数据库
        task.status = "completed"
        task.decision = str(decision)[:30]
        task.report = "\n\n".join(report_parts)

        db.commit()

        return {
            "task_id": task_id,
            "ticker": ticker,
            "status": task.status,
            "decision": task.decision
        }

    except Exception as exc:
        db.rollback()
        logger.exception("股票分析失败")

        # 记录任务失败信息
        failed_task = db.scalar(
            select(AnalysisTask).where(
                AnalysisTask.task_id == task_id
            )
        )

        if failed_task:
            failed_task.status = "failed"
            failed_task.error_message = (
                f"{type(exc).__name__}: {str(exc)[:500]}"
            )
            db.commit()

        raise HTTPException(
            status_code=500,
            detail="股票分析失败，请查看服务器日志"
        )


# 3. 查询历史分析任务
@app.get("/api/v1/analyses")
def get_analyses(db: Session = Depends(get_db)):
    tasks = db.scalars(
        select(AnalysisTask)
        .order_by(AnalysisTask.id.desc())
        .limit(20)
    ).all()

    return [
        {
            "task_id": task.task_id,
            "ticker": task.ticker,
            "analysis_date": task.analysis_date,
            "status": task.status,
            "decision": task.decision,
        }
        for task in tasks
    ]


# 4. 查询单个任务的详细报告
@app.get("/api/v1/analyses/{task_id}")
def get_analysis(
    task_id: str,
    db: Session = Depends(get_db)
):
    task = db.scalar(
        select(AnalysisTask).where(
            AnalysisTask.task_id == task_id
        )
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="任务不存在"
        )

    return {
        "task_id": task.task_id,
        "ticker": task.ticker,
        "analysis_date": task.analysis_date,
        "status": task.status,
        "decision": task.decision,
        "report": task.report,
        "error_message": task.error_message,
    }



# 模拟异步任务的请求参数
class DemoJobRequest(BaseModel):
    ticker: str


# 5. 提交异步模拟任务
@app.post("/api/v1/demo-jobs", status_code=202)
def create_demo_job(request: DemoJobRequest):
    ticker = request.ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=422,
            detail="股票代码不能为空"
        )

    try:
        job = analysis_queue.enqueue(
            demo_task,
            ticker,
            job_timeout=60,
            result_ttl=3600
        )
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Redis 任务队列暂时不可用"
        )

    return {
        "job_id": job.id,
        "status": "submitted",
        "message": "任务已提交到 Redis 队列"
    }


# 6. 查询异步任务状态
@app.get("/api/v1/demo-jobs/{job_id}")
def get_demo_job(job_id: str):
    try:
        job = Job.fetch(
            job_id,
            connection=redis_client
        )

        status = job.get_status(refresh=True)

        return {
            "job_id": job.id,
            "status": status.value,
            "result": (
                job.return_value()
                if status.value == "finished"
                else None
            )
        }

    except NoSuchJobError:
        raise HTTPException(
            status_code=404,
            detail="任务不存在或已过期"
        )
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Redis 服务不可用"
        )



# 7. 提交真实股票分析任务（异步）
@app.post("/api/v1/analyses", status_code=202)
def create_analysis_job(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    ticker = request.ticker.strip().upper()

    if not ticker:
        raise HTTPException(
            status_code=422,
            detail="股票代码不能为空"
        )

    task_id = str(uuid4())

    # 1. 在 MySQL 中创建待执行任务
    task = AnalysisTask(
        task_id=task_id,
        ticker=ticker,
        analysis_date=request.analysis_date,
        status="pending"
    )

    db.add(task)
    db.commit()

    try:
        # 2. 把任务提交到 Redis 队列
        analysis_queue.enqueue(
            "backend.tasks.analysis_task.run_analysis_job",
            task_id,
            ticker,
            request.analysis_date.isoformat(),
            job_id=task_id,
            job_timeout=1800,
            result_ttl=3600
        )

    except Exception:
        logger.exception("任务提交到 Redis 失败")

        db.rollback()
        task.status = "failed"
        task.error_message = "提交任务队列失败"
        db.commit()

        raise HTTPException(
            status_code=503,
            detail="任务提交失败，请检查 Redis"
        )

    # 3. 立即返回任务 ID
    return {
        "task_id": task_id,
        "ticker": ticker,
        "status": "pending",
        "message": "股票分析任务已提交"
    }
