
import os
import logging
import time

import httpx
from dotenv import load_dotenv


load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)

MAX_OUTPUT_TOKENS = 8192
MAX_CONTINUATIONS = 2

if not GEMINI_API_KEY:
    raise ValueError(
        "AI service credentials are not configured."
    )


def _generate_candidate(contents):
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
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "topP": 0.9,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=60.0,
        )

    except httpx.TimeoutException as exc:
        logger.error("AI service request timed out.")
        raise RuntimeError(
            "The AI service is temporarily unavailable."
        ) from exc

    except httpx.RequestError as exc:
        logger.error(
            "AI service connection failed | Error type: %s",
            type(exc).__name__,
        )
        raise RuntimeError(
            "The AI service is temporarily unavailable."
        ) from exc

    if response.status_code != 200:
        error_status = "UNKNOWN"

        try:
            error_data = response.json()
            error_status = (
                error_data.get("error", {}).get(
                    "status",
                    "UNKNOWN",
                )
            )
        except (ValueError, AttributeError):
            pass

        logger.error(
            "AI service request failed | HTTP status: %s | "
            "Error category: %s",
            response.status_code,
            error_status,
        )

        raise RuntimeError(
            "The AI service is temporarily unavailable."
        )

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("AI service returned invalid JSON.")
        raise RuntimeError(
            "The AI service returned an invalid response."
        ) from exc

    candidates = data.get("candidates", [])

    if not candidates:
        block_reason = (
            data.get("promptFeedback", {}).get(
                "blockReason",
                "UNKNOWN",
            )
        )

        logger.warning(
            "AI service returned no candidates | Reason: %s",
            block_reason,
        )

        raise RuntimeError(
            "The AI service could not produce an answer."
        )

    candidate = candidates[0]
    finish_reason = candidate.get("finishReason")

    parts = candidate.get(
        "content", {}
    ).get("parts", [])

    answer_parts = [
        part["text"]
        for part in parts
        if isinstance(part, dict) and "text" in part
    ]

    if not answer_parts:
        logger.warning(
            "AI service returned no text | Finish reason: %s",
            finish_reason,
        )
        raise RuntimeError(
            "The AI service returned an empty response."
        )

    return "\n".join(answer_parts), finish_reason


def generate_response(prompt: str) -> str:
    start_time = time.monotonic()

    logger.info("AI service request started.")

    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt}
            ],
        }
    ]

    answer_parts = []

    for attempt in range(MAX_CONTINUATIONS + 1):
        answer, finish_reason = _generate_candidate(contents)
        answer_parts.append(answer)

        if finish_reason != "MAX_TOKENS":
            elapsed = round(
                time.monotonic() - start_time,
                2,
            )

            logger.info(
                "AI service request completed | "
                "Duration: %s seconds | Continuations: %s",
                elapsed,
                attempt,
            )

            return "\n".join(answer_parts)

        if attempt < MAX_CONTINUATIONS:
            logger.warning(
                "AI response reached output limit. "
                "Starting continuation %s of %s.",
                attempt + 1,
                MAX_CONTINUATIONS,
            )

            contents.append(
                {
                    "role": "model",
                    "parts": [
                        {"text": answer}
                    ],
                }
            )

            contents.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Continue the previous answer from "
                                "exactly where it stopped. Do not "
                                "repeat or summarize the completed "
                                "part. Finish the remaining explanation."
                            )
                        }
                    ],
                }
            )

            continue

        logger.warning(
            "AI response reached the maximum continuation limit."
        )

    elapsed = round(
        time.monotonic() - start_time,
        2,
    )

    logger.info(
        "AI service request finished | Duration: %s seconds",
        elapsed,
    )

    return (
        "\n".join(answer_parts)
        + "\n\n"
        + "_This response may still be incomplete. "
        "Ask me to continue for the remaining part._"
    )
