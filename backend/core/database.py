import os

from pathlib import Path

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# 加载项目根目录的 .env 文件
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# 配置 MySQL 连接地址
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST", "127.0.0.1"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    database=os.getenv("MYSQL_DATABASE", "tradingagents_db"),
    query={"charset": "utf8mb4"}
)

# 创建数据库连接引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# 创建数据库会话工厂
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# 给 FastAPI 提供数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
