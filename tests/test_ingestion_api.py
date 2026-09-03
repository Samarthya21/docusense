from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import pytest
from fastapi.testclient import TestClient
import io

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

def test_upload_valid_pdf_success(client):
    # Mock redpanda client and writing file to disk
    with patch("app.services.redpanda_client.redpanda_client.publish_ingestion_task", new_callable=AsyncMock) as mock_publish, \
         patch("builtins.open", mock_open()) as mock_file:
         
        pdf_payload = b"%PDF-1.4 mock pdf header"
        response = client.post(
            "/upload",
            files={"file": ("sample.pdf", io.BytesIO(pdf_payload), "application/pdf")}
        )
        
        # Verify 202 Accepted response status code
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert data["filename"] == "sample.pdf"
        assert "task_id" in data
        
        # Verify file write was triggered
        mock_file.assert_called_once()
        
        # Verify redpanda task publish was called with expected arguments
        mock_publish.assert_called_once()
        args, kwargs = mock_publish.call_args
        assert kwargs["filename"] == "sample.pdf"
        assert "sample.pdf" in kwargs["file_path"]
        assert kwargs["task_id"] == data["task_id"]

def test_upload_invalid_extension_failure(client):
    txt_payload = b"plain text payload"
    response = client.post(
        "/upload",
        files={"file": ("sample.txt", io.BytesIO(txt_payload), "text/plain")}
    )
    
    # Assert 400 Bad Request
    assert response.status_code == 400
    assert "Only PDF and DOCX files are supported" in response.json()["detail"]
