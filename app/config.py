"""
config.py

Centralized configuration loaded from environment variables.

This module is intentionally simple:
- no dynamic logic
- no defaults that hide misconfiguration
"""

import os

USE_FAKE_AI = os.getenv("USE_FAKE_AI", "false") == "true"

def _required(name: str) -> str:
    if USE_FAKE_AI:
        return None
    
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


# -------------------------------------------------------------------
# Environment
# -------------------------------------------------------------------

ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# -------------------------------------------------------------------
# Sightengine
# -------------------------------------------------------------------

SIGHTENGINE_API_USER = _required("SIGHTENGINE_API_USER")
SIGHTENGINE_API_SECRET = _required("SIGHTENGINE_API_SECRET")
SIGHTENGINE_TIMEOUT = int(os.getenv("SIGHTENGINE_TIMEOUT", "10"))

# -------------------------------------------------------------------
# Cloude
# -------------------------------------------------------------------

CLAUDE_API_KEY = _required("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-opus-20240229"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# -------------------------------------------------------------------
# Storage (example: DynamoDB / Postgres abstraction)
# -------------------------------------------------------------------

DATABASE_URL = _required("DATABASE_URL")

# -------------------------------------------------------------------
# Queue
# -------------------------------------------------------------------

QUEUE_NAME = os.getenv("QUEUE_NAME", "content-analysis-jobs")
