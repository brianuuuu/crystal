"""
Crystal System - FastAPI Main Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings
from app.storage.database import init_db
from app.api import public_router, auth_router
from app.scheduler.runner import scheduler_runner


# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    settings.LOG_DIR / "crystal_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    init_db()
    
    # Start scheduler
    scheduler_runner.start()
    logger.info("Application ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    scheduler_runner.stop()
    logger.info("Application stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Crystal - Sentiment Monitoring System for Quantitative Trading",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(public_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)


# Additional endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get(f"{settings.API_PREFIX}/jobs")
async def get_scheduled_jobs():
    """Get list of scheduled jobs."""
    return {
        "jobs": scheduler_runner.get_jobs()
    }


@app.post(f"{settings.API_PREFIX}/jobs/trigger")
async def trigger_job(job_id: str = "daily_crystal_job"):
    """Manually trigger a scheduled job."""
    success = scheduler_runner.run_job_now(job_id)
    if success:
        return {"success": True, "message": f"Job {job_id} triggered"}
    return {"success": False, "message": f"Job {job_id} not found"}


# Mount static files for frontend (will be served from web/dist after build)
# app.mount("/", StaticFiles(directory="app/web/dist", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
