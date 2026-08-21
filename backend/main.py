import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.router import api_v1_router
from app.ws.stream import router as ws_router
from app.engine.worker_pool import WorkerPool
from app.engine.queue_engine import RedisQueueEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Chronos] Starting worker cluster and heartbeat reaper...")
    await WorkerPool.start()
    print("[Chronos] Engine fully operational.")
    yield
    print("[Chronos] Shutting down worker cluster...")
    await WorkerPool.stop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Chronos: Distributed Asynchronous Workflow Queue & DAG Execution Engine backed by Redis Sorted Sets.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

@app.get("/")
@app.get("/health")
def health_check():
    try:
        metrics = RedisQueueEngine.get_metrics_snapshot()
    except Exception:
        metrics = {}
    return {
        "status": "healthy",
        "engine": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "metrics": metrics
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
