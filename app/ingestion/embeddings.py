
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBEDDING_MODEL = "gemini-embedding-001"


def embed_text(text: str, task_type: str) -> list:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in .env")

    url = "https://generativelanguage.googleapis.com/v1beta/models/{}:embedContent".format(
    EMBEDDING_MODEL)

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "content": {
            "parts": [{"text": text}]
        },
        "taskType": task_type,
        "outputDimensionality": 768,
    }

    response = httpx.post(
        url,
        headers=headers,
        json=payload,
        timeout=60.0,
    )
    response.raise_for_status()

    data = response.json()
    return data["embedding"]["values"]
