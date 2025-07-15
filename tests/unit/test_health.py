"""
健康檢查端點測試

測試 /health 端點的功能。
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_endpoint_success(test_client: TestClient):
    """測試健康檢查端點成功情況"""
    response = test_client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "components" in data

    # 檢查組件狀態
    components = data["components"]
    assert "database" in components
    assert "api" in components

    # 檢查資料庫組件
    db_component = components["database"]
    assert "status" in db_component
    assert "connected" in db_component

    # 檢查 API 組件
    api_component = components["api"]
    assert "status" in api_component
    assert api_component["status"] == "healthy"


@pytest.mark.unit
def test_health_endpoint_structure(test_client: TestClient):
    """測試健康檢查響應結構"""
    response = test_client.get("/health")

    assert response.status_code == 200

    data = response.json()

    # 必需字段
    required_fields = ["status", "timestamp", "version", "components"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # 可選字段
    optional_fields = ["uptime_seconds", "memory_usage_mb"]
    for field in optional_fields:
        if field in data:
            assert isinstance(data[field], (int, float, type(None)))


@pytest.mark.unit
def test_root_endpoint(test_client: TestClient):
    """測試根端點"""
    response = test_client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "description" in data
    assert data["name"] == "Mnemosyne MCP API"


@pytest.mark.unit
def test_version_endpoint(test_client: TestClient):
    """測試版本端點"""
    response = test_client.get("/version")

    assert response.status_code == 200

    data = response.json()
    assert "version" in data
    assert "build" in data
    assert "api_version" in data
    assert "environment" in data

    assert data["version"] == "0.1.0"
    assert data["api_version"] == "v1"
