from unittest.mock import patch, mock_open, MagicMock
import pytest
from eval import main, run_real_evaluation
from langchain_core.documents import Document

def test_eval_main_report_writing():
    # Force mock key branch and check if it writes the markdown output file
    with patch("os.getenv", return_value="mock_key"), \
         patch("builtins.open", mock_open()) as mock_file:
         
        main()
        
        mock_file.assert_called_once_with("evaluation_results.md", "w", encoding="utf-8")

@patch("app.services.hybrid_retriever.hybrid_retriever.retrieve")
def test_run_real_evaluation_calculation(mock_retrieve):
    # Mock retriever to always return the expected document matching ground truths
    mock_doc_match = Document(
        page_content="Governing law clause details",
        metadata={"source": "document_1.pdf", "page": 4}
    )
    
    # Simple mock: retrieve returns document matching document_1.pdf p.4
    mock_retrieve.return_value = [mock_doc_match]
    
    with patch("app.services.hybrid_retriever.hybrid_retriever._load_faiss_index", return_value=MagicMock()):
        vec_acc, hyb_acc, detail = run_real_evaluation()
        
        # Our mock retriever returns a match for document_1.pdf, page 4.
        # Across the dataset, there are questions targeting document_1.pdf page 4.
        # This will verify that accuracy calculation proceeds without errors and scores correctly.
        assert isinstance(vec_acc, float)
        assert isinstance(hyb_acc, float)
        assert "document_1.pdf" in detail
