"""API v1 라우터 집합."""

from fastapi import APIRouter

from app.api.v1.endpoints import agent, auth, bi, crm, datasets, scm

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(scm.router, prefix="/scm", tags=["scm"])
api_router.include_router(crm.router, prefix="/crm", tags=["crm"])
api_router.include_router(bi.router, prefix="/bi", tags=["bi"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
