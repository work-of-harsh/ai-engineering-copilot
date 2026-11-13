
import os
import logging
import time

import httpx
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite"
)

if not GEMINI_API_KEY:
    raise ValueError("AI service credentials are not configured.")


def generate_response(prompt: str) -> str:
    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.9,
            "maxOutputTokens": 2048
        }
    }

    start_time = time.monotonic()

    logger.info("AI service request started.")

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=60.0,
        )

    except httpx.TimeoutException:
        logger.error("AI service request timed out.")
        raise RuntimeError(
            "The AI service is temporarily unavailable."
        )

    except httpx.RequestError as exc:
        logger.error(
            "AI service connection failed. Error type: %s",
            type(exc).__name__
        )
        raise RuntimeError(
            "The AI service is temporarily unavailable."
        )

    if response.status_code != 200:
        error_status = "UNKNOWN"

        try:
            error_data = response.json()
            error_status = (
                error_data.get("error", {}).get("status", "UNKNOWN")
            )
        except (ValueError, AttributeError):
            pass

        elapsed = round(time.monotonic() - start_time, 2)

        logger.error(
            "AI service request failed | HTTP status: %s | "
            "Error category: %s | Duration: %s seconds",
            response.status_code,
            error_status,
            elapsed
        )

        raise RuntimeError(
            "The AI service is temporarily unavailable."
        )

    try:
        data = response.json()
        candidates = data.get("candidates", [])

        if not candidates:
            logger.warning(
                "AI service returned no answer candidates."
            )
            raise RuntimeError(
                "The AI service returned an empty response."
            )

        parts = candidates[0].get(
            "content", {}
        ).get("parts", [])

        answer_parts = [
            part["text"]
            for part in parts
            if isinstance(part, dict) and "text" in part
        ]

        if not answer_parts:
            logger.warning(
                "AI service response contained no text."
            )
            raise RuntimeError(
                "The AI service returned an empty response."
            )

        elapsed = round(time.monotonic() - start_time, 2)

        logger.info(
            "AI service request completed successfully | "
            "Duration: %s seconds",
            elapsed
        )

        return "\n".join(answer_parts)

    except (ValueError, KeyError, TypeError):
        logger.exception(
            "Failed to process the AI service response."
        )
        raise RuntimeError(
            "The AI service returned an invalid response."
        )
