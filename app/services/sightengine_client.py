"""
sightengine_client.py

Async client for interacting with the Sightengine API.

Responsibilities:
- Send media URLs to Sightengine for visual moderation
- Handle HTTP/network/API-level errors
- Return raw Sightengine responses for downstream processing

This client is intentionally thin.
Business logic (scoring, thresholds, aggregation) lives elsewhere.
"""

from typing import Dict, Any

import httpx

from app.config import (
    SIGHTENGINE_API_USER,
    SIGHTENGINE_API_SECRET,
    SIGHTENGINE_TIMEOUT,
    USE_FAKE_AI,
)


class SightengineError(Exception):
    """
    Raised when Sightengine API returns an error response
    or an unrecoverable network issue occurs.
    """
    pass


class SightengineClient:
    """
    Async client for Sightengine content moderation API.

    Designed for high-concurrency worker environments.
    """

    BASE_URL = "https://api.sightengine.com/1.0/check.json"

    def __init__(self) -> None:
        if USE_FAKE_AI:
            self.session = None
            return
        
        if not SIGHTENGINE_API_USER or not SIGHTENGINE_API_SECRET:
            raise RuntimeError(
                "Sightengine credentials are not configured"
            )

        self._client = httpx.AsyncClient(
            timeout=SIGHTENGINE_TIMEOUT,
        )

    async def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze a single image URL using Sightengine.

        Parameters
        ----------
        image_url : str
            Publicly accessible image URL.

        Returns
        -------
        dict
            Raw JSON response from Sightengine.

        Raises
        ------
        SightengineError
            If the API returns an error or the request fails.
        """
        
        if USE_FAKE_AI:
            return {
                "status": "success",
                "nudity": {"sexual_activity": 0.01},
                "violence": {"violence": 0.02},
                "weapon": {"firearm": 0.0},
                "medical": {"gore": 0.0},
                "spoof": {"fake": 0.15},
            }

        params = {
            "url": image_url,
            "models": "nudity,weapon,violence,medical,spoof",
            "api_user": SIGHTENGINE_API_USER,
            "api_secret": SIGHTENGINE_API_SECRET,
        }

        try:
            response = await self._client.get(
                self.BASE_URL,
                params=params,
            )
        except httpx.RequestError as exc:
            raise SightengineError(
                f"Network error while calling Sightengine: {exc}"
            ) from exc

        if response.status_code != 200:
            raise SightengineError(
                f"Sightengine returned HTTP {response.status_code}"
            )

        payload = response.json()

        if payload.get("status") != "success":
            raise SightengineError(
                f"Sightengine API error: {payload}"
            )

        return payload

    async def close(self) -> None:
        """
        Gracefully close the underlying HTTP client.
        """
        await self._client.aclose()
