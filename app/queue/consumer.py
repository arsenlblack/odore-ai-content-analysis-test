"""
consumer.py

Queue consumer entrypoint for visual moderation workers.
"""

import asyncio

from app.workers.visual_moderation import process_visual_moderation_job
from app.storage.jobs_repository import JobsRepository


async def consume(job_id: str) -> None:
    """
    Consume a single job message.
    """
    job = await JobsRepository.get(job_id)
    if not job:
        return

    await process_visual_moderation_job(
        job_id=job_id,
        payload=job["payload"],
    )
