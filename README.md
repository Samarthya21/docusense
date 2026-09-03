# DocuSense — Production RAG Q&A System

DocuSense is a production-ready Retrieval-Augmented Generation (RAG) system that processes uploaded PDF and DOCX documents and answers user questions with strict inline citations. The system is designed to run asynchronously with a Redpanda ingestion pipeline, FAISS + BM25 hybrid retrieval, Redis query caching, and sliding-window rate limiting.

---

## 📽️ Demo Video & Visuals

### 📺 Video Demonstration
[![DocuSense Demo Video](https://img.youtube.com/vi/YOUR_VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)
*(Click above or view [Loom Video Demo](https://www.loom.com/share/YOUR_LOOM_ID) to watch the system in action)*

### 📸 Application Screenshots

| Interactive Q&A Dashboard | Source Citation Passages |
| :---: | :---: |
| ![UI Dashboard](docs/images/ui_dashboard.png) | ![Citations View](docs/images/citations_view.png) |

| Terminal Cache HIT/MISS Logs | 20 Automated Pytest Verification |
| :---: | :---: |
| ![Cache Logs](docs/images/cache_hit_logs.png) | ![Pytest Results](docs/images/test_results.png) |

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

## ⚡ Quick Start & Testing

### 1. Environment Configuration (`.env`)
Secrets like API keys are kept in `.env` (which is gitignored). Template default values are kept in `.env.example`.

1. Copy `.env.example` to create your local `.env` file:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env

   # Linux / macOS
   cp .env.example .env
   ```
2. Open `.env` and set your OpenAI API key:
   ```env
   OPENAI_API_KEY=sk-proj-your_actual_key_here
   ```

### 2. Launch Local Stack
Start all 5 containers in detached mode:
```bash
docker-compose up --build -d
```

### 3. Verify System URLs
- **Streamlit Frontend**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Run Automated Test Suite
Execute all 20 pytest unit tests inside the running container:
```bash
docker-compose exec api pytest tests/
```

---

## 🌐 How to Deploy for Free for Public Use

### Option 1: Streamlit Cloud (UI) + Render.com (Backend API) — Recommended
1. **Frontend UI (Free)**:
   - Push your code to GitHub.
   - Go to [share.streamlit.io](https://share.streamlit.io/) and connect your GitHub repo.
   - Set Main file path to `ui/app.py`.
   - Set environment variable `API_URL` to your live FastAPI backend URL.
2. **Backend API & Redis (Free)**:
   - Create a free Web Service on [Render.com](https://render.com/) pointing to your repo (using `Dockerfile`).
   - Create a free Redis instance on Render or [Upstash.com](https://upstash.com/).
   - Set `OPENAI_API_KEY` and `REDIS_URL` in Render environment settings.

### Option 2: Hugging Face Spaces (Docker Space — 100% Free 24/7)
1. Create a new Space on [Hugging Face Spaces](https://huggingface.co/spaces).
2. Choose **Docker** as the Space SDK.
3. Push your repository to Hugging Face. Hugging Face provides 16GB RAM and 2 vCPUs free 24/7 to host full Docker containers.

---

## 🛠️ Tech Stack & Constraints
- **Language**: Python 3.11+
- **Orchestration**: LangChain, FastAPI, Streamlit
- **Vector DB**: FAISS (persisted via Docker named volume `docusense_faiss_data`)
- **Async Broker**: Redpanda (Kafka compatible)
- **Cache**: Redis
