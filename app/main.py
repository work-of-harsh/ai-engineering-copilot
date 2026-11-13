import os

import httpx


from app.ingestion.diagnostics import diagnose_test_failure

from app.ingestion.qa import answer_question
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from app.middleware.rate_limit import RateLimitMiddleware
from fastapi.responses import FileResponse
from app.llm.client import generate_response
from app.ingestion.fix_validator import validate_fix as run_fix_validation
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
        "true"
    ).strip().lower() in ("true", "1", "yes", "on")
@app.get("/")
def home():
    html_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
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
        max_length=8000,
    )

class DiagnoseRequest(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=300)
    error_output: str = Field(..., min_length=1, max_length=12000)

class FixValidationRequest(BaseModel):
    file_path: str = Field(
        ...,
        min_length=1,
        max_length=300
    )

    new_content: str = Field(
        ...,
        min_length=1,
        max_length=500000
    )
    
class PatchGenerationRequest(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=300)
    error_output: str = Field(..., min_length=1, max_length=12000)
    file_path: str = Field(..., min_length=1, max_length=300)    
    
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
    
    


@app.post("/ask")
def ask(request: ChatRequest):
    try:
        return answer_question(request.message)

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "An AI API returned an error. "
                "Check the model name, API key, and quota."
            ),
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to an AI API. Check your internet connection.",
        ) from exc

@app.post("/diagnose")
def diagnose(request: DiagnoseRequest):
    try:
        return diagnose_test_failure(
            test_name=request.test_name,
            error_output=request.error_output,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="AI provider returned an error."
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Unable to reach the AI provider."
        )

@app.post("/validate-fix")
def validate_fix_endpoint(request: FixValidationRequest):
    if not feature_enabled("ENABLE_CODE_EXECUTION"):
        raise HTTPException(
        status_code=403,
        detail="Code execution is disabled on this deployment.",
        )
    try:
        result = run_fix_validation(
            file_path=request.file_path,
            new_content=request.new_content
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )
@app.post("/generate-fix")
def generate_fix_endpoint(request: PatchGenerationRequest):
    try:
        return generate_fix_patch(
            test_name=request.test_name,
            error_output=request.error_output,
            file_path=request.file_path,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except PatchGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

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
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except GitOperationError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )
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
        )

    except GitHubAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )