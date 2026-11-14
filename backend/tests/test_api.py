
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.database import get_db


# 创建测试客户端
@pytest.fixture
def client():
    # 使用模拟数据库，不连接真实 MySQL
    fake_db = MagicMock()
    fake_db.scalar.return_value = None

    # 替换 FastAPI 的数据库依赖
    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


# 测试1：健康检查接口
def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# 测试2：缺少分析日期
def test_analysis_missing_date(client):
    response = client.post(
        "/api/v1/analyses",
        json={
            "ticker": "AAPL"
        }
    )

    assert response.status_code == 422


# 测试3：查询不存在的任务
def test_analysis_not_found(client):
    response = client.get(
        "/api/v1/analyses/nonexistent-task-id"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "任务不存在"
