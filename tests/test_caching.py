from unittest.mock import AsyncMock, MagicMock, patch
import json
import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

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

def test_query_caching_hit_and_miss_flow(client):
    mock_doc = Document(
        page_content="RAG systems cache duplicate entries.",
        metadata={"source": "cache_spec.pdf", "page": 2}
    )
    mock_answer = "RAG queries are cached. [cache_spec.pdf, 2]"
    
    # Simulating Redis store locally
    redis_store = {}
    
    async def mock_get(key):
        return redis_store.get(key)
        
    async def mock_setex(key, seconds, value):
        redis_store[key] = value

    with patch("app.services.redis_client.redis_client.get", side_effect=mock_get) as mock_redis_get, \
         patch("app.services.redis_client.redis_client.setex", side_effect=mock_setex) as mock_redis_set, \
         patch("app.services.redis_client.redis_client.check_rate_limit", return_value=True), \
         patch("app.services.hybrid_retriever.hybrid_retriever.retrieve", return_value=[mock_doc]) as mock_retrieve, \
         patch("app.services.llm_service.llm_service.generate_answer", return_value=mock_answer) as mock_llm:
         
        payload = {"question": "How is caching structured?", "hybrid": True}
        cache_key = "query_cache:How is caching structured?:True:5"
        
        # --- First Query: CACHE MISS ---
        response_miss = client.post("/query", json=payload)
        assert response_miss.status_code == 200
        data_miss = response_miss.json()
        assert data_miss["answer"] == mock_answer
        
        # Assert database and LLM pipeline were executed
        mock_redis_get.assert_called_once_with(cache_key)
        mock_retrieve.assert_called_once()
        mock_llm.assert_called_once()
        mock_redis_set.assert_called_once()
        assert cache_key in redis_store
        
        # Reset mock call tracers
        mock_redis_get.reset_mock()
        mock_retrieve.reset_mock()
        mock_llm.reset_mock()
        mock_redis_set.reset_mock()
        
        # --- Second Query: CACHE HIT ---
        response_hit = client.post("/query", json=payload)
        assert response_hit.status_code == 200
        data_hit = response_hit.json()
        assert data_hit["answer"] == mock_answer
        
        # Assert response was served directly from Redis cache
        mock_redis_get.assert_called_once_with(cache_key)
        mock_retrieve.assert_not_called()
        mock_llm.assert_not_called()
        mock_redis_set.assert_not_called()
