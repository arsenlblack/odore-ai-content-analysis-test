# AI Content Analysis – System Diagram

## High-Level Architecture

Frontend
  |
  |  POST /v1/content-analysis/jobs
  |  GET  /v1/content-analysis/jobs/{job_id}
  v
API Gateway (FastAPI)
  |
  |  create job
  |  persist metadata
  v
Job Storage (DynamoDB / Postgres)
  |
  |  job_id
  |  payload
  |  status
  v
Message Queue (SQS / Broker)
  |
  |  async job message
  v
Background Workers
  |
  |-- Visual Moderation Worker
  |     - frame/image analysis
  |     - Sightengine API
  |
  |-- (future) Audio Worker
  |     - audio extraction
  |     - AssemblyAI STT
  |
  |-- (future) NLP Worker
  |     - Claude AI summary
  |
  v
Aggregation Layer
  |
  |  per-category scores
  |  weighted overall scores
  |  partial failure handling
  v
Job Storage (update results)
  |
  v
Frontend polls job status


## Key Design Principles

- Fully async, job-based processing
- External AI failures do not break the pipeline
- Each AI service is isolated behind a client abstraction
- Storage and queue are replaceable without code changes
- Human-readable summaries generated only after moderation completes


## Failure Modes & Handling

- AI provider timeout → retry or partial result
- Single media failure → job continues
- Queue failure → job fails fast
- Worker crash → job can be reprocessed (idempotent design)
