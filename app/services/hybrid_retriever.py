import os
import pickle
import logging
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from app.config import settings
from app.services.vector_store import get_embeddings

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self):
        self.embeddings = None
        self.bm25_retriever = None
        self.last_docs_mtime = 0
        self.documents_backup = []

    def _get_embeddings(self):
        if not self.embeddings:
            self.embeddings = get_embeddings()
        return self.embeddings

    def _load_faiss_index(self) -> FAISS | None:
        index_path = settings.faiss_index_path
        faiss_file = os.path.join(index_path, "index.faiss")
        if not os.path.exists(faiss_file):
            logger.warning(f"FAISS index file not found at {faiss_file}")
            return None
        return FAISS.load_local(
            index_path, 
            self._get_embeddings(), 
            allow_dangerous_deserialization=True
        )

    def _refresh_bm25_retriever(self) -> None:
        index_path = settings.faiss_index_path
        docs_pkl_path = os.path.join(index_path, "documents.pkl")
        
        if not os.path.exists(docs_pkl_path):
            logger.warning(f"Documents backup file not found at {docs_pkl_path}")
            self.bm25_retriever = None
            self.documents_backup = []
            return
            
        try:
            mtime = os.path.getmtime(docs_pkl_path)
            if mtime > self.last_docs_mtime or self.bm25_retriever is None:
                logger.info(f"Re-building BM25 index from {docs_pkl_path}...")
                with open(docs_pkl_path, "rb") as f:
                    self.documents_backup = pickle.load(f)
                if self.documents_backup:
                    self.bm25_retriever = BM25Retriever.from_documents(self.documents_backup)
                else:
                    self.bm25_retriever = None
                self.last_docs_mtime = mtime
                logger.info("BM25 index successfully re-built.")
        except Exception as e:
            logger.error(f"Failed to load documents for BM25: {e}")
            self.bm25_retriever = None
            self.documents_backup = []

    def retrieve(self, query: str, hybrid: bool = True, k: int = 5) -> list[Document]:
        # 1. Load FAISS index
        db = self._load_faiss_index()
        if db is None:
            logger.warning("Retrieval requested but FAISS index is empty/missing.")
            return []

        # 2. Dense Search
        dense_docs = db.similarity_search(query, k=k)

        if not hybrid:
            logger.info(f"Dense-only retrieval matching query. Found {len(dense_docs)} documents.")
            return dense_docs

        # 3. Sparse Search
        self._refresh_bm25_retriever()
        if self.bm25_retriever is None:
            logger.warning("Hybrid retrieval requested but BM25 index is unavailable. Defaulting to dense search.")
            return dense_docs

        # Configure retrieve size and execute sparse lookup
        self.bm25_retriever.k = k
        sparse_docs = self.bm25_retriever.invoke(query)

        # 4. Blending via Reciprocal Rank Fusion (RRF)
        logger.info(f"Blending {len(dense_docs)} dense and {len(sparse_docs)} sparse search results using RRF.")
        blended_docs = self._reciprocal_rank_fusion(dense_docs, sparse_docs, k=k)
        return blended_docs

    def _reciprocal_rank_fusion(self, dense_docs: list[Document], sparse_docs: list[Document], k: int = 5) -> list[Document]:
        rrf_scores = {}
        
        def add_ranks(doc_list):
            for rank, doc in enumerate(doc_list):
                source = doc.metadata.get("source", "unknown")
                page = doc.metadata.get("page", 0)
                chunk_idx = doc.metadata.get("chunk_index", 0)
                key = (doc.page_content, source, page, chunk_idx)
                
                if key not in rrf_scores:
                    rrf_scores[key] = {"doc": doc, "score": 0.0}
                # RRF weight formula: 1 / (60 + rank)
                rrf_scores[key]["score"] += 1.0 / (60.0 + (rank + 1))

        add_ranks(dense_docs)
        add_ranks(sparse_docs)

        # Sort blended documents by combined score descending
        sorted_results = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in sorted_results[:k]]

hybrid_retriever = HybridRetriever()
