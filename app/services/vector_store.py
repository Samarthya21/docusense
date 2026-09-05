import os
import pickle
import logging
import gc
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from app.config import settings

logger = logging.getLogger(__name__)

_cached_embeddings = None

def get_embeddings():
    global _cached_embeddings
    if _cached_embeddings is not None:
        return _cached_embeddings

    if getattr(settings, "embedding_provider", "huggingface").lower() == "huggingface":
        try:
            import torch
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
        except Exception:
            pass
        from langchain_community.embeddings import HuggingFaceEmbeddings
        logger.info("Using 100% Free Local HuggingFace Embeddings (all-MiniLM-L6-v2)")
        _cached_embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    else:
        from langchain_openai import OpenAIEmbeddings
        logger.info("Using OpenAI Embeddings")
        _cached_embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)

    return _cached_embeddings

def save_vector_store(documents: list[Document]) -> None:
    """
    Creates or updates the local FAISS index on disk and stores raw documents
    in a pickle file to build the hybrid BM25 index in subsequent steps.
    """
    embeddings = get_embeddings()
    index_path = settings.faiss_index_path
    
    # Ensure FAISS index directory exists
    os.makedirs(index_path, exist_ok=True)
    
    # 1. FAISS Index Operations
    faiss_file = os.path.join(index_path, "index.faiss")
    if os.path.exists(faiss_file):
        logger.info(f"Loading existing FAISS index from: {index_path}")
        # Local index loading requires allow_dangerous_deserialization
        db = FAISS.load_local(
            index_path, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        logger.info(f"Adding {len(documents)} chunks to existing FAISS index...")
        db.add_documents(documents)
    else:
        logger.info(f"Initializing new FAISS index with {len(documents)} chunks...")
        db = FAISS.from_documents(documents, embeddings)
        
    db.save_local(index_path)
    logger.info("FAISS index saved successfully.")
    
    # 2. Pickled Documents backup (for Hybrid/BM25 Index loader)
    docs_pkl_path = os.path.join(index_path, "documents.pkl")
    all_docs = []
    
    if os.path.exists(docs_pkl_path):
        try:
            with open(docs_pkl_path, "rb") as f:
                all_docs = pickle.load(f)
            logger.info(f"Loaded {len(all_docs)} existing documents from pickle backup.")
        except Exception as e:
            logger.error(f"Error reading existing documents pickle: {e}")
            
    # Append the new chunks
    all_docs.extend(documents)
    
    try:
        with open(docs_pkl_path, "wb") as f:
            pickle.dump(all_docs, f)
        logger.info(f"Saved total of {len(all_docs)} documents to pickle backup.")
    except Exception as e:
        logger.error(f"Error saving documents to pickle backup: {e}")
        raise
    finally:
        gc.collect()
