"""
publisher.py

Async job publisher.

In production, this would publish messages to SQS, RabbitMQ, or Kafka.
"""

from typing import Dict
import asyncio
from app.queue.consumer import consume
from app.config import ENVIRONMENT

import logging
logger = logging.getLogger(__name__)


async def publish_job(job_id: str, payload: Dict) -> None:
    """
    Publish a job to the background processing queue.

    This example simulates async queue behavior.
    """
    # simulate network latency
    await asyncio.sleep(0.01)

    if ENVIRONMENT == "local":
        # Local-only: run worker in the same process
        logger.info("Local mode: executing job %s in-process", job_id)

        async def safe_consume(job_id: str):
            try:
                await consume(job_id)
            except Exception as e:
                print(f"[WORKER ERROR] job={job_id}: {e}")

        asyncio.create_task(safe_consume(job_id))
    else:
        # in real life: 
        # publish to real queue
        # send message to SQS / broker
        pass

    return
