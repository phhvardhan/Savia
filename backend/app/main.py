import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.all_route import api_router

app = FastAPI(
    title="SAVIA - AI-Powered SDLC Assistant API",
    description="Production-oriented SDLC Workflow & Orchestration Platform featuring SAVIA Recommendation Layer, MOM, Agile User Stories, DDL3 Design, and Test Agents.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Static files for React Frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    async def serve_react_frontend():
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Frontend index.html not found"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "platform": "SAVIA SDLC Assistant"}