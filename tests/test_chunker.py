from langchain_core.documents import Document
from app.services.chunker import chunk_documents

def test_chunk_documents_splitting():
    # Setup doc with large text block to trigger splitting
    doc_text = "This is a test sentence that will be repeated to ensure chunking splits it. " * 30
    doc = Document(
        page_content=doc_text,
        metadata={"source": "split_test.pdf", "page": 5, "file_type": "pdf"}
    )
    
    chunks = chunk_documents([doc], chunk_size=500, chunk_overlap=100)
    
    # Assert it was split into multiple chunks
    assert len(chunks) > 1
    
    # Assert metadata integrity is preserved across all chunks
    for idx, chunk in enumerate(chunks):
        assert chunk.metadata["source"] == "split_test.pdf"
        assert chunk.metadata["page"] == 5
        assert chunk.metadata["file_type"] == "pdf"
        assert chunk.metadata["chunk_index"] == idx
        assert len(chunk.page_content) <= 500
