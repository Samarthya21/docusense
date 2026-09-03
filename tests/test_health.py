from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(name="client")
def fixture_client():
    # Patch the lifespans to prevent trying to connect to real services during startup
    with patch("app.services.redis_client.redis_client.connect", new_callable=AsyncMock), \
         patch("app.services.redpanda_client.redpanda_client.connect", new_callable=AsyncMock), \
         patch("app.services.redis_client.redis_client.close", new_callable=AsyncMock), \
         patch("app.services.redpanda_client.redpanda_client.close", new_callable=AsyncMock):
        
        # Import main only after patching to ensure lifespan mocks are active
        from app.main import app
        with TestClient(app) as test_c:
            yield test_c

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to DocuSense API" in response.json().get("message", "")

def test_health_check_all_healthy(client):
    with patch("app.services.redis_client.redis_client.ping", new_callable=AsyncMock, return_value=True), \
         patch("app.services.redpanda_client.redpanda_client.ping", new_callable=AsyncMock, return_value=True):
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["services"]["redis"] == "healthy"
        assert data["services"]["redpanda"] == "healthy"

def test_health_check_redis_unhealthy(client):
    with patch("app.services.redis_client.redis_client.ping", new_callable=AsyncMock, return_value=False), \
         patch("app.services.redpanda_client.redpanda_client.ping", new_callable=AsyncMock, return_value=True):
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["redis"] == "unhealthy"
        assert data["services"]["redpanda"] == "healthy"

def test_health_check_redpanda_unhealthy(client):
    with patch("app.services.redis_client.redis_client.ping", new_callable=AsyncMock, return_value=True), \
         patch("app.services.redpanda_client.redpanda_client.ping", new_callable=AsyncMock, return_value=False):
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["redis"] == "healthy"
        assert data["services"]["redpanda"] == "unhealthy"
