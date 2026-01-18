"""
claude_summary_service.py

Service responsible for generating human-readable summaries
of analyzed content using Claude AI.

This service is called only after moderation results are available.
"""

from typing import Dict

import httpx

from app.config import (
    CLAUDE_API_KEY,
    CLAUDE_API_URL,
    CLAUDE_MODEL,
    USE_FAKE_AI,
)

class ClaudeSummaryService:
    """
    Thin async wrapper around Claude AI for content summarization.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=15)

    async def generate_summary(self, analysis_results: Dict) -> str:
        """
        Generate a concise, human-readable summary of content analysis.

        The summary includes:
        - Overall safety assessment
        - Key risk areas (if any)
        - Recommendation for review or approval
        """
        
        if USE_FAKE_AI:
            return (
                "Content appears generally safe. "
                "Minor spoof-related risks detected. "
                "Manual review is recommended."
            )

        prompt = self._build_prompt(analysis_results)

        response = await self._client.post(
            CLAUDE_API_URL,
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": CLAUDE_MODEL,
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            },
        )

        response.raise_for_status()
        payload = response.json()

        return payload["content"][0]["text"].strip()

    def _build_prompt(self, analysis_results: Dict) -> str:
        """
        Construct a deterministic prompt for Claude.
        """

        visual = analysis_results.get("visual", {})
        overall = visual.get("overall_visual_score")

        return f"""
You are an AI content safety assistant.

Given the following moderation results, produce a short summary
for a non-technical reviewer.

Requirements:
- Be concise (3–5 sentences)
- Mention any Warning or Unsafe categories
- Clearly state whether the content appears safe for campaign use

Moderation results:
{analysis_results}

Overall visual safety score: {overall}
"""

    async def close(self) -> None:
        await self._client.aclose()
