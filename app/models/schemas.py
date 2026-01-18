"""
schemas.py

Pydantic models for the Content Analysis async pipeline.

This module defines:
- API input payloads
- Job creation responses
- Job status and result schemas

Design principles:
- Explicit over implicit
- Partial results are valid states
- Schemas reflect production realities, not happy-path demos
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal

from pydantic import BaseModel, Field, HttpUrl


# -------------------------------------------------------------------
# Input schemas
# -------------------------------------------------------------------

class MediaItem(BaseModel):
    """
    Single media unit belonging to a post.

    Supports images and videos.
    Videos are expected to be pre-processed into frames by workers.
    """

    media_id: str = Field(..., example="m1")
    type: Literal["image", "video"]
    url: HttpUrl


class PostItem(BaseModel):
    """
    Social media post containing one or more media items.
    """

    post_id: str = Field(..., example="post_123")
    media: List[MediaItem]


class ContentAnalysisRequest(BaseModel):
    """
    Payload sent by the frontend to initiate content analysis.

    This request is intentionally verbose to avoid implicit backend
    assumptions about content structure.
    """

    campaign_id: str = Field(..., example="cmp_456")
    creator_id: str = Field(..., example="tiktok_creator")
    posts: List[PostItem]


# -------------------------------------------------------------------
# Moderation result schemas
# -------------------------------------------------------------------

class CategoryResult(BaseModel):
    """
    Result of a single moderation category.

    score:
        Safety score expressed as percentage (0–100)

    status:
        One of: Safe, Warning, Unsafe
    """

    score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        example=92.4,
        description="Safety score as percentage",
    )
    status: Optional[Literal["Safe", "Warning", "Unsafe"]] = None
    explanation: Optional[str] = Field(
        None,
        description="Optional human-readable explanation or recommendation",
    )


class MediaModerationResult(BaseModel):
    """
    Moderation results for a single media item.

    Errors are media-scoped and do not fail the entire job.
    """

    media_id: str
    categories: Dict[str, CategoryResult]
    errors: List[str] = Field(default_factory=list)


class VisualSafetyReport(BaseModel):
    """
    Aggregated visual safety report across all analyzed media.
    """

    categories: Dict[str, CategoryResult]
    overall_visual_score: Optional[float] = Field(
        None,
        ge=0,
        le=100,
    )


# -------------------------------------------------------------------
# Job response schemas
# -------------------------------------------------------------------

class JobCreateResponse(BaseModel):
    """
    Response returned immediately after job creation.
    """

    job_id: str
    status: Literal["PENDING"]


class JobStatusResponse(BaseModel):
    """
    Response returned when querying job status.

    Results may be:
    - null (job not finished)
    - partial (completed with warnings)
    - complete
    """

    job_id: str
    status: Literal[
        "PENDING",
        "IN_PROGRESS",
        "COMPLETED",
        "COMPLETED_WITH_WARNINGS",
        "FAILED",
    ]

    results: Optional[Dict] = Field(
        None,
        description="Final or partial analysis results",
    )
    errors: List[str] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime
