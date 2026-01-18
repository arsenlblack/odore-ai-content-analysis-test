"""
visual_moderation.py

Async worker responsible for visual content moderation.

Responsibilities:
- Consume content analysis jobs from the queue
- Analyze visual media using Sightengine
- Normalize raw moderation signals into safety scores
- Apply status thresholds and business rules
- Aggregate results across all media items
- Persist partial and final job results

This worker is designed to be idempotent and fault-tolerant.
"""

from typing import Dict, List, Any
from statistics import mean
from datetime import datetime

from app.services.sightengine_client import SightengineClient, SightengineError
from app.services.claude_summary_service import ClaudeSummaryService
from app.models.schemas import (
    MediaModerationResult,
    CategoryResult,
    VisualSafetyReport,
)
from app.storage.jobs_repository import JobsRepository


# -------------------------------------------------------------------
# Configuration / constants
# -------------------------------------------------------------------

VISUAL_CATEGORIES = {
    "adult_content": "nudity",
    "violence": "violence",
    "weapons": "weapon",
    "medical": "medical",
    "spoof_fake": "spoof",
}

SAFE_THRESHOLD = 90.0
WARNING_THRESHOLD = 70.0


# -------------------------------------------------------------------
# Scoring & status logic
# -------------------------------------------------------------------

def safety_status(score: float) -> str:
    """
    Convert a numeric safety score into a standardized status.
    """
    if score >= SAFE_THRESHOLD:
        return "Safe"
    if score >= WARNING_THRESHOLD:
        return "Warning"
    return "Unsafe"


def extract_category_score(payload: Dict[str, Any], model: str) -> float:
    """
    Extract a safety score for a given Sightengine model.

    Sightengine returns probabilities of *presence*.
    We convert them into *safety* percentages.
    """
    model_data = payload.get(model, {})
    if not model_data:
        raise KeyError(f"Missing model data: {model}")

    # Highest risk probability defines the category risk
    risk_probability = max(model_data.values())
    safety_score = (1.0 - risk_probability) * 100

    return round(safety_score, 2)


# -------------------------------------------------------------------
# Media processing
# -------------------------------------------------------------------

async def process_media_item(
    client: SightengineClient,
    media: Dict[str, Any],
) -> MediaModerationResult:
    """
    Analyze a single media item and return moderation results.

    Errors are captured per media item and do not fail the job.
    """

    categories: Dict[str, CategoryResult] = {}
    errors: List[str] = []

    try:
        payload = await client.analyze_image(media["url"])

        for category, model in VISUAL_CATEGORIES.items():
            try:
                score = extract_category_score(payload, model)
                categories[category] = CategoryResult(
                    score=score,
                    status=safety_status(score),
                )
            except Exception as exc:
                categories[category] = CategoryResult(
                    score=None,
                    status=None,
                )
                errors.append(
                    f"{category}: {str(exc)}"
                )

    except SightengineError as exc:
        errors.append(str(exc))

    return MediaModerationResult(
        media_id=media["media_id"],
        categories=categories,
        errors=errors,
    )


# -------------------------------------------------------------------
# Aggregation
# -------------------------------------------------------------------

def aggregate_visual_results(
    media_results: List[MediaModerationResult],
) -> VisualSafetyReport:
    """
    Aggregate visual moderation results across all media items.
    """

    aggregated: Dict[str, List[float]] = {
        category: []
        for category in VISUAL_CATEGORIES.keys()
    }

    for media in media_results:
        for category, result in media.categories.items():
            if result.score is not None:
                aggregated[category].append(result.score)

    final_categories: Dict[str, CategoryResult] = {}

    for category, scores in aggregated.items():
        if not scores:
            final_categories[category] = CategoryResult(
                score=None,
                status=None,
                explanation="No valid data available",
            )
            continue

        avg_score = round(mean(scores), 2)
        status = safety_status(avg_score)

        explanation = None
        if category == "spoof_fake" and avg_score < SAFE_THRESHOLD:
            explanation = (
                "Potential spoof or manipulated content detected. "
                "Manual review recommended."
            )

        final_categories[category] = CategoryResult(
            score=avg_score,
            status=status,
            explanation=explanation,
        )

    overall_scores = [
        result.score
        for result in final_categories.values()
        if result.score is not None
    ]

    overall_visual_score = (
        round(mean(overall_scores), 2)
        if overall_scores
        else None
    )

    return VisualSafetyReport(
        categories=final_categories,
        overall_visual_score=overall_visual_score,
    )


# -------------------------------------------------------------------
# Job orchestration
# -------------------------------------------------------------------

async def process_visual_moderation_job(
    job_id: str,
    payload: Dict[str, Any],
) -> None:
    """
    Main entry point for processing a visual moderation job.
    """

    await JobsRepository.update_status(
        job_id,
        status="IN_PROGRESS",
    )

    client = None
    claude = None

    client = SightengineClient()
    media_results: List[MediaModerationResult] = []

    try:
        for post in payload["posts"]:
            for media in post["media"]:
                if media["type"] != "image":
                    continue  # video frames handled elsewhere

                result = await process_media_item(client, media)
                media_results.append(result)

        visual_report = aggregate_visual_results(media_results)

        statuses = [r.status for r in visual_report.categories.values()]

        if "Unsafe" in statuses:
            job_status = "FAILED"
        elif "Warning" in statuses:
            job_status = "COMPLETED_WITH_WARNINGS"
        else:
            job_status = "COMPLETED"

        claude = ClaudeSummaryService()

        summary = await claude.generate_summary(
            analysis_results={
                "visual": visual_report.model_dump()
            }
        )

        await JobsRepository.update_results(
            job_id,
            results={
                "visual": visual_report.model_dump(),
                "media": [r.model_dump() for r in media_results],
                "summary": summary,
            },
            status=job_status,
            updated_at=datetime.utcnow(),
        )

    except Exception as exc:
        print(f"[ERROR] Job {job_id} failed: {exc}")
        await JobsRepository.update_status(
            job_id,
            status="FAILED",
            error=str(exc),
        )

    finally:
        if client:
            await client.close()
        if claude:
            await claude.close()
