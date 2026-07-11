"""
Module: Firewall Demo API Server
Purpose: FastAPI server for the live GPTL Build 1 firewall demo.

BoundState AI 2026
Classification: BoundState Proprietary

Co-Authored-By: Claude "Beth" <noreply@anthropic.com>
Co-Authored-By: Dr. Joseph Wilde, BoundState AI

Safety Critical: False

Serves the JSON pipeline API and (in production) the built React SPA under one
configurable public base path (default empty for local dev, ``/gptl`` in production),
mirroring the bouncer service layout. RESEARCH_ONLY: no persistence, no external calls,
read-only in-memory compute over the real governed engine.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from gptl.core.canonical import CanonicalizationError
from pipeline import PipelineResult, PipelineScenario, run_pipeline

BASE_PATH = os.environ.get("PUBLIC_BASE_PATH", "").rstrip("/")
API_PREFIX = f"{BASE_PATH}/api"
WEB_DIST = Path(__file__).resolve().parent.parent / "web" / "dist"

app = FastAPI(
    title="GPTL Build 1 firewall demo",
    summary="Runs the real governed capture pipeline; RESEARCH_ONLY.",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
)

# RESEARCH_ONLY demo: read-only compute, no credentials/cookies, so a permissive
# origin policy is acceptable and keeps local dev + same-domain proxying simple.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get(f"{API_PREFIX}/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gptl-firewall-demo"}


@app.post(f"{API_PREFIX}/pipeline/run", response_model=PipelineResult)
def pipeline_run(scenario: PipelineScenario) -> PipelineResult:
    """Run the real Build 1 capture pipeline for one scenario and return the stage trace."""
    try:
        return run_pipeline(scenario)
    except (ValueError, CanonicalizationError) as exc:
        # Out-of-range / non-canonical values fail closed as a clean 422, not a 500.
        raise HTTPException(status_code=422, detail=str(exc)) from exc


# In production the built SPA is copied to web/dist and served by this same process
# (guarded so local dev, which uses the Vite dev server, does not require it). Assets are
# mounted directly; the app shell is served for the base path and any client route WITHOUT
# a dir->dir/ redirect — behind the boundstate.ai proxy such a redirect would resolve to the
# upstream (Railway) host and bounce the visitor off the boundstate.ai domain.
if WEB_DIST.is_dir():
    app.mount(f"{BASE_PATH}/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get(f"{BASE_PATH}/favicon.svg", include_in_schema=False)
    def favicon() -> FileResponse:
        return FileResponse(WEB_DIST / "favicon.svg")

    @app.get(BASE_PATH or "/", include_in_schema=False)
    @app.get(f"{BASE_PATH}/{{path:path}}", include_in_schema=False)
    def spa(path: str = "") -> FileResponse:
        return FileResponse(WEB_DIST / "index.html")
