from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

@pytest.fixture(name="client")
def fixture_client():
    # Patch lifespans to prevent connecting to live services
    with patch("app.services.redis_client.redis_client.connect", new_callable=AsyncMock), \
         patch("app.services.redpanda_client.redpanda_client.connect", new_callable=AsyncMock), \
         patch("app.services.redis_client.redis_client.close", new_callable=AsyncMock), \
         patch("app.services.redpanda_client.redpanda_client.close", new_callable=AsyncMock):
        
        from app.main import app
        with TestClient(app) as test_c:
            yield test_c

def test_query_documents_success(client):
    # Setup mock document chunks
    mock_doc = Document(
        page_content="FareNexus provides NDC API connection services for travel agencies.",
        metadata={"source": "FareNexus_spec.pdf", "page": 10, "chunk_index": 5}
    )
    
    with patch("app.services.hybrid_retriever.hybrid_retriever.retrieve", return_value=[mock_doc]) as mock_retrieve, \
         patch("app.services.llm_service.llm_service.generate_answer", return_value="FareNexus offers NDC connections. [FareNexus_spec.pdf, 10]") as mock_llm:
         
        payload = {
            "question": "What services does FareNexus offer?",
            "hybrid": True,
            "k": 5
        }
        
        response = client.post("/query", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert data["answer"] == "FareNexus offers NDC connections. [FareNexus_spec.pdf, 10]"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["source"] == "FareNexus_spec.pdf"
        assert data["sources"][0]["page"] == 10
        assert data["sources"][0]["content"] == "FareNexus provides NDC API connection services for travel agencies."
        
        # Verify retrievals and LLM invocations were called with proper arguments
        mock_retrieve.assert_called_once_with(query="What services does FareNexus offer?", hybrid=True, k=5)
        mock_llm.assert_called_once_with(query="What services does FareNexus offer?", documents=[mock_doc])

def test_query_validation_empty_question(client):
    payload = {
        "question": "   ",
        "hybrid": False,
        "k": 2
    }
    
    response = client.post("/query", json=payload)
    
    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]
