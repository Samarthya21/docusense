import asyncio
import json
import os
import logging
from aiokafka import AIOKafkaConsumer
from app.config import settings
from app.services.document_parser import parse_document
from app.services.chunker import chunk_documents
from app.services.vector_store import save_vector_store
from app.services.redis_client import redis_client

# Setup worker-specific logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] worker: %(message)s"
)
logger = logging.getLogger(__name__)

async def run_worker():
    logger.info("Initializing DocuSense consumer worker...")
    
    # 1. Connect to Redis
    try:
        await redis_client.connect()
    except Exception as e:
        logger.error(f"Failed to connect to Redis on worker startup: {e}")
        
    consumer = None
    topic_name = "ingestion-tasks"
    
    # Retry loop to connect to Redpanda (wait for container to be ready)
    while True:
        try:
            consumer = AIOKafkaConsumer(
                topic_name,
                bootstrap_servers=settings.redpanda_bootstrap_servers,
                group_id="docusense-worker-group",
                auto_offset_reset="earliest"
            )
            await consumer.start()
            logger.info(f"Redpanda consumer started. Subscribed to topic: '{topic_name}'")
            break
        except Exception as e:
            logger.warning(
                f"Could not connect to Redpanda at {settings.redpanda_bootstrap_servers}. "
                f"Retrying in 5 seconds... Error: {e}"
            )
            if consumer:
                try:
                    await consumer.stop()
                except Exception:
                    pass
            await asyncio.sleep(5)

    try:
        async for message in consumer:
            logger.info(
                f"Consumed message - Topic: {message.topic}, "
                f"Partition: {message.partition}, Offset: {message.offset}"
            )
            try:
                task_data = json.loads(message.value.decode("utf-8"))
                task_id = task_data.get("task_id")
                file_path = task_data.get("file_path")
                filename = task_data.get("filename")
                
                logger.info(f"Processing ingestion task {task_id} for file: {filename}")
                
                if not os.path.exists(file_path):
                    logger.error(f"File not found at path: {file_path}")
                    continue
                
                # 1. Parse document page-by-page or section-by-section
                parsed_docs = parse_document(file_path, filename)
                
                # 2. Chunk document text
                chunks = chunk_documents(parsed_docs)
                
                # 3. Embed & Save to FAISS & backup
                save_vector_store(chunks)
                
                # Invalidate stale query caches since database is updated
                try:
                    await redis_client.clear_cache_pattern("query_cache:*")
                except Exception as ex:
                    logger.error(f"Failed to clear query cache: {ex}")
                
                # 4. Clean up temporary uploaded file from the shared uploads folder
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary upload file: {file_path}")
                    
                logger.info(f"Ingestion task {task_id} completed successfully.")
                
            except Exception as e:
                logger.error(f"Error processing ingestion message: {e}", exc_info=True)
                
    except asyncio.CancelledError:
        logger.info("Worker run task cancelled.")
    except Exception as e:
        logger.error(f"Error in consumer execution loop: {e}")
    finally:
        if consumer:
            logger.info("Stopping Redpanda consumer worker...")
            await consumer.stop()
            logger.info("Redpanda consumer worker stopped.")
        # Close Redis connection
        await redis_client.close()

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped manually.")
