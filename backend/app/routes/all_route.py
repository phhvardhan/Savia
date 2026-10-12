from fastapi import APIRouter

from .auth_route import router as auth_router
from .jira_agent_route import router as jira_agent_router
from .ingestion_route import router as ingestion_router
from .savia_route import router as savia_router
from .savia_dashboard_route import router as savia_dashboard_router
from .workflow_route import router as workflow_router
from .agent_route import router as agent_router

api_router = APIRouter()

# Core SAVIA Orchestration & Recommendation Layer
api_router.include_router(savia_router, prefix="/savia", tags=["SAVIA Recommendation Engine"])
api_router.include_router(savia_dashboard_router, prefix="/savia", tags=["SAVIA Live Dashboard"])
api_router.include_router(ingestion_router, prefix="/ingestion", tags=["Document & Audio Ingestion"])
api_router.include_router(workflow_router, prefix="/workflows", tags=["SDLC Workflow Sessions"])
api_router.include_router(agent_router, prefix="/agents", tags=["SDLC Agents Execution"])
api_router.include_router(jira_agent_router, prefix="/jira-agent", tags=["Jira Story Agent"])

# Essential Authentication Route
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])