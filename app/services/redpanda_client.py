import logging
import asyncio
from aiokafka import AIOKafkaProducer
from app.config import settings

logger = logging.getLogger(__name__)

class RedpandaClient:
    def __init__(self):
        self.producer = None

    async def connect(self) -> None:
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.redpanda_bootstrap_servers
            )
            await self.producer.start()
            logger.info("Connected to Redpanda producer")

    async def close(self) -> None:
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Closed Redpanda connection")

    async def send_message(self, topic: str, key: bytes, value: bytes) -> None:
        if not self.producer:
            await self.connect()
        await self.producer.send_and_wait(topic, value=value, key=key)

    async def publish_ingestion_task(self, task_id: str, file_path: str, filename: str) -> None:
        import json
        payload = {
            "task_id": task_id,
            "file_path": file_path,
            "filename": filename
        }
        value = json.dumps(payload).encode("utf-8")
        key = task_id.encode("utf-8")
        logger.info(f"Publishing ingestion task to Redpanda: {payload}")
        await self.send_message(topic="ingestion-tasks", key=key, value=value)

    async def ping(self) -> bool:
        try:
            # Short-lived check for bootstrap connectivity
            temp_producer = AIOKafkaProducer(
                bootstrap_servers=settings.redpanda_bootstrap_servers
            )
            await asyncio.wait_for(temp_producer.start(), timeout=3.0)
            await temp_producer.stop()
            return True
        except Exception as e:
            logger.error(f"Redpanda connectivity check failed: {e}")
            return False

redpanda_client = RedpandaClient()
