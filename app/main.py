import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.llm.client import generate_response


app = FastAPI(
    title="AI Engineering Copilot",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=8000,
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ai-engineering-copilot",
    }


@app.post("/chat")
def chat(request: ChatRequest):
    try:
        answer = generate_response(request.message)

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini API returned an error. "
                "Check your API key, model name, and quota."
            ),
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to Gemini. "
                "Check your internet connection."
            ),
        ) from exc

    return {
        "answer": answer,
        "model": os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite",
        ),
    }