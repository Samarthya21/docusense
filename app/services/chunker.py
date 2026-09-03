from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging

logger = logging.getLogger(__name__)

def chunk_documents(documents: list[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    
    # split_documents automatically propagates source metadata (source, page, section, file_type)
    chunks = splitter.split_documents(documents)
    
    # Decorate chunks with chunk sequence numbers
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = idx
        
    logger.info(f"Split {len(documents)} document sections into {len(chunks)} chunks.")
    return chunks
