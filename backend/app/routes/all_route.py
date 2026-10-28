from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from .agent_route import router as agent_router
from .auth_route import router as auth_router
from .ingestion_route import router as ingestion_router
from .jira_agent_route import router as jira_agent_router
from .savia_dashboard_route import router as savia_dashboard_router
from .savia_route import router as savia_router
from .workflow_route import fonts_router, router as workflow_router

api_router = APIRouter()
protected = [Depends(get_current_user)]

api_router.include_router(savia_router, prefix="/savia", tags=["SAVIA Recommendation Engine"], dependencies=protected)
api_router.include_router(savia_dashboard_router, prefix="/savia", tags=["SAVIA Live Dashboard"], dependencies=protected)
api_router.include_router(ingestion_router, prefix="/ingestion", tags=["Document & Audio Ingestion"], dependencies=protected)
api_router.include_router(workflow_router, prefix="/workflows", tags=["SDLC Workflow Sessions"], dependencies=protected)
api_router.include_router(agent_router, prefix="/agents", tags=["SDLC Agents Execution"], dependencies=protected)
api_router.include_router(jira_agent_router, prefix="/jira-agent", tags=["Jira Story Agent"], dependencies=protected)
api_router.include_router(fonts_router, prefix="/workflows", tags=["SDLC Workflow Sessions"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
