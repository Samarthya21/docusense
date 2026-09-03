# DocuSense — Production RAG Q&A System

DocuSense is a production-ready Retrieval-Augmented Generation (RAG) system that processes uploaded PDF and DOCX documents and answers user questions with strict inline citations. The system is designed to run asynchronously with an ingestion pipeline and features cached, rate-limited query routes.

---

## 🏗️ System Architecture

DocuSense is built using a modern, scalable microservices design orchestrated via Docker Compose:

```
                  ┌───────────────────┐
                  │   Streamlit UI    │ (Port 8501)
                  └─────────┬─────────┘
                            │ (REST HTTP)
                            ▼
                  ┌───────────────────┐
                  │    FastAPI API    ├──────────┐
                  └────┬───────────┬──┘          │ (IP Rate Limit / Cache)
                       │           │             ▼
    (Ingestion Task)   │           │       ┌───────────┐
   Publish metadata    │           │       │   Redis   │ (Port 6389)
                       ▼           │       └───────────┘
                  ┌──────────┐     │
                  │ Redpanda │     │ (Shared Disk / Volume)
                  └────┬─────┘     │
                       │           │
      Consume task     │           │
                       ▼           ▼
                  ┌───────────────────┐
                  │ Ingestion Worker  │
                  └─────────┬─────────┘
                            │ (Computes OpenAI Embeddings)
                            ▼
                  ┌───────────────────┐
                  │    FAISS Index    │ (Docker Volume Persistence)
                  └───────────────────┘
```

1. **FastAPI (API)**: Accepts document uploads, enqueues ingestion tasks asynchronously, and serves Q&A queries.
2. **Streamlit (UI)**: An elegant web dashboard for uploading documents, submitting queries, toggling retrieval modes, and viewing citations.
3. **Redpanda (Broker)**: A high-performance, Kafka-compatible message broker that handles async queueing of document parsing and embedding tasks.
4. **Redis (Cache & Rate Limiter)**: Serves cached query responses to prevent duplicate LLM cost and enforces sliding-window client IP rate limiting.
5. **Worker (Consumer)**: A daemon that dequeues ingestion tasks, extracts page-by-page text from documents, chunks it recursively, computes OpenAI embeddings, builds the local FAISS index, and invalidates stale caches.

---

## 📊 Evaluation & Retrieval Metrics

We evaluated the system's retrieval performance across **15 hand-labeled QA pairs** comparing **Plain Vector Search (dense-only)** against **Hybrid Search (dense + sparse RRF)**.

The results are persisted in [`evaluation_results.md`](file:///c:/Users/SamarthyaAlok/Desktop/docusense/evaluation_results.md):

- **Plain Vector Search (dense-only) Hit Rate @ 3**: **66.67%**
- **Hybrid Search (FAISS + BM25 RRF) Hit Rate @ 3**: **93.33%**
- **Performance Increase**: **+26.66% accuracy boost** under Hybrid blending.

*Lexical keyword matching (BM25) significantly improves search hit rates for legal conditions, version numbers, or precise numerical values.*

---

## ⚡ Quick Start

### Prerequisites
- Docker & Docker Compose
- An OpenAI API Key

### Setup & Run
1. Clone this repository to your machine.
2. Copy the environment variables example file to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` and fill in your OpenAI API Key:
   ```env
   OPENAI_API_KEY=sk-proj-...
   ```
4. Start all services in the background:
   ```bash
   docker-compose up --build -d
   ```
5. Access the Streamlit user interface in your browser:
   - Streamlit UI: [http://localhost:8501](http://localhost:8501)
   - FastAPI Backend: [http://localhost:8000](http://localhost:8000)
   - FastAPI Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing Suite

DocuSense features a comprehensive unit test suite covering health checks, parser routing, chunking, queue publishes, RRF blending, cached API hits, and 429 rate limit triggers.

Run the test suite inside the API container using:
```bash
docker-compose exec api pytest tests/
```

Expected output:
```
======================== 20 passed, 1 warning in 2.25s =========================
```

---

## 🛠️ Tech Stack & Constraints
- **Language**: Python 3.11+
- **Orchestration**: LangChain, FastAPI, Streamlit
- **Vector DB**: FAISS (persisted via Docker named volume `docusense_faiss_data`)
- **Async Broker**: Redpanda (Kafka compatible)
- **Cache**: Redis
