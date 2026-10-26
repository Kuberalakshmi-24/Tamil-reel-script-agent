"""FastAPI REST service for the Tamil Reel Script Agent.

Enables seamless integration with React, Next.js, or mobile frontends.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from src.models import ScriptInput, FullDeliverable
from src.pipeline import TamilReelScriptPipeline
from src.config import LLM_PROVIDER

app = FastAPI(
    title="Tamil Reel Script Agent API",
    description="RESTful API for research-backed Tamil & Tanglish short-form video script generation.",
    version="1.0.0",
)

# Enable CORS for frontend clients (React, Next.js, Vite, mobile apps, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = TamilReelScriptPipeline()


class GenerateResponse(BaseModel):
    success: bool
    deliverable: FullDeliverable
    markdown: str


class RegenerateHookRequest(BaseModel):
    deliverable: FullDeliverable


class RegenerateCtaRequest(BaseModel):
    deliverable: FullDeliverable
    new_objective: Optional[str] = None


@app.get("/api/v1/health", tags=["System"])
def health_check():
    """Verify backend health and active LLM configuration."""
    return {
        "status": "healthy",
        "active_provider": LLM_PROVIDER,
        "service": "Tamil Reel Script Agent",
    }


@app.post(
    "/api/v1/scripts/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Script Generation"],
)
def generate_full_script(payload: ScriptInput):
    """Generate a complete 6-section research-backed script deliverable."""
    try:
        payload.mode = "full_script"
        deliverable = pipeline.run(payload)
        return GenerateResponse(
            success=True,
            deliverable=deliverable,
            markdown=deliverable.to_markdown(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline generation failed: {str(e)}",
        )


@app.post(
    "/api/v1/scripts/regenerate-hook",
    response_model=GenerateResponse,
    tags=["Regeneration"],
)
def regenerate_hook(payload: RegenerateHookRequest):
    """Regenerate 3 new hook options without re-searching or rewriting the body."""
    try:
        inp = payload.deliverable.input_data.model_copy(deep=True)
        inp.mode = "regenerate_hook"
        updated = pipeline.run(inp, previous_deliverable=payload.deliverable)
        return GenerateResponse(
            success=True,
            deliverable=updated,
            markdown=updated.to_markdown(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hook regeneration failed: {str(e)}",
        )


@app.post(
    "/api/v1/scripts/regenerate-cta",
    response_model=GenerateResponse,
    tags=["Regeneration"],
)
def regenerate_cta(payload: RegenerateCtaRequest):
    """Regenerate 3 new CTA options matching the objective."""
    try:
        inp = payload.deliverable.input_data.model_copy(deep=True)
        if payload.new_objective:
            inp.objective = payload.new_objective
        inp.mode = "regenerate_cta"
        updated = pipeline.run(inp, previous_deliverable=payload.deliverable)
        return GenerateResponse(
            success=True,
            deliverable=updated,
            markdown=updated.to_markdown(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CTA regeneration failed: {str(e)}",
        )
