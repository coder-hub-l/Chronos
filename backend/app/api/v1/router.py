from fastapi import APIRouter
from app.api.v1.workflows import router as workflows_router
from app.api.v1.queue import router as queue_router
from app.api.v1.workers import router as workers_router

api_v1_router = APIRouter()

api_v1_router.include_router(workflows_router, prefix="/workflows", tags=["Workflows"])
api_v1_router.include_router(queue_router, prefix="/queue", tags=["Redis Queue & DLQ"])
api_v1_router.include_router(workers_router, prefix="/workers", tags=["Worker Cluster"])
