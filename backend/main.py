"""FastAPI application — HTTP surface for the physics agent.

Endpoints
---------
GET  /                 service info
GET  /health           health check
GET  /api/providers    configured + available LLM providers
GET  /api/domains      supported physics domains + simulation types
POST /api/solve        full pipeline (classify -> extract -> solve -> explain)
POST /api/solve/quick  re-solve with new variable values (sliders, no LLM)
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents import PhysicsAgent
from config import get_settings
from providers import (
    LLMError,
    ProviderFactory,
    ProviderNotConfigured,
    SUPPORTED_PROVIDERS,
    UnknownProvider,
)
from solvers.sympy_solver import (
    DOMAIN_INFO,
    DOMAINS,
    SIMULATION_TYPES,
    MissingValueError,
    SolverError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("physics_agent.api")

settings = get_settings()

app = FastAPI(
    title="Physics Simulation Agent",
    description="Solves physics word problems symbolically and maps them to live simulations.",
    version="1.0.0",
)

# --- CORS --------------------------------------------------------------------
# Local dev origins are always allowed; production origins come from
# CORS_ORIGINS; Vercel preview/prod deployments are matched by regex.
_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:4173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_DEFAULT_ORIGINS + settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request models -----------------------------------------------------------

class SolveRequest(BaseModel):
    problem: str = Field(..., min_length=1, description="Physics problem in plain English.")
    provider: str | None = Field(None, description="Override the active LLM provider.")


class QuickSolveRequest(BaseModel):
    equation_id: str = Field(..., description="Equation id from a previous /api/solve response.")
    target: str = Field(..., description="Variable to solve for.")
    variables: dict[str, float] = Field(default_factory=dict, description="Updated known values.")


# --- Routes -------------------------------------------------------------------

@app.get("/")
def root() -> dict:
    return {
        "service": "Physics Simulation Agent",
        "version": app.version,
        "docs": "/docs",
        "endpoints": ["/health", "/api/providers", "/api/domains", "/api/solve", "/api/solve/quick"],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/providers")
def providers() -> dict:
    return {
        "providers": SUPPORTED_PROVIDERS,
        "available": ProviderFactory.available(settings),
        "default": settings.llm_provider,
    }


@app.get("/api/domains")
def domains() -> dict:
    return {
        "domains": [
            {"id": d, "name": DOMAIN_INFO[d]["name"], "description": DOMAIN_INFO[d]["description"]}
            for d in DOMAINS
        ],
        "simulations": SIMULATION_TYPES,
    }


@app.post("/api/solve")
async def solve(req: SolveRequest) -> dict:
    try:
        provider = ProviderFactory.create(req.provider, settings)
    except (ProviderNotConfigured, UnknownProvider) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    agent = PhysicsAgent(provider)
    try:
        return await agent.solve(req.problem)
    except MissingValueError as exc:
        raise HTTPException(status_code=422, detail=f"Missing information to solve: {exc}") from exc
    except SolverError as exc:
        raise HTTPException(status_code=422, detail=f"Could not solve: {exc}") from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error solving problem")
        raise HTTPException(status_code=500, detail="Internal error while solving the problem.") from exc


@app.post("/api/solve/quick")
def solve_quick(req: QuickSolveRequest) -> dict:
    try:
        return PhysicsAgent.resolve(req.equation_id, req.target, req.variables)
    except MissingValueError as exc:
        raise HTTPException(status_code=422, detail=f"Missing information: {exc}") from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown equation: {exc}") from exc
    except SolverError as exc:
        raise HTTPException(status_code=422, detail=f"Could not solve: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
