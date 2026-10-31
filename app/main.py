import os

import httpx


from app.ingestion.diagnostics import diagnose_test_failure

from app.ingestion.qa import answer_question
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from fastapi.responses import FileResponse
from app.llm.client import generate_response
from app.ingestion.fix_validator import validate_fix as run_fix_validation

app = FastAPI(
    title="AI Engineering Copilot",
    version="0.1.0",
)

@app.get("/")
def home():
    html_path = Path(__file__).resolve().parent.parent / "static" / "index.html"
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

