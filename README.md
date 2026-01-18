> This repository was created as part of a technical test assignment.
> It demonstrates system design and AI integration patterns.

# AI Content Analysis Service

Async backend service for analyzing Instagram/TikTok creator content using AI-powered moderation and summarization.

The system is designed as a production-ready, scalable pipeline that evaluates visual safety risks and produces structured results along with a human-readable summary.

---

## Features

* Async, job-based content analysis
* Visual safety moderation via Sightengine
* Category-level safety scoring and standardized statuses
* Partial failure tolerance (media-level isolation)
* Aggregated campaign-level safety scores
* Human-readable AI summary using Claude
* Clean separation of API, workers, storage, and AI integrations

---

## High-Level Flow

1. Frontend submits content for analysis
2. Backend creates an async job and returns `job_id`
3. Background workers analyze media content
4. Results are aggregated and stored
5. Claude AI generates a concise summary
6. Frontend polls job status and retrieves results

See `diagram.md` for architecture details.

---

## Tech Stack

* **Python 3.11**
* **FastAPI** – async REST API
* **httpx** – async HTTP client
* **Sightengine** – visual content moderation
* **Claude AI** – human-readable summarization
* **AWS-ready architecture** (SQS, DynamoDB, S3 abstractions)

---

## Project Structure

```
app/
 ├─ api/
 │   └─ jobs.py
 ├─ workers/
 │   └─ visual_moderation.py
 ├─ services/
 │   ├─ sightengine_client.py
 │   └─ claude_summary_service.py
 ├─ storage/
 │   └─ jobs_repository.py
 ├─ queue/
 │   ├─ publisher.py
 │   └─ consumer.py
 ├─ models/
 │   └─ schemas.py
 ├─ config.py
 └─ main.py
diagram.md
README.md
```

---

## Environment Variables

Required:

```bash
SIGHTENGINE_API_USER=your_user
SIGHTENGINE_API_SECRET=your_secret
CLAUDE_API_KEY=your_key
DATABASE_URL=postgres://...
```

Optional:

```bash
SIGHTENGINE_TIMEOUT=10
QUEUE_NAME=content-analysis-jobs
ENVIRONMENT=local
USE_FAKE_AI=true
```

---

## Running Locally

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start API server

```bash
uvicorn app.main:app --reload
```

### 3. Submit a job

```http
POST /v1/content-analysis/jobs
```

Example payload:

```json
{
  "campaign_id": "cmp_123",
  "creator_id": "tiktok_creator",
  "posts": [
    {
      "post_id": "post_1",
      "media": [
        {
          "media_id": "m1",
          "type": "image",
          "url": "https://example.com/image.jpg"
        }
      ]
    }
  ]
}
```

### 4. Poll job status

```http
GET /v1/content-analysis/jobs/{job_id}
```

---

## Job Statuses

* `PENDING` – job created
* `IN_PROGRESS` – processing started
* `COMPLETED` – all checks passed
* `COMPLETED_WITH_WARNINGS` – non-critical risks detected
* `FAILED` – unrecoverable error

---

## Partial Failure Handling

* Individual media failures do **not** fail the entire job
* Missing category scores are returned as `null`
* Errors are attached at the lowest possible scope (media-level)
* Aggregation proceeds with available data

---

## Optimization Notes

**Latency**

* Frame sampling for video
* Async HTTP calls
* Parallel media processing

**Cost Control**

* Media hash-based caching
* Early exit for safe-only content
* Configurable summary generation

**Future Improvements**

* Audio transcription via AssemblyAI
* Text moderation pipeline
* Weighted risk scoring across modalities
* Explainability layer for warnings

---

## Design Philosophy

This project prioritizes:

* Production realism over demo shortcuts
* Explicit data contracts
* Clear failure boundaries
* Replaceable infrastructure components
* Human-readable outputs for business stakeholders

---

## Disclaimer

This repository demonstrates system design and AI integration patterns.
It is not intended for direct production use without infrastructure hardening.
