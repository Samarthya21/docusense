import logging
import uuid
import os
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from app.services.redis_client import redis_client
from app.services.redpanda_client import redpanda_client

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up DocuSense services...")
    # Attempt to connect to services on startup
    try:
        await redis_client.connect()
    except Exception as e:
        logger.error(f"Could not connect to Redis on startup: {e}")

    try:
        await redpanda_client.connect()
    except Exception as e:
        logger.error(f"Could not connect to Redpanda on startup: {e}")

    yield

    logger.info("Shutting down DocuSense services...")
    await redis_client.close()
    await redpanda_client.close()

app = FastAPI(
    title="DocuSense API",
    description="FastAPI Backend for DocuSense Production RAG Q&A System",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from app.worker import process_document

def process_document_fallback(file_path: str, filename: str):
    try:
        logger.info(f"Processing document via direct BackgroundTasks fallback: {filename}")
        process_document(file_path, filename)
    except Exception as err:
        logger.error(f"Background worker fallback failed for {filename}: {err}")

@app.post("/upload", status_code=202)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    filename = file.filename
    _, ext = os.path.splitext(filename.lower())
    if ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")
        
    task_id = str(uuid.uuid4())
    # Save the file to the shared uploads folder
    safe_filename = f"{task_id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
        
    # Enqueue embedding task in Redpanda, with direct BackgroundTasks fallback
    try:
        await redpanda_client.publish_ingestion_task(
            task_id=task_id,
            file_path=file_path,
            filename=filename
        )
    except Exception as e:
        logger.warning(f"Redpanda broker unavailable ({e}). Falling back to direct BackgroundTasks ingestion...")
        background_tasks.add_task(process_document_fallback, file_path, filename)
        
    return {
        "task_id": task_id,
        "status": "queued",
        "filename": filename,
        "message": "Document uploaded successfully and enqueued for processing."
    }

import json
from app.config import settings
from pydantic import BaseModel, Field
from app.services.hybrid_retriever import hybrid_retriever
from app.services.llm_service import llm_service

class QueryRequest(BaseModel):
    question: str = Field(..., description="The query question string")
    hybrid: bool = Field(default=True, description="Enable hybrid retrieval (dense + sparse BM25)")
    k: int = Field(default=5, description="Number of source chunks to retrieve")

@app.post("/query")
async def query_documents(request: QueryRequest, http_request: Request):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    client_ip = http_request.client.host
    
    # 1. Rate Limiting Check
    rate_ok = await redis_client.check_rate_limit(
        ip=client_ip,
        limit=settings.rate_limit_per_ip,
        window=settings.rate_limit_window_seconds
    )
    if not rate_ok:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before submitting another query."
        )
        
    cache_key = f"query_cache:{request.question}:{request.hybrid}:{request.k}"
    
    # 2. Redis Cache Lookup
    cached_payload = await redis_client.get(cache_key)
    if cached_payload:
        logger.info(f"[CACHE HIT] Serving response from Redis cache for key: '{cache_key}'")
        return json.loads(cached_payload)
        
    logger.info(f"[CACHE MISS] Fetching fresh response from RAG pipeline for key: '{cache_key}'")

    try:
        # 3. Retrieve matching chunks from index
        docs = hybrid_retriever.retrieve(
            query=request.question,
            hybrid=request.hybrid,
            k=request.k
        )
        
        # 4. Call completion model
        answer = llm_service.generate_answer(
            query=request.question,
            documents=docs
        )
        
        # 5. Format citations sources list
        sources_list = []
        for doc in docs:
            sources_list.append({
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page") or doc.metadata.get("section") or 1,
                "content": doc.page_content
            })
            
        response_payload = {
            "answer": answer,
            "sources": sources_list
        }
        
        # 6. Save response in Redis Cache
        await redis_client.setex(
            key=cache_key,
            seconds=settings.cache_ttl_seconds,
            value=json.dumps(response_payload)
        )
        
        return response_payload
    except Exception as e:
        logger.error(f"Error handling query request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal query processing error: {e}")

@app.get("/health")
async def health_check():
    redis_ok = await redis_client.ping()
    redpanda_ok = await redpanda_client.ping()

    is_healthy = redis_ok and redpanda_ok
    status_str = "ok" if is_healthy else "unhealthy"

    return {
        "status": status_str,
        "services": {
            "redis": "healthy" if redis_ok else "unhealthy",
            "redpanda": "healthy" if redpanda_ok else "unhealthy"
        }
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to DocuSense API. Check /health for system status."
    }
