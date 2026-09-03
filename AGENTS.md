AGENTS.md — DocuSense (Production RAG Q&A System)
Rename this file to `AGENTS.md` and place it in the project root before opening the folder in Antigravity (or Cursor/Claude Code). Full context and rationale for every decision below lives in `AI_Projects_Brief.md` — read that first if anything here is ambiguous.
Goal
Build and deploy a Retrieval-Augmented Generation system that answers questions over uploaded PDF/DOCX documents with cited sources, using an async ingestion pipeline and query caching — not a single-file notebook script.
Hard Constraints — do not substitute without asking first
Language: Python 3.11+
Orchestration: LangChain
Vector DB: FAISS (local, on-disk, persisted via a Docker volume)
LLM: OpenAI or Claude API — read the key from `.env`, never hardcode it, never log it
Async broker: Redpanda (Kafka-API compatible) via Docker — not managed/cloud Kafka
Cache: Redis via Docker
API: FastAPI
UI: Streamlit
All services defined in a single `docker-compose.yml`
Definition of Done
[ ] Upload endpoint accepts PDF/DOCX, chunks text, and enqueues embedding jobs asynchronously via Redpanda (upload call returns immediately, doesn't block on processing)
[ ] A consumer processes the queue, generates embeddings, and writes them to FAISS
[ ] Query endpoint retrieves top-k relevant chunks, calls the LLM, and returns an answer with citation (source document + page/section)
[ ] Hybrid retrieval implemented (dense + keyword), with a toggle so plain-vector-only can be compared against it for the eval script below
[ ] Identical repeat queries are served from Redis cache — log a visible cache HIT/MISS marker so this is verifiable
[ ] A basic rate limit or fixed demo-query budget per IP is implemented (protects LLM API cost once this is public)
[ ] Streamlit UI: upload a document, ask a question, see the answer with its citation, with zero setup beyond `docker-compose up`
[ ] An eval script exists: runs a ~15–20 question hand-labeled QA set, reports retrieval accuracy for plain vector search vs. hybrid, and writes the result to a file (not just stdout)
[ ] `.env.example` committed with placeholder values; `.env` itself is gitignored
[ ] README follows the checklist in `AI_Projects_Brief.md`, including the real numbers from the eval script above — do not leave placeholder metrics in the final README
[ ] Fresh clone + `docker-compose up` brings the full stack up with no manual steps beyond copying `.env.example` to `.env` and filling in an API key
Stop and ask before doing any of the following
Provisioning any cloud resource (VM, domain, DNS record) — deployment infrastructure is handled by me, not the agent
Adding a paid dependency or service not already listed above
Committing, hardcoding, or printing any credential or API key
Deviating from the tech stack listed under Hard Constraints
Testing
Write pytest tests for: the ingestion/chunking logic, the retrieval function (mock the vector DB), and the query endpoint (mock the LLM call so tests don't burn API credits)
Do not mark a checklist item done until its corresponding test passes
Run the full test suite before declaring the project complete