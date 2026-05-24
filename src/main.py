"""
Adaptive Multimedia Traffic Management System
Main Application Entry Point
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.config.settings import settings
from src.api import health, telemetry, qos, analytics, commands, alerts
from src.utils.logger import setup_logging

# Setup logging
setup_logging(settings.LOG_LEVEL, settings.LOG_FILE)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Startup
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Coordination Center for Adaptive Multimedia Traffic Management",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
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
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        }
    
    # API v1 router
    api_v1 = APIRouter(prefix="/api/v1", tags=["API v1"])
    
    # Include routers
    api_v1.include_router(health.router, tags=["Health"])
    api_v1.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetry"])
    api_v1.include_router(qos.router, prefix="/qos", tags=["QoS"])
    api_v1.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
    api_v1.include_router(commands.router, prefix="/commands", tags=["Commands"])
    api_v1.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
    
    app.include_router(api_v1)
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    logger.info(f"Application {settings.APP_NAME} configured successfully")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        workers=settings.SERVER_WORKERS,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
