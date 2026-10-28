from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.llm import targets
from app.routes.all_route import api_router

app = FastAPI(
    title="SAVIA - SDLC Assistant API",
    description="Ingests requirements, recommends SDLC agents, runs them and takes their output through review and approval.",
    version="3.0.0",
)

origins = settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_targets": [f"{t.provider}/{t.model}" for t in targets()],
        "auth_required": settings.AUTH_REQUIRED,
    }
