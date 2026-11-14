
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    String,
    Text,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


# 创建 ORM 模型基类
class Base(DeclarativeBase):
    pass


# 映射 MySQL 中的 analysis_tasks 表
class AnalysisTask(Base):

    __tablename__ = "analysis_tasks"

    id: Mapped[int] = mapped_column( BigInteger, primary_key=True, autoincrement=True)

    task_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False )

    ticker: Mapped[str] = mapped_column(String(16), nullable=False)

    analysis_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    decision: Mapped[str | None] = mapped_column(String(30))

    report: Mapped[str | None] = mapped_column(Text)

    error_message: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime | None] = mapped_column(DateTime)

    updated_at: Mapped[datetime | None] = mapped_column(DateTime)
