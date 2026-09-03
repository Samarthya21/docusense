from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(name="client")
def fixture_client():
    # Patch lifespans
    with patch("app.services.redis_client.redis_client.connect", new_callable=AsyncMock), \
         patch("app.services.redpanda_client.redpanda_client.connect", new_callable=AsyncMock), \
         patch("app.services.redis_client.redis_client.close", new_callable=AsyncMock), \
         patch("app.services.redpanda_client.redpanda_client.close", new_callable=AsyncMock):
        
        from app.main import app
        with TestClient(app) as test_c:
            yield test_c

def test_query_endpoint_rate_limiting_blocks(client):
    # Setup rate limit check mock to return False (blocking the client)
    with patch("app.services.redis_client.redis_client.check_rate_limit", return_value=False) as mock_rate_limit:
        payload = {
            "question": "Is rate limiting enabled?",
            "hybrid": True
        }
        
        response = client.post("/query", json=payload)
        
        # Assert status code is 429 Too Many Requests
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        mock_rate_limit.assert_called_once()
