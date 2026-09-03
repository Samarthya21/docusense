from unittest.mock import MagicMock, patch
import pytest
from langchain_core.documents import Document
from app.services.hybrid_retriever import hybrid_retriever

def test_reciprocal_rank_fusion_logic():
    # Setup mock documents
    doc_a = Document(
        page_content="Dense chunk content",
        metadata={"source": "doc_a.pdf", "page": 1, "chunk_index": 0}
    )
    doc_b = Document(
        page_content="Shared chunk content",
        metadata={"source": "doc_b.pdf", "page": 2, "chunk_index": 1}
    )
    doc_c = Document(
        page_content="Sparse chunk content",
        metadata={"source": "doc_c.pdf", "page": 3, "chunk_index": 2}
    )
    
    # doc_b is returned by both dense and sparse retrievers
    dense_results = [doc_a, doc_b]
    sparse_results = [doc_b, doc_c]
    
    # Run fusion
    blended = hybrid_retriever._reciprocal_rank_fusion(dense_results, sparse_results, k=3)
    
    # doc_b should rank first due to appearing in both outputs (highest RRF score)
    assert len(blended) == 3
    assert blended[0].metadata["source"] == "doc_b.pdf"
    assert blended[0].page_content == "Shared chunk content"

def test_retriever_dense_only_toggle():
    # Mock vector database
    mock_db = MagicMock()
    mock_doc = Document(
        page_content="Dense search output content", 
        metadata={"source": "dense_only.pdf", "page": 1}
    )
    mock_db.similarity_search.return_value = [mock_doc]
    
    with patch.object(hybrid_retriever, "_load_faiss_index", return_value=mock_db):
        # hybrid=False enforces vector search only
        results = hybrid_retriever.retrieve("test question", hybrid=False, k=1)
        
        assert len(results) == 1
        assert results[0].page_content == "Dense search output content"
        mock_db.similarity_search.assert_called_once_with("test question", k=1)

def test_retriever_hybrid_fusion_routing():
    mock_db = MagicMock()
    doc_dense = Document(
        page_content="Dense document", 
        metadata={"source": "dense.pdf", "page": 1}
    )
    mock_db.similarity_search.return_value = [doc_dense]
    
    mock_bm25 = MagicMock()
    doc_sparse = Document(
        page_content="Sparse document", 
        metadata={"source": "sparse.pdf", "page": 2}
    )
    mock_bm25.invoke.return_value = [doc_sparse]
    
    with patch.object(hybrid_retriever, "_load_faiss_index", return_value=mock_db), \
         patch.object(hybrid_retriever, "_refresh_bm25_retriever") as mock_refresh:
        
        # Inject mock BM25 retriever
        hybrid_retriever.bm25_retriever = mock_bm25
        
        results = hybrid_retriever.retrieve("hybrid search query", hybrid=True, k=2)
        
        assert len(results) == 2
        mock_refresh.assert_called_once()
        mock_db.similarity_search.assert_called_once_with("hybrid search query", k=2)
        mock_bm25.invoke.assert_called_once_with("hybrid search query")
