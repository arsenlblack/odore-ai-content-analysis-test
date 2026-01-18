"""
jobs.py

Async API endpoints for content analysis jobs.

Responsibilities:
- Accept content analysis requests from the frontend
- Create async analysis jobs
- Persist job metadata and initial status
- Enqueue jobs for background processing
- Expose job status and results retrieval endpoints

This module does NOT perform any heavy processing.
All AI-related work is delegated to background workers.
"""

from uuid import uuid4
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    ContentAnalysisRequest,
    JobCreateResponse,
    JobStatusResponse,
)
from app.storage.jobs_repository import JobsRepository
from app.queue.publisher import publish_job

router = APIRouter(prefix="/v1/content-analysis", tags=["Content Analysis"])


@router.post(
    "/jobs",
    response_model=JobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_content_analysis_job(
    payload: ContentAnalysisRequest,
) -> JobCreateResponse:
    """
    Create a new async content analysis job.

    Flow:
    1. Validate incoming payload
    2. Create a job record with status = PENDING
    3. Publish job to background queue
    4. Return job_id to the caller

    This endpoint is intentionally fast and non-blocking.
    No AI calls are performed synchronously.
    """

    job_id = f"job_{uuid4().hex}"
    now = datetime.utcnow()

    job_record = {
        "job_id": job_id,
        "campaign_id": payload.campaign_id,
        "creator_id": payload.creator_id,
        "status": "PENDING",
        "created_at": now,
        "payload": payload.model_dump(),
        "updated_at": now,
        "results": None,
        "errors": [],
    }

    await JobsRepository.create(job_record)

    try:
        await publish_job(
            job_id=job_id,
            payload=payload.model_dump(),
        )
    except Exception as exc:
        # Queue failure should surface immediately
        await JobsRepository.update_status(
            job_id,
            status="FAILED",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to enqueue analysis job",
        )

    return JobCreateResponse(
        job_id=job_id,
        status="PENDING",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
)
async def get_content_analysis_job(job_id: str) -> JobStatusResponse:
    """
    Retrieve the current status and results of a content analysis job.

    Possible job statuses:
    - PENDING
    - IN_PROGRESS
    - COMPLETED
    - COMPLETED_WITH_WARNINGS
    - FAILED

    Results may be partially available if the job is still in progress
    or completed with warnings.
    """

    job = await JobsRepository.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        results=job.get("results"),
        errors=job.get("errors", []),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )
