
import os
import logging
import httpx

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.middleware.rate_limit import RateLimitMiddleware
from app.ingestion.diagnostics import diagnose_test_failure
from app.ingestion.qa import answer_question
from app.llm.client import generate_response
from app.ingestion.fix_validator import (
    validate_fix as run_fix_validation,
)
from app.ingestion.patch_generator import (
    generate_fix_patch,
    PatchGenerationError,
)
from app.ingestion.git_manager import (
    apply_validated_patch,
    GitOperationError,
)
from app.integrations.github_client import (
    create_pull_request,
    GitHubAPIError,
)


logger = logging.getLogger(__name__)

MAX_MESSAGE_CHARS = 16000

AI_ERROR_MESSAGE = (
    "I'm having trouble processing your request right now. "
    "Please try again in a moment."
)


app = FastAPI(
    title="AI Engineering Copilot",
    version="0.1.0",
)

app.add_middleware(
    RateLimitMiddleware,
    max_requests=100,
    window_seconds=100,
)


def feature_enabled(name):
    return os.getenv(
        name,
        "true",
    ).strip().lower() in ("true", "1", "yes", "on")


def log_ai_failure(endpoint, exc):
    # Never log prompts, credentials, provider names, or raw API errors.
    logger.error(
        "%s failed | Exception type: %s",
        endpoint,
        type(exc).__name__,
    )


def raise_ai_error(endpoint, exc):
    log_ai_failure(endpoint, exc)

    raise HTTPException(
        status_code=503,
        detail=AI_ERROR_MESSAGE,
    ) from exc


@app.get("/")
def home():
    html_path = (
        Path(__file__).resolve().parent.parent
        / "static"
        / "index.html"
    )
    return FileResponse(str(html_path))


@app.get("/chat-ui", include_in_schema=False)
def chat_ui():
    html_path = (
        Path(__file__).resolve().parent.parent
        / "static"
        / "chat.html"
    )
    return FileResponse(str(html_path))


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGE_CHARS,
    )


class DiagnoseRequest(BaseModel):
    test_name: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )
    error_output: str = Field(
        ...,
        min_length=1,
        max_length=12000,
    )


class FixValidationRequest(BaseModel):
    file_path: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )
    new_content: str = Field(
        ...,
        min_length=1,
        max_length=500000,
    )


class PatchGenerationRequest(BaseModel):
    test_name: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )
    error_output: str = Field(
        ...,
        min_length=1,
        max_length=12000,
    )
    file_path: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )


class CommitFixRequest(BaseModel):
    file_path: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )
    new_content: str = Field(
        ...,
        min_length=1,
        max_length=500000,
    )
    commit_message: str = Field(
        ...,
        min_length=1,
        max_length=200,
    )


class PullRequestRequest(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=256,
    )
    body: str = Field(
        ...,
        max_length=10000,
    )
    head: str = Field(
        ...,
        min_length=1,
        max_length=300,
    )
    base: str = Field(
        default="master",
        min_length=1,
        max_length=300,
    )


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ai-engineering-copilot",
    }


@app.post("/chat")
def chat(request: ChatRequest):
    logger.info("Chat request received.")

    try:
        answer = generate_response(request.message)

        return {
            "answer": answer,
            "model": "AI Assistant",
        }

    except (
        RuntimeError,
        httpx.HTTPStatusError,
        httpx.RequestError,
    ) as exc:
        raise_ai_error("/chat", exc)


@app.post("/ask")
def ask(request: ChatRequest):
    try:
        return answer_question(request.message)

    except FileNotFoundError as exc:
        logger.error("/ask failed | Index file not found.")
        raise HTTPException(
            status_code=500,
            detail="The knowledge index is currently unavailable.",
        ) from exc

    except (
        RuntimeError,
        httpx.HTTPStatusError,
        httpx.RequestError,
    ) as exc:
        raise_ai_error("/ask", exc)


@app.post("/diagnose")
def diagnose(request: DiagnoseRequest):
    try:
        return diagnose_test_failure(
            test_name=request.test_name,
            error_output=request.error_output,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        logger.error("/diagnose failed | Required file not found.")
        raise HTTPException(
            status_code=500,
            detail="The required knowledge index is unavailable.",
        ) from exc

    except (
        RuntimeError,
        httpx.HTTPStatusError,
        httpx.RequestError,
    ) as exc:
        raise_ai_error("/diagnose", exc)


@app.post("/validate-fix")
def validate_fix_endpoint(request: FixValidationRequest):
    if not feature_enabled("ENABLE_CODE_EXECUTION"):
        raise HTTPException(
            status_code=403,
            detail="Code execution is disabled on this deployment.",
        )

    try:
        return run_fix_validation(
            file_path=request.file_path,
            new_content=request.new_content,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.post("/generate-fix")
def generate_fix_endpoint(request: PatchGenerationRequest):
    try:
        return generate_fix_patch(
            test_name=request.test_name,
            error_output=request.error_output,
            file_path=request.file_path,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except PatchGenerationError as exc:
        raise_ai_error("/generate-fix", exc)

    except (
        RuntimeError,
        httpx.HTTPStatusError,
        httpx.RequestError,
    ) as exc:
        raise_ai_error("/generate-fix", exc)


@app.post("/commit-fix")
def commit_fix_endpoint(request: CommitFixRequest):
    if not feature_enabled("ENABLE_CODE_EXECUTION"):
        raise HTTPException(
            status_code=403,
            detail="Code execution is disabled on this deployment.",
        )

    try:
        return apply_validated_patch(
            file_path=request.file_path,
            new_content=request.new_content,
            commit_message=request.commit_message,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except GitOperationError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc


@app.post("/create-pull-request")
def create_pull_request_endpoint(
    request: PullRequestRequest,
):
    if not feature_enabled("ENABLE_GITHUB_AUTOMATION"):
        raise HTTPException(
            status_code=403,
            detail="GitHub automation is disabled on this deployment.",
        )

    try:
        return create_pull_request(
            title=request.title,
            body=request.body,
            head=request.head,
            base=request.base,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail="Connection Failed, Please Reload and Try again",
        ) from exc
