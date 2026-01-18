"""
jobs_repository.py

Persistence abstraction for content analysis jobs.

This repository intentionally hides the underlying storage
(DynamoDB, Postgres, etc.) behind a minimal async interface.
"""

from typing import Dict, Optional
from datetime import datetime


class JobsRepository:
    """
    Async repository for job persistence.

    NOTE:
    This is a simplified example. In production, this would be backed
    by DynamoDB, Aurora, or another durable store.
    """

    _STORE: Dict[str, Dict] = {}

    @classmethod
    async def create(cls, job: Dict) -> None:
        cls._STORE[job["job_id"]] = job

    @classmethod
    async def get(cls, job_id: str) -> Optional[Dict]:
        return cls._STORE.get(job_id)

    @classmethod
    async def update_status(
        cls,
        job_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        job = cls._STORE.get(job_id)
        if not job:
            return

        job["status"] = status
        job["updated_at"] = datetime.utcnow()

        if error:
            job.setdefault("errors", []).append(error)

    @classmethod
    async def update_results(
        cls,
        job_id: str,
        results: Dict,
        status: str,
        updated_at: datetime,
    ) -> None:
        job = cls._STORE.get(job_id)
        if not job:
            return

        job["results"] = results
        job["status"] = status
        job["updated_at"] = updated_at
