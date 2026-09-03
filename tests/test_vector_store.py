import os
import pickle
import shutil
from unittest.mock import patch, MagicMock
import pytest
from langchain_core.documents import Document
from app.services.vector_store import save_vector_store
from app.config import settings

@pytest.fixture(name="temp_index_path")
def fixture_temp_index_path(tmp_path):
    # Temporarily override settings FAISS index path for testing
    orig_path = settings.faiss_index_path
    temp_path = str(tmp_path / "faiss_index")
    settings.faiss_index_path = temp_path
    yield temp_path
    settings.faiss_index_path = orig_path
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)

def test_save_vector_store_success(temp_index_path):
    # Mock OpenAIEmbeddings to return dummy 1536-dimensional vectors
    mock_embeddings = MagicMock()
    mock_embeddings.embed_documents.return_value = [[0.1] * 1536]
    mock_embeddings.embed_query.return_value = [0.1] * 1536
    
    docs = [
        Document(
            page_content="This is a test chunk content to verify index generation.",
            metadata={"source": "test.pdf", "page": 1, "chunk_index": 0}
        )
    ]
    
    with patch("app.services.vector_store.get_embeddings", return_value=mock_embeddings):
        # Trigger index creation
        save_vector_store(docs)
        
        # Verify index files and backup documents are written
        faiss_file = os.path.join(temp_index_path, "index.faiss")
        pkl_file = os.path.join(temp_index_path, "index.pkl")
        docs_file = os.path.join(temp_index_path, "documents.pkl")
        
        assert os.path.exists(faiss_file)
        assert os.path.exists(pkl_file)
        assert os.path.exists(docs_file)
        
        # Deserialize backup pickle and check contents
        with open(docs_file, "rb") as f:
            saved_docs = pickle.load(f)
            
        assert len(saved_docs) == 1
        assert saved_docs[0].page_content == "This is a test chunk content to verify index generation."
        assert saved_docs[0].metadata["source"] == "test.pdf"
        assert saved_docs[0].metadata["page"] == 1
